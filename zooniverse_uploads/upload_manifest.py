""" Upload Manifest to Zooniverse """
import json
import os
import argparse
import time
import datetime
import hashlib
import configparser

from panoptes_client import Project, Panoptes, SubjectSet, Subject


# # For Testing
# args = dict()
# args['manifest'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest1.json"
# args['output_file'] = "/home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_manifest2.json"
# args['project_id'] = 5155
# args['subject_set_id'] = ''
# args['subject_set_name'] = 'RUA_S1_machine_learning_v1'
# args['password_file'] = '~/keys/passwords.ini'


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
        help="Zooniverse project id")

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

    args = vars(parser.parse_args())

    for k, v in args.items():
        print("Argument %s: %s" % (k, v))

    # Check Inputs
    if not os.path.exists(args['manifest']):
        raise FileNotFoundError("manifest: %s not found" %
                                args['manifest'])

    if not os.path.exists(args['password_file']):
        raise FileNotFoundError("password_file: %s not found" %
                                args['password_file'])

    # import manifest
    with open(args['manifest'], 'r') as f:
        mani = json.load(f)

    # read Zooniverse credentials
    config = configparser.ConfigParser()
    config.read(args['password_file'])

    # connect to panoptes
    Panoptes.connect(username=config['zooniverse']['username'],
                     password=config['zooniverse']['password'])

    # Get Project
    my_project = Project(args['project_id'])

    # Get or Create a subject set
    if args['subject_set_id'] is not '':
        # Get a subject set
        my_set = SubjectSet().find(args['subject_set_id'])
    else:
        # Create a new subject set
        my_set = SubjectSet()
        my_set.links.project = my_project
        my_set.display_name = args['subject_set_name']
        my_set.save()
        print("Created new subject set with id %s, name %s" %
              (my_set.id, my_set.display_name))
        my_project.add_subject_sets(my_set)

    # Loop through manifest and create subjects
    counter = 0
    n_tot = len(mani.keys())
    for capture_id, data in mani.items():
        # get subject data
        meta_data = data["upload_metadata"]
        images = data['images']["compressed_images"]
        anonymized_capture_id = hashlib.sha1(str.encode(capture_id)).hexdigest()
        # create subject
        subject = Subject()
        subject.links.project = my_project
        # add images
        for image in images:
            subject.add_location(image)
        # original images
        original_images = data['images']['original_images']
        # add metadata
        subject.metadata = meta_data
        # add image information
        subject.metadata['#original_images'] = original_images
        # add anonymized id to easily find and map images on
        # the zooniverse interface in the database
        subject.metadata['capture_id'] = anonymized_capture_id
        try:
            subject.save()
            # add subject to subject set
            my_set.add(subject)
            # add information to manifest
            data['info']['uploaded'] = True
            data['info']['subject_set_id'] = my_set.id
            data['info']['subject_set_name'] = my_set.display_name
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
            data['info']['upload_time'] = st
            data['info']['subject_id'] = subject.id
            data['info']['anonymized_capture_id'] = anonymized_capture_id
        except:
            print("Failed to upload subject %s" % capture_id)
        counter += 1
        if (counter % 1000) == 0:
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%H%M%S')
            print("Completed %s/%s - Time: %s" % (counter, n_tot, st), flush=True)

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
