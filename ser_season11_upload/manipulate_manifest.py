""" This code attempts to merge an "old" manifest with a "new" one
    in order to separate subjects of the "old" manifest that have already
    been uploaded. This is achieved by separating the "new" manifest into
    batches of which some only consist of the already uploaded subjects.
    Additionally, some information of subjects merged from the old manifest
    has to be merged into the new one. Yes it is complicated.
"""
import pandas as pd

old_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\ser_s11_upload\\previous_uploads\\'
new_path = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\ser_s11_upload\\'
merged_path =  'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\ser_s11_upload\\merged\\'

old_manifests = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\ser_s11_upload\\old_manifests\\'
new_manifests = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\ser_s11_upload\\new_manifests\\'
new_zooids = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\ser_s11_upload\\new_zooid\\'

new_zooid_path = new_path + 'SER_S11_ZOOID.csv'
old_zooid1_path = old_path + 'SER_S11_1_ZOOID.csv'
old_zooid2_path = old_path + 'SER_S11_2_ZOOID.csv'



################################
# SPLIT ZOOID FILES
################################


# read files
new_zooid = pd.DataFrame.from_csv(new_zooid_path)
old_zooid1 = pd.DataFrame.from_csv(old_zooid1_path)
old_zooid2 = pd.DataFrame.from_csv(old_zooid2_path)
len(old_zooid2.index)
len(old_zooid1.index)

old_zooid_frames = [old_zooid1, old_zooid2]
old_zooid = pd.concat(old_zooid_frames)

old_images = old_zooid.index
new_images = new_zooid.index

# merge old and new zooid files
merged = new_zooid.join(old_zooid, how='left', rsuffix='_old')


# Check overlap of old and new
n_total = len(merged.index)
n_not_in_old = sum(merged.anonimname_old.isnull())
n_in_old = len(old_zooid.index)
n_in_old_merged = sum(~merged.anonimname_old.isnull())
n_in_old_merged / n_in_old


# take old manifest information for old rows and new manifest information for
# new rows and combine in one data frame

only_new_ones = new_zooid[~new_zooid.index.isin(old_zooid.index)]

len(only_new_ones.index)
n_total - n_in_old

merged_stack = pd.concat([old_zooid, only_new_ones])


# copy used anonymized and uploaded old images to a specific folder
from shutil import copyfile, move
old_image_source_path = '/home/packerc/shared/zooniverse/ToUpload/SER_backup_will5448/backup_will5448/SER_S11_2_Compressed/'
old_image_move_to_path = '/home/packerc/shared/zooniverse/ToUpload/SER/SER_S11_ALREADY_UPLOADED_OLD/'
for i, (index, old_image_name) in enumerate(old_zooid.anonimname.iteritems()):
    src = old_image_source_path + old_image_name
    dst = old_image_move_to_path + old_image_name
    print("copy from %s to %s" % (src, dst))
    try:
        # copyfile(src, dst)
    except:
        print("Failed to copy from %s to %s" % (src, dst))

    print(old_image_name)
    if i > 10:
        break


# move unused new anonymized images to a specific folder
new_ones_already_in_old = new_zooid[new_zooid.index.isin(old_zooid.index)]
len(new_ones_already_in_old.index)

new_image_source_path = '/home/packerc/shared/zooniverse/ToUpload/SER/SER_S11_Compressed/'
new_image_move_to_path = '/home/packerc/shared/zooniverse/ToUpload/SER/SER_S11_NEW_ALREADY_UPLOADED/'
for i, (index, new_image_name) in enumerate(new_ones_already_in_old.anonimname.iteritems()):
    src = new_image_source_path + new_image_name
    dst = new_image_move_to_path + new_image_name
    print("move from %s to %s" % (src, dst))
    try:
        # move(src, dst)
    except:
        print("Failed to move from %s to %s" % (src, dst))
    print(old_image_name)
    if i > 10:
        break


# Split ZOOid files into batch 1 and 2 and rest
new_zooid_1 = merged_stack[merged_stack.index.isin(old_zooid1.index)]
print("New Zooid 1 n records: %s" % len(new_zooid_1 .index))

new_zooid_2 = merged_stack[merged_stack.index.isin(old_zooid2.index)]
print("New Zooid 2 n records: %s" % len(new_zooid_2.index))

