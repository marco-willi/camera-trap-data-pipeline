""" Upload Manifest to Zooniverse """
import json
import os
import argparse
import time
import datetime
import textwrap
import signal

from panoptes_client import Project, Panoptes, SubjectSet
from panoptes_client.panoptes import PanoptesAPIException

from zooniverse_uploads import uploader
from utils import (
    read_config_file, estimate_remaining_time,
    current_time_str, export_dict_to_json_with_newlines,
    file_path_splitter, file_path_generator)

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
        "--subject_set_name", type=str, default=None,
        help="Zooniverse subject set name. Default is to automatically derive\
              it from the manifest name.")

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
        "--debug_mode", action='store_true',
        help="Activate debug mode which will print more status messages.")

    args = vars(parser.parse_args())

    # Print arguments
    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Manifest file
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    # Check one of subject_set_id and subject_set_name exists
    if None not in (args['subject_set_name'], args['subject_set_id']):
        raise ValueError("Only one of 'subject_set_name' and 'subject_set_id' \
                          should be specified")

    file_name_parts = file_path_splitter(args['manifest'])

    # generate subject_set name if not specified
    if args['subject_set_name'] is None:
        sub_name = "%s_%s" % (file_name_parts['id'], file_name_parts['batch'])
        args['subject_set_name'] = sub_name
        print("Automatically generated subject_set_name: %s" % sub_name)

    # define tracker file path
    tracker_file_path = file_path_generator(
        dir=os.path.dirname(args['manifest']),
        id=file_name_parts['id'],
        name='upload_tracker_file',
        batch=file_name_parts['batch'],
        file_delim=file_name_parts['file_delim'],
        file_ext='txt'
    )

    # read upload tracker file
    if not os.path.exists(tracker_file_path):
        uploader.create_tracker_file(tracker_file_path)
    tracker_data = uploader.read_tracker_file(tracker_file_path)

    n_in_tracker_file = len(tracker_data.keys())
    print("Found %s already uploaded subjects in tracker file" %
          n_in_tracker_file)

    # import manifest
    with open(args['manifest'], 'r') as f:
        mani = json.load(f)

    print("Imported Manfest file %s with %s records" %
          (args['manifest'], len(mani.keys())), flush=True)

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
        print("Subject set %s found, will upload into this set" %
              args['subject_set_id'], flush=True)
    else:
        my_set = uploader.create_subject_set(
            my_project, args['subject_set_name'])
        print("Created new subject set with id %s, name %s" %
              (my_set.id, my_set.display_name))

    time_start = time.time()
    uploaded_subjects_count = 0

    capture_ids_all = list(mani.keys())

    n_tot = len(capture_ids_all)

    upload_batch_size = 100
    batch_data = batch_data_storage()

    # handle (Ctrl+C) keyboard interrupt
    def signal_handler(*args):
        print('You pressed Ctrl+C! - attempting to clean up gracefully')
        remaining_subjects_to_link = len(batch_data['subjects_to_link'])
        try:
            print("Linking %s remaining uploaded subjects" %
                  remaining_subjects_to_link)
            uploader.add_batch_to_subject_set(
                my_set, batch_data['subjects_to_link'])
            uploader.update_tracker_file(
                tracker_file_path, batch_data['capture_ids'],
                batch_data['subject_ids'])
        except PanoptesAPIException as e:
            print('Failed to link %s remaining subjects' %
                  remaining_subjects_to_link)
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
            images_to_upload = data['images']['compressed_images']
            metadata = data['upload_metadata']
            metadata['#original_images'] = data['images']['original_images']
            metadata['capture_id'] = uploader.anonymize_id(capture_id)
            subject = uploader.create_subject(
                my_project, images_to_upload, metadata)
            batch_data['subjects_to_link'].append(subject)
            batch_data['capture_ids'].append(capture_id)
            batch_data['subject_ids'].append(subject.id)
            if args['debug_mode']:
                print("finished saving %s - %s" %
                      (capture_id, current_time_str()), flush=True)

        except PanoptesAPIException as e:
            print('Error occurred for capture_id: %s' % capture_id)
            print('Details of error: {}'.format(e))
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
                time_start, n_tot, uploaded_subjects_count)
            st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            msg = "Saved %s/%s (%s %%) - Current Time: %s - \
                   Estimated Time Remaining: %s" % \
                  (uploaded_subjects_count, n_tot,
                   round((uploaded_subjects_count/n_tot) * 100, 2), st, tr)
            print(textwrap.shorten(msg, width=99), flush=True)

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

    print("Finished uploading subjects - total %s/%s successfully uploaded" %
          (uploaded_subjects_count, n_tot))

    # Export Manifest
    export_dict_to_json_with_newlines(mani, args['output_file'])

    # change permmissions to read/write for group
    os.chmod(args['output_file'], 0o660)

    # delete the tracker file
    os.remove(tracker_file_path)
