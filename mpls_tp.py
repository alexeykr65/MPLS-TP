#!/usr/bin/env python
#
# Generate configure files for MPLS-TP
#
# alexeykr@gmail.com
#
import sys
import argparse
# import string
import re
# import random

description = "MPLS-TP: Generate MPLS-TP tunnels configuration, v2.0"
epilog = "http://ciscoblog.ru"

listRing = list()
listTun = ['1', '3']
flagDebug = int()
sterraConfig = dict()
testList = list()
lastDigit = int()
flagFullMesh = 0
flagCentral = 1
flagInterfaces = 0
flagClock = 1
flagAllTun = 0
lastDigit = 0
numBandwidth = 10000
confRoutersAll = dict()
listInterfaceRouter = dict()
confInterfaceRouter = dict()

keyPreShare = ""
fileName = ""

initMPLSTP_LABEL = """
mpls label range 32760 32767 static 16 32700
mpls tp
"""

initBFD = """
bfd-template single-hop DEFAULT
 interval min-tx 5000 min-rx 5000 multiplier 3
"""


def cmdArgsParser():
    global fileName, keyPreShare, nameInterface, flagDebug, flagFullMesh, flagClock, listTun, lastDigit, listRing, flagAllTun, flagInterfaces
    if flagDebug > 0: print "Analyze options ... "
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('-f', '--file', help='File name with source data', dest="fileName", default='mpls_tp.conf')
    parser.add_argument('-d', '--debug', help='Debug information view(default =1, 2- more verbose)', dest="flagDebug", default=1)
    parser.add_argument('-n', '--num', help='Numbers of pair Routers (ex: 1,3)', dest="listTun", default="")
    parser.add_argument('-l', '--listring', help='Numbers of Routers', dest="listRing", default="6")
    parser.add_argument('-r', '--reverse', help='Against Clockwise LSP path', action="store_true")
    parser.add_argument('-i', '--interface', help='Create Config Interfaces', action="store_true")
    parser.add_argument('-a', '--alltun', help='Create All possible Tunnel', action="store_true")

    arg = parser.parse_args()
    fileName = arg.fileName
    flagDebug = int(arg.flagDebug)
    if arg.listTun != "":
        listTun = arg.listTun.split(',')
    if arg.listRing != "":
        for i in range(1, int(arg.listRing) + 1):
            listRing.append(str(i))

    print "Routers Ring list: " + str(listRing)
    print "Tunnel default numbers list: " + str(listTun)
    if arg.reverse:
        flagClock = 0
    if arg.alltun:
        flagAllTun = 1
    if arg.interface:
        flagInterfaces = 1
    print "flagDebug :" + str(flagDebug)
    lastDigit = len(listRing)
    print "LastDigit: " + str(lastDigit)


def fileConfigAnalyze():
    global listInterfaceRouter
    if flagDebug > 0: print "Analyze source file : " + fileName + " ..."
    f = open(fileName, 'r')
    for sLine in f:
        if re.match("[^\s](.*)$", sLine, re.IGNORECASE):
            if flagDebug > 1: print "========================================"
            intrLeft, sRouter, intrRight = sLine.split(':')
            listInterfaceRouter[sRouter] = [intrLeft.strip(), intrRight.strip()]
            if flagDebug > 1: print "General ...." + intrLeft + " " + intrRight
    f.close()
    # if flagDebug > 1: print " Sterra Configuration : " + str(sterraConfig)


def getLinkNumbers(curNum):
    global lastDigit
    if int(curNum) >= int(listTun[1]):
        if curNum == str(lastDigit):
            linkWorking = curNum + listRing[int(curNum) - 2]
            linkProtect = curNum + listRing[int(curNum) - lastDigit]
        else:
            linkWorking = curNum + listRing[int(curNum) - 2]
            linkProtect = curNum + listRing[int(curNum)]
    else:
        linkWorking = curNum + listRing[int(curNum)]
        linkProtect = curNum + listRing[int(curNum) - 2]
    # print "Linkworking : " + linkWorking
    # print "LinkProtect : " + linkProtect
    return linkWorking, linkProtect


