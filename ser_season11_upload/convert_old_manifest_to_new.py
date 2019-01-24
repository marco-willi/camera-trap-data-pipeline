""" Convert old-style manifest to a new one """
import csv
import os
from collections import OrderedDict

from utils import (
    export_dict_to_json_with_newlines)

# Example Input file
# site,roll,capture,Image 1,Image 2,Image 3,path 1,path 2,path 3,zoosubjsetid,zoosubjid,uploadstatus
# J09,2,1604,2382_6351_7502.JPG,3567_3709_6837.JPG,0974_6262_3717.JPG,SER_S11/J09/J09_R2/SER_S11_J09_R2_IMAG4235.JPG,SER_S11/J09/J09_R2/SER_S11_J09_R2_IMAG4236.JPG,SER_S11                    /J09/J09_R2/SER_S11_J09_R2_IMAG4237.JPG,N0,N0,N0

batch_no = '6'
input_path_old = '/home/packerc/shared/zooniverse/Manifests/SER/SER_S11_%s_manifest_v0.csv' % batch_no
manifest_path = '/home/packerc/shared/zooniverse/Manifests/SER/SER_S11__batch_%s__manifest.json' % batch_no

season = 'SER_S11'
attribution = 'University of Minnesota Lion Center + SnapshotSafari + Snapshot Serengeti + Serengeti National Park + Tanzania'
license = 'SnapshotSafari + Snapshot Serengeti'
compressed_images_path = '/home/packerc/shared/zooniverse/ToUpload/SER/SER_S11_Compressed/'

input = list()
with open(input_path_old, 'r') as f:
    csv_reader = csv.reader(f)
    header = next(csv_reader)
    name_to_id_mapper = {x: i for i, x in enumerate(header)}
    for row in csv_reader:
        input.append(row)

manifest = OrderedDict()
omitted_images_counter = 0
images_not_found_counter = 0
valid_codes = ('0', '3')

for row in input:
    # Extract important fields
    site = row[name_to_id_mapper['site']]
    roll = row[name_to_id_mapper['roll']]
    capture = row[name_to_id_mapper['capture']]
    compressed_images = [
        os.path.join(compressed_images_path, row[name_to_id_mapper[x]])
        for x in ['Image 1', 'Image 2', 'Image 3']]
    original_images = [
        row[name_to_id_mapper[x]] for x in
        ['path 1', 'path 2', 'path 3']]
    # replace NA string
    original_images = ['' if x == 'NA' else x for x in original_images]
    compressed_images = ['' if x.endswith('NA') else x for x in compressed_images]
    # skip if no images
    if not any([x is not '' for x in original_images]):
        continue
    # unique capture id
    capture_id = '#'.join([season, site, roll, capture])
    # Create a new entry in the manifest
    if capture_id not in manifest:
        # generate metadata for uploading to Zooniverse
        upload_metadata = {
            '#site': site,
            '#roll': roll,
            '#season': season,
            '#capture': capture,
            'attribution': attribution,
            'license': license
        }
        # store additional information
        info = {
            'uploaded': False
        }
        images = {
            'original_images': original_images,
            'compressed_images': compressed_images
        }
        manifest[capture_id] = {
            'upload_metadata': upload_metadata, 'info': info,
            'images': images}

print("Writing %s captures to %s" % (len(manifest.keys()), manifest_path))

export_dict_to_json_with_newlines(manifest, manifest_path)

# change permmissions to read/write for group
os.chmod(manifest_path, 0o660)
