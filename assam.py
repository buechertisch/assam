#!/usr/bin/python
# -*- coding: windows-1258 -*-

# Nötiges Encoding: cp 125*

# Assam Version 2.0 beta 7
# Assam is free and licensed under GPL
# Author: Franziska Hausmann <franziska.hausmann@posteo.de>
# Date: 2016-05-22

# Änderungen in Version 2.0

# Empfohlener Ladenpreis
# Neupreisanzeige
# Neue Entscheidungslogik
# CD-Recherche (in separatem Programm)
# Farbcode
# Quittungen
# Recherche von ISBNs aus Datei
# Assam arbeitet intern mit ISBN-13.
# Quirks bei Vorbestellungen und bei Warnung vor langen Antwortzeiten behoben
# Kategorie L50
# "Ein Ort zum Lesen"-Abgleich
# Anlegen, "drucken" und Löschen von Vorbestellungen


#(HTMLParser().unescape()	amazon-Titel
# eval("u'" + x + "'")	easyankauf-Titel

import time
import httplib
import re
import isbn
import threading
import csv
import webbrowser
from config import *
from colorama import init

from util import (string_to_float, get_blacklist, vorbestellungen_einlesen,
                  get_ort_zum_lesen)

init()

GEWICHTE = ('1', '2', '3')
my_isbn = None
interaktiv = True


def vorbestellungen_schreiben(vorbestellungsdatei):
    vorbestellungscsv = open(vorbestellungsdatei, 'wb')
    csvwriter = csv.writer(vorbestellungscsv, delimiter=';',
                           quotechar='"', quoting=csv.QUOTE_ALL)
    csvwriter.writerow(['ISBN'] + vorbestellungsheader)
    for vorbest_isbn in vorbestellungen:
        for vorbestellung in vorbestellungen[vorbest_isbn]:
            vorbestellungscsv.write(vorbest_isbn + ';')
            csvwriter.writerow(vorbestellung)
    vorbestellungscsv.close()


def debug_response(response):
    resp = open('response.htm', 'w')
    print >> resp, response
    resp.close()


def log(ereignis):
    logfile = open('fehler-isbns.csv', 'a')
    print >> logfile, time.strftime(
        '%Y-%m-%d_%H:%M') + ';' + my_isbn + ';' + ereignis
    logfile.close()



def float_to_string(preis):  # Konvertiert z.B. 2.5 zu "2,50".
    return ("%#.2f" % preis).replace('.', ',')


def print_title():
    print (amazon.Titel or easyankauf.Titel or 'Unbekannter Titel ') + \
        ' (' + (amazon.Ausgabe or easyankauf.Ausgabe or 'Unbekannte Ausgabe') + ')'
    print ''


def print_gewinntabelle():
    print 'Neupreis: ' + (float_to_string(amazon.Neupreis) + "¤" if amazon.Neupreis else '/')
    print 'Amazon-Verkaufsrang: ' + (amazon.Rang_Text or '/')

    def preis_format(preis):
        return '%10s' % float_to_string(preis) if preis else '%10s' % '/'

    print '%-20s' % '' + '%10s' % 'Preis' + '%11s' % 'Gewinn 1' + '%11s' % 'Gewinn 2' + '%11s' % 'Gewinn 3' + '%11s' % 'Kommentar'  # Statische Kopfzeile

    for plattform in plattformen_created:  # Tabellenkörper
        print '%-20s' % plattform.Name + preis_format(plattform.Preis),
        for gewicht in GEWICHTE:
            print preis_format(plattform.Gewinn[gewicht]),
        print ' ' + plattform.Kommentar,
        print ''
    print ''




