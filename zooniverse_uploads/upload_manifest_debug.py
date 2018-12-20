""" Upload Manifest to Zooniverse """
import json
import os
import argparse
import time
import datetime
import hashlib
import traceback
import textwrap

from panoptes_client import Project, Panoptes, SubjectSet, Subject

from utils import (
    read_config_file, estimate_remaining_time,
    slice_generator, current_time_str)

# # For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1_manifest1.json"
# args['output_file'] = "/home/packerc/shared/zooniverse/Manifests/KAR/KAR_S1_manifest2.json"
# args['project_id'] = 7679
# #args['subject_set_id'] = '40557'
# args['subject_set_name'] = 'KAR_S1_TEST_v2'
# args['password_file'] = '~/keys/passwords.ini'


def add_subject_data_to_manifest(subject_set, subject, data):
    """ Add subject data to manifest """
    data['info']['uploaded'] = True
    data['info']['subject_set_id'] = subject_set.id
    data['info']['subject_set_name'] = subject_set.display_name
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
    data['info']['upload_time'] = st
    data['info']['subject_id'] = subject.id
    data['info']['anonymized_capture_id'] = subject.metadata['capture_id']


def create_subject(project, capture_id, data, debug):
    """ Create a specific subject
        Args:
        - project: a Project() object defining the Zooniverse project
        - capture_id: a str defining the capture id
        - data: a dictionary containing all info to upload
    """
    meta_data = data["upload_metadata"]
    images = data['images']["compressed_images"]
    anonymized_capture_id = hashlib.sha1(str.encode(capture_id)).hexdigest()
    # create subject
    subject = Subject()
    subject.links.project = my_project
    # add images
    if debug:
        print("adding locations for %s - %s" %
              (capture_id, current_time_str()), flush=True)
    for image in images:
        subject.add_location(image)
    if debug:
        print("finished locations for %s - %s" %
              (capture_id, current_time_str()), flush=True)
    # original images
    original_images = data['images']['original_images']
    # add metadata
    subject.metadata = meta_data
    # add image information
    subject.metadata['#original_images'] = original_images
    # add anonymized id to easily find and map images on
    # the zooniverse interface in the database
    subject.metadata['capture_id'] = anonymized_capture_id
    if debug:
        print("saving %s - %s" % (capture_id, current_time_str()), flush=True)
    subject.save()
    if debug:
        print("finished saving %s - %s" %
              (capture_id, current_time_str()), flush=True)
    return subject


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-manifest", type=str, required=True,
        help="Path to manifest file (.json)")

    parser.add_argument(
        "-project_id", type=int, required=True,
        help="Zooniverse project id")

    parser.add_argument(
        "-subject_set_name", type=str, required=False, default='',
        help="Zooniverse subject set name")

    parser.add_argument(
        "-subject_set_id", type=str, required=False, default='',
        help="Zooniverse subject set id. Specify if you want to add subjects\
              to an existing set (useful if upload crashed)")

    parser.add_argument(
        "-output_file", type=str, required=True,
        help="Output file for updated manifest (.json)")

    parser.add_argument(
        "-password_file", type=str, required=True,
        help="File that contains the Zooniverse password (.ini),\
              Example File:\
              [zooniverse]\
              username: dummy\
              password: 1234")

    parser.add_argument(
        "-debug_mode", action='store_true',
        help="Activate debug mode which will print more status messages.")

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    if (args['subject_set_name'] == '') and (args['subject_set_id'] == ''):
        raise ValueError("Either 'subject_set_name or 'subject_set_id must \
            be specified")

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

    # Get or Create a subject set
    if args['subject_set_id'] is not '':
        # Get a subject set
        my_set = SubjectSet().find(args['subject_set_id'])
        print("Subject set found, looking for already uploaded subjects",
              flush=True)
        # find already uploaded subjects
        n_already_uploaded = 0
        for subject in my_set.subjects:
            n_already_uploaded += 1
            if (n_already_uploaded % 100) == 0:
                print("Found %s uploaded records and counting..." %
                      n_already_uploaded, flush=True)
            roll = subject.metadata['#roll']
            site = subject.metadata['#site']
            capture = subject.metadata['#capture']
            season = subject.metadata['#season']
            capture_id = '#'.join([season, site, roll, capture])
            data = mani[capture_id]
            add_subject_data_to_manifest(my_set, subject, data)
        print("Found %s already uploaded records" % n_already_uploaded)
    else:
        # Create a new subject set
        my_set = SubjectSet()
        my_set.links.project = my_project
        my_set.display_name = args['subject_set_name']
        my_set.save()
        print("Created new subject set with id %s, name %s" %
              (my_set.id, my_set.display_name))
        my_project.add_subject_sets(my_set)

    # Loop through manifest and upload subjects in blocks of 500 at a time
    time_start = time.time()
    counter = 0

    capture_ids_all = list(mani.keys())
    n_tot = len(mani.keys())

    uploads_per_cycle = 500
    n_blocks = max(round(n_tot / uploads_per_cycle), 1)

    # Loop over blocks
    slices = slice_generator(n_tot, n_blocks)
    for block_nr, (start_i, end_i) in enumerate(slices):
        subjects_to_upload = list()
        print("Starting to process batch %s/%s" % (block_nr + 1, n_blocks),
              flush=True)
        n_failed = 0
        for capture_id in capture_ids_all[start_i:end_i]:
            data = mani[capture_id]
            # upload if not already uploaded
            if not data['info']['uploaded']:
                try:
                    if args['debug_mode']:
                        print("creating %s - %s" %
                              (capture_id, current_time_str()), flush=True)
                    subject = create_subject(my_project, capture_id,
                                             data, args['debug_mode'])
                    if args['debug_mode']:
                        print("finished %s - %s" %
                              (capture_id, current_time_str()), flush=True)
                    # add information to manifest
                    add_subject_data_to_manifest(my_set, subject, data)
                    # add subject to subject set list to upload later
                    subjects_to_upload.append(subject)
                except:
                    traceback.print_exc()
                    print("Failed to save subject %s" % capture_id)
                    n_failed += 1
            counter += 1
            if (counter % 500) == 0:
                ts = time.time()
                tr = estimate_remaining_time(time_start, n_tot, counter)
                st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                msg = "Completed %s/%s (%s %%) - Current Time: %s - \
                       Estimated Time Remaining: %s" % \
                      (counter, n_tot, round((counter/n_tot) * 100, 2), st, tr)
                print(textwrap.shorten(msg, width=99), flush=True)

        # link the current block of subjects to the subjec set
        n_to_upload = len(subjects_to_upload)
        print("Number of subjects failed to save in batch: %s" % n_failed)
        print("Adding %s subjects of batch to subject_set at %s"
              % (n_to_upload, current_time_str()), flush=True)
        my_set.add(subjects_to_upload)
        print("Finished processing batch %s/%s at %s" %
              (block_nr + 1, n_blocks, current_time_str()), flush=True)

    # Export Manifest
    with open(args['output_file'], 'w') as outfile:
        first_row = True
        for _id, values in mani.items():
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

    # change permmissions to read/write for group
    os.chmod(args['output_file'], 0o660)
