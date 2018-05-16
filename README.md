# Payment Aggregation

Takes a BPY331 formatted log of payment records, aggregates the total of each
payee and writes it back to the file.

## How it works

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

## Processes

1. get_file_name() to get the most recent unmodified file in the directory,
read_file() to read the contents into memory and create_payments() to
create the Payment objects.
2. query_payments() to get or create the unique identifier for each Payment
object and group_payments() to create a dictionary using the unique
identifiers for keys.
3. sum_payments() to sum up the totals and create a new Payment object.
4. write_new_payments() to write the new Payment objects back to the file.
5. send_email() to send the email.

## Notes

* The database connection string is created using a .config file that isn't
on GitHub, so directly cloning the repository won't work.
* If a payment record doesn't include a rolling building society number
(i.e. the field is 0), the entry in the database will be NULL.
* Each field in the file is wrapped in double quotes and may have trailing
whitespace. The entries in the database don't have these characters, so
they are removed when checking against and writing to the table.
