""" Flatten ML predictions and Export to CSV """
import os
import logging
import json
import pandas as pd
import argparse
from collections import OrderedDict

from utils.logger import setup_logger, create_log_file
from utils.utils import set_file_permission, sort_df_by_capture_id
from machine_learning.flatten_preds import (
    flatten_ml_empty_preds, flatten_ml_species_preds
)

# args = dict()
# args['predictions_empty'] = '/home/packerc/shared/zooniverse/MachineLearning/GRU/GRU_S1_predictions_empty_or_not.json'
# args['predictions_species'] = '/home/packerc/shared/zooniverse/MachineLearning/GRU/GRU_S1_predictions_species.json'
# args['output_csv'] = '/home/packerc/shared/zooniverse/MachineLearning/GRU/GRU_S1_ml_preds_flat.csv'


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions_species", type=str, required=True)
    parser.add_argument("--predictions_empty", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='flatten_ml_predictions')

    args = vars(parser.parse_args())

    if not os.path.exists(args['predictions_species']):
        raise FileNotFoundError("predictions: %s not found" %
                                args['predictions_species'])

    if not os.path.exists(args['predictions_empty']):
        raise FileNotFoundError("predictions: %s not found" %
                                args['predictions_empty'])
    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # import predictions
    with open(args['predictions_species'], 'r') as f:
        preds_species = json.load(f)

    with open(args['predictions_empty'], 'r') as f:
        preds_empty = json.load(f)

    logger.info("Imported {} captures with species predictions".format(
        len(preds_species.keys())))

    logger.info("Imported {} captures with empty predictions".format(
        len(preds_empty.keys())))

    all_preds = OrderedDict()

    # get empty preds
    for capture_id, empty_preds in preds_empty.items():
        flat_empty = flatten_ml_empty_preds(empty_preds)
        all_preds[capture_id] = flat_empty

    # get species preds
    for capture_id, species_preds in preds_species.items():
        flat_species = flatten_ml_species_preds(species_preds)
        try:
            all_preds[capture_id].update(flat_species)
        except:
            all_preds[capture_id] = flat_species

    # export as csv
    df = pd.DataFrame.from_dict(all_preds, orient='index')
    df.index.name = 'capture_id'
    sort_df_by_capture_id(df)

    logger.info("Automatically generated output header: {}".format(
        df.columns.tolist()))

    # export
    df.to_csv(args['output_csv'], index=True)

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
