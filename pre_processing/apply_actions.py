""" Apply Actions """
import os
import argparse
import logging

from utils.logger import setup_logger, create_log_file
from pre_processing.utils import read_image_inventory, export_inventory_to_csv
from pre_processing.actions import apply_action
from config.cfg import cfg

# args = dict()
# args['actions_to_perform'] = '/home/packerc/shared/season_captures/MAD/captures/MAD_S1_actions_to_perform.csv'
# args['captures'] = '/home/packerc/shared/season_captures/MAD/captures/MAD_S1_captures.csv'
# args['log_dir'] = '/home/packerc/shared/season_captures/APN/log_files/'

flags = cfg['pre_processing_flags']

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--actions_to_perform", type=str, required=True)
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='apply_actions')
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['actions_to_perform']):
        raise FileNotFoundError(
            "actions_to_perform {} does not exist -- must be a file".format(
                args['actions_to_perform']))

    if not os.path.isfile(args['captures']):
        raise FileNotFoundError(
            "captures {} does not exist -- must be a file".format(
                args['captures']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    logger.info("Reading actions from {}".format(args['actions_to_perform']))
    actions = read_image_inventory(
        args['actions_to_perform'], unique_id=None)

    logger.info("Reading captures from {}".format(args['captures']))
    captures = read_image_inventory(
        args['captures'], unique_id='image_name')

    try:
        for _id, action in actions.items():
            apply_action(captures[action['image']], action, flags)
        logger.info("Successfully applied actions")
    except Exception as e:
        logger.error("Failed to apply actions", exc_info=True)

    export_inventory_to_csv(captures, args['captures'])

    logger.info("Updated captures file at: {}".format(args['captures']))
