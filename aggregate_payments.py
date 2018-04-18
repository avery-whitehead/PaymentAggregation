"""
Takes a BPY331 formatted log of payment records, aggregates the total of each
payee and writes it back to the file

TODO:
    Refactor - create a general Payment object for every record, not just the
    unique ones.
    Find some way of aggregating each Payment object. Sort code/acount number
    combination isn't unique enough.
"""

import os
import datetime

class Payment(object):
    """
    A payment recording according the BPY331 format
    """
    def __init__(self, **kwargs):
        defaults = {
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
        self.__dict__.update(defaults)
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
    for root, dirs, files in os.walk(files_dir):
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
    Creates a list of Payment objects given a file with some payment records.

    Args:
        dat_path (str): The path of the file with the payment records

    Returns:
        (list of Payment): A list of Payment objects made from the records
    """
    records_list = []
    payments_list = []
    with open(dat_path) as dat_file:
        dat = dat_file.read().splitlines()
    print(dat[0])
    #for i in range(1, len(dat_file), 29):

if __name__ == '__main__':
    SYSTIME = datetime.date.today().strftime('%d-%b-%Y').upper()
    NEW_DATS = gather_and_check_files('.\\data', '.\\checked_files.log')
    for new_dat in NEW_DATS:
        create_payment_objs(new_dat)
