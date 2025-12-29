#!/usr/bin/env python3
# -*- coding:utf-8 -*-

#import plotly.graph_objects as go
from collections import deque
from datetime import datetime

from ArticutAPI import Articut
articut = Articut()

from Loki_Model.merge.main import askLoki as askLokiMerge
import re
splitPAT = re.compile("(?<=>)(?=<)")
posPAT = re.compile("(<)>")

from pprint import pprint

# ## 以 Graph 建立句法樹 ######################################

def treeMaker(inputSentence):
    """
    input:
    inputSentence: "w1w2w3w4...wn"，為一個由 word w 組成的字串，其後的數字表示它是第幾個字。

    return: 一個最簡化的右向二元樹
    {"node_1": {"w1", "node2"}, "node_2": {"w2", "node_3"},..."node_n-1": ,{"wn-1", "wn"}}
    """
    startTime = datetime.now()
    wordLIST = [w for w in inputSentence.replace("w", " w").split(" ") if w != ""]
    #nodeLength = len(wordLIST) - 1
    treeDICT = {}
    for i in range(len(wordLIST) - 1, -1, -1):
        if i == len(wordLIST) - 1:
            pass
        elif wordLIST[i+1] == wordLIST[-1]:
            treeDICT[f"node{i + 1}"] = {wordLIST[i], wordLIST[i+1]}
        else:
            treeDICT[f"node{i + 1}"] = {wordLIST[i], f"node{i + 2}"}
    time = datetime.now() - startTime
    return treeDICT, time

def findParentNode(tree, childnode):
    for parentnode in tree.keys():
        if childnode in tree[parentnode]:
            return parentnode
    return childnode

def ccommandWithTree(tree, commander="w1", commandee=""):
    """
    計算 w1 是否 c-command 最後一個 wn
    input: tree : {'node9': {'w9', 'w10'}, 'node8': {'w8', 'node9'}, 'node7': {'node8', 'w7'}, 'node6': {'w6', 'node7'}, 'node5': {'w5', 'node6'}, 'node4': {'w4', 'node5'}, 'node3': {'w3', 'node4'}, 'node2': {'w2', 'node3'}, 'node1': {'w1', 'node2'}}
    return: True/False, time
    """
    startTime = datetime.now()
    #找到 commander 的 immediate dominating node
    for node in tree.keys():
        if commander in tree[node]:
            dominateNode = node

    #找到 commandee 的 所有可能 dominating node
    traceLIST = []
    for node in tree.keys():
        if commandee in tree[node]:
            traceLIST.append(node)
    while traceLIST[-1] != "node1":
        node = findParentNode(tree, traceLIST[-1])
        traceLIST.append(node)

    #如果兩者有交集，表示 commander c-commands commandee；反之則無。
    if dominateNode in traceLIST:
        ccommand_result = True
    else:
        ccommand_result = False
    time = datetime.now() - startTime
    return ccommand_result, time


#建二元樹使用
def find_root(graph):
    """Find the root node (node that is not a child of any other node)."""
    all_children = set()
    for children in graph.values():
        all_children.update(children)

    all_nodes = set(graph.keys())
    roots = all_nodes - all_children
    return list(roots)[0] if roots else None

#僅為建二元樹之視覺化時使用
def calculate_positions(graph, root):
    """Calculate x, y positions for each node with blue nodes at bottom, green nodes at right, rotated 45 degrees and horizontally flipped."""
    import math

    # BFS to assign levels
    queue = deque([(root, 0)])
    visited = set()
    level_nodes = {}

    while queue:
        node, level = queue.popleft()
        if node in visited:
            continue
        visited.add(node)

        if level not in level_nodes:
            level_nodes[level] = []
        level_nodes[level].append(node)

        if node in graph:
            for child in sorted(graph[node]):
                if child not in visited:
                    queue.append((child, level + 1))

    # Separate blue nodes (internal) and green nodes (leaf)
    coords = {}
    blue_nodes = []
    green_nodes = []

    for level, nodes in level_nodes.items():
        for node in nodes:
            if node in graph:
                blue_nodes.append((node, level))
            else:
                green_nodes.append((node, level))

    # Position blue nodes vertically (bottom of graph)
    for idx, (node, level) in enumerate(blue_nodes):
        x_orig = 5  # Center column
        y_orig = -idx * 2  # Vertical spacing

        # Rotate 45 degrees clockwise
        angle = -math.pi / 4  # -45 degrees in radians
        x_rotated = x_orig * math.cos(angle) - y_orig * math.sin(angle)
        y_rotated = x_orig * math.sin(angle) + y_orig * math.cos(angle)

        # Horizontal flip
        x_flipped = -x_rotated

        coords[node] = {
            'x': x_flipped,
            'y': y_rotated
        }

    # Position green nodes to the right
    for idx, (node, level) in enumerate(green_nodes):
        x_orig = 10  # Right side
        y_orig = -idx * 2  # Vertical spacing

        # Rotate 45 degrees clockwise
        angle = -math.pi / 4  # -45 degrees in radians
        x_rotated = x_orig * math.cos(angle) - y_orig * math.sin(angle)
        y_rotated = x_orig * math.sin(angle) + y_orig * math.cos(angle)

        # Horizontal flip
        x_flipped = -x_rotated

        coords[node] = {
            'x': x_flipped,
            'y': y_rotated
        }

    return coords