class Buch(object):

    def __init__(self):
        self.Gewinn = {'1': [], '2': [], '3': []}
        self.Preise = []
        self.Preise_gewichtet = []
        self.Verkaufsanteile = []
        self.Entscheidung = {'1': [], '2': [], '3': []}
        self.UVP = None
        self.gewichtsrelevanz = False

    def print_UVP(self):
        if self.UVP:
            print "Ladenpreisempfehlung:", float_to_string(self.UVP) + "¤"
        else:
            print "keine Ladenpreisempfehlung."
        print ''

    def print_entscheidung(self, gewicht):
        for kategorie in self.Entscheidung[gewicht]:
            # '\x1b[32mW\x1b[0m'
            print ' ' + (kategorie if (not(learners_mode)) else lerntexte[kategorie]),
        print ''

    def start(self):
        for plattformobjekt in plattformen_created:
            if plattformobjekt.Preis:  # Preise einsammeln
                self.Preise.append(plattformobjekt.Preis)
                self.Preise_gewichtet.append(
                    plattformobjekt.Preis * plattformobjekt.Verkaufsanteil)
                self.Verkaufsanteile.append(plattformobjekt.Verkaufsanteil)

            # Gewinne von non-Amazon, non-Buchfreund-Plattformen (!) einsammeln
            if plattformobjekt in [amazon, buchfreund]:
                continue
            for gewicht in GEWICHTE:
                self.Gewinn[gewicht].append(plattformobjekt.Gewinn[gewicht])

        if sum(self.Verkaufsanteile) > 0:  # UVP berechnen
            # 90% des gewichteten Mittels, dabei maximal des Amazon-Preises
            # falls es ihn gibt.
            self.UVP = 0.9 * min(sum(self.Preise_gewichtet) / sum(
                self.Verkaufsanteile), (amazon.Preis if amazon.Preis else ''))

        # Entscheiden:
        for gewicht in GEWICHTE:
            self.Gewinn[gewicht].sort(reverse=True)
            if self.Preise == []:  # Wenn das Buch gar nicht angeboten wird: O/Ox
                self.Entscheidung[gewicht].append('O/Ox')
                if easyankauf.Gewinn[gewicht] > easyankaufminimum:
                    self.Entscheidung[gewicht].append('W')
                continue
            # Wenn Easyankauf mehr bringt als jede andere Plattform: W!
            if easyankauf.Gewinn[gewicht] == max([amazon.Gewinn[gewicht]] + self.Gewinn[gewicht]) and easyankauf.Gewinn[gewicht] > 3:
                self.Entscheidung[gewicht].append('W!')
            # Wenn das Buch auf Amazon genug Gewinn bringt: O/Ox
            if amazon.Gewinn[gewicht] >= mindestgewinn:
                self.Entscheidung[gewicht].append('O/Ox')
                if easyankauf.Gewinn[gewicht] > easyankaufminimum:
                    self.Entscheidung[gewicht].append('W')
                continue
            if amazon.Rang <= o2_rang:
                if len(self.Gewinn[gewicht]) > 1:
                    # Wenn der zweithöchste non-Amazon-Wert über dem
                    # Mindestgewinn liegt: O/Ox
                    if self.Gewinn[gewicht][1] >= mindestgewinn:
                        self.Entscheidung[gewicht].append('O/Ox')
                        continue
                    # Wenn es nur einen non-None, non-Amazon-Wert gibt und der
                    # über dem Mindestgewinn liegt: O/Ox
                    if self.Gewinn[gewicht][1] == None and self.Gewinn[gewicht][0] >= mindestgewinn:
                        self.Entscheidung[gewicht].append('O/Ox')
                        continue
                # Wenn der einzige vorhandene (weil Plattformen ausgeschaltet
                # wurden) non-Amazon-Wert über dem Mindestgewinn liegt: O/Ox
                elif len(self.Gewinn[gewicht]) == 1 and self.Gewinn[gewicht][0] >= mindestgewinn:
                    self.Entscheidung[gewicht].append('O/Ox')
                    continue
            # Die Kriterien für H:
            if amazon.Rang <= h_rang and int(gewicht) < 3:
                if amazon.Gewinn[gewicht] >= h_mindestgewinn:
                    self.Entscheidung[gewicht].append('H')
                elif amazon.Rang <= h2_rang:
                    self.Entscheidung[gewicht].append('H')
            if markt and amazon.Rang <= markt_rang and amazon.Preis <= markt_hoechstpreis:  # Kriterien für L50
                self.Entscheidung[gewicht].append('L50')
            self.Entscheidung[gewicht].append('L')					# L, Y, W und K:
            self.Entscheidung[gewicht].append('Y')
            if easyankauf.Gewinn[gewicht] > easyankaufminimum:
                self.Entscheidung[gewicht].append('W')
            self.Entscheidung[gewicht].append('K')
        if self.Entscheidung['1'] != self.Entscheidung['3']:
            self.gewichtsrelevanz = True


