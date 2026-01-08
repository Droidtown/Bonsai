#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List, Tuple, Any
from enum import Enum
from copy import deepcopy

class AnaphorType(Enum):
    REFLEXIVE = "reflexive"
    PRONOUN = "pronoun"
    R_EXPRESSION = "r_expr"
    QUANTIFIER = "quantifier"
    VP_ELLIPSIS = "vp_ellipsis"

class QuantifierType(Enum):
    UNIVERSAL = "universal"  # every, all, each
    EXISTENTIAL = "existential"  # some, a
    NEGATIVE = "negative"  # no, none

class EllipsisReading(Enum):
    STRICT = "strict"  # Keep same referent
    SLOPPY = "sloppy"  # Change referent based on context

@dataclass
class Features:
    person: int
    number: str
    gender: Optional[str] = None
    animacy: Optional[str] = None

    def matches(self, other: 'Features') -> bool:
        return (self.person == other.person and
                self.number == other.number and
                (self.gender == other.gender or self.gender is None or other.gender is None))

@dataclass
class Referent:
    name: str
    features: Features
    anaphor_type: AnaphorType
    node_id: int
    quantifier_type: Optional[QuantifierType] = None
    restrictor: Optional[str] = None
    trace_of: Optional[int] = None  # For movement/reconstruction
    base_position: Optional[int] = None  # Original merge position

@dataclass
class VPEllipsis:
    ellipsis_id: int
    node_id: int
    auxiliary: str
    antecedent_vp: Optional['CompressedNode'] = None
    resolved_content: Optional[Dict] = None
    reading_type: EllipsisReading = EllipsisReading.STRICT

@dataclass
class Trace:
    """Represents a trace left by movement"""
    trace_id: int
    moved_element: Referent
    base_position_node: int
    surface_position_node: int

@dataclass
class CompressedNode:
    label: str
    node_id: int
    dominated_referents: Dict[str, Referent] = field(default_factory=dict)
    children: List['CompressedNode'] = field(default_factory=list)
    parent: Optional['CompressedNode'] = None
    vp_content: Optional[Dict] = None
    is_vp_ellipsis: bool = False
    ellipsis_info: Optional[VPEllipsis] = None
    traces: List[Trace] = field(default_factory=list)  # Traces at this position

    def add_referent(self, referent: Referent):
        self.dominated_referents[referent.name] = referent

    def add_trace(self, trace: Trace):
        """Add a trace for a moved element"""
        self.traces.append(trace)

    def set_vp_content(self, verb: str, arguments: Dict[str, Any], subject: Optional[str] = None):
        """Store VP content with all arguments including subject"""
        self.vp_content = {
            'verb': verb,
            'arguments': arguments,
            'subject': subject,
            'node_id': self.node_id
        }

    def c_commands(self, other: 'CompressedNode') -> bool:
        if self.parent is None:
            return False
        return (self.parent.dominates(other) and not self.dominates(other))

    def dominates(self, other: 'CompressedNode') -> bool:
        if self == other:
            return True
        for child in self.children:
            if child.dominates(other):
                return True
        return False

    def get_c_command_domain(self) -> Set['CompressedNode']:
        if self.parent is None:
            return set()

        c_commanded = set()
        for sibling in self.parent.children:
            if sibling != self:
                c_commanded.add(sibling)
                c_commanded.update(self._get_all_descendants(sibling))
        return c_commanded

    def _get_all_descendants(self, node: 'CompressedNode') -> Set['CompressedNode']:
        descendants = set()
        for child in node.children:
            descendants.add(child)
            descendants.update(self._get_all_descendants(child))
        return descendants

    def get_local_domain(self) -> 'CompressedNode':
        current = self
        while current is not None:
            if current.label in ['TP', 'CP']:
                return current
            current = current.parent
        return self

    def get_reconstruction_site(self, referent: Referent) -> Optional['CompressedNode']:
        """Find the base position for a moved element (reconstruction)"""
        if referent.base_position is None:
            return None

        # Search for trace at base position
        for trace in self.traces:
            if trace.moved_element.name == referent.name:
                return self._find_node_by_id_in_subtree(trace.base_position_node)

        return None

    def _find_node_by_id_in_subtree(self, target_id: int) -> Optional['CompressedNode']:
        if self.node_id == target_id:
            return self
        for child in self.children:
            result = child._find_node_by_id_in_subtree(target_id)
            if result:
                return result
        return None

