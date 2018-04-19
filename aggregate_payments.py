"""
Takes a BPY331 formatted log of payment records, aggregates the total of each
payee and writes it back to the file

TODO:
    Construct aggregate Payment objects and write back to file
"""

import os
import datetime

class Payment(object):
    """
    A payment recording according the BPY331 format
    """
    def __init__(self, **kwargs):
        self.defaults = {
            'interface_source': '"BEN"',
            'batch_run_id': '"batch_run_id"',
            'posting_ref': '"posting_ref"',
            'account_ref': '"account_ref"',
            'payee_type': '"CL"',
            'payee_name': '"payee_name"',
            'payee_address': '"payee_address"',
            'claim_ref': '"claim_ref"',
            'claimant_name': '"claimant_name"',
            'claimant_adddress': '"claimant_address"',
            'amount': '"amount"',
            'posting_start_date': '"posting_start_date"',
            'posting_end_date': '"posting_end_date"',
            'payment_method': '"BACS"',
            'creditor_account_ref': '""',
            'bank_sort_code': '"bank_sort_code"',
            'bank_account_num': '"bank_account_num"',
            'bank_account_name': '"bank_account_name"',
            'building_society_num': '"0"',
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

def gather_and_check_files(files_dir, log_path):
    """
    Looks in a directory for any new and unedited dat files

    Args:
        files_dir (str): The directory containing the dat files
        log_dir (str): The path of the log containing edited dat file paths

    Returns:
        (list of str): A list of paths of dat files to be aggregated
    """
    new_dats = []
    # Only lists files that have been modified in the past 120 minutes
    now = datetime.datetime.now()
    threshold = now - datetime.timedelta(minutes=99999999)
    with open(log_path) as log_file:
        log = log_file.readlines()
    for root, _, files in os.walk(files_dir):
        for file_name in files:
            # If file name matches the correct format
            if file_name.startswith('bpy331_') and file_name.endswith('.dat'):
                file_path = os.path.join(root, file_name)
                file_stats = os.stat(file_path)
                modif = datetime.datetime.fromtimestamp(file_stats.st_mtime)
                # If file is new and hasn't been processed already
                if modif > threshold and file_name not in log:
                    new_dats.append(file_path)
    return new_dats

def create_payment_objs(dat_path):
    """
    Creates a list of Payment objects given a file with some payment records

    Args:
        dat_path (str): The path of the file with the payment records

    Returns:
        (list of Payment): A list of Payment objects made from the records
    """
    payments_list = []
    with open(dat_path) as dat_file:
        dat = dat_file.read().splitlines()
    for i in range(1, len(dat), 29):
        #"<payee_name>/<bank_sort_code>/<bank_account_num>"
        account_ref = '{}/{}/{}'.format(
            (dat[i + 5])[:-2],
            (dat[i + 15])[1:-2],
            (dat[i + 16])[1:])
        # Sets the non-default attributes of a Payment
        payment = Payment(
            batch_run_id=dat[i + 1],
            posting_ref=dat[i + 2],
            account_ref=account_ref,
            payee_name=dat[i + 5],
            payee_address=dat[i + 6],
            amount=dat[i + 10],
            bank_sort_code=dat[i + 15],
            bank_account_num=dat[i + 16],
            bank_account_name=dat[i + 17])
        payments_list.append(payment)
    return payments_list

def combine_payments(payments_list):
    """
    Given a list of payments, combine them according to their account ref
    as a kind of primary key

    Args:
        payments_list (list of Payment): The list of Payment objects to
        aggregate

    Returns:
        (dict of str:list of Payment): A dictionary object with the structure
        {account ref: [list of Payment objects with this account ref]}
    """
    # Creates a unique set of account refs
    account_refs = []
    for payment in payments_list:
        account_refs.append(payment.account_ref)
    account_refs = set(account_refs)
    # Creates a dictionary of payments with each unique account ref
    combined_payments = {}
    for account_ref in account_refs:
        temp_payments_list = []
        for payment in payments_list:
            if payment.account_ref == account_ref:
                temp_payments_list.append(payment)
        combined_payments[account_ref] = temp_payments_list
    return combined_payments

def aggregate_payments(account_ref):
    """
    Given a tuple of payments attached to an account ref, creates a new
    Payment object with an aggregation of their total payment amounts.

    Args:
        combined_payments (tuple of str, list of Payment): A dictionary object
        with the structure (account_ref, [list of payments])

    Returns:
        (Payment): A single Payment object with an aggregated amount
    """
    total_amount = 0
    for payment in account_ref[1]:
        #Trims the quotes from the amount and casts to a float
        amount = float(payment.amount[1:-2])
        total_amount += amount
    total_amount = round(total_amount, 2)
    print('{}: {}'.format(account_ref[0], total_amount))


def print_payment_obj(payment):
    """
    Prints a formatted Payment object

    Args:
        payment (Payment): The Payment object to print

    Returns:
        None
    """
    items = payment.__dict__.items()
    for key, value in items:
        if key != 'defaults':
            if key != 'payee_address':
                print(str(value))
            else:
                print(str(value).replace(' ', ''))
    print()

def print_payments_dict(payments_dict):
    """
    Prints a formatted dictionary of account references and their associated
    Payment objects

    Args:
        payments_dict (dict of str:list of Payment): A dictionary object with
        the structure {account ref: [list of Payment objects with this account
        ref]}

    Returns:
        None
    """
    for account_ref, payments in payments_dict.items():
        print('{}'.format(account_ref))
        for payment in payments:
            print_payment_obj(payment)

if __name__ == '__main__':
    SYSTIME = datetime.date.today().strftime('%d-%b-%Y').upper()
    NEW_DATS = gather_and_check_files('.\\data', '.\\checked_files.log')
    for new_dat in NEW_DATS:
        payments_list = create_payment_objs(new_dat)
        combined_payments = combine_payments(payments_list)
        for account_ref in combined_payments.items():
            aggregate_payments(account_ref)
