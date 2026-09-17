import unittest
from scoring import score_lead


class ScoringTests(unittest.TestCase):
    def test_keywords_match_words_not_substrings(self):
        score, reasons, motivation = score_lead('Moderate home', 'A modern home with a barcode', 300000)
        self.assertEqual(score, 0)
        self.assertEqual(motivation, 'unknown')

    def test_real_estate_is_not_probate_evidence(self):
        score, reasons, motivation = score_lead('Real estate for sale', 'Real estate listing', 300000)
        self.assertEqual(score, 0)
        self.assertEqual(motivation, 'unknown')


if __name__ == '__main__':
    unittest.main()