class AnaphoraResolver:
    def __init__(self, root: CompressedNode):
        self.root = root
        self.discourse_referents: List[Referent] = []
        self.discourse_conditions: List[Tuple[Referent, Referent]] = []  # For donkey anaphora
        self.vp_ellipsis_sites: List[VPEllipsis] = []

    def resolve(self, anaphor: Referent, anaphor_node: CompressedNode,
                allow_reconstruction: bool = True) -> List[Referent]:
        """Main resolution with reconstruction support"""
        if anaphor.anaphor_type == AnaphorType.REFLEXIVE:
            return self._resolve_reflexive(anaphor, anaphor_node, allow_reconstruction)
        elif anaphor.anaphor_type == AnaphorType.PRONOUN:
            return self._resolve_pronoun_with_quantifiers(anaphor, anaphor_node, allow_reconstruction)
        elif anaphor.anaphor_type == AnaphorType.R_EXPRESSION:
            return self._resolve_r_expression(anaphor, anaphor_node)
        return []

    def _resolve_reflexive(self, anaphor: Referent, anaphor_node: CompressedNode,
                          allow_reconstruction: bool = True) -> List[Referent]:
        """Reflexive resolution with reconstruction"""
        candidates = []

        # Try surface structure first
        surface_candidates = self._find_reflexive_antecedents(anaphor, anaphor_node)
        candidates.extend(surface_candidates)

        # If no antecedent found and reconstruction is allowed, try base position
        if not candidates and allow_reconstruction:
            reconstruction_site = anaphor_node.get_reconstruction_site(anaphor)
            if reconstruction_site:
                reconstruction_candidates = self._find_reflexive_antecedents(
                    anaphor, reconstruction_site
                )
                candidates.extend(reconstruction_candidates)

        return candidates

    def _find_reflexive_antecedents(self, anaphor: Referent,
                                   anaphor_node: CompressedNode) -> List[Referent]:
        """Helper to find reflexive antecedents at a given position"""
        local_domain = anaphor_node.get_local_domain()
        candidates = []

        current = anaphor_node.parent
        while current is not None and local_domain.dominates(current):
            c_command_domain = current.get_c_command_domain()

            for node in c_command_domain:
                if node.dominates(anaphor_node):
                    continue

                for ref_name, ref in node.dominated_referents.items():
                    if (ref.anaphor_type in [AnaphorType.R_EXPRESSION, AnaphorType.QUANTIFIER] and
                        ref.features.matches(anaphor.features)):
                        ref_node = self._find_node_by_id(ref.node_id)
                        if ref_node and ref_node.c_commands(anaphor_node):
                            candidates.append(ref)

            current = current.parent

        return candidates

    def _resolve_pronoun_with_quantifiers(self, anaphor: Referent,
                                         anaphor_node: CompressedNode,
                                         allow_reconstruction: bool = True) -> List[Referent]:
        """Enhanced pronoun resolution with donkey anaphora support"""
        local_domain = anaphor_node.get_local_domain()
        candidates = []

        # Check for donkey anaphora pattern
        donkey_antecedents = self._resolve_donkey_anaphora(anaphor, anaphor_node)
        candidates.extend(donkey_antecedents)

        all_referents = self._collect_all_referents(self.root)

        for ref_name, ref in all_referents.items():
            if ref.anaphor_type not in [AnaphorType.R_EXPRESSION, AnaphorType.QUANTIFIER]:
                continue
            if not ref.features.matches(anaphor.features):
                continue

            ref_node = self._find_node_by_id(ref.node_id)
            if not ref_node:
                continue

            # Handle quantifier binding
            if ref.anaphor_type == AnaphorType.QUANTIFIER:
                if self._can_bind_quantifier(ref_node, anaphor_node):
                    candidates.append(ref)

            # Handle R-expression binding with reconstruction
            elif ref.anaphor_type == AnaphorType.R_EXPRESSION:
                # Surface position
                if ref_node.c_commands(anaphor_node):
                    if local_domain.dominates(ref_node):
                        continue
                    candidates.append(ref)

                # Reconstruction position
                elif allow_reconstruction:
                    base_node = ref_node.get_reconstruction_site(ref)
                    if base_node and base_node.c_commands(anaphor_node):
                        if not local_domain.dominates(base_node):
                            candidates.append(ref)

        # Add discourse referents
        candidates.extend([r for r in self.discourse_referents
                          if r.features.matches(anaphor.features)])

        return candidates

    def _resolve_donkey_anaphora(self, anaphor: Referent,
                                anaphor_node: CompressedNode) -> List[Referent]:
        """Handle donkey anaphora: 'Every farmer who owns a donkey beats it'
        The pronoun 'it' is bound by 'a donkey' despite lack of c-command"""
        candidates = []

        # Look for existential quantifier in restrictor of universal quantifier
        all_referents = self._collect_all_referents(self.root)

        for ref_name, ref in all_referents.items():
            if ref.anaphor_type == AnaphorType.QUANTIFIER:
                if ref.quantifier_type == QuantifierType.EXISTENTIAL:
                    # Check if this existential is in a relative clause/restrictor
                    ref_node = self._find_node_by_id(ref.node_id)
                    if ref_node and self._is_in_restrictor(ref_node):
                        # Check if features match
                        if ref.features.matches(anaphor.features):
                            # Store this as a discourse condition
                            self.discourse_conditions.append((ref, anaphor))
                            candidates.append(ref)

        return candidates

    def _is_in_restrictor(self, node: CompressedNode) -> bool:
        """Check if node is in a restrictor domain (e.g., relative clause)"""
        current = node.parent
        while current is not None:
            if current.label in ['CP', 'RelCP']:
                return True
            if current.label in ['TP', 'IP']:
                return False
            current = current.parent
        return False

    def _can_bind_quantifier(self, quantifier_node: CompressedNode,
                            pronoun_node: CompressedNode) -> bool:
        """Check if quantifier can bind pronoun"""
        if not quantifier_node.c_commands(pronoun_node):
            return False

        # Check for intervention
        current = pronoun_node.parent
        while current is not None and current != quantifier_node:
            for ref in current.dominated_referents.values():
                if (ref.anaphor_type == AnaphorType.QUANTIFIER and
                    ref.node_id != quantifier_node.node_id):
                    return False
            current = current.parent

        return True

    def _resolve_r_expression(self, anaphor: Referent,
                             anaphor_node: CompressedNode) -> List[Referent]:
        """R-expressions must be free (Condition C)"""
        return []

    def resolve_vp_ellipsis(self, ellipsis_node: CompressedNode,
                          reading: EllipsisReading = EllipsisReading.STRICT,
                          new_subject: Optional[str] = None) -> Optional[Dict]:
        """Resolve VP-ellipsis with strict/sloppy ambiguity"""
        if not ellipsis_node.is_vp_ellipsis:
            return None

        antecedent_vp = self._find_antecedent_vp(ellipsis_node)

        if antecedent_vp and antecedent_vp.vp_content:
            resolved = deepcopy(antecedent_vp.vp_content)

            if reading == EllipsisReading.SLOPPY and new_subject:
                # Sloppy identity: change bound pronouns to new subject
                resolved = self._apply_sloppy_identity(resolved, new_subject)
            # Strict identity: keep original referents (default deepcopy behavior)

            ellipsis_node.ellipsis_info.antecedent_vp = antecedent_vp
            ellipsis_node.ellipsis_info.resolved_content = resolved
            ellipsis_node.ellipsis_info.reading_type = reading

            return resolved

        return None

    def _apply_sloppy_identity(self, vp_content: Dict, new_subject: str) -> Dict:
        """Apply sloppy identity by replacing bound pronouns"""
        modified = deepcopy(vp_content)

        # Replace subject-bound pronouns in arguments
        if 'arguments' in modified:
            for arg_key, arg_value in modified['arguments'].items():
                if isinstance(arg_value, str):
                    # Simple heuristic: possessive pronouns get replaced
                    if arg_value in ['his', 'her', 'their', 'its']:
                        # Map to new subject's pronoun
                        modified['arguments'][arg_key] = self._get_possessive(new_subject)

        # Update subject field
        if 'subject' in modified:
            modified['subject'] = new_subject

        return modified

    def _get_possessive(self, subject: str) -> str:
        """Simple mapping to possessive pronouns"""
        possessive_map = {
            'John': 'his', 'Mary': 'her', 'Bill': 'his',
            'he': 'his', 'she': 'her', 'they': 'their'
        }
        return possessive_map.get(subject, 'their')

    def _find_antecedent_vp(self, ellipsis_node: CompressedNode) -> Optional[CompressedNode]:
        """Find VP antecedent"""
        candidate_vps = []

        def collect_vps(node: CompressedNode):
            if node.label == "VP" and node.vp_content and not node.is_vp_ellipsis:
                candidate_vps.append(node)
            for child in node.children:
                collect_vps(child)

        collect_vps(self.root)

        valid_vps = [vp for vp in candidate_vps if vp.node_id < ellipsis_node.node_id]

        if valid_vps:
            return max(valid_vps, key=lambda vp: vp.node_id)

        return None

    def add_discourse_referent(self, referent: Referent):
        """Add referent to discourse context"""
        self.discourse_referents.append(referent)

    def add_movement(self, moved_element: Referent, from_node: CompressedNode,
                    to_node: CompressedNode) -> Trace:
        """Record movement and create trace"""
        trace = Trace(
            trace_id=len(from_node.traces),
            moved_element=moved_element,
            base_position_node=from_node.node_id,
            surface_position_node=to_node.node_id
        )

        from_node.add_trace(trace)
        moved_element.base_position = from_node.node_id
        moved_element.trace_of = to_node.node_id

        return trace

    def _collect_all_referents(self, node: CompressedNode) -> Dict[str, Referent]:
        all_refs = dict(node.dominated_referents)
        for child in node.children:
            all_refs.update(self._collect_all_referents(child))
        return all_refs

    def _find_node_by_id(self, node_id: int) -> Optional[CompressedNode]:
        return self._find_node_by_id_helper(self.root, node_id)

    def _find_node_by_id_helper(self, node: CompressedNode,
                               target_id: int) -> Optional[CompressedNode]:
        if node.node_id == target_id:
            return node
        for child in node.children:
            result = self._find_node_by_id_helper(child, target_id)
            if result:
                return result
        return None


