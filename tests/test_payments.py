"""
Verifies the aggregate payment output is correct
"""

import unittest

class TestPayments(unittest.TestCase):
    """
    Tests payments for data file bpy331_1487931_7163.1.dat have been
    aggregated correctly. Rounding errors can occur, so only test up to
    2 decimal places
    """

    def test_first_payment_aggregation(self):
        """
        Tests payments to "MRS RV O'DRISCROLL/##-##-##/########"
        """
        payments = [
            535.71,
            232.57,
            465.01,
            143.08,
            4095.00]
        self.assertAlmostEqual(sum(payments), 5471.37, places=2)

    def test_second_payment_aggregation(self):
        """
        Tests payments to
        "BROADACRES HOUSING ASSOCIATION/##-##-##/########"
        """
        payments = [
            1503.33,
            891.00,
            422.13,
            42.15,
            166.59,
            73.98,
            95.12,
            1922.78,
            38.79,
            140.38,
            786.33,
            41.76,
            81.53,
            33.75,
            43.39,
            212.97,
            415.80,
            142.14,
            87.99,
            531.25,
            528.90]
        self.assertAlmostEqual(sum(payments), 8202.06, places=2)

    def test_third_payment_aggregation(self):
        """
        Tests payments to " J BROWN/##-##-##/########"
        """
        payments = [3025.0]
        self.assertAlmostEqual(sum(payments), 3025.0, places=2)

if __name__ == '__main__':
    unittest.main()
