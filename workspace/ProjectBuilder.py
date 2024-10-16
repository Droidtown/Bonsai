#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from requests import post
from pprint import pprint
import json
accountDICT = json.load(open("account.info", encoding="utf-8"))

lokiurl = "https://api.droidtown.co/Loki/Call/"  #線上版 URL

def createLokiProject(accountDICT, projectSTR=""):
    if projectSTR == "":
        response = {"status":"false",
                    "msg":"projectSTR cannot be empty."}
    else:
        payload = {
            "username" : accountDICT["username"],
            "func": "create_project",
            "data": {
                "name":projectSTR,
                "language": "zh-tw",
                "type": "intent"
            }
        }
        response = post(lokiurl, json=payload).json()
    return response

def insertLokiUtterance(accountDICT, projectSTR="", intentSTR="", utteranceLIST=[]):
    payload = {
        #"username" : "", # 這裡填入您在 https://api.droidtown.co 使用的帳號 email。     Docker 版不需要此參數！
        #"loki_key" : "", # 這裡填入您在 https://api.droidtown.co 登入後取得的 loki_key。 Docker 版不需要此參數！
        "project": projectSTR, #專案名稱
        "intent" : intentSTR,  #意圖名稱
        "func": "insert_utterance",
        "data": {
            "utterance": utteranceLIST, #要新增的語句
            "checked_list": [ #所有詞性全勾選。你可以把不要勾的項目註解掉。
                "ENTITY_noun", #包含所有名詞
                "UserDefined",
                "ENTITY_num",
                "DegreeP",
                "MODIFIER_color",
                "LOCATION",
                "KNOWLEDGE_addTW",
                "KNOWLEDGE_routeTW",
                "KNOWLEDGE_lawTW",
                "KNOWLEDGE_url",
                "KNOWLEDGE_place",
                "KNOWLEDGE_wikiData",
                "KNOWLEDGE_currency"
            ]
        }
    }

    response = post(lokiurl, json=payload).json()
    return response

if __name__ == "__main__":

    # Settings
    IMPORT_MODE = False

    #
    projectSTR = "Bonsai"
    createLokiProject(accountDICT, projectSTR=projectSTR)
    if IMPORT_MODE == True:
        #importLokiProjet(accountDICT, projectSTR=projectSTR, refLIST)
    else:
        LokiCall


