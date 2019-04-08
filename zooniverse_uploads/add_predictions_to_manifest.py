""" Integrate Aggregated Predictions into Manifest """
import json
import os
import argparse
import logging

from utils.logger import setup_logger, create_log_file
from utils.utils import (
    export_dict_to_json_with_newlines, file_path_splitter,
    file_path_generator, set_file_permission)
from machine_learning.flatten_preds import (
    flatten_ml_empty_preds, flatten_ml_species_preds)

# # For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1__complete__manifest.json"
# args['predictions_empty'] = None
# args['predictions_species'] = None
# args['add_all_species_scores'] = True
# args['output_file'] = None
#
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/MTZ/MTZ_S1__complete__manifest.json"
# args['predictions_empty'] = None
# args['predictions_species'] = None
# args['add_all_species_scores'] = True
# args['output_file'] = None
#
#
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/PLN/PLN_S1__complete__manifest.json"
# args['predictions_empty'] = None
# args['predictions_species'] = None
# args['add_all_species_scores'] = True
# args['output_file'] = None
#
#
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1__complete__manifest.json"
# args['predictions_empty'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1__complete__predictions_empty_or_not.json"
# args['predictions_species'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1__complete__predictions_species.json"
# args['output_file'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1__complete__manifest_TEST.json"
# args['add_all_species_scores'] = True

# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1__complete__manifest.json"
# args['predictions_empty'] = "/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1__complete__predictions_empty_or_not.json"
# args['predictions_species'] = "/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1__complete__predictions_species.json"
# args['output_file'] = "/home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1__complete__manifest.json"
# args['add_all_species_scores'] = True

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=str, required=True,
        help="Path to manifest file (.json)")
    parser.add_argument(
        "--predictions_empty", type=str, default=None,
        help="Path to the file with predictions from the empty model \
              (.json). Default is to generate the name based on the manifest.")
    parser.add_argument(
        "--predictions_species", type=str, default=None,
        help="Path to the file with predictions from the species model \
              (.json). Default is to generate the name based on the manifest.")
    parser.add_argument(
        "--output_file", type=str, default=None,
        help="Output file to write new manifest to (.json). \
              Default is to overwrite the manifest.")
    parser.add_argument(
        "--add_all_species_scores", action='store_true',
        help="Whether to save all species scores into the manifest \
              (and not just the top prediction).")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='add_predictions_to_manifest')

    args = vars(parser.parse_args())

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # Check Inputs
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    if args['output_file'] is None:
        args['output_file'] = args['manifest']
        logger.info("Updating {} with machine scores".format(
            args['output_file']))

    file_name_parts = file_path_splitter(args['manifest'])
    if args['predictions_empty'] is None:
        args['predictions_empty'] = file_path_generator(
            dir=os.path.dirname(args['manifest']),
            id=file_name_parts['id'],
            name='predictions_empty_or_not',
            batch=file_name_parts['batch'],
            file_delim=file_name_parts['file_delim'],
            file_ext='json'
        )
        logger.info("Reading empty predictions from {}".format(
            args['predictions_empty']))
    if args['predictions_species'] is None:
        args['predictions_species'] = file_path_generator(
            dir=os.path.dirname(args['manifest']),
            id=file_name_parts['id'],
            name='predictions_species',
            batch=file_name_parts['batch'],
            file_delim=file_name_parts['file_delim'],
            file_ext='json'
        )
        logger.info("Reading species predictions from {}".format(
              args['predictions_species']))

    if not os.path.exists(args['predictions_species']):
        raise FileNotFoundError("predictions: %s not found" %
                                args['predictions_species'])

    if not os.path.exists(args['predictions_empty']):
        raise FileNotFoundError("predictions: %s not found" %
                                args['predictions_empty'])

    # import manifest
    with open(args['manifest'], 'r') as f:
        mani = json.load(f)

    # import predictions
    with open(args['predictions_species'], 'r') as f:
        preds_species = json.load(f)

    with open(args['predictions_empty'], 'r') as f:
        preds_empty = json.load(f)

    captures_with_preds = 0
    n_total = len(mani.keys())

    # Extract predictions and add to manifest
    for capture_id, data in mani.items():
        # set ml to False per default
        data['info']['machine_learning'] = False
        meta_data = data['upload_metadata']
        # get predictions empty
        if capture_id in preds_empty:
            flat_empty = flatten_ml_empty_preds(preds_empty[capture_id])
            flat_empty = {'#{}'.format(k): v for k, v in flat_empty.items()}
            meta_data.update(flat_empty)
            data['info']['machine_learning'] = True
        # add species predictions
        if capture_id in preds_species:
            flat_species = flatten_ml_species_preds(preds_species[capture_id])
            flat_species = {'#{}'.format(k): v for k, v in flat_species.items()}
            meta_data.update(flat_species)
            data['info']['machine_learning'] = True
        if data['info']['machine_learning']:
            captures_with_preds += 1

    # statistic
    logger.info("Added predictions to {} / {} captures".format(
          captures_with_preds, n_total))

    # Export Manifest
    export_dict_to_json_with_newlines(mani, args['output_file'])

    # change permmissions to read/write for group
    set_file_permission(args['output_file'])