#僅為建二元樹之視覺化時使用
def build_edges(graph, coords):
    """Build edge coordinates for drawing lines between nodes."""
    edge_x = []
    edge_y = []

    for parent, children in graph.items():
        if parent not in coords:
            continue
        for child in children:
            if child in coords:
                # Add line from parent to child
                edge_x.extend([coords[parent]['x'], coords[child]['x'], None])
                edge_y.extend([coords[parent]['y'], coords[child]['y'], None])

    return edge_x, edge_y

#僅為建二元樹之視覺化時使用
def visualize_tree(tree, title="Tree Structure Visualization"):
    """
    Visualize a tree structure using Plotly.

    Args:
        tree: Dictionary where keys are nodes and values are sets/lists of children
        title: Title for the plot
    """
    # Find root and calculate positions
    root = find_root(tree)
    if not root:
        print("No root node found!")
        return

    coords = calculate_positions(tree, root)
    edge_x, edge_y = build_edges(tree, coords)

    # Prepare node data
    node_x = []
    node_y = []
    node_text = []
    node_colors = []

    for node in coords:
        node_x.append(coords[node]['x'])
        node_y.append(coords[node]['y'])
        node_text.append(node)
        # Color leaf nodes (not in graph keys) differently
        if node in tree:
            node_colors.append('#60A5FA')  # Blue for internal nodes
        else:
            node_colors.append('#34D399')  # Green for leaf nodes

    # Create edge trace
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=2, color='#94A3B8'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node trace
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition='middle center',
        textfont=dict(size=12, color='white', family='Arial'),
        marker=dict(
            size=30,
            color=node_colors,
            line=dict(color='#1E293B', width=2)
        )
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                   layout=go.Layout(
                       title=dict(text=title, font=dict(size=20)),
                       showlegend=False,
                       hovermode='closest',
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       plot_bgcolor='#F8FAFC',
                       paper_bgcolor='#F8FAFC',
                       margin=dict(l=40, r=40, t=80, b=40)
                   ))

    fig.show()





# ## 以 SET 建立句法樹 ######################################
def setMaker(inputSentence):
    """
    input:
    inputSentence: "w1w2w3w4...wn"，為一個由 word w 組成的字串，其後的數字表示它是第幾個字。

    return: 一個最簡化的右向二元素的集合
    {"w1", {"w2", {"w3", "w4"...}}}
    """
    startTime = datetime.now()
    wordLIST = [w for w in inputSentence.replace("w", " w").split(" ") if w != ""]
    workLIST = wordLIST[:]
    result = set()
    for i in range(len(wordLIST) - 1, -1, -1):
        if i == len(wordLIST) - 1:
            pass
        else:
            workspaceSET = frozenset({workLIST[i], workLIST[i+1]})
            workLIST.insert(i, workspaceSET)
            if i == 0:
                result.add(workspaceSET)
    time = datetime.now() - startTime
    return result, time

def ccommandWithSet(inputSET, commander="w1", commandee=""):
    startTime = datetime.now()
    for i in inputSET:
        for j in i:
            if j == commander:
                domainSet = j

    stack = [domainSet]
    workingSET = set()

    while stack:
        current = stack.pop()
        for item in current:
            if isinstance(item, frozenset):
                stack.append(item)
            else:
                workingSET.add(item)

    if commander in workingSET:
        ccommand_result = True
    else:
        ccommand_result = False
    time = datetime.now() - startTime
    return ccommand_result, time




