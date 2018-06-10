""" Process images by copying source images to a specific upload
    folder (for Zooniverse) while compressing and anonymizing them
    - uses multiprocessing (default 16 processes)
"""
import sys, os, glob, random, getpass, time, re
from PIL import Image
from shutil import move, copytree, ignore_patterns, rmtree
import pandas as pd
import numpy as np
from multiprocessing import Process, Manager


#______FUNCTIONS______#

#####SET AND TEST VARIABLES#####
def set_output_vars(compvars):

    if re.match(r'[A-Z0-9]+_S[0-9]',compvars['input_csv']) :
        compvars['loc_code'] = compvars['input_csv'].split("_")[0]
        compvars['s_num'] = compvars['input_csv'].split("_")[1]
    else:
        compvars['loc_code'] = raw_input("\n -> Enter location code (ex. SER, NIA, DEB): ")
        compvars['s_num'] = raw_input("\n -> Enter season number (ex. S1): ")

    if os.path.basename(compvars['output_loc']) != compvars['loc_code']:
        compvars['output_loc'] = os.path.join(compvars['output_loc'],compvars['loc_code'])
        compvars['zooid_loc'] = os.path.join(compvars['zooid_loc'],compvars['loc_code'])
        compvars['manifest_loc'] = os.path.join(compvars['manifest_loc'],compvars['loc_code'])

    if compvars['label'] == "":
        compvars['prefix'] = compvars['loc_code']+"_"+compvars['s_num']

    else:
        compvars['prefix'] = compvars['prefix']+"_"+compvars['label']

    compvars['out_dir_name'] = compvars['prefix']+"_"+"Compressed"
    compvars['out_dir_path'] = os.path.join(compvars['output_loc'],compvars['out_dir_name'])
    compvars['zooid_csv'] = compvars['prefix']+"_ZOOID.csv"
    compvars['zooid_path'] = os.path.join(compvars['zooid_loc'],compvars['zooid_csv'])
    compvars['manifest_csv'] = compr_vars['prefix']+"_manifest_v0.csv"
    compvars['manifest_path'] = os.path.join(compvars['manifest_loc'],compvars['manifest_csv'])
    compr_vars['temp_dir_path'] = os.path.join(compr_vars['output_loc'],"temp_compr_" + str(random.randint(1,10000)))

    return compvars

def test_output_paths(compvars):
    error = []
    for loc in [compvars['output_loc'],compvars['zooid_loc'],compvars['manifest_loc']]:
        if os.path.isdir(loc)==False:
            error.append("\t !! Directory "+loc+" does not exist.\n")
    for path in [compvars['out_dir_path'],compvars['zooid_path'],compvars['manifest_path']]:
        if os.path.isdir(path)==True:
            error.append("\t !! "+path+" already exists.\n")
    return error

def find_full_res_img_path (img_entry):
    img_key = img_entry['imname'].split('_')  #0:LOC 1:S# 2:Site 3:Roll 4:ImageName
    keyed_path = "/"+img_key[2]+"/"+img_key[2]+"_"+img_key[3]+"/"+img_entry['imname']
    fr_img_path = img_entry['inputdir']+keyed_path #don't know why, but os.path.join refuses to incorporate img_entry['inputdir']
    if os.path.isfile(fr_img_path) == False:
        print("Not found %s" % fr_img_path)
        fr_img_path = "NF"
    #   for root,dirs,files in os.walk(img_entry['inputdir']):
    # 	    if img_entry['imname'] in files:
    # 		     fr_img_path = os.path.join(root,img_entry['imname'])
    return fr_img_path


###############################
# Image Compression and
# multiprocessing Functions
###############################

def slice_generator(sequence_length, n_blocks):
    """ Creates a generator to get start/end indexes for dividing a
        sequence_length into n blocks
    """
    return ((int(round((b - 1) * sequence_length/n_blocks)),
             int(round(b * sequence_length/n_blocks)))
            for b in range(1, n_blocks+1))


