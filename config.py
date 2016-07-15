# -*- coding: windows-1258 -*-

# Module for Assam Version 1.1
# Assam is free and licensed under GPL
# Author: Franziska Hausmann <franziska.hausmann@posteo.de>
# Date: 2016-05-23

##########################################################################
#                                                                                 #
# Diese Datei enthält die Werte, auf denen die Kategorien von Assam basieren.     #
# Sie lassen sich bei Bedarf anpassen.                                            #
#                                                                                 #
##########################################################################

#_________________________________________________________________________
#__________Kosten, die beim Verkauf entstehen:____________________________

# import time #für Timestamp im Quittungs-Dateinamen

# Tatsächliche Kosten fürs Porto für die drei Gewichtsklassen 1:<450g,
# 2:450-950g, 3:>950g.
porto_real = {'1': 0.82, '2': 1.42, '3': 5.0}
# geschätzte Kosten fürs Einstellen, Lagern, Raussuchen, Verpacken...
zusatzkosten = 1.0
# Mehrwertsteuer als Anteil von 1. Also: 0.07 eingeben wenns 7% sind.
mwst = 0.07

amazon_kosten = {
    # VerkaufspreisUNabhaengige Kosten (Einstellgebuehren, Betrag der vom
    # Porto einbehalten wird etc.) in Euro.
    'Fixkosten': 1.14,
    # Anteil des Verkaufspreises, den der Vermittler bekommt.
    'Provision': 0.15,
    # Ausgewiesenes Porto/Verpackung, für die 3 Gewichtsklassen.
    'Porto_dekl': {'1': 3.0, '2': 3.0, '3': 3.0},
}

booklooker_kosten = {
    'Fixkosten': 0.0,
    'Provision': 0.082,
    'Porto_dekl': {'1': 3.0, '2': 3.0, '3': 3.0},
}

buchfreund_kosten = {
    'Fixkosten': 0.0,
    'Provision': 0.1,
    'Porto_dekl': {'1': 3.0, '2': 3.0, '3': 3.0},
}

zvab_kosten = {
    'Fixkosten': 0,
    'Provision': 0.15,
    'Porto_dekl': {'1': 3.0, '2': 3.0, '3': 3.0},
}

ebay_kosten = {
    'Fixkosten': 0.2,
    'Provision': 0.11,
    'Porto_dekl': {'1': 3.0, '2': 3.0, '3': 3.0},
}


amazon_verkaufsanteil = 62.5
booklooker_verkaufsanteil = 12.5
buchfreund_verkaufsanteil = 0
zvab_verkaufsanteil = 25
ebay_verkaufsanteil = 0
# Der Anteil der über die jeweilige Plattform verkauft wird (zur
# Gewichtung der Preise für die Ladenpreisempfehlung). Die Werte können
# z.B. in Prozent, als Anteile von 1 oder als Anzahl der verkauften Bücher
# angegeben werden. Wichtig ist nur das Verhältnis der Zahlen zueinander.
easyankauf_verkaufsanteil = 0


#_________________________________________________________________________
#__________Die Werte nach denen die Kategorien (O/Ox, H, L, W, K, W!) gebi

# Für O/Ox:
# Was nach Abzug von Versand, Provision und Einstellgebühr übrig bleiben
# muss, damit sich Onlineverkauf lohnt.
mindestgewinn = 3
# Mindestverkaufsrang, damit ein Buch sich zum Onlineverkauf auf
# non-Amazon-Plattformen qualifizieren kann.
o2_rang = 1500000

# Für H:
h_rang = 500000  # Notwendiger Höchstrang für H.
h_mindestgewinn = 0.75  # Nötiger Amazon-Gewinn für H
h2_rang = 5000  # (preisunabhängig) hinreichender Höchstrang für H

# Für M:
markt = True  # Ob "L50" (Marktbuch) als Kategorie überhaupt erscheinen soll
markt_rang = 300000  # Notwendiger Höchstrang für L50
markt_hoechstpreis = 3.5  # Maximaler Amazon-Preis (mit Porto) für L50

# Für W:
easyankaufminimum = 0.5  # Mindestgebot von Easyankauf, damit W in Frage kommt.
#_________________________________________________________________________
#__________Weitere Optionen.______________________________________________

# Modus in dem gestartet wird. Darf True oder False sein.
learners_mode = False
tabelle = True			# "
logging = True			# "
# verbose = False		# "
# Hier False stehenlassen. (Es ergibt keinen Sinn, defaultmäßig zu quittieren)
quittieren = False

kategoriefarben = {'O/Ox': '41', 'W!': '47;35', 'W': '45', 'H': '44', 'L50': '47',
                   'L': '46', 'K': '42', 'Y': '43'}  # Farben: 	30: grau (Vordergrund) 40: grau (Hintergrund)
