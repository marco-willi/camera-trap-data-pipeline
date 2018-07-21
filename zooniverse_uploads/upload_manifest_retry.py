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
# args['overwrite_output'] = False


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
              to an existing set (useful if upload crashes)")

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
        "-overwrite", default=False,
        action='store_true', required=False,
        help="Whether to overwrite the 'output_file' or to re-use if it\
              exists (useful if upload crashes)")

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

    # check if output file exists and read already processed capture events
    if os.path.isfile(args['output_file']):
        if args['overwrite']:
            print("Overwriting %s" % args['output_file'])
        else:
            with open(args['output_file'], 'r') as f:
                out_mani = json.load(f)
        n_processed = len(out_mani.keys())
        print("Already processed %s records as found in %s" %
              (n_processed, args['output_file']))
        # remove already processed from mani
        for k in out_mani:
            mani.pop(k, None)
    # If the outputfile does not exist create it
    else:
        with open(args['output_file'], 'w') as outfile:
            outfile.write('{')

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

    def upload_subject(project, subjet_set, capture_id, data, outfile):
        """ Upload a specific subject
            Args:
            - project: a Project() object defining the Zooniverse project
            - subject_set: a SubjectSet() object
            - capture_id: a str defining the capture id
            - data: a dictionary containing all info to upload
            - outfile: a file-object to write successful uploads to
        """
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
            subjet_set.add(subject)
            # add information to manifest
            data['info']['uploaded'] = True
            data['info']['subject_set_id'] = subjet_set.id
            data['info']['subject_set_name'] = subjet_set.display_name
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
            data['info']['upload_time'] = st
            data['info']['subject_id'] = subject.id
            data['info']['anonymized_capture_id'] = anonymized_capture_id
            outfile.write(',\n')
            outfile.write('"%s":' % capture_id)
            json.dump(data, outfile)
        except:
            print("Failed to upload subject %s" % capture_id)

    def estimate_remaining_time(start_time, n_total, n_current):
        """ Estimate remaining time """
        time_elapsed = time.time() - start_time
        n_remaining = n_total - (n_current - 1)
        avg_time_per_record = time_elapsed / (n_current + 1)
        estimated_time = n_remaining * avg_time_per_record
        return time.strftime("%H:%M:%S", time.gmtime(estimated_time))

    # Loop through manifest and create subjects
    counter = 0
    time_start = time.time()
    n_tot = len(mani.keys())

    with open(args['output_file'], 'a') as outfile:
        for capture_id, data in mani.items():
            # upload subject
            upload_subject(project=my_project, subjet_set=my_set,
                           capture_id=capture_id, out_file=outfile)
            counter += 1
            if counter > 30:
                break
            if (counter % 1000) == 0:
                ts = time.time()
                st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                est_time = estimate_remaining_time(time_start, n_tot, counter)
                print("Completed %s/%s (%s %%)- Current Time: %s - \
                      Estimated Time Remaining: %s" %
                      (counter, n_tot, 100 * round(counter/n_tot, 2), st,
                       est_time), flush=True)
        # close the file
        outfile.write('}')
