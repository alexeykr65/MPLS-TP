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

description = "mpls: Generate MPLS-TP tunnel configuration"
epilog = "ciscoblog.ru"

listRing = ['1', '2', '3', '4', '5', '6']
listTun = ['1', '3']
flagDebug = int()
flagL2vpn = int()
sterraConfig = dict()
testList = list()
lastDigit = int()
flagFullMesh = 0
flagCentral = 1
flagClock = 1
numBandwidth = 20000

keyPreShare = ""
fileName = ""

initMPLSTP01 = [
    'mpls label range 32760 32767 static 16 32700',
    'mpls tp'

]

initBFD = [
    'bfd-template single-hop DEFAULT',
    ' interval min-tx 5000 min-rx 5000 multiplier 3'
]


def cmdArgsParser():
    global fileName, keyPreShare, nameInterface, flagDebug, flagFullMesh, flagL2vpn, flagClock, listTun, lastDigit
    if flagDebug > 0: print "Analyze options ... "
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('-f', '--file', help='File name with source data', dest="fileName", default='mpls_tp.conf')
    parser.add_argument('-d', '--debug', help='Debug information view(default =1, 2- more verbose', dest="flagDebug", default=1)
    parser.add_argument('-n', '--num', help='Numbers of pair router (ex: 1,3)', dest="listTun", default="")
    parser.add_argument('-r', '--reverse', help='Against Clockwise LSP path', action="store_true")

    arg = parser.parse_args()
    fileName = arg.fileName
    flagDebug = int(arg.flagDebug)
    if arg.listTun != "":
        listTun = arg.listTun.split(',')

    print "Tunnel numbers list: " + str(listTun)
    if arg.reverse:
        flagClock = 0
    print "flagDebug :" + str(flagDebug)
    lastDigit = len(listRing)
    print "LastDigit: " + str(lastDigit)


def fileConfigAnalyze():
    if flagDebug > 0: print "Analyze source file : " + fileName + " ..."
    f = open(fileName, 'r')

    # dictSterra = dict()
    for sLine in f:
        if re.match("#!(.*)$", sLine, re.IGNORECASE):
            print "General ...."

    f.close()
    if flagDebug > 1: print " Sterra Configuration : " + str(sterraConfig)


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


def printResult(strR, fw):
    if flagDebug > 1:
        print strR
    fw.write(strR)
    fw.write("\n")