# ## 以 Constituent Algebra 建立句法樹 ######################################
def algMaker(inputSentence):
    """
    input:
    inputSentence: "w1w2w3w4...wn"，為一個由 word w 組成的字串，其後的數字表示它是第幾個字。

    return: 一個最簡化的右向線性函式的集合，每個字 word 以 w 指代；每個 BASE 以 B 指代
    {"+".join(w1B1, w2B2, w3B3, ...wnBn), "+".join(w1B1, w2B2, w3B3, ...wn-1Bn-1), "+".join(w1B1, w2B2, w3B3, ...wn-2Bn-2)}
    """
    startTime = datetime.now()
    wordLIST = [w for w in inputSentence.replace("w", " w").split(" ") if w != ""]
    workLIST = []
    result = dict()
    for i in range(len(wordLIST) - 1, -1, -1):
        if i == len(wordLIST) - 1:
            workLIST.append(f"{wordLIST[i]}_B{i+1}")
        else:
            alg = "_+_".join((f"{wordLIST[i]}_B{i+1}", f"{workLIST[-1]}"))
            workLIST.append(alg)
            algset = set([a for a in alg.split("_")])
            result[wordLIST[i]] = algset


    time = datetime.now() - startTime
    return result, time

def ccommandWithAlg(inputDICT, commander="w1", commandee=""):
    startTime = datetime.now()
    result = False

    if commandee & inputDICT[commander]:
        result = True
    time = datetime.now() - startTime
    return result, time




def finalNounMerge(sentenceSTR):
    headParameter = "final"
    refDICT = {headParameter: []}
    lokiDICT = askLokiMerge(sentenceSTR, refDICT=refDICT)

    articutDICT = articut.parse(sentenceSTR)
    sentenceLIST = splitPAT.split(articutDICT["result_pos"][0])

    resultLIST = []
    for n in lokiDICT[headParameter]:
        resultLIST = merge(sentenceLIST, n, headParameter)

    return resultLIST

def initialNounMerge(sentenceSTR):
    headParameter = "initial"
    refDICT = {headParameter: []}
    lokiDICT = askLokiMerge(sentenceSTR, refDICT=refDICT)

    articutDICT = articut.parse(sentenceSTR)
    sentenceLIST = splitPAT.split(articutDICT["result_pos"][0])

    resultLIST = []
    for n in lokiDICT[headParameter]:
        resultLIST = merge(sentenceLIST, n, headParameter)

    return resultLIST


def merge(sentenceLIST, head, headParameter):
    if headParameter in ("initial", "final"):
        pass
    else:
        headParameter = "initial"

    resultLIST = []
    #if headParameter == "initial":
        #for i in reversed(range(len(sentenceLIST))):
            #if sentenceLIST[i-1].startswith(f"<{head}>"):
                #resultLIST.append(f"({sentenceLIST[i-1]}, {sentenceLIST[i]})")
                #sentenceLIST[i-1] = ""
            #else:
                #resultLIST.append(sentenceLIST[i])
    #else: #headParameter == "final":
        #for i in reversed(range(len(sentenceLIST))):
            #if sentenceLIST[i].startswith(f"<{head}>"):
                #resultLIST.append(f"({sentenceLIST[i-1]}, {sentenceLIST[i]})")
                #sentenceLIST[i-1] = ""
            #else:
                #resultLIST.append(sentenceLIST[i])

    #Performance version: I guess this is harder for linguists to understand what is happening here.
    if headParameter == "initial":
        indexShift = 1
    else:
        indexShift = 0

    for i in reversed(range(len(sentenceLIST))):
        if sentenceLIST[i-indexShift].startswith(f"{head}"):
            resultLIST.append(f"({sentenceLIST[i-1]}, {sentenceLIST[i]})")
            sentenceLIST[i-1] = ""
        else:
            resultLIST.append(sentenceLIST[i])

    return [word for word in reversed(resultLIST) if word!=""]




def bbtree(sentenceLIST):
    leftMergeLIST = ["<RANGE_locality>", "<FUNC_inner>的"]
    rightMergeLIST = ["<FUNC_inner>在", "<AUX>"]

    #resultSTR = ""
    resultLIST = []
    for l in leftMergeLIST:
        sentenceLIST =  merge(sentenceLIST, l, "final")
    for r in rightMergeLIST:
        sentenceLIST =  merge(sentenceLIST, r, "initial")

    #mergeBOOL = True



    resultLIST = sentenceLIST

    return resultLIST

