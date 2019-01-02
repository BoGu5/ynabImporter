#!/usr/bin/python3
import csv
import json
import sys
import os
import re 

#Check of er genoeg argumenten zijn meegegeven
if len(sys.argv) < 3:
    print('Gebruik: twee argumenten: (knab|abn) en filename van de csv')
    sys.exit()
elif sys.argv[1] == 'help':
    print('Gebruik: twee argumenten: (knab|abn) en filename van de csv')
    sys.exit()

#Lees de argumenten van de commandline
argbanknaam = sys.argv[1]
arginputfile = sys.argv[2]
#Bepaal de outputfile
outputfile = os.path.splitext(arginputfile)[0] + '.out.csv'
#De regexxen om bepaalde transacties te identificeren
ibanRegex = re.compile(r'^[a-zA-Z]{2}\d{2}[a-zA-Z0-9]{4}\d{7}([a-zA-Z0-9]?){0,16}&')
sepaRegex = re.compile(r"[a-zA-Z]{2}\d{2}[a-zA-Z0-9]{4}\d{7}([a-zA-Z0-9]?){0,16}")
beaRegex = re.compile(r'^BEA.*PAS\d{3}')
geaRegex = re.compile(r'^GEA.*PAS\d{3}')
stortingRegex = re.compile(r'^STORTING')
omschrijvingRemiRegex = re.compile(r'/REMI/(.*)/EREF/')
omschrijvingKenmerkRegex = re.compile(r'Omschrijving: (.*)Kenmerk:')
pinInWinkelRegex = re.compile(r'\d{2}\.\d{2}\.\d{2}\/\d{2}\.\d{2} (.*),PAS\d{3}')

#De csvlijst waar alles in komt
csvList = []
count = 0

#Open twee json files met een dictionary. De een met een lijst met importnamen en friendlynames en de ander met een IBAN naar friendlyname 
with open("reknaammatch.json") as reknaammatch:
    rekNaamDict = json.load(reknaammatch)
with open("reknrmatch.json") as reknrmatch:
    rekNrDict = json.load(reknrmatch)

#Trek de datum uit een csv en bouw daar een YNAB versie van
def ynabDate(datumstring, banknaam):
    if banknaam == 'knab':
        datum = re.sub(r'-',r'/',datumstring)
        return(datum)
    elif banknaam == 'abn':
        datum = datumstring[6:8] + '/' + datumstring[4:6] + '/' + datumstring[0:4]
        return(datum)
    
    
def ynabPayeeKNAB(rekeningNummer, rekeningHouder):
    if rekeningNummer in rekNrDict.keys(): #Kijk of het rekeningnummer bekend is in de dictionary
        return rekNrDict[rekeningNummer]
    elif len(rekeningNummer)>1:             #Kijk of er een IBAN is en geef deze dan terug
        return rekeningNummer
    elif rekeningHouder in rekNaamDict.keys(): #Kijk of de naam uit de csv voorkomt in de friendlynames
        return rekNaamDict[rekeningHouder]
    else:
        return rekeningHouder.title() #Anders geef ruw de rekeningHouder terug

