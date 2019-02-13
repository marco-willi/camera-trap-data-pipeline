""" Check Captures and Images """
import csv
import numpy as np
import pandas as pd
from datetime import datetime
from collections import OrderedDict

args = dict()

args['input_grouped_inventory'] = '/home/packerc/will5448/image_inventory_grouped.csv'
args['output_csv'] = '/home/packerc/will5448/image_inventory_to_inspect.csv'
args['ignore_excluded_images'] = False



# read grouped data
inventory = OrderedDict()
with open(args['input_grouped_inventory'], "r") as ins:
    csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
    header = next(csv_reader)
    row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
    for line_no, line in enumerate(csv_reader):
        # print status
        if ((line_no % 10000) == 0) and (line_no > 0):
            print("Read {:,} images".format(line_no))
        image_path_original = line[row_name_to_id_mapper['image_path_original']]
        inventory[image_path_original] = {
            k: line[v] for k, v in row_name_to_id_mapper.items()}

# do checks
inventory_to_check = dict()
check_columns = [x for x in header if x.startswith('image_check__')]
basic_checks = ['image_check__{}'.format(x) for x in flags['image_checks_basic']]
time_checks = ['image_check__{}'.format(x) for x in flags['image_checks_time']]

for image_path_original, image_data in inventory.items():
    at_least_one_basic_check = \
        any([int(image_data[x])==1 for x in basic_checks if x in check_columns])
    at_least_one_time_check = \
        any([int(image_data[x])==1 for x in time_checks if x in check_columns])
    # export problematic cases only
    if at_least_one_basic_check or at_least_one_time_check:
        inventory_to_check[image_path_original] = image_data
