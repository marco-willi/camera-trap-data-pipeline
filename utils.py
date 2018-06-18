""" Util Functions """
import sys
import csv


def print_progress(count, total):
    """ Print Progress to stdout """
    pct_complete = float(count) / total

    # Note the \r which means the line should overwrite itself.
    msg = "\r- Progress: {0:.1%}".format(pct_complete)

    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stdout.write('')


def write_first_nrows_of_csv_to_csv(input_file, output_file, n_rows):
    """ Write the first n rows of a input csv to a new csv """
    with open(input_file, "r") as ins:
        parsed_lines = []
        for _id, line in enumerate(ins):
            if _id > n_rows:
                break
            parsed_lines.append(line)
    with open(output_file, 'w') as outs:
        for line in parsed_lines:
            outs.write(line)