def estimate_remaining_time(start_time, n_total, n_current):
    """ Estimate remaining time """
    time_elapsed = time.time() - start_time
    n_remaining = n_total - (n_current - 1)
    avg_time_per_record = time_elapsed / (n_current + 1)
    estimated_time = n_remaining * avg_time_per_record
    return time.strftime("%H:%M:%S", time.gmtime(estimated_time))


def compress_images(pid, image_source_list, image_dest_list,
                    result_dict,
                    save_quality=None,
                    max_pixel_of_largest_side=None):
    """ Compresses images for use with multiprocessing

        Arguments:
        -----------
        pid (int):
            the id of the process for status printing
        image_source_list (list):
            image source paths
        image_source_list (list):
            image destination paths
        results_dict (dict):
            shared dictionary to store results into
        save_quality (int):
            compression quality of images
        max_pixel_of_largest_side (int):
            max allowed size in pixels of largest side of an image,
            if an image exceeds this, its largest side is resized to this
            while preserving the aspect ratio
    """
    # Check Input
    assert any([save_quality, max_pixel_of_largest_side]) is not None,\
        "At least one of save_quality or max_pixel_of_largest_side must be \
         specified"
    if save_quality is not None:
        assert (save_quality <= 100) and (save_quality > 0), \
            "save_quality must be between 1 and 100"
    print("PID %s is using parameters: %s %s" %
          (pid, save_quality, max_pixel_of_largest_side))
    # Loop over all images and process each
    counter = 0
    n_tot = len(image_source_list)
    start_time = time.time()
    for source, dest in zip(image_source_list, image_dest_list):
        if (counter % 2000) == 0:
            print("Process ID %s - done %s/%s - estimated time remaining: %s" %
                  (pid, counter, n_tot,
                   estimate_remaining_time(start_time, n_tot, counter)))
            sys.stdout.flush()
        try:
            img = Image.open(source)
            # Check largest side of image and resize if necessary
            if max_pixel_of_largest_side is not None:
                if any([x > max_pixel_of_largest_side for x in img.size]):
                    img.thumbnail(size=[max_pixel_of_largest_side,
                                        max_pixel_of_largest_side],
                                  resample=1)
            if save_quality is not None:
                img.save(dest, "JPEG",
                         quality=save_quality)
            else:
                img.save(dest)
            img.close()
            # save result "Successful Compression"
            result_dict[source] = 'SC'
        except:
            # save result "Not Compressed"
            print("Failed to compress %s" % source)
            result_dict[source] = 'CR'
        counter += 1
    # Print process end status
    print("Process " + str(pid) + "  has finished")


def process_images_multiprocess(
        image_source_list,
        image_dest_list,
        image_process_function,
        n_processes=4,
        **kwargs):
    """ Processes a list of images using multiprocessing
        Arguments:
        ----------
        image_source_list (list):
            list of source image paths
        image_dest_list (list):
            list of destination image paths, order must be the same as
            image_source_list
        image_process_function (func):
            a function to process images, takes as input:
            pid (int), image_source_list, image_dest_list,
            status_messages (dict), additional keyword arguments
        n_processes (int): the number of processes to use
    """
    n_records = len(image_source_list)
    # Shared dictionary to store status messages for each record
    manager = Manager()
    status_messages = manager.dict()
    # initialize with empty messages
    for f in image_source_list:
        status_messages[f] = ''
    try:
        processes_list = list()
        slices = slice_generator(n_records, n_processes)
        for i, (start_i, end_i) in enumerate(slices):
            pr = Process(target=compress_images,
                         args=(i, image_source_list[start_i:end_i],
                               image_dest_list[start_i:end_i],
                               status_messages),
                         kwargs=kwargs)
            pr.start()
            processes_list.append(pr)
        for p in processes_list:
            p.join()
    except Exception, e:
        print e
        raise
    return status_messages