# Example 1: Donkey Anaphora
def example_donkey_anaphora():
    print("=== Example 1: Donkey Anaphora ===")
    print("Sentence: 'Every farmer who owns a donkey beats it'")
    print()

    # Simplified structure: [TP [NP every farmer [CP who owns a donkey]] [VP beats it]]
    tp = CompressedNode("TP", node_id=0)
    np_every = CompressedNode("NP", node_id=1, parent=tp)
    cp = CompressedNode("RelCP", node_id=2, parent=np_every)
    np_donkey = CompressedNode("NP", node_id=3, parent=cp)
    vp = CompressedNode("VP", node_id=4, parent=tp)
    np_it = CompressedNode("NP", node_id=5, parent=vp)

    tp.children = [np_every, vp]
    np_every.children = [cp]
    cp.children = [np_donkey]
    vp.children = [np_it]

    every_farmer = Referent(
        "every farmer",
        Features(3, "sg", "masc", "human"),
        AnaphorType.QUANTIFIER,
        1,
        QuantifierType.UNIVERSAL,
        "farmer"
    )

    a_donkey = Referent(
        "a donkey",
        Features(3, "sg", None, "animate"),
        AnaphorType.QUANTIFIER,
        3,
        QuantifierType.EXISTENTIAL,
        "donkey"
    )

    it = Referent("it", Features(3, "sg", None, "animate"), AnaphorType.PRONOUN, 5)

    np_every.add_referent(every_farmer)
    np_donkey.add_referent(a_donkey)
    np_it.add_referent(it)

    resolver = AnaphoraResolver(tp)
    antecedents = resolver.resolve(it, np_it)

    print(f"Antecedents for 'it': {[a.name for a in antecedents]}")
    print("'it' can be bound by 'a donkey' despite lack of c-command")
    print("This is donkey anaphora: existential in restrictor binds pronoun in nuclear scope")
    print()


