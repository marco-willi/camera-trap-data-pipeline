import sys, os, glob, random, getpass, time, re
from PIL import Image
from shutil import move, copytree, ignore_patterns, rmtree
import pandas as pd
import numpy as np


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
		fr_img_path = "NF"
		for root,dirs,files in os.walk(img_entry['inputdir']):
			if img_entry['imname'] in files:
				fr_img_path = os.path.join(root,img_entry['imname'])

	return fr_img_path

#####COMPRESS IMAGE FILE#####

def compress_image (img_entry):

	if img_entry['imnum']%2000 == 500:
		approxtrem = (img_entry['totim'] - img_entry['imnum'] - 1) * (time.time()-img_entry['t0'])/(img_entry['imnum']+1)
		print("\nEstimated time remaining: " + time.strftime("%H:%M:%S",time.gmtime(approxtrem)))
		print("(Approx. "+str(img_entry['imnum'])+" out of "+str(img_entry['totim'])+" images compressed...)")

	if img_entry['invalid'] in [0,3]: 
		if img_entry['absimpath'] != "NF":
			try:
				img = Image.open(img_entry['absimpath'])
				img.thumbnail(img.size)
				img.save(img_entry['comprimgpath'],"JPEG",quality=img_entry['quality'])
				img.close()
			except Exception, e:
				print e

			if os.path.isfile(img_entry['comprimgpath']):
				return "SC" #Successful compression
			else:
				return "CR" #not compressed
		else:
			return "NF" #not found
	else:
		return "IN" #invalid


#______GLOBAL VARS _______#

compr_vars = dict.fromkeys(['home_dir','input_dir','input_dir_path','input_csv_path','input_csv','label','output_loc','out_dir_name','zooid_loc','zooid_path','zooid_csv','manifest_loc','manifest_path','manifest_csv','quality','loc_code','s_num','prefix','set_label','temp_dir_path','out_dir_path'])
compr_stat = {'SC':"Successfully Compressed", 'NF':"Not Found", 'CR':"Compression Error",'IN':"Invalid"}

compr_vars['output_loc'] = "/home/packerc/shared/zooniverse/ToUpload/"
compr_vars['zooid_loc'] = "/home/packerc/shared/zooniverse/ZOOIDs/"
compr_vars['manifest_loc'] = "/home/packerc/shared/zooniverse/Manifests"
compr_vars['home_dir'] = "packerc"


#compr_vars['output_loc'] = "/Users/befort/Desktop/zooniverse/ToUpload/"
#compr_vars['zooid_loc'] = "/Users/befort/Desktop/zooniverse/ZOOIDs/"
#compr_vars['manifest_loc'] = "/Users/befort/Desktop/zooniverse/Manifests/"
#compr_vars['home_dir'] = "befort"

compr_vars['quality'] = 17

compr_vars['label'] = ""


#______MAIN PROGRAM_______#

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

compr_vars['input_csv_path']  = sys.argv[1]
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

three_rand_ints      = pd.DataFrame(np.random.randint(1,10000,size=(len(img_df),3)),columns=['R1','R2','R3']).applymap(lambda x:'%04d' % x)
print("Chkpt 3")
img_df['anonimname'] = three_rand_ints['R1']+'_'+three_rand_ints['R2']+'_'+three_rand_ints['R3']+'.JPG'
print("Chkpt 4")
img_df['comprimgpath'] = compr_vars['out_dir_path']+"/"+img_df['anonimname']
print("Chkpt 5")

img_df['inputdir'] = pd.Series([compr_vars['input_dir']]*len(img_df.index))
print("Chkpt 6")
img_df['absimpath'] = img_df.apply(find_full_res_img_path,axis=1)
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
		
img_df['comprstat'] = img_df.apply(compress_image, axis=1)  

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
capture_df = img_df[['site','roll','capture','image','anonimname']].set_index(['site','roll','capture','image']).unstack(fill_value="NA") #unstacks the anonimname column into manifest form
capture_df.columns = capture_df.columns.get_level_values(1)
capture_df = capture_df.reset_index()

	#A fancy way of renaming image column headers... flexible, in case there are less/more than 3 image columns
int_col_names = [col for col in list(capture_df) if col in list(img_df['image'].unique())]
str_col_names = ["Image "+str(col) for col in int_col_names]
capture_df = capture_df.rename(columns = dict(zip(int_col_names,str_col_names)))

	#Sets the metadata capture id key...
#capture_df['captureidkey'] = pd.Series(capture_df.index.values)
#capture_df['captureidkey'] = capture_df['captureidkey'].apply(lambda captrid: compr_vars['prefix']+"_C"+str(captrid))

capture_df['zoosubjsetid'] = "N0"
capture_df['zoosubjid'] = "N0"
capture_df['uploadstatus'] = "N0"

capture_df.to_csv(compr_vars['manifest_path'],index=False)

#####CLEANUP#####
rmtree(compr_vars['temp_dir_path'],ignore_errors=True)