# ______GLOBAL VARS _______#
compr_vars = dict.fromkeys([
    'home_dir', 'input_dir', 'input_dir_path',
    'input_csv_path', 'input_csv', 'label', 'output_loc', 'out_dir_name',
    'zooid_loc', 'zooid_path', 'zooid_csv', 'manifest_loc', 'manifest_path',
    'manifest_csv', 'quality', 'loc_code', 's_num', 'prefix', 'set_label',
    'temp_dir_path', 'out_dir_path'])

compr_stat = {'SC': "Successfully Compressed", 'NF': "Not Found",
              'CR': "Compression Error", 'IN': "Invalid"}

compr_vars['output_loc'] = "/home/packerc/shared/zooniverse/ToUpload/"
compr_vars['zooid_loc'] = "/home/packerc/shared/zooniverse/ZOOIDs/"
compr_vars['manifest_loc'] = "/home/packerc/shared/zooniverse/Manifests"
compr_vars['home_dir'] = "packerc"

compr_vars['quality'] = 50
compr_vars['max_image_pixel_side'] = 1440

compr_vars['label'] = ""


#______MAIN PROGRAM_______#

# For testing
#sys.argv.append('/home/packerc/shared/season_captures/SER/cleaned/SER_S11_cleaned_V3.csv')
#sys.argv.append('/home/packerc/shared/albums/SER/SER_S11')

#####CHECK INPUT#####
if len(sys.argv) < 3:
    print ("format: python2 compress_images.py  <LOC_SX_cleaned_csv> <full_res_file_directory>")
    exit(1)

try:
    img_df = pd.read_csv(sys.argv[1])
except Exception, e:
    print e
    exit(1)

if os.path.isdir(sys.argv[2])==False:
    print ("\nSpecified input directory does not exist.\n")
    exit(1)

#####SET AND CHECK INPUT/OUTPUT VARIABLES#####

compr_vars['input_csv_path'] = sys.argv[1]
compr_vars['input_csv'] = os.path.basename(compr_vars['input_csv_path'])
compr_vars['input_dir'] = "/home/"+compr_vars['home_dir']+os.path.abspath(sys.argv[2]).split(compr_vars['home_dir'])[1] #get path from 'home'... no trailing /


compr_vars = set_output_vars(compr_vars)

print("\nBy default:")
print("\tCompressed image file directory: "+compr_vars['output_loc'])
print("\tZOOID file directory: "+compr_vars['zooid_loc'])
print("\tUpload manifest file directory: "+compr_vars['manifest_loc'])

print("\nBased on input: ")
print("\tCompressed images will be saved to: "+compr_vars['out_dir_path'])
print("\tZOOID csv will be saved to: "+compr_vars['zooid_path'])
print("\tManifest csv will be saved to: "+compr_vars['manifest_path'])

compr_vars['label'] = raw_input("\n -> Optional: Enter an additional label for output directory and csvs (ex. version number, site, etc):  ")

if compr_vars['label'] !="":
    compr_vars = set_output_vars(compr_vars)
    print("\nNew output locations: ")
    print("\tCompressed images will be saved to: "+compr_vars['out_dir_path'])
    print("\tZOOID csv will be saved to: "+compr_vars['zooid_path'])
    print("\tManifest csv will be saved to: "+compr_vars['manifest_path'])

error = test_output_paths(compr_vars)
if len(error) != 0:
    print("\n")
    for e in error:
        print(e)
    exit(1)

#####CONFIRM PROCESS#####

proceed = ""

while proceed.upper() not in ["Y","N"]:
    proceed = raw_input(" -> Proceed with compression (Y/N)? ")

if proceed.upper() == "N":
    exit(1)

#####CREATE OUTPUT DIRECTORY#####

print("Chkpt 1")
os.makedirs(compr_vars['out_dir_path'])
print("Chkpt 2")

#####SET ANONYMOUS FILE NAMES AND FILE PATHS#####

three_rand_ints = pd.DataFrame(np.random.randint(1,10000,size=(len(img_df),3)),columns=['R1','R2','R3']).applymap(lambda x:'%04d' % x)
print("Chkpt 3")

