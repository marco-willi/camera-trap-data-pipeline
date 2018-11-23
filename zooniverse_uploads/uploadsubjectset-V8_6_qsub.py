import os
import time
import csv
import argparse
from panoptes_client import Project, Panoptes, Subject, SubjectSet
from utils import read_config_file, estimate_remaining_time, slice_generator
from collections import OrderedDict


def create_and_upload_subject(capture_event, uvar, zvar):
    # NA-Not Applicable, IN-Invalid, NF-Not found, CR - Compression Error
    img_excl_code = ["NA", "IN", "NF", "CR"]

    # initialize Subject object
    subject = Subject()
    subject.links.project = zvar['project_obj']

    # add image file locations and metadata
    capture_img_n = 0
    capture_cols = list(capture_event.keys())
    image_anonym_cols = [imgn for imgn in capture_cols if 'Image' in imgn]
    image_msipath_cols = [imgn for imgn in capture_cols if 'path' in imgn]
    for img_n, path_col in zip(image_anonym_cols, image_msipath_cols):
        if capture_event[img_n] not in img_excl_code:
            print("Adding image: %s" % img_n)
            subject.add_location(os.path.join(uvar['upload_dir_path'],
                                 capture_event[img_n]))
            subject.metadata[img_n] = capture_event[img_n]
            # Add MSI path as meta data
            meta_name_path = '#' + path_col
            meta_name_path = meta_name_path.replace(' ', '')
            subject.metadata[meta_name_path] = capture_event[path_col]
            capture_img_n += 1

    if capture_img_n > 0:
        # add capture metadata
        subject.metadata['attribution'] = zvar['attribution']
        subject.metadata['license'] = zvar['license']
        subject.metadata['#site'] = capture_event['site']
        subject.metadata['#roll'] = capture_event['roll']
        subject.metadata['#capture'] = capture_event['capture']
        try:
            subject.save()
            capture_event['zoosubjid'] = int(subject.id)
            print("Subject %s saved" % capture_event['zoosubjid'], flush=True)
            return subject
        except Exception as e:
            print(e)
            capture_event['uploadstatus'] = "ERR"
    else:
        # No valid/viable images
        capture_event['uploadstatus'] = "NVI"
        print("No viable/valid images in capture", flush=True)
    return None


def set_upload_vars(uplvars):
    uplvars['input_manifest'] = os.path.basename(uplvars['input_manifest_path'])
    uplvars['loc_code'] = uplvars['input_manifest'].split("_")[0]
    uplvars['prefix'] = uplvars['input_manifest'].rsplit("_",2)[0]
    uplvars['season_code'] = uplvars['input_manifest'].split("_")[1]
    uplvars['upload_loc'] = os.path.join(uplvars['upload_loc'],uplvars['loc_code'])
    uplvars['upload_dir_name'] = '_'.join([uplvars['loc_code'], uplvars['season_code'],"Compressed"])
    uplvars['upload_dir_path'] = os.path.join(uplvars['upload_loc'],uplvars['upload_dir_name'])
    uplvars['output_manifest_vN'] = int(uplvars['input_manifest'].split("_")[-1].split('.')[0][1:])+1 #set manifest version number
    uplvars['output_manifest'] = uplvars['prefix']+"_"+"manifest_v"+str(uplvars['output_manifest_vN'])+'.csv'
    uplvars['manifest_loc'] = os.path.join(uplvars['manifest_loc'],uplvars['loc_code'])
    uplvars['output_manifest_path'] = os.path.join(uplvars['manifest_loc'],uplvars['output_manifest'])
    return uplvars


def test_upload_paths(uplvars):
    error = []
    for loc in [uplvars['upload_dir_path'],uplvars['upload_loc'],uplvars['manifest_loc']]:
        if os.path.isdir(loc)==False:
            error.append("\n\t !! Directory "+loc+" does not exist.")
    for path in [uplvars['output_manifest_path']]:
        if os.path.isdir(path)==True:
            error.append("\n\t !! "+path+" already exists.")
    return error


def test_zoo_vars(zoovars):
    Panoptes.connect(username=zoovars['username'], password=zoovars['password'])
    zoovars['project_id'] = int(zoovars['project_id'])
    zoovars['project_obj'] = Project.find(zoovars['project_id'])
    if zoovars['subject_set_id'] == -1:
        print("Creating new SubjectSet with name %s" %
              zoovars['subject_set_name'])
        zoovars['subject_set_obj'] = SubjectSet()
        zoovars['subject_set_obj'].links.project = zoovars['project_obj']
        zoovars['subject_set_obj'].display_name = zoovars['subject_set_name']
        zoovars['subject_set_obj'].save()
        zoovars['subject_set_id'] = int(zoovars['subject_set_obj'].id)
    else:
        print("Linking to existing subject set with id %s" %
              zoovars['subject_set_id'])
        zoovars['subject_set_obj'] = SubjectSet.find(zoovars['subject_set_id'])
    return zoovars