def ynabPayeeABN(commentaarvak):
    omschrijving = None
    #IBAN: 
    #SEPA Overboeking                 IBAN: NL00ABNA1234567890        BIC: ABNANL2A                    Naam: Jantje Pietersen          Omschrijving: Ik dacht ik heb geld teveel, dus ik stort wat
    if sepaRegex.search(commentaarvak):
        sepa = sepaRegex.search(commentaarvak)
        rekeningnummer = sepa.group(0)
        if rekeningnummer in rekNrDict.keys():
            rekeningnummer = rekNrDict[rekeningnummer]
        omschrijving = omschrijvingRemiRegex.search(commentaarvak)
        if omschrijving == None:
            omschrijving = omschrijvingKenmerkRegex.search(commentaarvak)
        if omschrijving != None:
            omschrijving = omschrijving.group(1)
        if omschrijving == None:
            omschrijving = ''
        return rekeningnummer, '', omschrijving.rstrip()
    #PIN: 
    #BETAALAUTOMAAT
    #BEA   NR:Z1X3X9   01.01.19/13.15 Gebr. Van Beek Kaash VEE,PAS111
    elif beaRegex.search(commentaarvak):
        gepind = pinInWinkelRegex.search(commentaarvak)
        rekeningHouder = gepind.group(1)
        if rekeningHouder in rekNaamDict.keys():
            return rekNaamDict[rekeningHouder], '', ''
        else: 
            return rekeningHouder, '', ''
    #Begint met BEA Eindigt met PAS???
    #GELDAUTOMAAT:
    #GEA   NR:S5A011   01.02.19/12.21 AFRIKADREEF 9 AMSTERDAM ,PAS111
    elif geaRegex.search(commentaarvak):
        return 'Bankautomaat', '', 'Contant gepind'
    #Storting: 
    #STORTING      01-03-19 14:03 UUR GELDAUTOMAAT   S4Y123           AFRIKADREEF 2 AMSTERDAM,PAS 111                                 
    elif stortingRegex.search(commentaarvak):
        return 'Bankautomaat', 'Income', 'Storting contant'
    
    #Pakketkosten ABN
    #ABN AMRO Bank N.V.               BetaalGemak E               3,75 
    elif re.match(r'ABN AMRO Bank N.V.', commentaarvak):
        return 'ABN Amro', 'Vaste lasten overig: Bankkosten ABN', 'Pakketkosten'
    
    else:
        return 'Kon er geen chocola van maken', '', commentaarvak
    
    

def ynabBedrag(debetCredit, bedrag, banknaam):
    waarde = re.sub(r',',r'.',bedrag)
    if banknaam == 'knab':
        if debetCredit == 'C':
            return(',' + waarde)
        elif debetCredit == 'D':
            return(waarde + ',')
    elif banknaam == 'abn':
        floatwaarde = float(waarde)
        if floatwaarde >= 0:
            return(',' + str(floatwaarde))
        elif floatwaarde < 0:
            floatwaarde *= -1
            return(str(floatwaarde) + ',') 


def generateYNABfromKNAB(inputfile, banknaam):
    with open(inputfile, newline='') as csvfile: #Open de inputfile
        bankReader = csv.reader(csvfile, delimiter=";", quotechar='\"') #Lees deze als csv in
        for row in bankReader: #Loop de regels af
            if ibanRegex.findall(row[0]): #kijk of de zin in de csv begint met een IBAN
                csvList.append(ynabDate(row[1], banknaam) + ',' + ynabPayeeKNAB(row[5], row[6]) + ',,,' + ynabBedrag(row[3], row[4], banknaam)) # Schrijf alle waarden naar een list

def generateYNABfromABN(inputfile, banknaam):
    with open(inputfile, newline='') as csvfile: #Open de inputfile 
        bankReader = csv.reader(csvfile, delimiter="\t", quotechar='\'') #Lees deze als csv in
        for row in bankReader: #Loop de regels af
            csvList.append(ynabDate(row[5], banknaam) + ',' + ynabPayeeABN(row[7])[0] + ',' + ynabPayeeABN(row[7])[1] + ',' + re.sub(r',',r'.',ynabPayeeABN(row[7])[2]) + ',' + ynabBedrag(None, row[6], banknaam))

#check welke bank er als command line argument mee is genomen en kies daar de procedure op uit
if argbanknaam.lower() == 'knab':                
    generateYNABfromKNAB(arginputfile, 'knab')
elif argbanknaam.lower() == 'abn':
    generateYNABfromABN(arginputfile, 'abn')
else:
    print('bank niet ondersteund')

#Schrijf de lijst csvList naar output csv met naam van de inputfile + .out.csv en tel het aantal transacties
with open(outputfile, 'w') as outfile:
    outfile.write('Date,Payee,Category,Memo,Outflow,Inflow\n')
    for i in csvList:
        count += 1
        outfile.write(i + '\n')

#Print het aantal transacties naar de console
print(str(count) + ' transacties naar ' + outputfile + ' geschreven.')
