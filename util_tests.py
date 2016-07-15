#!/usr/bin/env python
import unittest

from util import string_to_float, get_ort_zum_lesen, get_blacklist


class UtilTests(unittest.TestCase):
    def test_string_to_float(self):
        result = string_to_float("2,50")
        self.assertEqual(result, 2.5)

    def test_get_ort_zum_lesen(self):
        header, data = get_ort_zum_lesen()

        # The "ISBN" field must be removed from the header.
        self.assertEqual(header, ["Titel", "Autor"])
        self.assertEqual(data, {})

    def test_get_ort_zum_lesen_file_with_data(self):
        with open("testfile.csv", "w") as csv_file:
            csv_file.write('"ISBN","Titel","Autor"\n')
            csv_file.write('"1-58488-540-8","some title","some author"\n')
            csv_file.write('"3-499-22415-1","another title","another author"\n')
        header, data = get_ort_zum_lesen(csv_file="testfile.csv")

        self.assertEqual(header, ["Titel", "Autor"])
        self.assertEqual(data, {
                '9781584885405': ['some title', 'some author'],
                '9783499224157': ['another title', 'another author']})

    def test_get_ort_zum_lesen_file_with_one_invalid_line(self):
        with open("testfile.csv", "w") as csv_file:
            csv_file.write('"ISBN","Titel","Autor"\n')
            csv_file.write('"123456","some title","some author"\n')
            csv_file.write('"3-499-22415-1","another title","another author"\n')
        header, data = get_ort_zum_lesen(csv_file="testfile.csv")

        self.assertEqual(header, ["Titel", "Autor"])
        self.assertEqual(data, {
                '9783499224157': ['another title', 'another author']})

    def test_get_ort_zum_lesen_nonexisting_file(self):
        header, data = get_ort_zum_lesen(csv_file="nonexstingfile")
        self.assertEqual(header, [])
        self.assertEqual(data, {})

    def test_get_blacklist(self):
        header, blacklist = get_blacklist()
        # The "ISBN" field must be removed from the header.
        self.assertEqual(header, ["Titel", "Autorin", "Anmerkungen"])
        self.assertEqual(blacklist, {})

    def test_get_blacklist_nonexisting_file(self):
        header, blacklist = get_blacklist("nonexistingfile")
        self.assertEqual(header, [])
        self.assertEqual(blacklist, {})


if __name__ == "__main__":
    unittest.main()
