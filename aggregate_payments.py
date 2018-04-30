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
    1. create_payments()
    2. create_keys()
    3. assign_keys()
    4. sum_payments()
    5. write_payments()
"""

import os

def load_files(file_dir: str) -> list:
    """
    Gets the names of all the BPY331 formatted files from a directory.
    Args:
        file_dir (str): The directory to search
    Returns:
        (list): A list of the paths of the files
    """
    files_list = []
    for _, _, files in os.walk(file_dir):
        for file in files:
            if file.startswith('bpy331_') and file.endswith('.dat'):
                files_list.append('{}/{}'.format(file_dir, file))
    return files_list


if __name__ == '__main__':
    files = load_files('./data')
    print(files)
