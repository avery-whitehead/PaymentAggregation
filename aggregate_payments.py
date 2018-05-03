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

https://github.com/james-whitehead/PaymentAggregation
"""

import os
import datetime
import shutil
import sys
import smtplib
from email.message import EmailMessage

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
            'payee_address': '"payee_address"',
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

    def set_account_ref(self, orig_ref: str, orig_claim: str) -> None:
        """
        Sets the account reference and claim reference of a Payment object
        to the string generated by the call to gen_account_ref().
        Args:
            orig_ref (str): If the building society number is not 0, use the
            original account reference instead of a new one.
            orig_claim (str): If the building society numebr is not 0, use the
            original claim reference instead of a new one.
        """
        sort_code = self.bank_sort_code.replace('"', '').replace(' ', '')
        account_num = self.bank_account_num.replace('"', '').replace(' ', '')
        if self.building_society_num == '"0" ':
            account_ref = self.gen_account_ref(sort_code, account_num)
            self.account_ref = account_ref
            self.claim_ref = account_ref
        else:
            self.account_ref = orig_ref
            self.claim_ref = orig_claim

    def gen_account_ref(self, sort_code: str, account_num: str) -> str:
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
        return '"{}{}{}"'.format(mod_char, account_num[2:], str(checkdig))

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
    Gets the most-recently modified file in the directory, as long as it
    hasn't been modified in the past 5 minutes and hasn't been aggregated
    before.
    Args:
        file_dir (str): The directory to search.
    Returns:
        (str): The path of the most-recently modified file that meets the
        rules. If no files meet the rules, throws a ValueError exception.
    """
    with open('.\\already_checked.log', 'r') as already_checked:
        checked = already_checked.read().splitlines()
    files_list = []
    now = datetime.datetime.now()
    delta = now - datetime.timedelta(minutes=5)
    for root, _, files in os.walk(file_dir):
        for file in files:
            if file.startswith('bpy331_') and file.endswith('.dat'):
                path = os.path.join(root, file)
                stats = os.stat(path)
                modif = datetime.datetime.fromtimestamp(stats.st_mtime)
                if modif > delta and path not in checked:
                    files_list.append(path)
    return max(files_list, key=lambda f: os.stat(f).st_mtime)

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
        payment = Payment(
            batch_run_id = records[i + 1],
            posting_ref = records[i + 2],
            payee_name = records[i + 17],
            payee_address = records[i + 6],
            amount = records[i + 10],
            bank_sort_code = records[i + 15],
            bank_account_num = records[i + 16],
            bank_account_name = records[i + 17],
            building_society_num = records[i + 18])
        payment.set_account_ref(records[i + 3], records[i + 7])
        payments.append(payment)
    return payments

def create_keys(payments: list) -> dict:
    """
    Creates a series of primary keys based on each unique combination of
    account reference and building society number in each Payment object.
    Args:
        payments (list): A list of Payment objects used to generate the keys.
    Returns:
        (dict): A dictionary with the keys being the primary keys and the
        values being empty lists, to be filled with the associated Payment
        objects later.
    """
    keys = []
    for payment in payments:
        # Trims the quotation marks and trailing whitespace
        key = '{}/{}'.format(
            payment.account_ref[1:-1],
            payment.building_society_num[1:-2])
        keys.append(key)
    # Sets the default value for each key in the dict to be an empty list
    # Note: doesn't work using fromkeys(); each value refers to the same list
    return {k: [] for k in keys}

def assign_keys(payments: list, keys: dict) -> dict:
    """
    Fills the values for each key with the appropriate Payment objects. Each
    Payment object has an account reference and a building society number,
    which when stripped of quotation marks and whitespace and joined
    together with a forward-slash in between, will equal a key in the dict.
    Args:
        keys (dict): A dictionary of keys and empty lists to be filled with
        Payment objects.
    Returns:
        (dict): The dictionary passed as an argument with Payment objects
        taking the place of the values.
    """
    for payment in payments:
        payment_key = '{}/{}'.format(
            payment.account_ref[1:-1],
            payment.building_society_num[1:-2])
        for key in keys:
            if key == payment_key:
                keys[payment_key].append(payment)
    return keys

