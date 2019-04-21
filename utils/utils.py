""" Util Functions """
import sys
import os
import time
import datetime
import json
import random
import pandas as pd
from hashlib import md5
import logging
import configparser
from collections import Counter, OrderedDict


logger = logging.getLogger(__name__)


class OrderedCounter(Counter, OrderedDict):
    """ Counter that keeps insert order """
    pass


def check_dir_existence(dir):
    if not os.path.isdir(dir):
        raise FileNotFoundError(
            "path {} does not exist -- must be a directory".format(
                dir))


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

    OLD: S8/O09/O09_R3/S8_O09_R3_IMAG9279.JPG
    NEW: S8/O09/O09_R3/S8_O09_R3_IMAG9279.JPG

    OLD: S4/J12/J12_R2/IMG_6068.JPG
    NEW: S4/J12/J12_R2/S4_J12_R2_IMG6068.JPG
    """
    if '/' not in name:
        return name
    name_splits = name.split('/')
    if '_' in name_splits[-1]:
        n_ = len(name_splits[-1].split('_'))
        if n_ == 4:
            return name
        elif n_ == 2:
            name_splits[-1] = ''.join(name_splits[-1].split('_'))
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


def create_capture_id(season, site, roll, capture):
    return '{}#{}#{}#{}'.format(season, site, roll, capture)


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


def sort_df_by_capture_id(df):
    """ Sort df by capture_id """
    if 'capture_id' in df.columns.tolist():
        sort_id = [x.split('#') for x in df.capture_id]
    else:
        sort_id = [x.split('#') for x in df.index]
    sort_id = ['{}#{}#{}#{:05}'.format(
        x[0], x[1], x[2], int(x[3])) for x in sort_id]
    df['sort_id'] = sort_id
    df.sort_values(['sort_id'], inplace=True)
    df.drop('sort_id', inplace=True, axis=1)


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


def _append_season_to_image_path(path, season):
    """ Appned season tag to image path """
    path_first = next(part for part in path.split(os.path.sep) if part)
    if not path_first == season:
        return os.path.join(season, path)
    else:
        return path


def read_cleaned_season_file_df(path):
    df = pd.read_csv(path, dtype='str', index_col=None)
    df.fillna('', inplace=True)
    required_header_cols = ('capture_id', 'season', 'site', 'roll', 'capture',
                            'path')
    if 'path' not in df.columns:
        if 'image_path_rel' in df.columns:
            df['path'] = df[['image_path_rel', 'season']].apply(
                lambda x: _append_season_to_image_path(*x), axis=1)

    if 'capture_id' not in df.columns:
        df['capture_id'] = df[['season', 'site', 'roll', 'capture']].apply(
                        lambda x: create_capture_id(*x), axis=1)

    for col in required_header_cols:
        if col not in df.columns:
            print("Column {} not found in cleaned_season_file".format(col))
    return df


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
    """ Sample as balanced as possible from labels
    Args:
        y: list - class labels of all observations
        n_samples: int - number of samples to take
    Returns:
        sampled_list: list - indexes of 'y' that have been sampled
    Example:
        y: ['zebra', 'zebra', 'elephant', 'lion']
        n_samples: 3
        sampled_list: [3, 2, 0]
    """
    # calculate class frequencies
    class_to_frequency = Counter(y)
    class_ordered_by_freq = class_to_frequency.most_common()
    # calculate how many samples to (ideally) get per class
    n_tot = sum(class_to_frequency.values())
    n_samples = min(n_samples, n_tot)
    # create class to id map / class to sample ids
    class_to_ids_map = {k: [] for k in class_to_frequency.keys()}
    class_ids_sampled = {k: [] for k in class_to_frequency.keys()}
    for _id, yy in enumerate(y):
        class_to_ids_map[yy].append(_id)
    # sample iteratively
    n_sampled = 0
    n_to_sample_per_step = 1
    while n_sampled < n_samples:
        # sample from least frequent class
        for k, f in reversed(class_ordered_by_freq):
            n_in_group = len(class_to_ids_map[k])
            n_to_sample = min(n_in_group, n_to_sample_per_step)
            # randomly sample n_to_sample from the class and remove them
            class_ids_sampled[k] += [
                class_to_ids_map[k].pop(
                    random.randrange(len(class_to_ids_map[k])))
                for _ in range(n_to_sample)]
            n_sampled += n_to_sample
    # get all sampled ids
    sampled_ids = [class_ids_sampled[k] for k, f in
                   reversed(class_ordered_by_freq)]
    sampled_list = list()
    # ensure that sampled list has the correct length
    for i, x in enumerate(sampled_ids):
        sampled_list += x
        if i >= n_samples:
            break
    sampled_list = sampled_list[0:n_samples]
    return sampled_list


def merge_csvs(base_csv, to_add_csv, key, merge_new_cols_to_right=True):
    """ Merge two csvs and return a df """

    df_base = pd.read_csv(
        base_csv, dtype='str')
    df_base.fillna('', inplace=True)

    assert key in df_base.columns.tolist(), \
        "column {} not found in {}".format(key, base_csv)

    df_add = pd.read_csv(
        to_add_csv, dtype='str', index_col=key)
    df_add.fillna('', inplace=True)
    df_add.index = df_add.index.astype('str')

    # drop duplicate cols
    to_add_cols = df_add.columns.tolist()
    base_cols = df_base.columns.tolist()
    to_add_cols = [
        x for x in to_add_cols if
        (x not in base_cols) or (x == key)]

    print("Adding cols {}".format(to_add_cols))

    df_add = df_add[to_add_cols]

    df_merged = pd.merge(
        df_base, df_add, how='left',
        left_on=key, right_index=True)

    all_cols = df_merged.columns.tolist()

    # sort columns
    if not merge_new_cols_to_right:
        first_cols = [x for x in to_add_cols if x in all_cols]
    else:
        first_cols = [x for x in base_cols if x in all_cols]
    cols_rearranged = first_cols + [x for x in all_cols if x not in first_cols]
    df_merged = df_merged[cols_rearranged]

    return df_merged
