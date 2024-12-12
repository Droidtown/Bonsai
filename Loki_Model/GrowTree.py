#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from Bonsai import execLoki
from pathlib import Path
rootDIR = "Tree"
gardener = Path(rootDIR)
gardener.mkdir(parents=True, exist_ok=True)

cpDIR = "Tree/CP/C_bar/C"
ipDIR = "Tree/CP/C_bar/IP/I_bar/I"
vpDIR = "Tree/CP/C_bar/IP/I_bar/VP/V_bar/V"

def main(inputSTR=""):
    """"""
    if inputSTR == "":
        return None
    else:
        #CP
        gardener = Path(cpDIR)
        gardener.mkdir(parents=True, exist_ok=True)
        gardener = Path(ipDIR)
        gardener.mkdir(parents=True, exist_ok=True)

        refDICT = {"CP":[]}
        resultDICT = execLoki(inputSTR, refDICT=refDICT)
        if resultDICT["CP"] != []:
            currentDIR = gardener.glob("**")
            print("currentDIR:", list(currentDIR))


    return cpDIR


if __name__ == "__main__":
    inputSTR = "我認為他懂"
    main(inputSTR)