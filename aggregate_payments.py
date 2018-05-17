"""
Takes a BPY331 formatted log of payment records, aggregates the total of each
payee and writes it back to the file.

HOW IT WORKS:
    1. The most recent unmodified file in the directory is read and a list of
    Payment objects is created for each payment record in the file. If no such
    file exists, the program exits.
    2. The fields of each Payment object are checked against the database. If
    the fields match an entry, the unique identifier for that entry is used to
    group together identical Payment objects. If the fields don't match an
    entry, a new entry is created and the unique identifier for the new entry
    is used.
    3. For each group of identical Payment objects, the total amount paid is
    summed up, and a new Payment object is created with the summation.
    4. Each new Payment object is written back to the file, overwriting the old
    records.
    5. An email is sent containing details about the aggregation.

PROCESSES:
    1. get_file_name() to get the most recent unmodified file in the directory,
    read_file() to read the contents into memory and create_payments() to
    create the Payment objects.
    2. query_payments() to get or create the unique identifier for each Payment
    object and group_payments() to create a dictionary using the unique
    identifiers for keys.
    3. sum_payments() to sum up the totals and create a new Payment object.
    4. write_new_payments() to write the new Payment objects back to the file.
    5. send_email() to send the email.

NOTES:
    * The database connection string is created using a .config file that isn't
    on GitHub, so directly cloning the repository won't work.
    * Each field in the file is wrapped in double quotes and may have trailing
    whitespace. The entries in the database don't have these characters, so
    they are removed when checking against and writing to the table.

https://github.com/james-whitehead/PaymentAggregation
"""

import datetime
import os
import sys
import json
import pyodbc

class Payment:
    """
    A payment record according to the BPY331 format.
    """
    def __init__(self, **kwargs: str) -> None:
        """
        Initialises a Payment object.  Fields with "NOT SET" are variable and
        set with details read from the file. Other fields are either static or
        can be set right away.
        Args:
            **kwargs (str): Keyword arguments for the fields that need to be
            set from the file.
        """
        self.defaults = {
            'interface_source': '"BEN"',
            'batch_run_id': '"NOT SET"',
            'posting_ref': '"NOT SET"',
            'account_ref': '"NOT SET"',
            'payee_type': '"CL"',
            'payee_name': '"NOT SET"',
            'payee_address': '"NOT SET"',
            'claim_ref': '"NOT SET"',
            'claimant_name': '"Aggregated DHP UC Payment"',
            'claimant_adddress': '"Aggregated DHP UC Payment"',
            'amount': '"amount"',
            'posting_start_date': f'"{SYSTIME}"',
            'posting_end_date': f'"{SYSTIME}"',
            'payment_method': '"BACS"',
            'creditor_account_ref': '""',
            'sort_code': '"NOT SET"',
            'bank_account': '"NOT SET"',
            'bank_account_name': '"NOT SET"',
            'building_society_num': '"NOT SET"',
            'post_office_name': '""',
            'post_office_address': '""',
            'collection_flag': '"N"',
            'document_num': '""',
            'document_type': '""',
            'replacement_flag': '"N"',
            'effective_date': f'"{SYSTIME}"',
            'blank_one': '""',
            'blank_two': '""',
            'document_date': '""'}
        # Initialises an instance of Payment with default and kwargs values
        for key, value in self.defaults.items():
            setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def print_payment(self, index: int) -> None:
        """
        Formats and prints Payment object line-by-line in the same style as
        the records in the file.
        Args:
            index (int): The index of the Payment object as it would be in the
            file.
        """
        print(f'--{index}--')
        items = self.__dict__.items()
        for key, value in items:
            if key != 'defaults':
                # Removing whitespace in the address makes it more readable
                if key == 'payee_address':
                    print(value.replace(' ', ''))
                else:
                    print(value)
        print()

    def get_sql_fields(self) -> dict:
        """
        Gets the bank account, sort code, name and building society number
        fields (the ones used in the SQL database) from this Payment object
        with surrounding quotes and trailing whitespace removed.
        Returns:
            (dict): A dictionary with keys of the column names and the values
            of this Payment object.
        """
        return {
            'bank_account': self.bank_account[1:-2],
            'sort_code': self.sort_code[1:-2],
            'payee_name': self.payee_name[1:-2],
            'building_society_num': self.building_society_num[1:-2]}


