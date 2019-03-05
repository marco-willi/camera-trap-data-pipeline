""" Upload Manifest to Zooniverse """
import json
import os
import argparse
import time
import datetime
import textwrap
import signal
import logging

from panoptes_client import Project, Panoptes, SubjectSet
from panoptes_client.panoptes import PanoptesAPIException

from logger import setup_logger, create_log_file
from zooniverse_uploads import uploader
from image_compression.resize_and_compress_images import (
    process_images_list_multiprocess,
    resize_and_compress_list_of_images)
from utils import (
    read_config_file, estimate_remaining_time,
    current_time_str, export_dict_to_json_with_newlines,
    file_path_splitter, file_path_generator, set_file_permission)

# # For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1_manifest1.json"
# args['output_file'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1_manifest2.json"
# args['project_id'] = 7679
# #args['subject_set_id'] = '40557'
# args['subject_set_name'] = 'KAR_S1_TEST_v2'
# args['password_file'] = '~/keys/passwords.ini'


def add_subject_data_to_manifest(subject_set, capture_id, subject_id, data):
    """ Add subject data to manifest
        - extracts data as uploaded and created to/by Zooniverse
        - saves data into the manifest for local storage
        Args:
        - subject_set: the SubjectSet object
        - capture_id: the capture_id
        - subject_id: the subject_id
        - data: a dictionary linking the current subject to the manifest
    """
    data['info']['uploaded'] = True
    data['info']['subject_set_id'] = subject_set.id
    data['info']['subject_set_name'] = subject_set.display_name
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
    data['info']['upload_time'] = st
    data['info']['subject_id'] = subject_id
    data['info']['anonymized_capture_id'] = uploader.anonymize_id(capture_id)


