#!/usr/bin/env python
import unittest

from util import string_to_float, get_ort_zum_lesen


class UtilTests(unittest.TestCase):
    def test_string_to_float(self):
        result = string_to_float("2,50")
        self.assertEqual(result, 2.5)

    def test_get_ort_zum_lesen(self):
        header, data = get_ort_zum_lesen()

        # The "ISBN" field must be removed from the header.
        self.assertEqual(header, ["Titel", "Autor"])
        self.assertEqual(data, {})

    def test_get_ort_zum_lesen_nonexisting_file(self):
        header, data = get_ort_zum_lesen(csv_file="nonexstingfile")
        self.assertEqual(header, [])
        self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
