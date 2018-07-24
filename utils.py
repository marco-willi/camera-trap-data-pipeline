""" Util Functions """
import sys
import os
import time
import configparser


def print_progress(count, total):
    """ Print Progress to stdout """
    pct_complete = float(count) / total

    # Note the \r which means the line should overwrite itself.
    msg = "\r- Progress: {0:.1%}".format(pct_complete)

    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stdout.write('')


def estimate_remaining_time(start_time, n_total, n_current):
    """ Estimate remaining time """
    time_elapsed = time.time() - start_time
    n_remaining = n_total - (n_current - 1)
    avg_time_per_record = time_elapsed / (n_current + 1)
    estimated_time = n_remaining * avg_time_per_record
    return time.strftime("%H:%M:%S", time.gmtime(estimated_time))


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


def slice_generator(sequence_length, n_blocks):
    """ Creates a generator to get start/end indexes for dividing a
        sequence_length into n blocks
    """
    return ((int(round((b - 1) * sequence_length/n_blocks)),
             int(round(b * sequence_length/n_blocks)))
            for b in range(1, n_blocks+1))


def read_config_file(cfg_file_path):
    """ Reads a cfg (.ini) file """
    # replace ~ in path
    if '~' in cfg_file_path:
        user_path = os.path.expanduser('~')
        cfg_file_path = cfg_file_path.replace('~', user_path)

    if not os.path.exists(cfg_file_path):
        raise FileNotFoundError("config file: %s not found" %
                                cfg_file_path)

    # read config file and return
    config = configparser.ConfigParser()
    config.read(cfg_file_path)
    return config