#		x	31: rot                41: rot (Hintergrund)
#		x	32: grün               ...
#		x	33: gelb
#		x	34: blau
#		x	35: magenta
#		x	36: cyan
#			37: weiß
# Werte 30-38 sind farbiger Text, 40-48 farbiger Hintergrund.


intros = ['Arbeiten und Tee trinken.', 'Kein Buch ohne eine Tasse Tee.',
          'Kennst Du alle Assam-Funktionen? Tipp doch mal "Hilfe" ein!']

# Alle verfügbaren Plattformen. Bitte nicht ändern!
plattformen_available = ['Amazon', 'Booklooker',
                         'Buchfreund', 'ZVAB', 'Ebay', 'Easyankauf']
# Plattformen die tatsächlich angefragt werden sollen. Hier dürfen nur
# Namen stehen, die in der gleichen Schreibweise in plattformen_available
# vorkommen. Die Reihenfolge hier bestimmt die Reihenfolge in der
# Gewinntabelle.
plattformen_requested = ['Amazon', 'Booklooker',
                         'Buchfreund', 'ZVAB', 'Ebay', 'Easyankauf']

# Der Pfad zur csv-Datei, die die Vorbestellungen enthält. Sie muß in der
# ersten Spalte die ISBNs enthalten, Texttrenner ist das
# Anführungszeichen: " , Feldtrenner das Semikolon: ; .
vorbestellungsdatei = './vorbestellungen.csv'
schwarze_liste = './schwarze_liste.csv'
ort_zum_lesen = './ort_zum_lesen.csv'
logdatei = './fehler-isbns.csv'
quittungsdatei = 'Quittung.csv'
laufzettelpfad = './'
#quittungsdatei='./Quittung_' + time.strftime('%Y-%m-%d_%H:%M') + '.csv'

hilfetext = """Gib eine ISBN ein um das Buch zu recherchieren.
Wenn das Ergebnis vom Gewicht des Buches abhängt wirst du danach gefragt werden. Du kannst dann die Gewichtsklasse mit 1 (<450g), 2 (450-950g) oder 3 (>950g) angeben.
Mit "Ende" beendest du das Programm, mit "Hilfe" bekommst Du diesen Hilfetext angezeigt. Wenn du "Web" eingibst kannst du die Ergebnisse im Browser überprüfen.

Weitere Optionen:
+/- Lernen: Schaltet den Lernmodus an/aus.
+/- Tabelle: Schaltet die Anzeige der Gewinnübersicht an/aus
+/- <Plattform>: Wählt die angegebene Plattform an oder ab. z.B: "-Ebay" wählt Ebay ab, "+Booklooker Easyankauf" fügt Booklooker und Easyankauf dazu. Wählbare Plattformen sind: """ + ', '.join(plattformen_available) + """.
+/- Quittung: Beginnt und beendet eine Quittung. Sie steht in der Datei \"""" + quittungsdatei + """\".
+/- L50: Schaltet die Anzeige der Kategorie L50 an/aus.
+/- Log: Schaltet das Logging an/aus. Die Logdatei ist """ + logdatei + """.
Datei <dateiname>: Liest ISBNs aus der Datei ein und schreibt die Ergebnisse in <dateiname-ergebnisse.csv>.
Vorbestellung: Nimmt eine neue Vorbestellung auf.
"""


lerntexte = {'W!': "Achtung, das Buch erzielt bei Easyankauf mehr Gewinn als auf irgendeiner Plattform! Bitte frag' einen anderen Mitarbeiter ob Easyankauf hier Priorität hat. Falls ja:\n-> W!\n", 'O/Ox': 'Ist das Buch kleiner als der Maßstab aus Holz?\n-> O\n\nIst es größer?\n-> Ox\n', 'H': 'Ist das Buch kleiner als der Maßstab aus Holz und in gutem Zustand?\n-> H\n',
             'L': 'Ist das Buch nur wenig abgenutzt, frei von Markierungen und Eselsohren und weder Leseexemplar noch Bild- oder Weltbild-Edition? (Bei Krimis, Thrillern und historischen Romanen bitte eher streng sein).\n-> L\n', 'L50': 'Ist das Buch in gutem Zustand?\n-> L50\n', 'Y': 'Passt das Buch in eines der Themen die derzeit gesammelt werden?\n-> Y, also ins entsprechende Regal stellen.\n', 'W': 'Ist der Zustand in Ordnung?\n-> W\n', 'K': 'Wenn nichts davon zutrifft:\n-> K\n'}

# Ab dieser Anfragedauer (in sec.) wird gewarnt, daß die Plattform lange
# braucht.
time_warning = 5
timeout = 10			# Nach dieser Dauer wird nicht weiter auf eine Antwort gewartet.
