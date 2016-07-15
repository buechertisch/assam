# -*- coding: windows-1258 -*-
import csv
import isbn

from config import schwarze_liste, ort_zum_lesen


def string_to_float(preis):  # Konvertiert z.B. "2,50" zu 2.5.
    return float(preis.replace(',', '.'))


def get_blacklist(blacklist_file=schwarze_liste):
    try:
        blacklistcsv = csv.reader(open(blacklist_file, 'rb'), delimiter=';')
        blacklistheader = blacklistcsv.next()[1:]
    except Exception:
        blacklistcsv = []
        blacklistheader = []
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

def get_ort_zum_lesen(csv_file=ort_zum_lesen):
    try:
        ortzumlesencsv = csv.reader(open(csv_file, 'rb'), delimiter=',')
        ortzumlesenheader = ortzumlesencsv.next()[1:]
    except Exception:
        ortzumlesencsv = []
        ortzumlesenheader = []
        print ('Es konnte keine Liste für "Ein Ort zum Lesen" eingelesen '
               'werden. Die Datei', ort_zum_lesen, "existiert nicht oder "
               "hat ein falsches Format.")
    ortzumlesen = {}
    zeile = 1
    for row in ortzumlesencsv:
        zeile += 1
        try:
            if row == []:
                continue
            if isbn.isValid(row[0]):
                ortzumlesen[isbn.toI13(row[0])] = row[1:]
            else:
                print ('Es ist ein Fehler beim Einlesen der Liste für '
                       '"Ein Ort zum Lesen" aufgetreten. Zeile', zeile,
                       "enthält keine gültige ISBN.")
        except Exception:
            print ('Es ist ein Fehler beim Einlesen der Liste für "Ein Ort '
                   'zum Lesen" aufgetreten. Zeile', zeile, "enthält einen Fehler.")

    return ortzumlesenheader, ortzumlesen


def vorbestellungen_einlesen(vorbestellungsdatei):
    try:
        vorbestellungscsv = csv.reader(
            open(vorbestellungsdatei, 'rb'), delimiter=';')
        vorbestellungsheader = vorbestellungscsv.next()[1:]
    except Exception:
        vorbestellungscsv = []
        print ("Es konnten keine Vorbestellungen eingelesen werden. Die Datei",
               vorbestellungsdatei, "existiert nicht oder hat ein falsches Format.")
    vorbestellungen = {}
    zeile = 1
    for row in vorbestellungscsv:
        zeile += 1
        try:
            if row == []:
                continue
            if isbn.isValid(row[0]):
                if isbn.toI13(row[0]) not in vorbestellungen:
                    vorbestellungen[isbn.toI13(row[0])] = [row[1:]]
                else:
                    vorbestellungen[isbn.toI13(row[0])].append(row[1:])
            else:
                print ("Es ist ein Fehler beim Einlesen der Vorbestellungen "
                       "aufgetreten. Zeile {0} enthält keine gültige ISBN."
                       ).format(zeile)
        except Exception:
            print ("Es ist ein Fehler beim Einlesen der Vorbestellungen "
                   "aufgetreten. Zeile", zeile, "enthält einen Fehler.")
    return(vorbestellungsheader, vorbestellungen)
