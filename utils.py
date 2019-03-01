""" Util Functions """
import sys
import os
import csv
import time
import datetime
import json
import random
import math
from hashlib import md5
import logging
import configparser
from collections import Counter


logger = logging.getLogger(__name__)


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


def current_time_str():
    """ Return current time as formatted string """
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
    return st


def current_date_time_str():
    """ Return current time as formatted string """
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
    return st


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


def open_file_with_rw_permissions(file):
    """ Open a file with rw permissions on group level """
    umask_original = os.umask(0o117)
    try:
        flags = os.O_WRONLY | os.O_CREAT
        fdesc = os.open(file, flags, 0o770)
    finally:
        os.umask(umask_original)
    return fdesc


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
    try:
        hashed = hash_string(value, constant="")
        num = assign_hash_to_zero_one(hashed)
    except:
        raise ValueError("value %s could not be hashed" % value)
    return num


def hash_string(value, constant=""):
    """ Return hashed value """
    to_hash = str(value) + str(constant)
    hashed = md5(to_hash.encode('ascii')).hexdigest()
    return hashed


def assign_hash_to_zero_one(value):
    """ Assign a md5 string to a value between 0 and 1 """
    assert type(value) == str, \
        "value is not a string, is of type %s" % type(value)
    assert len(value) == 32, \
        "value is not of len 32, has len %s, raw %s" % (len(value), value)

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


def export_dict_to_json_with_newlines(data, path):
    """ Export a dictionary to a json file with newlines between each
        dictionary entry
    """
    with open(path, 'w') as outfile:
        first_row = True
        for _id, values in data.items():
            if first_row:
                outfile.write('{')
                outfile.write('"%s":' % _id)
                json.dump(values, outfile)
                first_row = False
            else:
                outfile.write(',\n')
                outfile.write('"%s":' % _id)
                json.dump(values, outfile)
        outfile.write('}')


def file_path_generator(
        dir, id, name, batch="complete",
        file_delim="__", file_ext='json'):
    """ Create consistent file paths based on dir/id/name """
    file_name = file_delim.join([x for x in [id, batch, name] if x is not ''])
    file_name = '%s.%s' % (file_name, file_ext)
    file_path = os.path.join(dir, file_name)
    return file_path


def file_path_splitter(path, file_delim="__", file_ext='json'):
    """ Split a file created with 'file_path_generator' into components """
    fname = os.path.basename(path)
    f_ext = ".%s" % file_ext
    # Check if file extension matches
    if f_ext not in fname:
        raise ValueError("Specified file extension %s does not match %s" %
                         (file_ext, fname))
    fname_no_ext = fname.split(".%s" % file_ext)[0]
    fname_splits = fname_no_ext.split(file_delim)
    id = fname_splits[0]
    batch = fname_splits[1]
    name = fname_splits[2]
    return {'id': id, 'batch': batch, 'name': name,
            'file_delim': file_delim, 'file_ext': file_ext}


def read_cleaned_season_file(path, quotechar='"'):
    """ Check the input file """
    cleaned_captures = list()
    required_header_cols = ('season', 'site', 'roll', 'capture',
                            'path', 'invalid')
    with open(path, newline='') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',', quotechar=quotechar)
        header = next(csv_reader)
        name_to_id_mapper = {x: i for i, x in enumerate(header)}
        # check header
        if not all([x in header for x in required_header_cols]):
            print("Missing columns -- found %s, require %s" %
                  (header, required_header_cols))

        for _id, row in enumerate(csv_reader):
            cleaned_captures.append(row)

    return cleaned_captures, name_to_id_mapper


def print_nested_dict(key, dic):
    """ Print potentially nested dictionary """
    if isinstance(dic, dict):
        for _id, _data in dic.items():
            if isinstance(_data, list):
                for _sub_data in _data:
                    print_nested_dict("{}_{}".format(key, _id), _sub_data)
            else:
                print_nested_dict("{}_{}".format(key, _id), _data)
    elif isinstance(dic, list) or isinstance(dic, tuple):
        for _sub_data in dic:
            print_nested_dict(key, _sub_data)
    else:
        logger.info("Key: {:40} - Value: {:<15}".format(key, dic))


def set_file_permission(path):
    """ set permission of a file to r/w for group """
    try:
        os.chmod(path, 0o660)
    except PermissionError:
        pass


def balanced_sample_best_effort(y, n_samples):
    """ Sample as balanced as possible """
    class_samples = Counter(y)
    freq = class_samples.most_common()
    n_tot = sum(class_samples.values())
    n_samples = min(n_samples, n_tot)
    n_samples_per_step = math.ceil(n_samples / len(class_samples))
    # n_samples_per_step = math.ceil(
    #     np.quantile(list(class_samples.values()), 0.01))
    n_samples_per_step = 1
    maps = {k: [] for k in class_samples.keys()}
    sampled = {k: [] for k in class_samples.keys()}
    for _id, yy in enumerate(y):
        maps[yy].append(_id)
    n_sampled = 0
    while n_sampled < n_samples:
        for k, f in reversed(freq):
            n_in_group = len(maps[k])
            n_to_sample = min(n_in_group, n_samples_per_step)
            sampled[k] += [
                maps[k].pop(random.randrange(len(maps[k])))
                for _ in range(n_to_sample)]
            n_sampled += n_to_sample
    sampled_ids = [sampled[k] for k, f in reversed(freq)]
    sampled_list = list()
    for i, x in enumerate(sampled_ids):
        sampled_list += x
        if i >= n_samples:
            break
    sampled_list = sampled_list[0:n_samples]
    return sampled_list