def get_file_name(file_dir: str) -> str:
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
    with open('.\\logs\\already_checked.log', 'r') as already_checked:
        checked = already_checked.read().splitlines()
    files_list = []
    now = datetime.datetime.now()
    delta = now - datetime.timedelta(minutes=99999999)
    for root, _, files in os.walk(file_dir):
        for file in files:
            if file.startswith('bpy331_') and file.endswith('.dat'):
                path = os.path.join(root, file)
                stats = os.stat(path)
                modif = datetime.datetime.fromtimestamp(stats.st_mtime)
                if modif > delta and path not in checked:
                    files_list.append(path)
    return max(files_list, key=lambda f: os.stat(f).st_mtime)

def read_file(filepath: str) -> list:
    """
    Reads a file line-by-line to create a list, with each line as a separate
    element.
    Args:
        filepath (str): The path of the file to read.
    Returns:
        (list): A list of strings for each line in the file.
    """
    with open(filepath) as f:
        lines = f.read().splitlines()
    return lines

def create_payments(lines: list) -> list:
    """
    Given a list of lines in a file, creates a Payment object for each record.
    Each record in the file is 29 lines long.
    Args:
        lines (list): A list of lines in the file.
    Returns:
        (list): A list of Payment objects created from the records in the file.
    """
    payments = []
    for i in range(1, len(lines), 29):
        payment = Payment(
            batch_run_id = lines[i + 1],
            posting_ref = lines[i + 2],
            payee_name = lines[i + 17],
            payee_address = lines[i + 6],
            amount = lines[i + 10],
            sort_code = lines[i + 15],
            bank_account = lines[i + 16],
            bank_account_name = lines[i + 17],
            building_society_num = lines[i + 18])
        payments.append(payment)
    return payments

def query_payments(connection: pyodbc.Connection, payments: list) -> None:
    """
    Queries the SQL database to either get or create the unique reference
    for each Payment object and sets the attribute of the object to that
    reference. Payment object are updated in-place, so we don't need to
    return anything.
    Args:
        payments (list): The list of Payment objects to query.
    """
    with open('.\\sql\\insert_query.sql') as insert_f:
        insert_query = insert_f.read()
    with open('.\\sql\\select_query.sql') as select_f:
        select_query = select_f.read()
    for payment in payments:
        sql = payment.get_sql_fields()
        cursor = connection.cursor()
        # Creates an entry in the database if one doesn't exist
        cursor.execute(insert_query, (
            sql['bank_account'], sql['sort_code'], sql['payee_name'],
            sql['building_society_num'], sql['bank_account'],
            sql['sort_code'], sql['payee_name'],
            sql['building_society_num']))
        connection.commit()
        # Gets the account reference from the database
        cursor.execute(select_query, (
            sql['bank_account'], sql['sort_code'], sql['payee_name'],
            sql['building_society_num']))
        payment.account_ref = f'"{cursor.fetchone()[0]}"'


if __name__ == '__main__':
    SYSTIME = datetime.date.today().strftime('%d-%b-%Y').upper()
    WRITETIME = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
    with open('.\\.config') as config_f:
        config = json.load(config_f)
    # Attempts to connect to the SQL database
    try:
        DB_CONN = pyodbc.connect(
            driver=config['driver'],
            server=config['server'],
            database=config['database'],
            uid=config['uid'],
            pwd=config['pwd'])
    except pyodbc.InterfaceError as error:
        # Writes to log with current time and error
        with open('.\\logs\\payments.log', 'a') as log:
            log.write(f'{WRITETIME} - {error}\n')
        sys.exit(1)
    # Attempts to open the most recent file
    try:
        f = get_file_name('.\\data')
    except ValueError:
        # Writes to log with just the current time
        with open('.\\logs\\payments.log', 'a') as log:
            log.write(f'{WRITETIME}\n')
        sys.exit(1)
    lines = read_file(f)
    payments = create_payments(lines)
    query_payments(DB_CONN, payments)
    for index, payment in enumerate(payments):
        payment.print_payment(index)