def outResult(strR, numRouter):
    global confRoutersAll
    if flagDebug > 1:
        print strR
    if numRouter in confRoutersAll:
        confRoutersAll[numRouter] = confRoutersAll[numRouter] + strR + "\n"
    else:
        confRoutersAll[numRouter] = strR + "\n"


def createConfigInterfaces():
    global listInterfaceRouter
    for i in listInterfaceRouter:
        confInterfaceRouter[i] = "default interface " + listInterfaceRouter[i][0] + "\n"
        confInterfaceRouter[i] += "interface " + listInterfaceRouter[i][0] + "\n"
        confInterfaceRouter[i] += " medium p2p\n"
        if (int(i) - 1) > 0:
            confInterfaceRouter[i] += " mpls tp link " + str(i) + str(int(i) - 1) + "\n"
        else:
            confInterfaceRouter[i] += " mpls tp link " + str(i) + str(lastDigit) + "\n"
        confInterfaceRouter[i] += " ip rsvp bandwidth percent 100 \n\n"
        confInterfaceRouter[i] += "default interface " + listInterfaceRouter[i][1] + "\n"
        confInterfaceRouter[i] += "interface " + listInterfaceRouter[i][1] + "\n"
        confInterfaceRouter[i] += " medium p2p\n"
        if (int(i) + 1) <= lastDigit:
            confInterfaceRouter[i] += " mpls tp link " + str(i) + str(int(i) + 1) + "\n"
        else:
            confInterfaceRouter[i] += " mpls tp link " + str(i) + '1' + "\n"
        confInterfaceRouter[i] += " ip rsvp bandwidth percent 100 \n"

        confInterfaceRouter[i] += "end\n"
        # outResult("!=========== Create Config Interfaces for " + str(i) + " ===========\nconf t\n", str(i))


def createMPLSTPconfig():
    global initBFD, initMPLSTP_LABEL
    for i in range(1, lastDigit + 1):
        outResult("!=========== Create Configuration for R" + str(i) + " ===========\nconf t\n", str(i))
        outResult(initMPLSTP_LABEL, str(i))
        outResult("router-id 1.1.1." + str(i), str(i))
        outResult("l2 router-id 1.1.1." + str(i), str(i))
        outResult(initBFD, str(i))
        outResult("\n", str(i))


def createTunnelEnds(routerNumFirst, routerNumLast):
    global initBFD, listTun, numBandwidth, flagClock
    tunNum = listTun[0] + listTun[1]

    outResult("!=========== Create Tunnel " + str(tunNum) + " ===========\n\n", routerNumFirst)
    if flagClock:
        linkWorking, linkProtect = getLinkNumbers(routerNumFirst)
    else:
        linkProtect, linkWorking = getLinkNumbers(routerNumFirst)

    outResult("interface Tunnel-tp" + tunNum, routerNumFirst)
    outResult(" tp bandwidth " + str(numBandwidth), routerNumFirst)
    outResult(" tp source 1.1.1." + routerNumFirst, routerNumFirst)
    outResult(" tp destination 1.1.1." + routerNumLast, routerNumFirst)
    outResult(" bfd DEFAULT", routerNumFirst)
    outResult(" working-lsp", routerNumFirst)
    outResult("  out-label " + tunNum + linkWorking + " out-link " + linkWorking, routerNumFirst)
    outResult("  in-label " + tunNum + ''.join(reversed(linkWorking)), routerNumFirst)
    outResult("  lsp-number " + tunNum, routerNumFirst)
    outResult(" protect-lsp", routerNumFirst)
    outResult("  out-label " + tunNum + linkProtect + " out-link " + linkProtect, routerNumFirst)
    outResult("  in-label " + tunNum + ''.join(reversed(linkProtect)), routerNumFirst)
    outResult("  lsp-number 1" + tunNum, routerNumFirst)
    # outResult("end\n", routerNumFirst)