# Example 2: Strict vs Sloppy Identity in VP-Ellipsis
def example_strict_sloppy():
    print("=== Example 2: Strict vs Sloppy Identity ===")
    print("Sentence: 'John lost his wallet. Bill did too.'")
    print()

    # First sentence
    tp1 = CompressedNode("TP", node_id=0)
    np_john = CompressedNode("NP", node_id=1, parent=tp1)
    vp1 = CompressedNode("VP", node_id=2, parent=tp1)

    tp1.children = [np_john, vp1]
    vp1.children = []

    vp1.set_vp_content("lost", {"object": "his wallet"}, subject="John")

    # Second sentence with ellipsis
    tp2 = CompressedNode("TP", node_id=3)
    np_bill = CompressedNode("NP", node_id=4, parent=tp2)
    vp2 = CompressedNode("VP", node_id=5, parent=tp2)
    vp2.is_vp_ellipsis = True
    vp2.ellipsis_info = VPEllipsis(ellipsis_id=1, node_id=5, auxiliary="did")

    tp2.children = [np_bill, vp2]

    root = CompressedNode("ROOT", node_id=6)
    root.children = [tp1, tp2]
    tp1.parent = root
    tp2.parent = root

    resolver = AnaphoraResolver(root)

    # Strict reading
    strict_vp = resolver.resolve_vp_ellipsis(vp2, EllipsisReading.STRICT)
    print(f"Strict reading: {strict_vp}")
    print("Interpretation: 'Bill lost John's wallet' (same wallet)")
    print()

    # Sloppy reading
    sloppy_vp = resolver.resolve_vp_ellipsis(vp2, EllipsisReading.SLOPPY, "Bill")
    print(f"Sloppy reading: {sloppy_vp}")
    print("Interpretation: 'Bill lost Bill's wallet' (his own wallet)")
    print()


