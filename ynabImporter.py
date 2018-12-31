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

def ynabDate(inputLijst):
    datum = re.sub(r'-',r'/',inputLijst[1])
    return(datum)
    
def ynabPayee(inputLijst):
    if inputLijst[5] in rekNrDict.keys():
        return rekNrDict[inputLijst[5]]
    elif len(inputLijst[5])>1:
        return inputLijst[5]
    elif inputLijst[6] in rekNaamDict.keys():
        return rekNaamDict[inputLijst[6]]
    else:
        return inputLijst[6].title()

def ynabBedrag(inputLijst):
    waarde = re.sub(r',',r'.',inputLijst[4])
    if inputLijst[3] == 'C':
        return(',' + waarde)
    elif inputLijst[3] == 'D':
        return(waarde + ',')

def generateYNABfromKNAB(inputfile):
    with open(inputfile, newline='') as csvfile:
        bankReader = csv.reader(csvfile, delimiter=";", quotechar='\"')
        for row in bankReader:
            if ibanRegex.findall(row[0]):
                csvList.append(ynabDate(row) + ',' + ynabPayee(row) + ',,,' + ynabBedrag(row))

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
