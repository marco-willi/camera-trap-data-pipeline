""" Split a manifest into multiple batches
"""
import json
import os
import argparse
import math
import random
from collections import OrderedDict

from utils import (
    slice_generator, export_dict_to_json_with_newlines,
    file_path_splitter, file_path_generator)


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=str, required=True,
        help="Path to the manifest file (.json) file")
    parser.add_argument(
        "--split_order", type=str, default='random',
        choices=['sequential', 'random'],
        help="How to select the capture events for the different splits\
              (default random)")
    parser.add_argument(
        "--max_batch_size", type=int, default=None,
        help="Max number of capture events per batch.\
              Choose either max_batch_size or number_of_batches.")
    parser.add_argument(
        "--number_of_batches", type=int, default=None,
        help="How many batches to create. \
             Choose either batch_size or number_of_batches.")

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Manifest exists
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" % args['manifest'])

    # check Manifest filename
    assert args['manifest'].endswith('.json'), \
        "manifest file must end with '.json'"

    # check inputs
    if (args['number_of_batches'] is None) and (args['max_batch_size'] is None):
        raise ValueError(
            "Either number_of_batches or max_batch_size must be specified")

    if None not in (args['number_of_batches'], args['max_batch_size']):
        raise ValueError(
            "Only one of: number_of_batches/max_batch_size can be specified")

    file_name_parts = file_path_splitter(args['manifest'])

    # import manifest
    with open(args['manifest'], 'r') as f:
        manifest = json.load(f)

    n_captures = len(manifest.keys())

    print("Imported Manfest file %s with %s records" %
          (args['manifest'], n_captures), flush=True)

    # Create evenly sized splits
    if args['number_of_batches'] is not None:
        n_batches = args['number_of_batches']
    else:
        n_batches = math.ceil(n_captures / args['batch_size'])

    slices = slice_generator(n_captures, n_batches)

    # select captures
    capture_ids = list(manifest.keys())

    if args['split_order'] is 'random':
        random.seed(123)
        random.shuffle(capture_ids)

    print("Creating %s splits" % (n_batches))

    for batch_no, i_start, i_end in enumerate(slices):
        batch_manifest = OrderedDict()

        batch_path = file_path_generator(
            dir=os.path.dirname(args['manifest']),
            id=file_name_parts['id'],
            batch="batch%s" % batch_no,
            name=file_name_parts['name'],
            file_delim=file_name_parts['file_delim'],
            file_ext=file_name_parts['file_ext']
        )

        for batch_id in capture_ids[i_start: i_end]:
            batch_manifest[batch_id] = manifest[batch_id]

        print("Writing batch %s to %s with %s records" %
              (batch_no, batch_path, len(batch_manifest.keys())))

        export_dict_to_json_with_newlines(batch_manifest, batch_path)

        # change permmissions to read/write for group
        os.chmod(batch_manifest, 0o660)