if __name__ == "__main__":

    inputSTR = "那個帽子是紫色的女孩坐在紅色長凳上"
    resultLIST = longNounMerge(inputSTR)
    result = bbtree(resultLIST)
    #["<ENTITY_DetPhrase>那個</ENTITY_DetPhrase>", "<ENTITY_noun>帽子</ENTITY_noun>", "<AUX>是</AUX>", "<MODIFIER_color>紫色</MODIFIER_color>", "<FUNC_inner>的</FUNC_inner>", "<ENTITY_nouny>女孩</ENTITY_nouny>", "<ACTION_verb>坐</ACTION_verb>", "<FUNC_inner>在</FUNC_inner>", "<ENTITY_nouny>長凳</ENTITY_nouny>", "<RANGE_locality>上</RANGE_locality>"]
    #["((那個((帽子(是(紫色的)))女孩))(坐(在(長凳上))))"]

    #from ArticutAPI import Articut
    #articut = Articut()
    #resultDICT = articut.parse(inputSTR)
    #inputPOS = resultDICT["result_pos"][0]
    #inputPOS = "".join(["<ENTITY_DetPhrase>那個</ENTITY_DetPhrase>", "<ENTITY_noun>帽子</ENTITY_noun>", "<AUX>是</AUX>", "<MODIFIER_color>紫色</MODIFIER_color>", "<FUNC_inner>的</FUNC_inner>", "<ENTITY_nouny>女孩</ENTITY_nouny>", "<ACTION_verb>坐</ACTION_verb>", "<FUNC_inner>在</FUNC_inner>", "<ENTITY_nouny>長凳</ENTITY_nouny>", "<RANGE_locality>上</RANGE_locality>"])
    #bbtree(inputPOS)
    #l =  ["<ENTITY_DetPhrase>那個</ENTITY_DetPhrase>", "<ENTITY_noun>帽子</ENTITY_noun>", "<AUX>是</AUX>", "<MODIFIER_color>紫色</MODIFIER_color>", "<FUNC_inner>的</FUNC_inner>", "<ENTITY_nouny>女孩</ENTITY_nouny>", "<ACTION_verb>坐</ACTION_verb>", "<FUNC_inner>在</FUNC_inner>", "<ENTITY_nouny>長凳</ENTITY_nouny>", "<RANGE_locality>上</RANGE_locality>"]
    #result = merge(resultLIST, "<RANGE_locality>", "final")
    pprint(result)
    #result = merge(l, "<ENTITY_DetPhrase>", "initial")
    #print(result)


    #print("\n#以 Graph 建立句法樹 >>>")
    #sentenceLengthLIST = [10, 100, 1000]
    #for l in sentenceLengthLIST:
        #sentenceLength = l
        #inputSentence = ""
        #for i in range(sentenceLength):
            #inputSentence += f"w{i + 1}"
        #result = treeMaker(inputSentence)
        #tree = result[0]
        #time = result[1]
        ##print(f"句子字數:{l:<5}; 以二元樹建立句法樹，需耗時：{time}")
        ##visualize_tree() #只是為了視覺化，不涉及計算
        #visualize_tree(tree)
        ##ccmdresult = ccommandWithTree(tree, commandee=f"w{l}")
        ##ccommand = ccmdresult[0]
        ##ccommand_computation_time = ccmdresult[1]
        ##print(f"句子字數:{l:<5}; 在二元樹裡計算 w1 是否 c-command w{l}，需耗時：{ccommand_computation_time}")

    #print("\n#以 SET 建立句法樹 >>>")
    #sentenceLengthLIST = [10, 100, 1000]
    #for l in sentenceLengthLIST:
        #sentenceLength = l
        #inputSentence = ""
        #for i in range(sentenceLength):
            #inputSentence += f"w{i + 1}"
        #result = setMaker(inputSentence)
        #setrepresentation = result[0]
        #time = result[1]
        #print(f"句子字數:{l:<5}; 以二元集合建立句法樹，需耗時：{time}")
        #ccmdresult = ccommandWithSet(setrepresentation, commandee=f"w{l}")
        #ccommand = ccmdresult[0]
        #ccommand_computation_time = ccmdresult[1]
        #print(f"句子字數:{l:<5}; 在二元素集合裡計算 w1 是否 c-command w{l}，需耗時：{ccommand_computation_time}")


    #print("\n#以 Constituent Algebra 建立句法樹 >>>")
    #sentenceLengthLIST = [10, 100, 1000]
    #for l in sentenceLengthLIST:
        #sentenceLength = l
        #inputSentence = ""
        #for i in range(sentenceLength):
            #inputSentence += f"w{i + 1}"
        #result = algMaker(inputSentence)
        #linArepresenatation = result[0]
        #time = result[1]
        ##print(linArepresenatation)
        #print(f"句子字數:{l:<5}; 以代數集合建立句法樹，需耗時：{time}")
        #ccmdresult = ccommandWithAlg(linArepresenatation, commandee=set(f"w{l}"))
        #ccommand = ccmdresult[0]
        #ccommand_computation_time = ccmdresult[1]
        #print(f"句子字數:{l:<5}; 在代數集合裡計算 w1 是否 c-command w{l}，需耗時：{ccommand_computation_time}")