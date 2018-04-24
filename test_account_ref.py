"""
Verifies the mod10 (Luhn) algorithm to generate a check digit is correct
"""

import unittest

class TestCheckdigits(unittest.TestCase):
    """
    Tests the check digit of the mod10 (Luhn) algorithm has been generated
    correctly.
    """

    def test_first_check_digit(self):
        """
        Tests digit for 7992739871 (Wikipedia example)
        """
        check_digit = generate_check_digit('7992739871')
        self.assertEqual(check_digit % 10, 3)
        self.assertEqual(verify_check_digit(check_digit), True)

    def test_second_check_digit(self):
        """
        Tests digit for 40-35-03 (Payment example)
        """
        check_digit = generate_check_digit('40-35-03')
        self.assertEqual(check_digit % 10, 6)
        self.assertEqual(verify_check_digit(check_digit), True)

def generate_check_digit(sort_code):
    """
    Generates a mod10 (Luhn) algorithm checkdigit from a bank sort code

    Args:
        sort_code (str): The sort code to generate a check digit for

    Returns:
        (int): The sort code (without hyphens) with the check digit appended
        to the end
    """
    sort_code = sort_code.replace('-', '')
    sort_code_ints = [int(num) for num in list(sort_code)]
    # Multiply every second element by 2
    ints_mult = [
        num * 2 if index % 2 != 0 else num
        for index, num in enumerate(sort_code_ints)]
    # Change any two-digit numbers into two elements (e.g. [18] -> [1, 8])
    temp_list = ''.join(str(c) for c in ints_mult)
    ints_mult = [int(num) for num in temp_list]
    # Sum the ints and subtract from the nearest multiple of 10
    check_digit = 10 - sum(ints_mult) % 10
    if check_digit == 10:
        check_digit = 0
    return int(str(sort_code) + str(check_digit))

def verify_check_digit(check_digit):
    """
    Verifies the check digit is correct

    Args:
        check_digit (int): The string of digits with the check digit appended

    Returns:
        (bool): True if the check digit is correct, False if incorrect
    """
    # Reverse the check digit (to read right-to-left)
    reversed_list = [int(i) for i in str(check_digit)]
    reversed_list.reverse()
    # Multiply every second element by 2
    rev_mult = [
        num * 2 if index % 2 != 0 else num
        for index, num in enumerate(reversed_list)]
    # Change any two-digit numbers into two elements (e.g. [18] -> [1, 8])
    temp_list = ''.join(str(c) for c in rev_mult)
    rev_mult = [int(num) for num in temp_list]
    # Sum the digits and mod10 to verify the number
    return sum(rev_mult) % 10 == 0


if __name__ == '__main__':
    unittest.main()
