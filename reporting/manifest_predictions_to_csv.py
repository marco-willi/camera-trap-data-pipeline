""" Convert Manifest with ML to CSV """
import os
import logging
import json
import csv
import argparse
from collections import OrderedDict

from logger import setup_logger, create_logfile_name
from utils import set_file_permission

# args = dict()
# args['manifest'] = '/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1__complete__manifest.json'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1_machine_learning.csv'
#

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['manifest']):
        raise FileNotFoundError("manifest: {} not found".format(
                                args['manifest']))

    # Check Manifest exists
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" % args['manifest'])

    # check Manifest filename
    assert args['manifest'].endswith('.json'), \
        "manifest file must end with '.json'"

    # logging
    log_file_name = create_logfile_name('flatten_manifest_predictions')
    log_file_path = os.path.join(
            os.path.dirname(args['manifest']), log_file_name)

    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # import manifest
    with open(args['manifest'], 'r') as f:
        manifest = json.load(f)

    n_captures = len(manifest.keys())

    data_with_ml = OrderedDict()
    all_attributes = set()
    for capture_id, capture_data in manifest.items():
        (season, site, roll, capture) = capture_id.split('#')
        data_to_add = {
            'capture_id': capture_id
            }
        for upload_key, upload_data in capture_data['upload_metadata'].items():
            if upload_key.startswith('#machine_'):
                data_to_add[upload_key.split('#')[1]] = upload_data
        data_with_ml[capture_id] = data_to_add
        all_attributes = all_attributes.union(data_to_add.keys())

    # write to file
    header = list(all_attributes)
    header.sort()

    logger.info("Automatically generated output header: {}".format(
        header))

    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(header)
        tot = len(data_with_ml.keys())
        for line_no, (capture_id, record) in enumerate(data_with_ml.items()):
            to_write = list()
            for x in header:
                try:
                    to_write.append(record[x])
                except:
                    to_write.append('')
            csv_writer.writerow(to_write)
        logger.info("Wrote {} records to {}".format(
            line_no, args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