class Verkauf(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.Preis = None
        self.Gewinn = {'1': None, '2': None, '3': None}

    def gewinn(self):
        for gewicht in self.Gewinn:
            self.Gewinn[gewicht] = (
                # Vom ausgewiesenen Preis: MwSt abziehen
                (self.Preis - self.Porto_dekl[gewicht]) * (1 - mwst)
                * (1 - self.Provision)  # Provision abziehen
                - self.Fixkosten  # Fixkosten abziehen
                # Tatsächlich anfallendes Porto und Zusatzkosten abziehen
                - (porto_real[gewicht] + zusatzkosten)
                # Das ausgewiesene Porto wieder addieren
                + self.Porto_dekl[gewicht]
            )

    def log(self, ereignis):
        log(ereignis)

class Amazon(Verkauf):

    def __init__(self, my_isbn):
        Verkauf.__init__(self)
        self.Name = 'Amazon'
        self.Titel = None
        self.Ausgabe = None
        self.Rang = None
        self.Rang_Text = None
        self.Neupreis = None
        # VerkaufspreisUNabhängige Kosten (Einstellgebühren etc.)
        self.Fixkosten = amazon_kosten['Fixkosten']
        # Anteil des Verkaufspreises, den der Vermittler bekommt.
        self.Provision = amazon_kosten['Provision']
        # Ausgewiesenes Porto/Verpackung. Dieser Betrag ist immun gegen
        # Provisionsabzüge.
        self.Porto_dekl = amazon_kosten['Porto_dekl']
        self.Verkaufsanteil = amazon_verkaufsanteil
        self.host = 'www.amazon.de'
        self.pfad = '/o/ASIN/' + isbn.toI10(my_isbn)
        self.Kommentar = ''
        self.Dauer = None

    def run(self):
        self.Start = time.time()
        # Strings und Regexps
        ergebnislos_string1 = 'gibt es auf unserer Website nicht'
        ergebnislos_string2 = 'Derzeit nicht verf'
        titel_regexp = '(?s)<span id="productTitle" class="a-size-large">(.*?)</span>.*?<span class="a-size-medium a-color-secondary a-text-normal">(.*?)</span>'
        rang_regexp = '<b>Amazon Bestseller-Rang:</b> \n*Nr\..([\d.]*) in'
        preisblock_regexp = '(?s)(<div class="a-section a-spacing-small a-spacing-top-small">.*?ab <span class=\'a-color-price\'>EUR \d+,\d+</span></span>.*?</div>)'
        preisstr_regexp = "<span class='a-color-price'>EUR (\d+,\d+)</span></span>"
        neupreis_regexp = '<span class="a-size-medium a-color-price offer-price a-text-normal">EUR (\d+,\d+)</span>'
        #preisstr_regexp='<span class="price".*?>EUR (\d+,\d+)</span>'
        # Verbindung
        verbindung = httplib.HTTPSConnection(self.host, timeout=timeout)
        self.log('0')
        try:
            verbindung.request('GET', self.pfad)
            response = verbindung.getresponse().read()
            # Fehler abfangen
            if response == '':
                self.Kommentar += 'Keine Antwort. '
                self.log('1')
                return
            if ergebnislos_string1 in response:
                #self.Kommentar+='Unbekannter Titel. '
                return
            # Titel
            try:
                self.Titel, self.Ausgabe = re.search(
                    titel_regexp, response).groups()
            except Exception:
                self.Kommentar += 'Auslesefehler (Titel). '
                self.log('2')
            # Bestseller-Rang
            try:
                self.Rang_Text = re.search(rang_regexp, response).groups()[0]
                self.Rang = int(re.sub('\.', '', self.Rang_Text))
            except Exception:
                #self.Kommentar+='Auslesefehler (Verkaufsrang). '
                self.log('3')
            # Auch 'derzeit nicht verfügbare' Bücher haben Titel und
            # Bestsellerrang.
            if ergebnislos_string2 in response:
                #self.Kommentar+='Kein Angebot. '
                return
            # Preis
            try:
                preisblock = re.search(preisblock_regexp, response).group()
                preisstr = re.findall(preisstr_regexp, preisblock)
                self.Preis = min([string_to_float(preis)
                                  for preis in preisstr]) + 3
            except Exception:
                self.Kommentar += 'Auslesefehler (Preis). '
                self.log('4')
                return

            try:
                self.Neupreis = string_to_float(
                    re.search(neupreis_regexp, response).groups()[0])
            except Exception:
                #self.Kommentar+='Auslesefehler (Neupreis). '
                self.log('4.5')

        except Exception:
            self.Kommentar += 'Offline oder Zeitüberschreitung. '
            self.log('5')
        if self.Preis:
            self.gewinn()


class ZVAB(Verkauf):

    def __init__(self, my_isbn):
        Verkauf.__init__(self)
        self.Name = 'ZVAB'
        self.Preise = []
        self.Fixkosten = zvab_kosten['Fixkosten']
        self.Provision = zvab_kosten['Provision']
        self.Porto_dekl = zvab_kosten['Porto_dekl']
        self.Verkaufsanteil = zvab_verkaufsanteil
        self.host = 'www.zvab.com'
        self.pfad = '/servlet/SearchResults?bi=0&ds=1&exactsearch=on&isbn=' + \
            my_isbn + '&recentlyadded=all&sortby=17&sts=t&wassortselected=true'
        self.Kommentar = ''
        self.Dauer = None

    def run(self):
        self.Start = time.time()
        # Strings und Regexps
        ergebnislos_string = 'Leider konnten keine Treffer'
#		preis_regexp='<span class="total">Gesamt:&nbsp;EUR&nbsp;(\d+,\d+)</span>'
        preisblock_regexp = '(?s)Preis:(.*?)Innerhalb Deutschland'
        preis_und_porto_regexp = 'EUR (\d+,\d+)'

        verbindung = httplib.HTTPConnection(self.host, timeout=timeout)
        try:
            verbindung.request('GET', self.pfad)
            response = verbindung.getresponse().read()
            # Fehler abfangen
            if response == '':
                self.Kommentar += 'Keine Antwort'
                self.log('6')
                return
            if ergebnislos_string in response:
                return
            else:
                # Preise laut ZVAB
                try:
                    preisblock = re.search(preisblock_regexp, response).group()
                    preis_und_porto = re.findall(
                        preis_und_porto_regexp, preisblock)
                    self.Preis = sum([string_to_float(wert)
                                      for wert in preis_und_porto])
                except Exception:
                    self.Kommentar += 'Auslesefehler'
                    self.log('7')
        except Exception:
            self.Kommentar += 'Offline oder Zeitüberschreitung. '
            self.log('8')
        if self.Preis:
            self.gewinn()


class Booklooker(Verkauf):

    def __init__(self, my_isbn):
        Verkauf.__init__(self)
        self.Name = 'Booklooker'
        self.Preis = None
        self.Porto = 0
        self.Fixkosten = booklooker_kosten['Fixkosten']
        self.Provision = booklooker_kosten['Provision']
        self.Porto_dekl = booklooker_kosten['Porto_dekl']
        self.Verkaufsanteil = booklooker_verkaufsanteil
        self.host = 'www.booklooker.de'
        self.pfad = '/app/result.php?sortOrder=preis_total&isbn=' + my_isbn
        self.Kommentar = ''
        self.Dauer = None

    def run(self):
        self.Start = time.time()
        # Strings und Regexps
        ergebnislos_string = 'Es wurden keine passenden Artikel'

        preisblock_regexp = "(?s)<div class='productPrices'>.*?</div>"
        rohpreis_regexp = "<span class='price'>(\d+,\d+)&nbsp;&euro;</span>"
        porto_regexp = '</a> (\d+,\d+)&nbsp;&euro;</div>'

        # Verbindung zu Booklooker
        verbindung = httplib.HTTPSConnection(self.host, timeout=timeout)
        try:
            verbindung.request('GET', self.pfad)
            response = verbindung.getresponse().read()
            # Fehler abfangen
            if response == '':
                self.Kommentar += 'Keine Antwort. '
                self.log('9')
                return
            if ergebnislos_string in response:
                return
            # Block mit Preis und Porto extrahieren
            try:
                preisblock = re.search(preisblock_regexp, response).group()
            except Exception:
                self.Kommentar += 'Auslesefehler (Preis+Porto). '
                self.log('10')
                return
            # Rohpreis laut Booklooker
            try:
                self.Preis = string_to_float(
                    re.search(rohpreis_regexp, preisblock).groups()[0])
            except Exception:
                self.Kommentar += 'Auslesefehler (Preis). '
                self.log('11')
                return
            # Porto laut Booklooker
            if '???' in preisblock:
                self.Kommentar += 'Keine Versandkosten angegeben.'
            elif 'versandkostenfrei' or 'ab 0,00' in preisblock:
                next
            else:
                try:
                    self.Porto = string_to_float(
                        re.search(porto_regexp, preisblock).groups()[0])
                    self.Preis += self.Porto
                except Exception:
                    self.Kommentar += 'Auslesefehler (Porto). '
                    self.log('12')
        except Exception:
            self.Kommentar += 'Offline oder Zeitüberschreitung. '
            self.log('13')
        if self.Preis:
            self.gewinn()


class Buchfreund(Verkauf):

    def __init__(self, my_isbn):
        Verkauf.__init__(self)
        self.Name = 'Buchfreund'
        self.Rohpreis = None
        self.Porto = 0
        self.Fixkosten = buchfreund_kosten['Fixkosten']
        self.Provision = buchfreund_kosten['Provision']
        self.Porto_dekl = buchfreund_kosten['Porto_dekl']
        self.Verkaufsanteil = buchfreund_verkaufsanteil
        self.host = 'www.buchfreund.de'
        self.pfad = '/results.php?q=' + my_isbn + '&sO=7'
        self.Kommentar = ''
        self.Dauer = None

    def run(self):
        self.Start = time.time()
        # Strings und Regexps
        ergebnislos_string = 'Partnerplattform www.buchhai.de'
        preisblock_regexp = '<div class="resultPrice"><table.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n.*?</tr></table>'
        portofrei_regexp = '<td class="resultShipping" align="right">Inklusive</td>'
        rohpreis_regexp = '<td align="right">(\d+,\d+) EUR</td>'
        porto_regexp = '<td class="resultShipping" align="right">(\d+,\d+) EUR</td>'
        # Verbindung zu Buchfreund
        verbindung = httplib.HTTPSConnection(self.host, timeout=timeout)
        try:
            verbindung.request('GET', self.pfad)
            response = verbindung.getresponse().read()

            # Fehler abfangen
            if response == '':
                self.Kommentar += 'Keine Antwort. '
                self.log('14')
                return
            if ergebnislos_string in response:
                #self.Kommentar+='Kein Angebot. '
                return
            # Block mit Preis und Porto extrahieren
            try:
                preisblock = re.search(preisblock_regexp, response).group()
            except Exception:
                self.Kommentar += 'Auslesefehler (Preis+Porto). '
                self.log('15')
                return
            # Rohpreis
            try:
                self.Preis = string_to_float(
                    re.search(rohpreis_regexp, preisblock).groups()[0])
            except Exception:
                self.Kommentar += 'Auslesefehler (Preis). '
                self.log('16')
                return
            # Porto laut Buchfreund
            try:
                if portofrei_regexp in preisblock:
                    next
                else:
                    self.Porto = string_to_float(
                        re.search(porto_regexp, preisblock).groups()[0])
                    self.Preis += self.Porto
            except Exception:
                self.Kommentar += 'Auslesefehler (Porto). '
                self.log('17')
        except Exception:
            self.Kommentar += 'Offline oder Zeitüberschreitung. '
            self.log('17.5')

        if self.Preis:
            self.gewinn()


class Easyankauf(threading.Thread):

    def __init__(self, my_isbn):
        threading.Thread.__init__(self)
        self.Name = 'Easyankauf'
        self.Preis = None
        self.Amazon_Preis = None
        self.Gewinn = {'1': None, '2': None, '3': None}
        self.Verkaufsanteil = easyankauf_verkaufsanteil
        self.host = 'www.easy-ankauf.de'
        self.pfad = '/ajax/angebote'
        self.my_isbn = my_isbn
        self.Kommentar = ''
        self.Titel = None
        self.Ausgabe = None
        self.Dauer = None

    def log(self, event):
        log(event)

    def run(self):
        self.Start = time.time()
        # Strings und Regexps
        ergebnislos_string = 'LOOKUP_FAILED'
        requested_string = 'LOOKUP_REQUESTED'
        successful_string = 'LOOKUP_SUCCESSFUL'
        preis_regexp = '"price":(\d+\.?\d*)}}'
        titel_regexp = '"title":"(.*?)"'
        ausgabe_regexp = '"binding":"(.*?)"'

        # Verbindung zu Easyankauf
        verbindung = httplib.HTTPSConnection(self.host)
        try:
            attempts = timeout
            while attempts:
                verbindung.request('POST', self.pfad, 'codes%5B1%5D=' + self.my_isbn, {
                                   'Accept-Encoding': 'gzip, deflate', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded'})
                response = verbindung.getresponse().read()
                # Fehler abfangen
                if response == '':
                    self.Kommentar += 'Keine Antwort. '
                    self.log('18')
                    return None
                elif ergebnislos_string in response:
                    #self.Kommentar+='Unbekannter Titel. '
                    self.log('19')
                    return None
                elif requested_string in response:
                    attempts -= 1
                    # Easyankauf braucht eine Weile um den Preis zu ermitteln.
                    # Es hilft nicht, viele Anfragen in kurzer Zeit zu stellen,
                    # besser nach je 1 sec. nochmal probieren.
                    time.sleep(1)
                    continue
                elif successful_string in response:
                    # Titel laut Easyankauf
                    try:
                        self.Titel = re.search(
                            titel_regexp, response).groups()[0]
                    except Exception:
                        self.Kommentar += 'Auslesefehler (Titel). '
                        self.log('20')

                    # Ausgabe laut Easyankauf
                    try:
                        self.Ausgabe = re.search(
                            ausgabe_regexp, response).groups()[0]
                    except Exception:
                        self.Kommentar += 'Auslesefehler (Ausgabe). '
                        self.log('21')

                    # Preis laut Easyankauf
                    try:
                        gewinn = float(
                            re.search(preis_regexp, response).groups()[0])
                        if gewinn == 0:
                            gewinn = None
                            #self.Kommentar+='Kein Angebot. '
                        self.Gewinn = {'1': gewinn, '2': gewinn, '3': gewinn}
                        return self.Preis
                    except Exception:
                        self.Kommentar += 'Auslesefehler (Preis). '
                        self.log('22')
                        return None
                else:
                    self.Kommentar += 'Verbindungsfehler [1]. '
                    self.log('23')
                    return None
            self.Kommentar += 'Offline oder Zeitüberschreitung. '
            self.log('23.5')
        except Exception:
            self.Kommentar += 'Verbindungsfehler [2]. '
            self.log('24')




class Ebay(Verkauf):

    def __init__(self, my_isbn):
        Verkauf.__init__(self)
        self.Name = 'Ebay'
        self.Porto = 0
        self.Preis = None
        self.Fixkosten = ebay_kosten['Fixkosten']
        self.Provision = ebay_kosten['Provision']
        self.Porto_dekl = ebay_kosten['Porto_dekl']
        self.Verkaufsanteil = ebay_verkaufsanteil
        self.host = 'www.ebay.de'
        # _ipg bestimmte mal die Suchergebnisse pro Seite. _sop=15 sortiert
        # nach Preis+Porto. _rdc=1 verhindert offenbar Redirects auf die erste
        # Ergebnisseite
        self.pfad = '/sch/i.html?_ipg=1&LH_BIN=1&_sop=15&_nkw=' + my_isbn + '&_rdc=1'
        # www.ebay.de/sch/i.html?_ipg=1&LH_BIN=1&_sop=15&gbr=1&_nkw=9783492264402&_rdc=1
        self.Kommentar = ''
        self.Dauer = None

    def run(self):
        self.Start = time.time()

        ergebnislos_string = '<b>0</b> Ergebnisse gefunden'
        preis_regexp = '(?s)<li class="lvprice prc">.*?<b>EUR</b> (\d+,\d+)</span>'
        portomodus_regexp = 'class=(".*?bfsp"|"fee")'
        porto_regexp = '(?s)<span class="fee">.*?\+ EUR (\d+,\d+) Versand</span>'
        #porto_regexp = '<span class="fee">.\n.*?\+ EUR (\d+,\d+) Versand</span>'

        # Verbindung zu Ebay
        try:
            redirect_countdown = 10
            while redirect_countdown > 0:
                redirect_countdown -= 1
                verbindung = httplib.HTTPConnection(self.host, timeout=timeout)
                verbindung.request('GET', self.pfad)
                response_complete = verbindung.getresponse()
                location = response_complete.getheader('Location')
                if location:
                    try:
                        # Bei Redirect wird die Schleife neu durchlaufen.
                        pfad = re.search(
                            'http://www.ebay.de(:80)?(.*)', location).groups()[1]
                        location = None
                    except Exception:
                        break
                else:
                    break
            response = response_complete.read()
            # Fehler abfangen
            if response == '':
                self.Kommentar += 'Keine Antwort. '
                self.log('25')
                return
            if ergebnislos_string in response:
                return  # Kein Angebot

            # Preis
            try:
                self.Preis = string_to_float(
                    re.search(preis_regexp, response).groups()[0])
            except Exception:
                self.Kommentar += 'Auslesefehler (Preis). '
                self.log('26')
                return

            # Porto
            if re.search(portomodus_regexp, response):
                if re.search(portomodus_regexp, response).groups()[0] == '"fee"':
                    try:
                        self.Porto = string_to_float(
                            re.search(porto_regexp, response).groups()[0])
                        self.Preis += self.Porto
                    except Exception:
                        self.Kommentar += 'Auslesefehler (Porto) [1]. '
                        self.log('27')
                else:
                    next  # Portofrei
            else:
                self.Kommentar += 'Auslesefehler (Porto) [2]. '
                self.log('28')

            if self.Preis:
                self.gewinn()
        except Exception:
            self.Kommentar += 'Offline oder Zeitüberschreitung. '
            self.log('29')
#=Programmstart===========================================================

# Hier wird jedes _mögliche_ Plattformobjekt mit None-Werten initialisiert
# weil die spaeter erwartet werden.
for plattform in plattformen_available:
    exec(plattform.lower() + ' = ' + plattform + '("3981471601")')

# Gibt eins der möglichen Intros aus.
print '\n' + 'Willkommen bei Assam - ' + intros[int(str(time.time())[-1]) % len(intros)] + '\n'

vorbestellungsheader, vorbestellungen = vorbestellungen_einlesen(
    vorbestellungsdatei)
# um evt. Fehlerzeilen in der Datei zu entfernen
vorbestellungen_schreiben(vorbestellungsdatei)

print "Es wurden", sum(len(vorbestellungen[isbn]) for isbn in vorbestellungen), "Vorbestellungen für", len(vorbestellungen), "verschiedene Titel eingelesen"

blacklistheader, blacklist = get_blacklist()
print "Es wurden", len(blacklist), "Einträge der Schwarzen Liste eingelesen"

ortzumlesenheader, ortzumlesen = get_ort_zum_lesen()
print "Es wurden", len(ortzumlesen), 'Einträge für "Ein Ort zum Lesen" eingelesen'


while 1:  # Während das Programm läuft
    if interaktiv:  # Interaktiver Modus
        while 1:  # Bis eine gültige Eingabe gemacht wurde
            print '_' * 80, '\n'
            eingabe = raw_input('ISBN: ')

            if eingabe == '':
                continue

            elif isbn.isValid(eingabe):
                my_isbn = isbn.toI13(eingabe)
                if learners_mode:
                    print '\n' * 55
                break

            elif 'vorbest' in eingabe.lower():
                vorbestellungsheader, vorbestellungen = vorbestellungen_einlesen(
                    vorbestellungsdatei)
                print 'Vorbestellung eingeben:'
                key = ''
                key = raw_input('ISBN? ')
                while not isbn.isValid(key):
                    key = raw_input(
                        'Das war keine gültige ISBN. Bitte gib eine ISBN ein: ')
                key = isbn.toI13(key)
                neue_vorbestellung = []
                if key not in vorbestellungen:
                    vorbestellungen[key] = []
                for i in vorbestellungsheader:
                    if i == 'Bestelldatum':
                        neue_vorbestellung += [time.strftime('%d.%m.%Y')]
                    else:
                        neue_vorbestellung += [raw_input(i + '? ')]
                vorbestellungen[key] += [neue_vorbestellung]
                vorbestellungen_schreiben(vorbestellungsdatei)

            elif 'datei' in eingabe.lower():
                try:
                    isbnquelle = re.search('.*? (.*)', eingabe).groups()[0]
                    isbndatei = open(isbnquelle, 'r')
                    ergebnisdatei = open(isbnquelle + '-ergebnisse.csv', 'w')
                    print >> ergebnisdatei, ';'.join([
                        'ISBN',
                        'Titel',
                        'Kategorien [1]',
                        'Kategorien [2]',
                        'Kategorien [3]'
                    ])
                    interaktiv = False
                    print 'Assam verarbeitet jetzt die ISBNs aus der Datei ' + isbnquelle + ':'
                    while 1:
                        # print 1
                        eingabe = isbndatei.next()
                        if isbn.isValid(eingabe):
                            # print 2
                            my_isbn = isbn.isbn_strip(eingabe)
                            # print 3
                            print ''
                            print my_isbn
                            break  # Aus dem  'while' vor 5 Zeilen ausbrechen
                    break  # Aus dem 2. 'while' oben ausbrechen

                except Exception:
                    print 'Es gab einen Fehler mit der Datei.'

            elif eingabe in GEWICHTE:
                buch.print_entscheidung(eingabe)
                continue
            elif eingabe.lower() == 'ende':
                exit()
            elif eingabe.lower() == 'hilfe':
                print hilfetext
            elif eingabe.lower() == 'web':
                for plattform in plattformen_requested:
                    url = 'http://' + \
                        eval(plattform.lower() + '.host') + \
                        eval(plattform.lower() + '.pfad')
                    webbrowser.open(url)
                    time.sleep(1)
            elif eingabe[0] == '-':
                plattformbefehl = False
                # Nur die Plattformen testen, die aktuell angefragt werden. [:]
                # ist nötig, falls der Nutzer zwei aufeinanderfolgende
                # Plattformen entfernen will. Mit Eliminieren der ersten würde
                # die zweite in der folgenden Schleife nicht mehr abgefragt.
                for plattform in plattformen_requested[:]:
                    if plattform.lower() in eingabe.lower():
                        plattformbefehl = True
                        plattformen_requested.remove(plattform)
                        # Aktuelle mit leerem Objekt überschreiben.
                        exec(plattform.lower() + ' = ' +
                             plattform + '("3981471601")')
                        print plattform, 'wird nun nicht mehr angefragt. Mit "+', plattform, '" kannst du es wieder aktivieren.'
                if plattformbefehl:
                    continue
                elif 'lern' in eingabe.lower():
                    learners_mode = False
                    tabelle = True
                    print 'Assam läuft nun im Profi-Modus. Mit "+ Lernen" schaltest Du den Lern-Modus wieder an.'
                elif 'tabelle' in eingabe.lower():
                    tabelle = False
                    print 'Die Tabelle wird nun nicht mehr angezeigt. Mit "+ Tabelle" kannst du sie wieder aktivieren.'
                elif 'quitt' in eingabe.lower():
                    if quittieren == True:
                        quittieren = False
                        print >> quittung, ';'.join(
                            ['', '', '', 'Summe:', '=summe(e2:e' + str(quittungsposten) + ')'])
                        quittung.close()
                        print 'Die Quittung wurde beendet. Sie steht in der Datei "Quittung.csv".'
                    else:
                        print 'Es wird derzeit keine Quittung erstellt.'
                elif 'l50' in eingabe.lower():
                    markt = False
                    print 'Die Kategorie "L50" wird nun nicht mehr berücksichtigt.'
                else:
                    print 'Diesen Befehl versteht Assam nicht. Tippe "Hilfe" um zu erfahren welche Befehle es gibt.'

            elif eingabe[0] == '+':
                plattformbefehl = False
                # Alle ursprünglich vorhandenen Plattformen testen.
                for plattform in plattformen_available:
                    if plattform.lower() in eingabe.lower():
                        plattformbefehl = True
                        if plattform in plattformen_requested:
                            print plattform, 'wird bereits angefragt.'
                        else:
                            plattformen_requested.append(plattform)
                            print plattform, 'wird nun wieder angefragt.'
                if plattformbefehl:
                    continue
                elif 'lern' in eingabe.lower():
                    learners_mode = True
                    tabelle = False
                    print 'Assam läuft nun im Lern-Modus. Mit "- Lernen" wechselst Du zum Profi-Modus.'
                elif 'tabelle' in eingabe.lower():
                    tabelle = True
                    print 'Die Tabelle wird ab nun immer angezeigt. Mit "- Tabelle" kannst du sie wieder deaktivieren.\n'
                    print_gewinntabelle()
                elif 'quitt' in eingabe.lower():
                    if quittieren == False:
                        quittieren = True
                        quittungsposten = 1
                        quittung = open(quittungsdatei, 'w')
                        print >> quittung, ';'.join(
                            ['Nr.', 'ISBN', 'Titel', 'Ausgabe', 'Wert'])
                        print 'Die folgenden Eingaben werden in eine Quittung geschrieben. "-Quittung" schließt sie ab, die Einträge stehen in der Datei "Quittung.csv".'
                    else:
                        print 'Die Eingaben werden bereits in eine Quittung geschrieben. Schließe sie mit "-Quittung" ab und sichere ggf. ihren Inhalt bevor Du eine neue beginnst.'
                elif 'l50' in eingabe.lower():
                    markt = True
                    print 'Die Kategorie "L50" wird nun wieder angegeben'
                else:
                    print 'Diesen Befehl versteht Assam nicht. Tippe "Hilfe" um zu erfahren welche Befehle es gibt.'

            else:
                print 'Die ISBN scheint falsch zu sein...'

    else:  # Bei ISBNs aus Datei (non-interaktiver Modus)
        try:
            while 1:
                eingabe = isbndatei.next()
                if isbn.isValid(eingabe):
                    my_isbn = isbn.isbn_strip(eingabe)
                    print my_isbn
                    break
                else:
                    continue
        except Exception:
            interaktiv = True
            ergebnisdatei.close()
            print '\nFertig!'
            continue

    # Alle Objekte initialisieren
    buch = Buch()  # mit leeren Attributen
    # Enthält später die tatsächlich generierten Objekte.
    plattformen_created = []

    for plattform in plattformen_requested:
        # z.B.: amazon=Amazon('9783831018192')
        exec(plattform.lower() + ' = ' + plattform + '(my_isbn)')
        # z.B.: plattformen_created.append(amazon)
        plattformen_created.append(eval(plattform.lower()))
        eval(plattform.lower() + '.start()')				# z.B.: amazon.start()
    # Jede Plattform wird frühestens dann gejoint wenn die Antwort der
    # vorangegangenen Plattform vollständig ist. Überschreitet eine Plattform
    # das Zeitlimit, erscheinen alle folgenden auch verzögert. Die Warnung ist
    # aber nur dann gerechtfertigt wenn sie über die fremdverschuldete
    # Verzögerung hinaus länger brauchen.
    time_warning_alt = 0
    for plattformobjekt in plattformen_created:
        plattformobjekt.join()
        plattformobjekt.Dauer = (round(time.time() - plattformobjekt.Start, 1))
        if plattformobjekt.Dauer > max(time_warning, time_warning_alt):
            time_warning_alt = plattformobjekt.Dauer
            plattformobjekt.Kommentar += 'Lange Antwortzeit (' + str(
                plattformobjekt.Dauer).replace('.', ',') + ' sec). '

    buch.start()  # Füllt die Attribute von buch mit Werten

    if interaktiv:
        print ''
        print_title()
        if tabelle:
            print_gewinntabelle()
        buch.print_UVP()
        if buch.gewichtsrelevanz:
            while 1:
                gewicht = raw_input(
                    'Das Ergebnis ist gewichtsabhängig, bitte gib die Gewichtsklasse an (<450g: 1, 450-950g: 2, >950g: 3.): ')
                if gewicht == '':
                    gewicht = '1'
                if gewicht in GEWICHTE:
                    print ''
                    break
        else:
            gewicht = '1'
        buch.print_entscheidung(gewicht)

        if my_isbn in blacklist:
            print '\n\x1b[30;31mAchtung, dieses Buch steht auf der schwarzen Liste!\x1b[0m'
            for i in range(len(blacklistheader)):
                print '%-20s' % (blacklistheader[i] + ':') + blacklist[my_isbn][i]

        if my_isbn in ortzumlesen:
            print '\nDieses Buch könnte für "Ein Ort zum Lesen" interessant sein'
            for i in range(len(ortzumlesenheader)):
                print '%-20s' % (ortzumlesenheader[i] + ':') + ortzumlesen[my_isbn][i]

        if my_isbn in vorbestellungen:
            # Neu einlesen falls es zwischenzeitlich Änderungen gab (und vor
            # allem weil wieder geschrieben werden wird)
            vorbestellungsheader, vorbestellungen = vorbestellungen_einlesen(
                vorbestellungsdatei)
        if my_isbn in vorbestellungen:
            print ''
            einfach = False
            if len(vorbestellungen[my_isbn]) == 1:
                einfach = True
                print 'Es gibt eine Vorbestellung für dieses Buch:\n'
                for i in range(len(vorbestellungsheader)):
                    print '%-20s' % (vorbestellungsheader[i] + ':') + vorbestellungen[my_isbn][0][i]

            else:
                print 'Es gibt', len(vorbestellungen[my_isbn]), 'Vorbestellungen für dieses Buch:'
                for i in range(len(vorbestellungen[my_isbn])):
                    print '\nVorbestellung', str(i + 1) + ':'
                    for j in range(len(vorbestellungsheader)):
                        print '%-20s' % (vorbestellungsheader[j] + ':') + vorbestellungen[my_isbn][i][j]

            print ''
            drucken = ''
            while drucken not in ('j', 'n'):  # Druckentscheidung
                # das erste Zeichen in Lowercase, falls es existiert.
                drucken = raw_input('Möchtest Du ' + ('die' if einfach else 'eine') +
                                    ' Vorbestellung drucken (Ja/Nein)? ')[:1].lower()
            if drucken == 'j':
                if einfach:
                    drucken = '1'
                # ggf. Auswahl
                while drucken not in [str(x) for x in range(1, len(vorbestellungen[my_isbn]) + 1)]:
                    drucken = raw_input(
                        'Welche Vorbestellung möchtest Du drucken (Nummer von 1 bis ' + str(len(vorbestellungen[my_isbn])) + ')? ')
                drucken = int(drucken)
                mitarbeiter = raw_input(
                    'Mit welchem Namen möchtest Du im Laufzettel stehen? ')

            print ''
            loeschen = ''
            # Löschentscheidung für den Eintrag von eben (einzigen oder
            # ausgewählten)
            while loeschen not in ('j', 'n'):
                loeschen = raw_input('Möchtest Du ' + ('diese' if (einfach or drucken != 'n')
                                                       else 'eine') + ' Vorbestellung löschen (Ja/Nein)? ')[:1].lower()
            if loeschen == 'j':
                if einfach:
                    loeschen = 1
                elif drucken != 'n':
                    loeschen = drucken
                else:
                    while str(loeschen) not in [str(x) for x in range(1, len(vorbestellungen[my_isbn]) + 1)]:
                        loeschen = raw_input(
                            'Welche Vorbestellung möchtest Du löschen (Nummer von 1 bis ' + str(len(vorbestellungen[my_isbn])) + ')? ')
                    loeschen = int(loeschen)

            if drucken in range(1, len(vorbestellungen[my_isbn]) + 1):
                dateiname = laufzettelpfad + 'Laufzettel_' + ''.join(x for x in (amazon.Titel or easyankauf.Titel or 'Unbekannter Titel ').replace(
                    ' ', '-') if x.isalnum() or x == '-')[0:18] + '...' + str(int(time.time()))[6:] + '.txt'
                laufzettel = open(dateiname, 'w')
                laufzettel.write(
                    '-Laufzettel-\nDieses Buch passt auf eine Vorbestellung und kommt aus der Vorrecherche.\n\n')
                laufzettel.write('%-20s' % 'Datum:' +
                                 time.strftime('%d.%m.%Y') + '\n')
                laufzettel.write('%-20s' % 'Gefunden von:' +
                                 mitarbeiter + '\n\n')

                laufzettel.write('Gefundenes Buch:\n')
                laufzettel.write('%-20s' % 'ISBN:' + my_isbn +
                                 ' / ' + isbn.convert(my_isbn) + '\n')
                laufzettel.write(
                    '%-20s' % 'Titel:' + (amazon.Titel or easyankauf.Titel or 'Unbekannter Titel ') + '\n')
                laufzettel.write('%-20s' % 'Ladenpreisempf.:' +
                                 (float_to_string(buch.UVP) + "¤" if buch.UVP else '/') + '\n\n')

                laufzettel.write('Bestelltes Buch:\n')
                for i in range(len(vorbestellungsheader)):
                    print >> laufzettel, '%-20s' % (vorbestellungsheader[i] + ':') + vorbestellungen[
                        my_isbn][drucken - 1][i]
                laufzettel.write('\n' + '%-20s' % 'Aus Assam gelöscht?' +
                                 ('Nein' if loeschen == 'n' else 'Ja') + '\n\n')

                laufzettel.write('%-20s' % 'Kunde informiert am' + '...\n')
                laufzettel.write('%-20s' % 'durch' + '...\n')
                laufzettel.close()

            # if loeschen !='n':
                # vorbestellungen[my_isbn].pop(loeschen-1)
                # with open('vorbestellungen.csv', 'wb') as vorbestellungscsv:
                #csvwriter = csv.writer(vorbestellungscsv, delimiter=';',quotechar='"', quoting=csv.QUOTE_ALL)
                # csvwriter.writerow(vorbestellungsheader)
                # for vorbest_isbn in vorbestellungen:
                # for vorbestellung in vorbestellungen[vorbest_isbn]:
                #vorbestellungscsv.write(vorbest_isbn+ ';')
                # csvwriter.writerow(vorbestellung)

            if loeschen != 'n':
                vorbestellungen[my_isbn].pop(loeschen - 1)
                vorbestellungen_schreiben(vorbestellungsdatei)

            # andere_loeschen=''
            # if not einfach and andere_loeschen != 'n':
                # while andere_loeschen not in ('j', 'n'): # Löschentscheidung für weiteren Eintrag
                #andere_loeschen = raw_input('Möchtest Du eine ' + ('andere' if loeschen =='n' else 'weitere') + ' Vorbestellung löschen? ')[:1].lower()

                # if andere_loeschen=='j':
                # print 'loesch...' #eig. loeschprozess von Nr x

    else:
        print >> ergebnisdatei, ';'.join([
            my_isbn,
            (amazon.Titel or easyankauf.Titel or 'Unbekannter Titel ').replace(';', ','),
            ' '.join(buch.Entscheidung['1']),
            (' '.join(buch.Entscheidung['2']) if (
                ' '.join(buch.Entscheidung['2']) != ' '.join(buch.Entscheidung['1'])) else ''),
            (' '.join(buch.Entscheidung['3']) if (
                ' '.join(buch.Entscheidung['3']) != ' '.join(buch.Entscheidung['2'])) else ''),
        ])

        #(' '.join(Entscheidung['2']) if (' '.join(Entscheidung['2']) != ' '.join(Entscheidung['1']))),
    if quittieren:
        print >> quittung, ';'.join([
            str(quittungsposten),
            my_isbn + ' / ' + isbn.convert(my_isbn),
            (amazon.Titel or easyankauf.Titel or 'Unbekannter Titel ').replace(';', ','),
            (amazon.Ausgabe or easyankauf.Ausgabe or 'Unbekannte Ausgabe').replace(
                ';', ','),
            float_to_string(min(buch.Preise)) if buch.Preise else '???'
        ])
        quittungsposten += 1
