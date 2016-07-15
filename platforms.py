# -*- coding: windows-1258 -*-
import httplib
import re
import threading
import time

import isbn
from util import string_to_float
from config import (amazon_kosten, booklooker_kosten, buchfreund_kosten,
                    zvab_kosten, ebay_kosten)
from config import (amazon_verkaufsanteil, booklooker_verkaufsanteil,
                    buchfreund_verkaufsanteil, zvab_verkaufsanteil,
                    ebay_verkaufsanteil, easyankauf_verkaufsanteil)
from config import (mwst, porto_real, zusatzkosten, timeout)


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
        # FIXME
        my_isbn = "unknown"


        logfile = open('fehler-isbns.csv', 'a')
        print >> logfile, time.strftime(
            '%Y-%m-%d_%H:%M') + ';' + my_isbn + ';' + ereignis
        logfile.close()

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
