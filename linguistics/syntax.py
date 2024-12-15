#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from ArticutAPI import Articut
from pprint import pprint
import re

class TransformationalGrammar:
    def __init__(self, username="", apikey="", lang="tw", llmkey="", online=False):
        self.username = username
        self.apikey = apikey
        self.llmkey = llmkey
        self.purgePAT = re.compile("</?[a-zA-Z]+(_[a-zA-Z]+)?>")
        self.whoPAT = re.compile("<CLAUSE_whoQ>[^<]+</CLAU>")
        self.twPAT = {"who" :re.compile("(?<=<ENTITY_person>)[^<]+(?=</ENTITY_person><A[CU])|(?<=<ENTITY_pronoun>)[^<]+(?=</ENTITY_pronoun><A[CU])"),
                      "what":re.compile("((?<=<ENTITY_oov>)|(?<=<ENTITY_noun>)|(?<=<ENTITY_nouny>)|(?<=<ENTITY_nounHead>))[^<]+((?=</ENTITY_oov>(?!<RANGE))|(?=</ENTITY_noun>(?!<RANGE))|(?=</ENTITY_nouny>(?!<RANGE))|(?=</ENTITY_nounHead>(?!<RANGE)))"),
                    #   "where":re.compile("((?=</FUNC_inner><LOCATION>).*)"),
                      "yesno":re.compile("((.+)不\2)"),
                      "anota":re.compile("")
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
                      "AnotA":[]
                      }

    def makeQ(self, inputSTR):
        #if #damn...這裡需要孟軒的模型
        self.inputSTR = inputSTR
        resultDICT = self.articut.parse(self.inputSTR)
        self._whoQ(resultDICT)
        self._whatQ(resultDICT)
        #self._whereQ(resultDICT)
        self._yesnoQ(resultDICT)
        return self.QDICT

    def _whoQ(self, resultDICT):
        self.whoQLSIT = []
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
                        self.QDICT["who"].append(self.purgePAT.sub("", self.twPAT["who"].sub("誰", resultDICT["result_pos"][i], count=1))+"呢？")
        return None

    def _whatQ(self, resultDICT):
        self.whoQLSIT = []
        for i in range(0, len(resultDICT["result_pos"])):
            if len(resultDICT["result_pos"][i]) == 1:
                pass
            elif resultDICT["result_pos"][i] in self.QDICT["what"]:
                pass
            else:
                if self.lang == "tw":
                    if resultDICT["result_pos"][i].endswith("呢</CLAUSE_particle>"):
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
        self.whoQLSIT = []
        for i in range(0, len(resultDICT["result_pos"])):
            if len(resultDICT["result_pos"][i]) == 1:
                pass
            elif resultDICT["result_pos"][i] in self.QDICT["yesno"]:
                pass
            else:
                if self.lang == "tw":
                    if resultDICT["result_pos"][i].endswith("呢</CLAUSE_particle>"):
                        pass
                    elif self.twPAT["yesno"].search(self.purgePAT.sub("", resultDICT["result_pos"][i])) == None:
                        self.QDICT["yesno"].append(self.purgePAT.sub("", resultDICT["result_pos"][i])+"嗎？")
        return None

if __name__ == "__main__":
    tg = TransformationalGrammar(lang="tw")
    resultDICT = tg.makeQ("川普出生並成長於紐約州紐約市皇后區，他是美國歷史上最富有的總統，他是不是美國歷史上最富有的總統呢")
    #resultDICT = tg._whatQ("川普出生並成長於紐約州紐約市皇后區，他是美國歷史上最富有的總統")

    pprint(resultDICT)