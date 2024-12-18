#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from json import encoder

from ArticutAPI import Articut
from pprint import pprint
import json
import re

from discord.ui import dynamic
from pandas.core.reshape import encoding

class TransformationalGrammar:
    def __init__(self, username="", apikey="", lang="tw", llmkey="", online=False):
        self.username = username
        self.apikey = apikey
        self.llmkey = llmkey
        self.purgePAT = re.compile("</?[a-zA-Z]+(_[a-zA-Z]+)?>")
        self.entityPat = re.compile("(<ENTITY_(nounHead|nouny|noun|oov)>[^<]+</ENTITY_\\2>)|(<UserDefined>[^<]+</UserDefined>)")
        self.dynamicUdPAT = re.compile("<ACTION_verb>([^<]+)</ACTION_verb>[^、]+、(<ACTION_verb>\1</ACTION_verb>[^、]+(?=[、，。]))+|((?<=包.</ACTION_verb>)|(?<=：))[^，。]+(?=[，。])")
        self.twPAT = {"who" :re.compile("(?<=<ENTITY_person>)[^<]+(?=</ENTITY_person><A[CU])|(?<=<ENTITY_pronoun>)[^<]+(?=</ENTITY_pronoun><A[CU])"),
                      "what":re.compile("((?<=<ENTITY_oov>)|(?<=<ENTITY_noun>)|(?<=<ENTITY_nouny>)|(?<=<ENTITY_nounHead>)|(?<=<UserDefined>))[^<]+((?=</ENTITY_oov>(?!<RANGE))|(?=</ENTITY_noun>(?!<RANGE))|(?=</ENTITY_nouny>(?!<RANGE))|(?=</ENTITY_nounHead>(?!<RANGE))|(?=</UserDefined>(?!<RANGE)))"),
                    #   "where":re.compile("((?=</FUNC_inner><LOCATION>).*)"),
                      "yesno":re.compile("((.+)不\\2)"),
                      "anota":re.compile("((?<=</ENTITY_noun>)|(?<=</ENTITY_nouny>)|(?<=</ENTITY_oov>)|(?<=</UserDefined>)|(?<=</ENTITY_person>)|(?<=</ENTITY_pronoun>))<((?=MODAL)|(?=ACTION)|(?=AUX))")
                      }
        if online == False:
            self.url = ""
        else:
            pass
        self.lang = lang
        if self.lang == "tw":
            self.url="https://api.droidtown.co"
        elif self.lang == "en":
            self.url="https://nlu.droidtown.co"
        self.articut = Articut(username=self.username, apikey=self.apikey, url=self.url)

        self.QDICT = {"who"  :[],
                      "what" :[],
                      "where":[],
                      "when" :[],
                      "how"  :[],
                      "how-m":[],
                      "why"  :[],
                      "yesno":[],
                      "anota":[],
                      "which-pl":[],
                      "which-sg":[]
                      }

    def makeQ(self, inputSTR, userDefinedFILE=None):
        #if #damn...這裡需要孟軒的模型
        self.inputSTR = inputSTR
        preProcDICT =  self.articut.parse(self.inputSTR)
        prePosSTR = "".join(preProcDICT["result_pos"])
        with open("ud.json", "r+", encoding="utf-8") as f:
            dynamicDICT = json.load(f)
            
        dynamicDICT.update({"listSTR": [self.purgePAT.sub("", l.group(0)) for l in self.dynamicUdPAT.finditer(prePosSTR)]})
        with open("ud.json", "w", encoding="utf-8") as f:
            json.dump(dynamicDICT, f, ensure_ascii=False)
        resultDICT = self.articut.parse(self.inputSTR, userDefinedDictFILE=userDefinedFILE)
        self._whoQ(resultDICT)
        self._whatQ(resultDICT)
        #self._whereQ(resultDICT)
        self._yesnoQ(resultDICT)
        self._anotaQ(resultDICT)
        return self.QDICT

    def _whoQ(self, resultDICT):
        for i in range(0, len(resultDICT["result_pos"])):
            if len(resultDICT["result_pos"][i]) == 1:
                pass
            elif resultDICT["result_pos"][i] in self.QDICT["who"]:
                pass
            else:
                if self.lang == "tw":
                    if resultDICT["result_pos"][i].endswith("呢</CLAUSE_particle>"):
                        pass
                    else:
                        whoSlot = [(w.start(), w.end(), w.group(0)) for w in list(self.twPAT["who"].finditer(resultDICT["result_pos"][i]))]
                        if whoSlot == []:
                            pass
                        else:
                            self.QDICT["who"].append(self.purgePAT.sub("", self.twPAT["who"].sub("誰", resultDICT["result_pos"][i], count=1))+"呢？")
        return None

    def _whatQ(self, resultDICT):
        for i in range(0, len(resultDICT["result_pos"])):
            if len(resultDICT["result_pos"][i]) == 1:
                pass
            elif resultDICT["result_pos"][i] in self.QDICT["what"]:
                pass
            else:
                if self.lang == "tw":
                    if len(resultDICT["result_pos"][i]) <= 1:
                        pass
                    elif [e.group(0) for e in self.entityPat.finditer(resultDICT["result_pos"][i])] == [resultDICT["result_pos"][i]]:
                        pass
                    elif resultDICT["result_pos"][i].endswith("呢</CLAUSE_particle>"):
                        pass
                    elif  resultDICT["result_pos"][i].endswith("</FUNC_inner>"):
                        pass
                    elif resultDICT["result_pos"][i].startswith("<FUNC_in"):
                        pass                    
                    else:
                        whatSlot = [(w.start(), w.end(), w.group(0)) for w in list(self.twPAT["what"].finditer(resultDICT["result_pos"][i]))]
                        if whatSlot == []:
                            pass
                        else:
                            
                            self.QDICT["what"].append(self.purgePAT.sub("", self.twPAT["what"].sub("什麼", resultDICT["result_pos"][i], count=1))+"呢？")
        return None

    #def _whereQ(self, resultDICT):
        #self.whoQLSIT = []
        #for i in range(0, len(resultDICT["result_pos"])):
            #if len(resultDICT["result_pos"][i]) == 1:
                #pass
            #elif resultDICT["result_pos"][i] in self.QDICT["where"]:
                #pass
            #else:
                #if self.lang == "tw":
                    #print(resultDICT["result_pos"][i])
                    #self.QDICT["where"].append(self.purgePAT.sub("", self.twPAT["where"].sub("哪裡", resultDICT["result_pos"][i], count=1)))
        #return None

    def _yesnoQ(self, resultDICT):
        for i in range(0, len(resultDICT["result_pos"])):
            if len(resultDICT["result_pos"][i]) == 1:
                pass
            elif resultDICT["result_pos"][i] in self.QDICT["yesno"]:
                pass
            else:
                if self.lang == "tw":
                    if resultDICT["result_pos"][i].endswith("呢</CLAUSE_particle>"):
                        pass
                    elif resultDICT["result_pos"][i].endswith("嗎</CLAUSE_YesNoQ>"):
                        pass
                    elif  resultDICT["result_pos"][i].endswith("</FUNC_inner>"):
                        pass
                    elif resultDICT["result_pos"][i].startswith("<FUNC_in"):
                        pass
                    elif self.twPAT["yesno"].search(self.purgePAT.sub("", resultDICT["result_pos"][i])) == None:
                        self.QDICT["yesno"].append(self.purgePAT.sub("", resultDICT["result_pos"][i])+"嗎？")
        return None

    def _anotaQ(self, resultDICT):
        for i in range(0, len(resultDICT["result_pos"])):
            if len(resultDICT["result_pos"][i]) == 1:
                pass
            elif resultDICT["result_pos"][i] in self.QDICT["anota"]:
                pass
            else:
                if self.lang == "tw":
                    if resultDICT["result_pos"][i].endswith("嗎</CLAUSE_particle>"):
                        pass
                    else:
                        AnotAslot = [(a.start(), a.end(), a.group(0)) for a in list(self.twPAT["anota"].finditer(resultDICT["result_pos"][i]))]
                        if AnotAslot == []:
                            pass
                        elif  resultDICT["result_pos"][i].endswith("</FUNC_inner>"):
                            pass
                        elif resultDICT["result_pos"][i].startswith("<FUNC_in"):
                            pass
                        else:
                            if resultDICT["result_pos"][i][AnotAslot[0][1]:AnotAslot[0][1]+5] == "MODAL":
                                m = "<"+resultDICT["result_pos"][i][AnotAslot[0][1]:AnotAslot[0][1]+7]+"不"
                                self.QDICT["anota"].append(self.purgePAT.sub("", f"{resultDICT['result_pos'][i][:AnotAslot[0][0]]}{m}{resultDICT['result_pos'][i][AnotAslot[0][1]+6:]}"))
                            elif resultDICT["result_pos"][i][AnotAslot[0][1]:AnotAslot[0][1]+3] == "AUX":
                                m = "<"+resultDICT["result_pos"][i][AnotAslot[0][1]:AnotAslot[0][1]+5]+"不"
                                self.QDICT["anota"].append(self.purgePAT.sub("", f"{resultDICT['result_pos'][i][:AnotAslot[0][0]]}{m}{resultDICT['result_pos'][i][AnotAslot[0][1]+4:]}"                                ))
                            else:
                                a = AnotAslot[0][2].replace("<", "<CLAUSE_AnotA>是不是</CLAUSE_AnotA><")
                                self.QDICT["anota"].append(self.purgePAT.sub("", f"{resultDICT['result_pos'][i][:AnotAslot[0][0]]}{a}{resultDICT['result_pos'][i][AnotAslot[0][1]:]}"))

        return None

if __name__ == "__main__":

    with open("account.info", encoding="utf-8") as f:
        accountDICT = json.load(f)
    
    tg = TransformationalGrammar(username=accountDICT["username"], apikey=accountDICT["apikey"], lang="tw")
    resultDICT = tg.makeQ("立普妥膜衣錠的衛生署許可證適應症包含高膽固醇血症、高三酸甘油脂血症。對於臨床上沒有冠心病的第二型糖尿病患者，但是至少有任一其他冠心病危險因子，包括高血壓、視網膜病變、白蛋白尿、或吸煙，Lipitor適用於：降低心肌梗塞的風險、降低中風的風險。降低冠心病高危險群的心血管事件發生率對於臨床上沒有冠心病的高血壓患者，但是至少有三個其他冠心病危險因子，包括第二型糖尿病、年紀大於等於55歲、微白蛋白尿或蛋白尿、吸煙、或第一等親在55歲(男性)或60歲(女性)前曾經發生冠心病事件，Lipitor適用於：降低心肌梗塞的風險、降低中風的風險、降低血管再造術與心絞痛的風險。", userDefinedFILE="./ud.json")

    pprint(resultDICT)