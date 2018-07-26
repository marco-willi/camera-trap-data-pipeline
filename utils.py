""" Util Functions """
import sys
import os
import time
from hashlib import md5
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


def correct_image_name(name):
    """ change image name
    OLD: S1/G12/G12_R1/PICT3981.JPG
    NEW: S1/G12/G12_R1/S1_G12_R1_PICT3981.JPG

    OLD: S8/O09/O09_R3/S8_O09_R3_S8_O09_R3_IMAG9279.JPG
    NEW: S8/O09/O09_R3/S8_O09_R3_S8_O09_R3_IMAG9279.JPG
    """
    if '/' not in name:
        return name
    name_splits = name.split('/')
    if '_' in name_splits[-1]:
        return name
    path = '/'.join(name_splits[0:-1])
    file_name_new = '_'.join([name_splits[0], name_splits[2], name_splits[3]])
    return path + '/' + file_name_new


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


def id_to_zero_one(value):
    """ Deterministically assign string to value 0-1 """
    hashed = hash_string(value, constant="")
    num = assign_hash_to_zero_one(hashed)
    return num


def hash_string(value, constant=""):
    """ Return hashed value """
    to_hash = str(value) + str(constant)
    hashed = md5(to_hash.encode('ascii')).hexdigest()
    return hashed


def assign_hash_to_zero_one(value):
    """ Assign a md5 string to a value between 0 and 1 """
    assert type(value) == str
    assert len(value) == 32

    value_6_chars = value[:6]
    value_hex = int(value_6_chars, base=16)

    max_6_char_hex_value = 0xFFFFFF

    zero_one = value_hex / max_6_char_hex_value

    return zero_one


def assign_zero_one_to_split(zero_one_value, split_percents, split_names):
    """ Assign a value between 0 and 1 to a split according to a percentage
        distribution
    """
    split_props_cum = [sum(split_percents[0:(i+1)]) for i in
                       range(0, len(split_percents))]
    for sn, sp in zip(split_names, split_props_cum):
        if zero_one_value <= sp:
            return sn