if __name__ == "__main__":

    upld_vars = dict.fromkeys(
        ['input_manifest_path', 'input_manifest', 'loc_code', 's_num',
        'prefix', 'upload_loc', 'upload_dir_name', 'upload_dir_path',
        'output_manifest_vN', 'output_manifest', 'manifest_loc',
        'output_manifest_path'])

    zoo_vars = dict.fromkeys(['username', 'password', 'project_id',
     'project_obj', 'subject_set_name', 'subject_set_id', 'subject_set_obj',
     'attribution','license'])

    upld_stat = dict.fromkeys(['UC','SO','NVI','ERR','N0'])
    upld_stat['UC'] = {'status': "Upload Complete",'change': 0,'new_total': 0}
    upld_stat['SO'] = {'status':"Subject Saved not Added",'change': 0,'new_total': 0}
    upld_stat['ERR'] = {'status':"Subject Save Error",'change': 0,'new_total': 0}
    upld_stat['NVI'] = {'status':"No Valid Images",'change': 0,'new_total': 0}
    upld_stat['N0'] = {'status': "No Upload Attempts Made",'change': 0,'new_total': 0}


    upld_vars['upload_loc'] = "/home/packerc/shared/zooniverse/ToUpload/"
    upld_vars['manifest_loc'] = "/home/packerc/shared/zooniverse/Manifests"

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-manifest", type=str, required=True)

    parser.add_argument(
        "-project_id", type=int, required=True,
        help="Zooniverse project id")

    parser.add_argument(
        "-subject_set_name", type=str, required=False, default='',
        help="Zooniverse subject set name")

    parser.add_argument(
        "-subject_set_id", type=int, required=False, default=None,
        help="Zooniverse subject set id")

    parser.add_argument("-attribution", type=str, required=True)
    parser.add_argument("-license", type=str, required=True)

    parser.add_argument(
        "-password_file", type=str, required=True,
        help="File that contains the Zooniverse password (.ini),\
              Example File:\
              [zooniverse]\
              username: dummy\
              password: 1234")

    args = vars(parser.parse_args())

    # # For Testing
    # args = {'manifest': '/home/packerc/shared/zooniverse/Manifests/SER/SER_S11_4_manifest_v0.csv',
    #  'project_id': 4996, 'subject_set_name': 'SER_S11_4_v4', 'password_file': '~/keys/passwords.ini',
    # 'attribution': 'University of Minnesota Lion Center + SnapshotSafari + Snapshot Serengeti + Serengeti National Park + Tanzania',
    # 'license': 'SnapshotSafari + Snapshot Serengeti', 'subject_set_id': None}

    # Print Function Arguments
    for k, v in args.items():
        print("Argument %s: %s" % (k, v), flush=True)

    #######################
    # Read Manifest File
    #######################

    manifest_headers = [
     'site', 'roll', 'capture', 'Image 1', 'Image 2',
     'Image 3', 'path 1', 'path 2', 'path 3',
     'zoosubjsetid', 'zoosubjid', 'uploadstatus']

    manifest = OrderedDict()
    print("Importing manifest %s ..." % args['manifest'])
    with open(args['manifest'], 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        header = next(csv_reader)
        assert all([x in header for x in manifest_headers]), \
            "CSV must have a header containing following \
             entries: %s, found following: %s" \
             % (manifest_headers, header)
        # map columns to position
        col_mapper = {x: header.index(x) for x in
                      manifest_headers}
        for i, row in enumerate(csv_reader):
            roll = str(row[col_mapper['roll']])
            site = str(row[col_mapper['site']])
            capture = str(row[col_mapper['capture']])
            capture_id = '#'.join([site, roll, capture])
            manifest[capture_id] = {col_name: row[col_mapper[col_name]]
                                    for col_name in col_mapper.keys()}

    print("Imported Manfest file %s with %s records" %
          (args['manifest'], len(manifest.keys())), flush=True)

    ##### SET AND CHECK UPLOAD VARIABLES#####

    print("\nBy default:")
    print("\tCompressed image file directory: "+upld_vars['upload_loc'])
    print("\tUpload manifest file directory: "+upld_vars['manifest_loc'])

    upld_vars['input_manifest_path'] = args['manifest']
    upld_vars = set_upload_vars(upld_vars)

    print("\nBased on input manifest title: ")
    print("\tImages will be uploaded from: "+upld_vars['upload_dir_path'])
    print("\tUpdated manifest will be saved to: "+upld_vars['output_manifest_path'])

    error = test_upload_paths(upld_vars)
    if len(error) != 0:
        print("\n")
        for e in error:
            print(e)
        exit(1)

    #####SET AND CHECK ZOONIVERSE VARIABLES#####

    # read Zooniverse credentials
    config = read_config_file(args['password_file'])

    # connect to panoptes
    zoo_vars['username'] = config['zooniverse']['username']
    zoo_vars['password'] = config['zooniverse']['password']
    zoo_vars['project_id'] = args['project_id']

    if args['subject_set_id'] is not None: #
        zoo_vars['subject_set_id'] = args['subject_set_id']
        zoo_vars['subject_set_name'] = ""
    else:
        zoo_vars['subject_set_name'] = args['subject_set_name']
        zoo_vars['subject_set_id'] = -1

    try:
        zoo_vars = test_zoo_vars(zoo_vars)
    except Exception as e:
        print(e)
        exit(1)

    zoo_vars['attribution'] = args['attribution']
    zoo_vars['license'] = args['license']

    # check content of existing subject set
    my_set = zoo_vars['subject_set_obj']
    uploaded_subjects = dict()
    print("Looking for already uploaded subjects..", flush=True)
    for i, subject in enumerate(my_set.subjects):
        if ((i % 500) == 0) and (i > 0):
            print("Found %s subjects and counting..." % i, flush=True)
        roll = str(subject.metadata['#roll'])
        site = str(subject.metadata['#site'])
        capture = str(subject.metadata['#capture'])
        subject_id = subject.id

        capture_id = '#'.join([site, roll, capture])
        uploaded_subjects[capture_id] = subject_id

    print("Found %s already existing subjects" %
          len(uploaded_subjects.keys()), flush=True)

    ########################
    # upload subjects
    ########################

    # exclusion codes
    # NVI - No valid images, SO - Subject saved but not added to Subject Set,
    # UC - Upload Complete
    cap_excl_code = ["NVI", "SO", "UC"]

    print("Starting subject upload...", flush=True)
    t0 = time.time()

    # Divide upload into separate blocks of 500 subjects
    n_total = len(manifest.keys())
    n_current = 0
    uploads_per_cycle = 500
    n_blocks = max(round(n_total / uploads_per_cycle), 1)
    capture_ids_all = list(manifest.keys())

    # Loop over blocks
    for start_i, end_i in slice_generator(n_total, n_blocks):
        capture_ids = capture_ids_all[start_i: end_i]
        subjects_to_upload = list()
        # Loop over all subjects/captures in a block
        for capture_id in capture_ids:
            n_current += 1
            manifest_row = manifest[capture_id]
            if capture_id in uploaded_subjects:
                manifest_row['zoosubjid'] = int(uploaded_subjects[capture_id])
                manifest_row['zoosubjsetid'] = my_set.id
                manifest_row['uploadstatus'] = 'UC'
            if manifest_row['uploadstatus'] not in cap_excl_code:
                # upload subject
                try:
                    print("--------------------------------------------------")
                    print("Uploading subject: %s" % capture_id, flush=True)
                    subject = create_and_upload_subject(manifest_row,
                                                        upld_vars, zoo_vars)
                    if subject is not None:
                        subjects_to_upload.append(subject)
                except Exception as e:
                    print(e)
                    print("Failed to upload subject: %s" % capture_id)

            est_remaining = estimate_remaining_time(t0, n_total, n_current)
            print("Estimated remaining time: %s" % est_remaining)

        print("Adding subjects of block to subject_set..", flush=True)
        zoo_vars['subject_set_obj'].add(subjects_to_upload)
        for capture_id in capture_ids:
            manifest_row = manifest[capture_id]
            manifest_row['uploadstatus'] = 'UC'

        print("Finished adding subjects to subject_set", flush=True)

        # add stat
        for capture_id in capture_ids:
            upload_stat = manifest[capture_id]['uploadstatus']
            if upload_stat in upld_stat:
                upld_stat[upload_stat]['new_total'] += 1

    # print stats
    for us, us_val in upld_stat.iteritems():
        print("\t"+us_val['status'] + ": " + str(us_val['new_total']))
    print(time.strftime("%H:%M:%S", time.gmtime(time.time()-t0)) +
          " to save/add "+str(upld_stat['UC']['change'])+" captures.")

    ########################
    # Save output Manifest
    ########################

    output_file = upld_vars['output_manifest_path']

    with open(output_file, "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(manifest_headers)
        for capture_id, manifest_row in manifest.items():
            line = [manifest_row[col] for col in manifest_headers]
            csv_writer.writerow(line)