new_zooid_rest = merged_stack[~merged_stack.index.isin(old_zooid.index)]
print("New Zooid rest n records: %s" % len(new_zooid_rest.index))


new_zooid_1.to_csv(new_zooids   + 'SER_S11_1_ZOOID_v0.csv')
new_zooid_2.to_csv(new_zooids  + 'SER_S11_2_ZOOID_v0.csv')
new_zooid_rest.to_csv(new_zooids  + 'SER_S11_3to6_ZOOID_v0.csv')


################################
# CREATE MANIFESTS
################################

manifest = pd.DataFrame.from_csv(new_path + 'SER_S11_manifest_v0_ADDITIONAL_PATH.csv', index_col=[0,1,2]).fillna('NA')


uploaded_manifest_1 = pd.DataFrame.from_csv(old_manifests + 'SER_S11_1_manifest_v0.csv',
                                            index_col=[0,1,2]).fillna('NA')
uploaded_manifest_2 = pd.DataFrame.from_csv(old_manifests + 'SER_S11_2_manifest_v0.csv',
                                            index_col=[0,1,2]).fillna('NA')
uploaded_manifest = pd.concat([uploaded_manifest_1, uploaded_manifest_2])

print("Number of already uploaded %s" % len(uploaded_manifest.index))



new_manifest_1 = manifest[manifest.index.isin(uploaded_manifest_1.index)]
print("New Manifest 1 n records: %s Old has %s" %
      (len(new_manifest_1.index), len(uploaded_manifest_1.index)))

new_manifest_2 = manifest[manifest.index.isin(uploaded_manifest_2.index)]
print("New Manifest 2 n records: %s Old has %s" %
      (len(new_manifest_2.index), len(uploaded_manifest_2.index)))


new_manifest_rest = manifest[~manifest.index.isin(uploaded_manifest_1.index)]
new_manifest_rest = new_manifest_rest[~new_manifest_rest.index.isin(uploaded_manifest_2.index)]

print("New Manifest REST n records: %s Old has %s" %
      (len(new_manifest_rest.index), len(manifest.index) - len(uploaded_manifest_1.index) - len(uploaded_manifest_2.index)))


# Save new already uploaded and REST manifests
#new_manifest_1.to_csv(new_manifests  + 'SER_S11_1_manifest_v0.csv')
#new_manifest_2.to_csv(new_manifests  + 'SER_S11_2_manifest_v0.csv')
new_manifest_rest.to_csv(new_manifests + 'SER_S11_REST_manifest_v0.csv')



# Split a manifest into N chunks of a specific size
import math
n_rows = len(new_manifest_rest.index)
max_rows_per_file = 50e3
n_files = math.ceil(n_rows / max_rows_per_file)

source_file = new_manifests + 'SER_S11_REST_manifest_v0.csv'
output_files = [new_manifests + 'SER_S11_%s_manifest_v0.csv' % i
                for i in range(3, n_files+3)]


# Functions to split a file
def slice_generator(sequence_length, n_blocks):
    """ Creates a generator to get start/end indexes for dividing a
        sequence_length into n blocks
    """
    return ((int(round((b - 1) * sequence_length/n_blocks)),
             int(round(b * sequence_length/n_blocks)))
            for b in range(1, n_blocks+1))


def split_file_equally_into_files(input_file, output_files,
                                  input_has_header=True):
    """ Split input file into list of output_files distributing the rows
        as equally as possible
    """

    # Read input files and store lines in memory
    with open(input_file, 'r') as f:
        lines = f.readlines()
        n_files = len(output_files)
        file_splits = dict()
        if input_has_header:
            header = lines[0]
            del lines[0]
        n_rows = len(lines)

        # split lines equally among the output_files
        for i, (start, end) in enumerate(slice_generator(n_rows, n_files)):
            file_lines = lines[start:end]
            file_splits[i] = file_lines

    # write the output_files
    n_total_rows_written = 0
    for i, lines in file_splits.items():
        # remove last linebreak
        lines[-1] = lines[-1].strip('\n')
        print("Writing %s with %s lines" % (output_files[i], len(lines)))
        with open(output_files[i], 'w') as f:
            if input_has_header:
                f.write(header)
            f.writelines(lines)
            n_total_rows_written += len(lines)
    print("Wrote in total %s rows to new files" % n_total_rows_written)


split_file_equally_into_files(source_file, output_files)