def createTunnelTransit(routerNumFirst, routerNumLast):
    global listRing, listTun, flagClock
    tunNum = listTun[0] + listTun[1]
    for intR in listRing:
        flagLink = "working"
        if intR == listTun[0] or intR == listTun[1]:
            continue

        if (int(intR) > int(listTun[0]) and int(intR) < int(listTun[1])) and not flagClock:
            flagLink = "protect"
        if (int(intR) < int(listTun[0]) or int(intR) > int(listTun[1])) and flagClock:
            flagLink = "protect"

        outResult("!=========== Create Transit Tunnel " + str(tunNum) + " ===========\n\n", intR)
        linkWorking, linkProtect = getLinkNumbers(intR)
        if intR == lastDigit:
            outResult("mpls tp lsp source 1.1.1." + routerNumFirst + " tunnel-tp " + tunNum + " lsp " + flagLink + " destination 1.1.1." + routerNumLast + " tunnel-tp " + tunNum, intR)
            outResult(" forward-lsp", intR)
            outResult("  bandwidth " + str(numBandwidth), intR)
            outResult("  in-label " + tunNum + ''.join(reversed(linkProtect)) + " out-label " + tunNum + linkWorking + " out-link " + linkWorking, intR)
            outResult(" reverse-lsp", intR)
            outResult("  bandwidth " + str(numBandwidth), intR)
            outResult("  in-label " + tunNum + ''.join(reversed(linkWorking)) + " out-label " + tunNum + linkProtect + " out-link " + linkProtect, intR)
        else:
            outResult("mpls tp lsp source 1.1.1." + routerNumFirst + " tunnel-tp " + tunNum + " lsp " + flagLink + " destination 1.1.1." + routerNumLast + " tunnel-tp " + tunNum, intR)
            outResult(" forward-lsp", intR)
            outResult("  bandwidth " + str(numBandwidth), intR)
            outResult("  in-label " + tunNum + ''.join(reversed(linkProtect)) + " out-label " + tunNum + linkWorking + " out-link " + linkWorking, intR)
            outResult(" reverse-lsp", intR)
            outResult("  bandwidth " + str(numBandwidth), intR)
            outResult("  in-label " + tunNum + ''.join(reversed(linkWorking)) + " out-label " + tunNum + linkProtect + " out-link " + linkProtect, intR)
        # outResult("end\n", intR)


def createConfigRouters():
    global listTun
    createTunnelEnds(listTun[0], listTun[1])
    createTunnelEnds(listTun[1], listTun[0])
    createTunnelTransit(listTun[0], listTun[1])


if __name__ == '__main__':
    cmdArgsParser()
    fileConfigAnalyze()
    if flagInterfaces:
        createConfigInterfaces()
        for sR in listInterfaceRouter:
            fw = open("config_interfaces_" + "R" + str(sR) + '.txt', 'w')
            fw.write(confInterfaceRouter[sR])
            fw.write("\n\n")
            fw.close()

    createMPLSTPconfig()
    if flagClock:
        if flagDebug > 0: print "Flag: Clockwise ... "
    else:
        if flagDebug > 0: print "Flag: Against Clockwise ... "
    intReverse = int(lastDigit / 2)
    print "intReverse : " + str(intReverse)
    if flagAllTun:
        for i in listRing:
            flagClock = 1
            for j in range(int(i) + 1, lastDigit + 1):
                if (int(j) - int(i)) > int(intReverse):
                    flagClock = 0
                listTun[0] = str(i)
                listTun[1] = str(j)
                createConfigRouters()
    else:
        createConfigRouters()

    for i in confRoutersAll:
        fw = open("config_tunnels_" + "R" + str(i) + '.txt', 'w')
        fw.write(confRoutersAll[i])
        fw.write("\n\n")
        fw.close()

    if flagDebug > 0: print "Script complete successful!!! "

    sys.exit()