def batch_data_storage():
    return {'subjects_to_link': list(),
            'capture_ids': list(),
            'subject_ids': list()}


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=str, required=True,
        help="Path to manifest file (.json)")

    parser.add_argument(
        "--project_id", type=int, required=True,
        help="Zooniverse project id")

    parser.add_argument(
        "--subject_set_id", type=str, default=None,
        help="Zooniverse subject set id. Specify if you want to add subjects\
              to an existing set (useful if upload crashed)")

    parser.add_argument(
        "--output_file", type=str, default=None,
        help="Output file for updated manifest (.json). \
              Default is to overwrite the manifest.")

    parser.add_argument(
        "--password_file", type=str, required=True,
        help="File that contains the Zooniverse password (.ini),\
              Example File:\
              [zooniverse]\
              username: dummy\
              password: 1234")

    parser.add_argument(
        "--dont_compress_images", action='store_true',
        help="Don't compress images (default IS to compress)")

    parser.add_argument(
        "--max_pixel_of_largest_side", type=int, default=1440,
        help="The largest side of the image after compressing the images if\
        '--dont_compress_images' is not specified.")

    parser.add_argument(
        "--save_quality", type=int, default=50,
        help="The save quality of the image after compressing the images if\
        '--dont_compress_images' is not specified.")

    parser.add_argument(
        "--n_processes", type=int, default=3,
        help="The number of processes to use in parallel if\
        '--dont_compress_images' is not specified.")

    parser.add_argument(
        "--image_root_path", type=str, default=None,
        help="The root path of all images in the manifest. Used when reading \
        them from disk.")

    parser.add_argument(
        "--debug_mode", action='store_true',
        help="Activate debug mode which will print more status messages.")

    parser.add_argument(
        "--log_dir", type=str, default=None)

    parser.add_argument(
        "--log_filename", type=str,
        default='upload_manifest')

    args = vars(parser.parse_args())

    # Check Manifest file
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    if args['image_root_path'] is not None:
        if not os.path.isdir(args['image_root_path']):
            raise FileNotFoundError("image_root_path: %s not found" %
                                    args['image_root_path'])

    # Check Input
    if not args['dont_compress_images']:
        qual = args['save_quality']
        if qual is not None:
            assert (qual <= 100) and (qual > 15), \
                "save_quality must be between 15 and 100"

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    file_name_parts = file_path_splitter(args['manifest'])

    # generate subject_set name
    sub_name = "%s_%s" % (file_name_parts['id'], file_name_parts['batch'])
    args['subject_set_name'] = sub_name
    logger.info("Automatically generated subject_set_name: {}".format(
        sub_name))

    # define tracker file path
    tracker_file_path = file_path_generator(
        dir=os.path.dirname(args['manifest']),
        id=file_name_parts['id'],
        name='upload_tracker_file',
        batch=file_name_parts['batch'],
        file_delim=file_name_parts['file_delim'],
        file_ext='txt'
    )

    logger.info("Defining upload tracker file at: {}".format(
        tracker_file_path))

    # read upload tracker file
    if not os.path.exists(tracker_file_path):
        uploader.create_tracker_file(tracker_file_path)
        set_file_permission(tracker_file_path)
    tracker_data = uploader.read_tracker_file(tracker_file_path)

    n_in_tracker_file = len(tracker_data.keys())
    logger.info("Found {} already uploaded subjects in tracker file".format(
                n_in_tracker_file))

    # define output_file
    if args['output_file'] is None:
        args['output_file'] = file_path_generator(
            dir=os.path.dirname(args['manifest']),
            id=file_name_parts['id'],
            name="%s_%s" % (file_name_parts['name'], 'uploaded'),
            batch=file_name_parts['batch'],
            file_delim=file_name_parts['file_delim'],
            file_ext='json'
            )
        logger.info("Outputfile is {}".format(args['output_file']))

    # import manifest
    with open(args['manifest'], 'r') as f:
        mani = json.load(f)

    logger.info("Imported Manfest file {} with {} records".format(
                args['manifest'], len(mani.keys())))

    # read Zooniverse credentials
    config = read_config_file(args['password_file'])

    # connect to panoptes
    Panoptes.connect(username=config['zooniverse']['username'],
                     password=config['zooniverse']['password'])

    # Get Project
    my_project = Project(args['project_id'])

    # get or create a subject set
    if args['subject_set_id'] is not None:
        # Get an existing subject_set
        my_set = SubjectSet().find(args['subject_set_id'])
        logger.info("Subject set {} found, will upload into this set".format(
                    args['subject_set_id']))
        # check subject_set name is identical to what is expected from the
        # manifest name, if not abort
        if not my_set.display_name == args['subject_set_name']:
            msg = "Found subject-set with id {} and name {} on Zooniverse -- \
            but tried to continue uploading from manifest with \
            id {} -- this discrepancy is unexpected, threfore, \
            upload is aborted - did you choose the wrong manifest?".format(
                my_set.id, my_set.display_name, args['subject_set_name'])
            logger.error(textwrap.shorten(msg, width=150))
            raise ValueError("Subject-set name {} not identical to {}".format(
                my_set.display_name, args['subject_set_name']
            ))
    else:
        my_set = uploader.create_subject_set(
            my_project, args['subject_set_name'])
        logger.info("Created new subject set with id {}, name {}".format(
                     my_set.id, my_set.display_name))

    time_start = time.time()
    uploaded_subjects_count = 0

    capture_ids_all = list(mani.keys())

    n_tot = len(capture_ids_all)
    n_remaining = n_tot - n_in_tracker_file

    upload_batch_size = 100
    batch_data = batch_data_storage()

    # handle (Ctrl+C) keyboard interrupt
    def signal_handler(*args):
        logger.info('You pressed Ctrl+C! - attempting to clean up gracefully')
        remaining_subjects_to_link = len(batch_data['subjects_to_link'])
        try:
            logger.info("Linking {} remaining uploaded subjects".format(
                        remaining_subjects_to_link))
            uploader.add_batch_to_subject_set(
                my_set, batch_data['subjects_to_link'])
            uploader.update_tracker_file(
                tracker_file_path, batch_data['capture_ids'],
                batch_data['subject_ids'])
        except PanoptesAPIException as e:
            logger.error('Failed to link {} remaining subjects'.format(
                         remaining_subjects_to_link))
            uploader.handle_batch_failure(batch_data['subjects_to_link'])
        finally:
            raise SystemExit

    # register the handler for interrupt signal
    signal.signal(signal.SIGINT, signal_handler)

    # loop over manifest
    for capture_id in capture_ids_all:

        # current subject data
        data = mani[capture_id]

        # skip if capture_id arleady in tracker_file / uploaded
        if capture_id in tracker_data:
            uploaded_subjects_count += 1
            continue
        try:
            if isinstance(data['images'], dict):
                images_to_upload = data['images']['original_images']
            elif isinstance(data['images'], list):
                images_to_upload = data['images']
            else:
                logger.warning("no images found for capture_id: {}".format(
                    capture_id))
            # append root path if specified
            if args['image_root_path'] is not None:
                images_to_upload = [
                    os.path.join(args['image_root_path'], x)
                    for x in images_to_upload]
            # Compress images if specified
            if not args['dont_compress_images']:
                images_to_upload = \
                    process_images_list_multiprocess(
                            images_to_upload,
                            resize_and_compress_list_of_images,
                            n_processes=args['n_processes'],
                            print_status=False,
                            max_pixel_of_largest_side=args['max_pixel_of_largest_side'],
                            save_quality=args['save_quality'])
                # remove images that failed to process
                images_to_upload = [
                    x for x in images_to_upload if x is not None]
                # skip subject if no images present
                if len(images_to_upload) == 0:
                    logger.warning(
                        "capture_id {} has no valid images - skipping".format(
                         capture_id))
                    continue
            metadata = data['upload_metadata']
            metadata['#original_images'] = data['images']['original_images']
            metadata['capture_id_anonymized'] = \
                uploader.anonymize_id(capture_id)
            subject = uploader.create_subject(
                my_project, images_to_upload, metadata)
            batch_data['subjects_to_link'].append(subject)
            batch_data['capture_ids'].append(capture_id)
            batch_data['subject_ids'].append(subject.id)
            if args['debug_mode']:
                logger.info("finished saving {} - {}".format(
                            capture_id, current_time_str()))

        except PanoptesAPIException as e:
            logger.info('Error occurred for capture_id: %s' % capture_id)
            logger.info('Details of error: {}'.format(e))
            uploader.handle_batch_failure(batch_data['subjects_to_link'])
            raise SystemExit

        # link each batch of new subjects to the subject set
        if len(batch_data['subjects_to_link']) % upload_batch_size == 0:
            uploader.add_batch_to_subject_set(
                my_set, batch_data['subjects_to_link'])
            uploaded_subjects_count += len(batch_data['subjects_to_link'])

            # update upload tracker
            uploader.update_tracker_file(
                tracker_file_path,
                batch_data['capture_ids'],
                batch_data['subject_ids'])

            # reset batch data
            batch_data = batch_data_storage()

            # print progress information
            ts = time.time()
            tr = estimate_remaining_time(
                time_start,
                n_remaining,
                max(0, uploaded_subjects_count-n_remaining))
            st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            msg = "Saved {:5}/{:5} ({:4} %) - Current Time: {} - \
                   Estimated Time Remaining: {}".format(
                   uploaded_subjects_count, n_tot,
                   round((uploaded_subjects_count/n_tot) * 100, 2), st, tr)
            logger.info(textwrap.shorten(msg, width=99))

    # catch any left over batches in the file
    if len(batch_data['subjects_to_link']) > 0:
        uploader.add_batch_to_subject_set(
            my_set, batch_data['subjects_to_link'])
        uploaded_subjects_count += len(batch_data['subjects_to_link'])
        uploader.update_tracker_file(
            tracker_file_path,
            batch_data['capture_ids'],
            batch_data['subject_ids'])

    # update manifest
    tracker_data = uploader.read_tracker_file(tracker_file_path)

    for capture_id, subject_id in tracker_data.items():
        data = mani[capture_id]
        add_subject_data_to_manifest(my_set, capture_id, subject_id, data)

    logger.info(
      "Finished uploading subjects - total {}/{} successfully uploaded".format(
       uploaded_subjects_count, n_tot))

    # Export Manifest
    export_dict_to_json_with_newlines(mani, args['output_file'])

    # change permmissions to read/write for group
    set_file_permission(args['output_file'])

    # delete the tracker file
    os.remove(tracker_file_path)