img_df['anonimname'] = three_rand_ints['R1']+'_'+three_rand_ints['R2']+'_'+three_rand_ints['R3']+'.JPG'
print("Chkpt 4")

img_df['comprimgpath'] = compr_vars['out_dir_path']+"/"+img_df['anonimname']
print("Chkpt 5")

img_df['inputdir'] = pd.Series([compr_vars['input_dir']]*len(img_df.index))
print("Chkpt 6")

img_df['absimpath'] = img_df.apply(find_full_res_img_path, axis=1)
print("Chkpt 7")

img_df['quality'] = compr_vars['quality']
print("Chkpt 8")

img_df['imnum'] = img_df.index
print("Chkpt 9")

img_df['totim'] = pd.Series([len(img_df.index)]*len(img_df.index))
print("Chkpt 10")

t0 = time.time()
print("Chkpt 11")

img_df['t0'] = pd.Series([t0]*len(img_df.index))
print("Chkpt 12")

#####COMPRESS AND ANONYMIZE IMAGE FILES#####
print ("\n\tCOMPRESSING FILES...\n")

# get all source and destination file paths and store to list
image_source_path_list = [x for x in img_df['absimpath']]
image_dest_path_list = [x for x in img_df['comprimgpath']]

# run parallelized image compression and return status messages
status_results = process_images_multiprocess(
    image_source_path_list,
    image_dest_path_list,
    compress_images,
    n_processes=16,
    save_quality=compr_vars['quality'],
    max_pixel_of_largest_side=compr_vars['max_image_pixel_side']
)

# order status results as returned by the multiprocessing
ordered_status_results = list()
for img_path in img_df['absimpath']:
    ordered_status_results.append(status_results[img_path])

# generate original status messages
new_status_messages = list()
for i in range(0, len(img_df['absimpath'])):
    if img_df['invalid'][i] not in [0, 3]:
        new_status_messages.append('IN')
    elif img_df['absimpath'][i] == 'NF':
        new_status_messages.append('NF')
    else:
        new_status_messages.append(ordered_status_results[i])

img_df['comprstat'] = new_status_messages

#Print compression stats
for cs,text in compr_stat.iteritems():
    if cs != 'SC':
        img_df.loc[img_df['comprstat']==cs,'anonimname'] = cs #set error code for image files that were not compressed
    if cs in img_df['comprstat'].values:
        print("\t"+text+": "+str(img_df['comprstat'].value_counts()[cs]) + " image files")

print ("\tTotal compression time: "+time.strftime("%H:%M:%S",time.gmtime(time.time()-t0)))

#####SAVE ZOOID CSV#####
img_df.loc[img_df['comprstat'] == "SC"].to_csv(compr_vars['zooid_path'],columns=["imname","anonimname","absimpath","path"],index=False)

#####CREATE AND SAVE UPLOAD INPUT MANIFEST FILE#####
#Reshape table... split images by capture
# img_df_copy = img_df.copy()
# img_df = img_df[img_df['image'] < 4]

capture_df = img_df[['site','roll','capture','image','anonimname', 'path']].set_index(['site','roll','capture','image']).unstack(fill_value="NA") #unstacks the anonimname column into manifest form
transposed_names = capture_df.columns.get_level_values(0)
transposed_values = capture_df.columns.get_level_values(1)
cols = [k + " " + str(v) for k, v in zip(transposed_names, transposed_values)]
cols = [n.replace('anonimname', 'Image') for n in nams]
capture_df.columns = cols
capture_df = capture_df.reset_index()

#Sets the metadata capture id key...
#capture_df['captureidkey'] = pd.Series(capture_df.index.values)
#capture_df['captureidkey'] = capture_df['captureidkey'].apply(lambda captrid: compr_vars['prefix']+"_C"+str(captrid))
capture_df['zoosubjsetid'] = "N0"
capture_df['zoosubjid'] = "N0"
capture_df['uploadstatus'] = "N0"
capture_df.to_csv(compr_vars['manifest_path'],index=False)