def createConfigFileRevers():
    global flagDebug, flagL2vpn, numBandwidth, flagClock, lastDigit
    if flagDebug > 0: print "Create Configuration Files ... "

    # Create Configuration file
    routerNumFirst = listTun[0]
    routerNUmLast = listTun[1]
    tunNum = listTun[0] + listTun[1]
    fw = open("config_" + listTun[0] + "_" + listTun[1] + 'r.txt', 'w')

    printResult("=========== Create Configuration for R" + routerNumFirst + " ===========\nconf t\n", fw)
    linkWorking, linkProtect = getLinkNumbers(routerNumFirst)
    for sStr in initMPLSTP01:
        printResult(sStr, fw)
    printResult("router-id 1.1.1." + routerNumFirst, fw)
    printResult("router-id 1.1.1." + routerNumFirst, fw)
    printResult("l2 router-id 1.1.1." + routerNumFirst, fw)
    for sStr in initBFD:
        printResult(sStr, fw)
    printResult("interface Tunnel-tp" + tunNum, fw)
    printResult(" tp bandwidth " + str(numBandwidth), fw)
    printResult(" tp source 1.1.1." + routerNumFirst, fw)
    printResult(" tp destination 1.1.1." + routerNUmLast, fw)
    printResult(" bfd DEFAULT", fw)
    printResult(" working-lsp", fw)
    printResult("  out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)), fw)
    printResult("  lsp-number " + tunNum, fw)
    printResult(" protect-lsp", fw)
    printResult("  out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)), fw)
    printResult("  lsp-number 1" + tunNum, fw)
    printResult("end\n", fw)

    printResult("=========== Create Configuration for R" + routerNUmLast + " ===========\nconf t\n", fw)
    linkWorking, linkProtect = getLinkNumbers(routerNUmLast)
    for sStr in initMPLSTP01:
        printResult(sStr, fw)
    printResult("router-id 1.1.1." + routerNUmLast, fw)
    printResult("l2 router-id 1.1.1." + routerNUmLast, fw)
    for sStr in initBFD:
        printResult(sStr, fw)
    printResult("interface Tunnel-tp" + tunNum, fw)
    printResult(" tp bandwidth " + str(numBandwidth), fw)
    printResult(" tp source 1.1.1." + routerNUmLast, fw)
    printResult(" tp destination 1.1.1." + routerNumFirst, fw)
    printResult(" bfd DEFAULT", fw)
    printResult(" working-lsp", fw)
    printResult("  out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)), fw)
    printResult("  lsp-number " + tunNum, fw)
    printResult(" protect-lsp", fw)
    printResult("  out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)), fw)
    printResult("  lsp-number 1" + tunNum, fw)
    printResult("end\n", fw)
    # exit()
    for intR in listRing:
        flagLink = "working"
        if intR == listTun[0] or intR == listTun[1]:
            continue
        if int(intR) > int(listTun[0]) and int(intR) < int(listTun[1]):
            flagLink = "protect"

        printResult("=========== Create Configuration for R" + intR + " ===========\nconf t", fw)

        linkWorking, linkProtect = getLinkNumbers(intR)
        for sStr in initMPLSTP01:
            printResult(sStr, fw)
        printResult("router-id 1.1.1." + str(intR), fw)
        printResult("l2 router-id 1.1.1." + str(intR), fw)
        for sStr in initBFD:
            printResult(sStr, fw)
        if intR == lastDigit:
            printResult("mpls tp lsp source 1.1.1." + routerNumFirst + " tunnel-tp " + tunNum + " lsp " + flagLink + " destination 1.1.1." + routerNUmLast + " tunnel-tp " + tunNum, fw)
            printResult(" forward-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)) + " out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
            printResult(" reverse-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)) + " out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)

        else:
            printResult("mpls tp lsp source 1.1.1." + routerNumFirst + " tunnel-tp " + tunNum + " lsp " + flagLink + " destination 1.1.1." + routerNUmLast + " tunnel-tp " + tunNum, fw)
            printResult(" forward-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)) + " out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
            printResult(" reverse-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)) + " out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)

        printResult("end\n", fw)
    fw.write("\n\n")
    fw.write("\n")
    fw.close()


def createConfigFileClockwise():
    global flagDebug, flagL2vpn, numBandwidth, flagClock, LastDigit
    if flagDebug > 0: print "Create Configuration Files ... "

    # Create Configuration file
    routerNumFirst = listTun[0]
    routerNUmLast = listTun[1]
    tunNum = listTun[0] + listTun[1]
    fw = open("config_" + listTun[0] + "_" + listTun[1] + '.txt', 'w')

    printResult("=========== Create Configuration for R" + routerNumFirst + " ===========\nconf t\n", fw)
    linkWorking, linkProtect = getLinkNumbers(routerNumFirst)
    for sStr in initMPLSTP01:
        printResult(sStr, fw)
    printResult("router-id 1.1.1." + routerNumFirst, fw)
    printResult("router-id 1.1.1." + routerNumFirst, fw)
    printResult("l2 router-id 1.1.1." + routerNumFirst, fw)
    for sStr in initBFD:
        printResult(sStr, fw)
    printResult("interface Tunnel-tp" + tunNum, fw)
    printResult(" tp bandwidth " + str(numBandwidth), fw)
    printResult(" tp source 1.1.1." + routerNumFirst, fw)
    printResult(" tp destination 1.1.1." + routerNUmLast, fw)
    printResult(" bfd DEFAULT", fw)
    printResult(" working-lsp", fw)
    printResult("  out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)), fw)
    printResult("  lsp-number " + tunNum, fw)
    printResult(" protect-lsp", fw)
    printResult("  out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)), fw)
    printResult("  lsp-number 1" + tunNum, fw)
    printResult("end\n", fw)

    printResult("=========== Create Configuration for R" + routerNUmLast + " ===========\nconf t\n", fw)
    linkWorking, linkProtect = getLinkNumbers(routerNUmLast)
    for sStr in initMPLSTP01:
        printResult(sStr, fw)
    printResult("router-id 1.1.1." + routerNUmLast, fw)
    printResult("l2 router-id 1.1.1." + routerNUmLast, fw)
    for sStr in initBFD:
        printResult(sStr, fw)
    printResult("interface Tunnel-tp" + tunNum, fw)
    printResult(" tp bandwidth " + str(numBandwidth), fw)
    printResult(" tp source 1.1.1." + routerNUmLast, fw)
    printResult(" tp destination 1.1.1." + routerNumFirst, fw)
    printResult(" bfd DEFAULT", fw)
    printResult(" working-lsp", fw)
    printResult("  out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)), fw)
    printResult("  lsp-number " + tunNum, fw)
    printResult(" protect-lsp", fw)
    printResult("  out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)
    printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)), fw)
    printResult("  lsp-number 1" + tunNum, fw)
    printResult("end\n", fw)
    for intR in listRing:
        flagLink = "working"
        if intR == listTun[0] or intR == listTun[1]:
            continue
        if int(intR) < int(listTun[0]) or int(intR) > int(listTun[1]):
            flagLink = "protect"

        printResult("=========== Create Configuration for R" + intR + " ===========\nconf t", fw)
        linkWorking, linkProtect = getLinkNumbers(intR)
        for sStr in initMPLSTP01:
            printResult(sStr, fw)
        printResult("router-id 1.1.1." + str(intR), fw)
        printResult("l2 router-id 1.1.1." + str(intR), fw)
        for sStr in initBFD:
            printResult(sStr, fw)
        if intR == lastDigit:
            printResult("mpls tp lsp source 1.1.1." + routerNumFirst + " tunnel-tp " + tunNum + " lsp " + flagLink + " destination 1.1.1." + routerNUmLast + " tunnel-tp " + tunNum, fw)
            printResult(" forward-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)) + " out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
            printResult(" reverse-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)) + " out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)

        else:
            printResult("mpls tp lsp source 1.1.1." + routerNumFirst + " tunnel-tp " + tunNum + " lsp " + flagLink + " destination 1.1.1." + routerNUmLast + " tunnel-tp " + tunNum, fw)
            printResult(" forward-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkProtect)) + " out-label " + tunNum + linkWorking + " out-link " + linkWorking, fw)
            printResult(" reverse-lsp", fw)
            printResult("  bandwidth " + str(numBandwidth), fw)
            printResult("  in-label " + tunNum + ''.join(reversed(linkWorking)) + " out-label " + tunNum + linkProtect + " out-link " + linkProtect, fw)
        printResult("end\n", fw)
    fw.write("\n\n")
    fw.write("\n")
    fw.close()


if __name__ == '__main__':
    cmdArgsParser()
    # fileConfigAnalyze()
    if flagClock:
        if flagDebug > 0: print "Flag: Clockwise ... "
        createConfigFileClockwise()
    else:
        if flagDebug > 0: print "Flag: Against Clockwise ... "
        createConfigFileRevers()
    if flagDebug > 0: print "Script complete successful!!! "
    sys.exit()