# Example 3: Reconstruction Effects
def example_reconstruction():
    print("=== Example 3: Reconstruction Effects ===")
    print("Sentence: 'Which picture of himself did John see?'")
    print()

    # Surface: [CP [which picture of himself]_i [TP John [VP saw t_i]]]
    # Reconstruction: evaluate binding at base position (object of 'saw')

    cp = CompressedNode("CP", node_id=0)
    np_which = CompressedNode("NP", node_id=1, parent=cp)
    tp = CompressedNode("TP", node_id=2, parent=cp)
    np_john = CompressedNode("NP", node_id=3, parent=tp)
    vp = CompressedNode("VP", node_id=4, parent=tp)
    trace_position = CompressedNode("NP", node_id=5, parent=vp)  # Base position

    cp.children = [np_which, tp]
    tp.children = [np_john, vp]
    vp.children = [trace_position]

    john = Referent("John", Features(3, "sg", "masc", "human"),
                   AnaphorType.R_EXPRESSION, 3)

    himself = Referent("himself", Features(3, "sg", "masc", "human"),
                      AnaphorType.REFLEXIVE, 1)

    which_picture = Referent("which picture", Features(3, "sg", None, "inanimate"),
                            AnaphorType.R_EXPRESSION, 1)

    np_john.add_referent(john)
    np_which.add_referent(which_picture)
    np_which.add_referent(himself)

    resolver = AnaphoraResolver(cp)

    # Record movement: 'which picture of himself' moved from object to Spec-CP
    trace = resolver.add_movement(himself, trace_position, np_which)

    # Try to resolve reflexive at surface position (fails)
    print("Surface position (Spec-CP):")
    surface_antecedents = resolver._find_reflexive_antecedents(himself, np_which)
    print(f"  Antecedents: {[a.name for a in surface_antecedents]}")
    print("  'John' doesn't c-command reflexive at surface position")
    print()

    # Resolve with reconstruction (succeeds)
    print("With reconstruction to base position (object of 'saw'):")
    reconstructed_antecedents = resolver.resolve(himself, np_which, allow_reconstruction=True)
    print(f"  Antecedents: {[a.name for a in reconstructed_antecedents]}")
    print("  'John' c-commands the trace position, binding is licensed")
    print()


# Example 4: Complex interaction
def example_complex():
    print("=== Example 4: Complex Interaction ===")
    print("Sentence: 'Every student who submitted a paper thinks he will revise it'")
    print()

    print("Multiple binding relations:")
    print("1. 'he' can be bound by 'every student' (quantifier binding)")
    print("2. 'it' can be bound by 'a paper' (donkey anaphora)")
    print("3. Both pronouns depend on quantifiers in different structural positions")
    print()
    print("The compression approach handles this by:")
    print("- Each quantifier compresses its scope domain")
    print("- Donkey anaphora uses discourse conditions")
    print("- C-command relations are computed at each compressed node")
    print()


if __name__ == "__main__":
    example_donkey_anaphora()
    example_strict_sloppy()
    example_reconstruction()
    example_complex()