def sum_payments(keys_vals: dict) -> list:
    """
    For each key-value pair in the dictionary, sums the total amount paid
    for each Payment object in each value list and creates a single new
    Payment object based on that total amount and the other attributes
    taken from the first Payment object in the list.
    Because each Payment object in the list has the same values, it doesn't
    matter which object we take the attributes from, but some lists only have
    a single Payment object in them, so we take the first.
    Args:
        keys_vals (dict): A dictionary with each Payment object assigned to a
        unique key depending on their attributes. Matching Payment objects
        have the same key.
    Returns:
        (list): A list of newly-aggregated Payment objects, one for each key
        in the dictionary.
    """
    new_payments = []
    for _, payments in keys_vals.items():
        total = 0
        for payment in payments:
            amount = payment.amount.replace('"', '').replace(' ', '')
            total += float(amount)
        # Rounds the total to two decimal places and adds the quotes back
        total = '"{:.2f}"'.format(total)
        new_payment = Payment(
            batch_run_id = payments[0].batch_run_id,
            posting_ref = payments[0].posting_ref,
            account_ref = payments[0].account_ref,
            payee_name = payments[0].payee_name,
            payee_address = payments[0].payee_address,
            claim_ref = payments[0].claim_ref,
            amount = total,
            bank_sort_code = payments[0].bank_sort_code,
            bank_account_num = payments[0].bank_account_num,
            bank_account_name = payments[0].bank_account_name,
            building_society_num = payments[0].building_society_num)
        new_payments.append(new_payment)
    return new_payments

def write_payments(path: str, backup: str, new_payments: list) -> str:
    """
    Writes a list of Payment objects to a file in the same format as the file
    they were read from.
    Args:
        path (str): The path of the file to write to (the same as the
        file we read from in load_files())
        backup (str): The path to back the files up to
        new_payments (list): A list of Payment objects to write to file
    Returns:
        (str): A string indicating the file written to and the amount of
        Payment objects in the file
    """
    count = 0
    # Backs up the original file
    shutil.copy2(path, backup)
    # Gets the header from the original file
    with open(path, 'r') as read:
        header = read.read().splitlines()[0]
    with open(path, 'w') as write:
        write.write('{}\n'.format(header))
        for payment in new_payments:
            for key, value in payment.__dict__.items():
                if key != 'defaults':
                    write.write('{}\n'.format(value))
            count += 1
    # Logs the file so it isn't aggregated again
    with open('.\\already_checked.log', 'a') as already_checked:
        already_checked.write('{}\n'.format(path))
    success_string = '{} - Successfully written {}/{} payments to {}\n'.format(
        WRITETIME, count, len(new_payments), path)
    with open('.\\payments.log', 'a') as log:
        log.write(success_string)
    return success_string

def send_email(path: str, success_string: str) -> None:
    """
    Sends an email indicating success.
    Args:
        path (str): The path written to by write_payments()
        success_string (str): The string returned from write_payments()
    """
    msg = EmailMessage()
    msg.set_content(success_string)
    msg['Subject'] = path[-23:]
    msg['From'] = 'svc.hdc@hambleton.gov.uk'
    msg['To'] = 'ITSYSTEMS@hambleton.gov.uk'
    server = smtplib.SMTP('10.62.128.127')
    server.send_message(msg)
    server.quit()

if __name__ == '__main__':
    SYSTIME = datetime.date.today().strftime('%d-%b-%Y').upper()
    WRITETIME = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
    try:
        f = load_files('G:\\spool\\RBTEST\\frb_output')
    except ValueError:
        with open('.\\payments.log', 'a') as log:
            log.write('{}\n'.format(WRITETIME))
        sys.exit(1)
    payments = create_payments(f)
    keys = create_keys(payments)
    keys_vals = assign_keys(payments, keys)
    new_payments = sum_payments(keys_vals)
    success = write_payments(f, 'G:\\spool\\RBTEST\\archive', new_payments)
    send_email(f, success)
