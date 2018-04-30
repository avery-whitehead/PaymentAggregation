"""
Takes a BPY331 formatted log of payment records, aggregates the total of each
payee and writes it back to the file.

HOW IT WORKS:
    1. The filenames of new files are read from the directory.
    2. A Payment object is created for each record in a file. An account
    reference is made for each Payment object. A mod10 algorithm is used to
    create a checkdigit from the bank sort code, and a mod26 algorithm on the
    first two digits of the bank account number is used to create an A-Z
    character. The first two digits of the bank account number are replaced
    with the A-Z character, and the checkdigit is appended to the end of that.
    3. A primary key is created for each unique combination of account
    reference and building society number.
    4. Each Payment object is assigned to its matching primary key based on
    the value of its account reference and building society number.
    5. For each primary key, the total amount paid for each Payment object
    belonging to it is summed up, and a new Payment object is created.
    6. Each of these new Payment objects is written back to file.

PROCESSES:
    1. load_files() - gets the file names from a directory. Returns a list of
    the file paths for the files.
    2. create_payments() - reads in the files and create a Payment object for
    each record. Returns a list of Payment objects. Calls gen_account_ref() to
    return a string for the account reference.
    3. create_keys() - makes a series of primary keys. Returns a dictionary
    with the primary keys as the keys and an empty list for each value.
    4. assign_keys() - fills the lists in the dictionary values with the
    matching Payment objects. Returns the dictionary from create_keys() but
    with Payment objects filling the empty list.
    5. sum_payments() - goes through each Payment object in each list and
    sums the total of their payment amounts. Creates a new Payment object for
    each key with the same attributes as the old Payment objects, but with the
    sum total attribute replacing the old individual amounts. Returns a list
    of new Payment objects.
    6. write_payments() - writes the new Payment objects to a file in the same
    structure as the original files. Returns a success string about which
    files were written.

TODO:
    1. create_keys()
    2. assign_keys()
    3. sum_payments()
    4. write_payments()
"""

import os
import datetime

class Payment(object):
    """
    A payment recording according the BPY331 format. The 'defaults' dict lets
    us use the 'attribute=value' syntax when creating a Payment object.
    """
    def __init__(self, **kwargs: str) -> None:
        self.defaults = {
            'interface_source': '"BEN"',
            'batch_run_id': '"batch_run_id"',
            'posting_ref': '"posting_ref"',
            'account_ref': '"NOT_YET_SET"',
            'payee_type': '"CL"',
            'payee_name': '"payee_name"',
            'payee_address': '"Aggregated DHP UC Payment"',
            'claim_ref': '"claim_ref"',
            'claimant_name': '"Aggregated DHP UC Payment"',
            'claimant_adddress': '"Aggregated DHP UC Payment"',
            'amount': '"amount"',
            'posting_start_date': '"{}"'.format(SYSTIME),
            'posting_end_date': '"{}"'.format(SYSTIME),
            'payment_method': '"BACS"',
            'creditor_account_ref': '""',
            'bank_sort_code': '"bank_sort_code"',
            'bank_account_num': '"bank_account_num"',
            'bank_account_name': '"bank_account_name"',
            'building_society_num': '"building_society_num"',
            'post_office_name': '""',
            'post_office_address': '""',
            'collection_flag': '"N"',
            'document_num': '""',
            'document_type': '""',
            'replacement_flag': '"N"',
            'effective_date': '"{}"'.format(SYSTIME),
            'blank_one': '""',
            'blank_two': '""',
            'document_date': '""'}
        # Fancy kwargs magic for default constructor values
        self.__dict__.update(self.defaults)
        self.__dict__.update(kwargs)

    def print_payment(self) -> None:
        """
        Formats and prints Payment object line-by-line in the same style as
        the records in the file.
        """
        items = self.__dict__.items()
        for key, value in items:
            if key != 'defaults':
                print(value)
        print()

def load_files(file_dir: str) -> list:
    """
    Gets the names of all the BPY331 formatted files from a directory.
    Args:
        file_dir (str): The directory to search.
    Returns:
        (list): A list of the paths of the files.
    """
    files_list = []
    for _, _, files in os.walk(file_dir):
        for file in files:
            if file.startswith('bpy331_') and file.endswith('.dat'):
                files_list.append('{}/{}'.format(file_dir, file))
    return files_list

def create_payments(filepath: str) -> list:
    """
    Reads a file line-by-line and makes a Payment object for each record in
    the file.
    Args:
        filepath (str): The path of the file to read in.
    Returns:
        (list): A list of Payment objects created from the records in the file.
    """
    payments = []
    with open(filepath) as file:
        records = file.read().splitlines()
    # Each record is 29 lines long, so each loop iteration covers one record
    for i in range(1, len(records), 29):
        account_ref = gen_account_ref(
            records[i + 15].replace('"', '').replace(' ', ''),
            records[i + 16].replace('"', '').replace(' ', ''))
        payment = Payment(
            batch_run_id = records[i + 1],
            posting_ref = records[i + 2],
            account_ref = account_ref,
            payee_name = records[i + 17],
            claim_ref = account_ref,
            amount = records[i + 10],
            bank_sort_code = records[i + 15],
            bank_account_num = records[i + 16],
            bank_account_name = records[i + 17],
            building_society_num = records[i + 18])
        payments.append(payment)
    return payments

def gen_account_ref(sort_code, account_num) -> str:
    """
    Generates a mod10 (Luhn) algorithm checkdigit from a bank sort code
    and, does a mod26 on the first two digits of the account number and
    uses these values with the account number to create the account
    reference.
    Args:
        sort_code (str): The bank sort code, a six-digit number with three
        pairs of two digits separated by a '-'
        account_num (str): An eight digit number
    Returns:
        (str): The account ref in the format "<first two digits of
        account_num mod26 as A-Z><remaining digits of account_num>
        <sort_code check digit>"
    """
    # Splits up the sort code into its digits
    sort_digits = [
        int(dig) for dig
        in list(sort_code.replace('-', ''))]
    # Multiplies every second element by 2
    doubles = [
        num * 2 if index % 2 != 0 else num for index, num
        in enumerate(sort_digits)]
    # Changes any two-digit numbers into two elements (e.g. [18] tp [1, 8])
    temp = ''.join(str(num) for num in doubles)
    doubles = [int(dig) for dig in temp]
    # Sums the digits and subtracts from the nearest multiple of 10
    checkdig = 10 - sum(doubles) % 10
    if checkdig == 10:
        checkdig = 0
    # mod26 the first two digits of the account number
    mod_digs = int(account_num[:2]) % 26
    if mod_digs == 0:
        mod_char = 'A'
    else:
        mod_char = chr(mod_digs + 64)
    return '"{}{}{}"'.format(mod_char, account_num, str(checkdig))

if __name__ == '__main__':
    SYSTIME = datetime.date.today().strftime('%d-%b-%Y').upper()
    files = load_files('./data')
    for f in files:
        payments = create_payments(f)
