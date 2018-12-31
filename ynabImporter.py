#!/usr/bin/python3
import csv
import json
import sys
import os
import re 

if len(sys.argv) < 3:
    print('Gebruik: twee argumenten: (knab|abn) en filename van de csv')
    sys.exit()
elif sys.argv[1] == 'help':
    print('Gebruik: twee argumenten: (knab|abn) en filename van de csv')
    sys.exit()

banknaam = sys.argv[1]
arginputfile = sys.argv[2]
outputfile = os.path.splitext(arginputfile)[0] + '.out.csv'
ibanRegex = re.compile(r'^[a-zA-Z]{2}\d{2}[a-zA-Z0-9]{4}\d{7}([a-zA-Z0-9]?){0,16}$')
csvList = []
count = 0

with open("reknaammatch.json") as reknaammatch:
    rekNaamDict = json.load(reknaammatch)
with open("reknrmatch.json") as reknrmatch:
    rekNrDict = json.load(reknrmatch)

def ynabDate(datumstring):
    datum = re.sub(r'-',r'/',datumstring)
    return(datum)
    
def ynabPayee(rekeningNummer, rekeningHouder):
    if rekeningNummer in rekNrDict.keys():
        return rekNrDict[rekeningNummer]
    elif len(rekeningNummer)>1:
        return rekeningNummer
    elif rekeningHouder in rekNaamDict.keys():
        return rekNaamDict[rekeningHouder]
    else:
        return rekeningHouder.title()

def ynabBedrag(debetCredit, bedrag):
    waarde = re.sub(r',',r'.',bedrag)
    if debetCredit == 'C':
        return(',' + waarde)
    elif debetCredit == 'D':
        return(waarde + ',')

def generateYNABfromKNAB(inputfile):
    with open(inputfile, newline='') as csvfile:
        bankReader = csv.reader(csvfile, delimiter=";", quotechar='\"')
        for row in bankReader:
            if ibanRegex.findall(row[0]):
                csvList.append(ynabDate(row[1]) + ',' + ynabPayee(row[5], row[6]) + ',,,' + ynabBedrag(row[3], row[4]))

if banknaam.lower() == 'knab':
    generateYNABfromKNAB(arginputfile)
elif banknaam.lower() == 'abn':
    print('generateABN(inputfile)')
else:
    print('bank niet ondersteund')

with open(os.path.splitext(arginputfile)[0] + '.out.csv', 'w') as outfile:
    outfile.write('Date,Payee,Category,Memo,Outflow,Inflow\n')
    for i in csvList:
        count += 1
        outfile.write(i + '\n')

print(str(count) + ' transacties naar ' + os.path.splitext(arginputfile)[0] + '.out.csv geschreven.')
