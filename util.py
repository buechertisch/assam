# -*- coding: windows-1258 -*-
import csv

from config import schwarze_liste


def string_to_float(preis):  # Konvertiert z.B. "2,50" zu 2.5.
    return float(preis.replace(',', '.'))


def get_blacklist():
    try:
        blacklistcsv = csv.reader(open(schwarze_liste, 'rb'), delimiter=';')
        blacklistheader = blacklistcsv.next()[1:]
    except Exception:
        blacklistcsv = []
        print ("Es konnte keine Schwarze Liste eingelesen werden. Die Datei"
               "{0} existiert nicht oder hat ein falsches Format.".format(schwarze_liste))
    blacklist = {}
    zeile = 1
    for row in blacklistcsv:
        zeile += 1
        try:
            if row == []:
                continue
            if isbn.isValid(row[0]):
                blacklist[isbn.toI13(row[0])] = row[1:]
            else:
                print ("Es ist ein Fehler beim Einlesen der Schwarzen Liste "
                       "aufgetreten. Zeile {0} enthält keine gültige ISBN.".format(zeile))
        except Exception:
            print ("Es ist ein Fehler beim Einlesen der Schwarzen Liste "
                   "aufgetreten. Zeile", zeile, "enthält einen Fehler.")

    return blacklistheader, blacklist
