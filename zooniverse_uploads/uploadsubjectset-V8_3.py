import sys, os, glob, random, getpass, time
from PIL import Image
from shutil import move, copytree, ignore_patterns
from panoptes_client import Project, Panoptes, Subject, SubjectSet
import pandas as pd
import numpy as np


#_________ FUNCTIONS __________#

	######ADD SUBJECT TO SUBJECT SET#####

def add_capture_as_subject(capture_event,uvar,zvar):

	cap_excl_code = ["NVI","SO","UC"] #NVI - No valid images, SO - Subject saved but not added to Subject Set, UC - Upload Complete
	img_excl_code = ["NA","IN","NF","CR"] #NA-Not Applicable, IN-Invalid, NF-Not found, CR - Compression Error  <-- FROM COMPRESSION SCRIPT
		
	if capture_event['uploadstatus'] not in cap_excl_code:

		#initialize Subject object
		subject               = Subject()
		subject.links.project = zvar['project_obj']
		
			#add image file locations and metadata
		capture_img_n = 0
		for img_n in [imgn for imgn in list(capture_event.index) if 'Image' in imgn]:
			if capture_event[img_n] not in img_excl_code:
				print("Adding "+img_n+" to subject "+ str(capture_event['zoosubjid']))
				subject.add_location(os.path.join(uvar['upload_dir_path'],capture_event[img_n]))
				subject.metadata[img_n] = capture_event[img_n]
				capture_img_n += 1

		if capture_img_n > 0:
				
			#add capture metadata
			subject.metadata['attribution'] = zvar['attribution']
			subject.metadata['license'] = zvar['license']
			#subject.metadata['#captureidkey'] = capture_event['captureidkey']
			subject.metadata['#site'] = capture_event['site']
			subject.metadata['#roll'] = capture_event['roll']
			subject.metadata['#capture'] = capture_event['capture']

			#try saving subject and adding to subject set, annotate results in 'uploadstatus'
			try:
				subject.save()
				capture_event['zoosubjid'] = int(subject.id) #from unicode
				print("Subject " + str(capture_event['zoosubjid']) + " saved.")
			except Exception, e:
				print e
				capture_event['uploadstatus'] = "ERR" #Error saving subject - subject not created
			else:
				try:
					zvar['subject_set_obj'].add(subject)
					capture_event['zoosubjsetid'] = zvar['subject_set_id']
					capture_event['uploadstatus'] = "UC" #Upload complete
					print("Subject " + str(capture_event['zoosubjid']) + " added to subject set "+ str(zvar['subject_set_id']))
				except Exception, e:
					capture_event['uploadstatus'] = "SO" #Subject Saved but not added
					print e
					print("Subject " + str(capture_event['zoosubjid']) + " NOT added to subject set "+ str(zvar['subject_set_id']))				
		else:
			capture_event['uploadstatus'] = "NVI"  #No valid/viable images
			print("No viable/valid images in capture")

	elif capture_event['zoosubjsetid'] == "SO":
		try:
			subject_set.add(subject)
			capture_event['zoosubjsetid'] = zvar['subject_set_id']
			capture_event['uploadstatus'] = "UC"
			print("Subject " + str(capture_event['zoosubjid']) + " added to subject set "+ str(capture_event['zoosubjsetid']))
		except:
			capture_event['uploadstatus'] = "SO" #Subject Saved but not added
	
	return capture_event

	#####RECONNECT TO ZOONIVERSE#####


def set_upload_vars(uplvars):

	uplvars['input_manifest'] = os.path.basename(uplvars['input_manifest_path'])
	uplvars['loc_code'] = uplvars['input_manifest'].split("_")[0]
	uplvars['prefix'] = uplvars['input_manifest'].rsplit("_",2)[0]
	
	uplvars['upload_loc'] = os.path.join(uplvars['upload_loc'],uplvars['loc_code'])
	uplvars['upload_dir_name'] = uplvars['prefix']+"_Compressed"
	uplvars['upload_dir_path'] = os.path.join(uplvars['upload_loc'],uplvars['upload_dir_name'])

	uplvars['output_manifest_vN'] = int(uplvars['input_manifest'].split("_")[-1].split('.')[0][1:])+1 #set manifest version number
	uplvars['output_manifest'] = uplvars['prefix']+"_"+"manifest_v"+str(uplvars['output_manifest_vN'])

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
	zoovars['project_obj']=Project.find(zoovars['project_id'])

	if zoovars['subject_set_id'] == -1:
		zoovars['subject_set_obj'] = SubjectSet()
		zoovars['subject_set_obj'].links.project = zoovars['project_obj']
		zoovars['subject_set_obj'].display_name = zoovars['subject_set_name']
		zoovars['subject_set_obj'].save()
		zoovars['subject_set_id'] = int(zoovars['subject_set_obj'].id)
	else:
		zoovars['subject_set_obj'] = SubjectSet.find(zoovars['subject_set_id'])

	return zoovars

#_________ GLOBAL VARIABLES ________#

upld_vars = dict.fromkeys(['input_manifest_path','input_manifest','loc_code','s_num','prefix','upload_loc','upload_dir_name','upload_dir_path','output_manifest_vN','output_manifest','manifest_loc','output_manifest_path'])

zoo_vars = dict.fromkeys(['username','password','project_id','project_obj','subject_set_name','subject_set_id','subject_set_obj','attribution','license'])

upld_stat = dict.fromkeys(['UC','SO','NVI','ERR','N0'])
upld_stat['UC'] = {'status': "Upload Complete",'change': 0,'new_total': 0}
upld_stat['SO'] = {'status':"Subject Saved not Added",'change': 0,'new_total': 0}
upld_stat['ERR'] = {'status':"Subject Save Error",'change': 0,'new_total': 0}
upld_stat['NVI'] = {'status':"No Valid Images",'change': 0,'new_total': 0}
upld_stat['N0'] = {'status': "No Upload Attempts Made",'change': 0,'new_total': 0}


upld_vars['upload_loc'] = "/home/packerc/shared/zooniverse/ToUpload/"
upld_vars['manifest_loc'] = "/home/packerc/shared/zooniverse/Manifests"

#upld_vars['upload_loc'] = "/Users/befort/Desktop/zooniverse/ToUpload/"
#upld_vars['manifest_loc'] = "/Users/befort/Desktop/zooniverse/Manifests/"


#_________ MAIN PROGRAM _________#

#####CHECK INPUT#####

if len(sys.argv) < 2:
    print ("format: python2 upload_images.py </path/LOC_SX_(label)_Manifest_vN>")
    exit(1)

try: 
	upload_df = pd.read_csv(sys.argv[1],keep_default_na=False)
except Exception, e:
	print e
	exit(1)

#####SET AND CHECK UPLOAD VARIABLES#####

print("\nBy default:")
print("\tCompressed image file directory: "+upld_vars['upload_loc'])
print("\tUpload manifest file directory: "+upld_vars['manifest_loc'])

upld_vars['input_manifest_path'] = sys.argv[1]
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

zoo_vars['username'] = raw_input("\n -> Enter Zooniverse username: ")
zoo_vars['password'] = getpass.getpass("\n -> Enter password: ")
zoo_vars['project_id'] = raw_input("\n -> Enter Zooniverse Project ID number: ")

new_or_add = ""
while new_or_add == "": 
	new_or_add = raw_input("\n -> Enter A) existing subject set id number OR B) new subject set name: ")

if new_or_add.isdigit(): #
	zoo_vars['subject_set_id'] = int(new_or_add)
	zoo_vars['subject_set_name'] = ""
else:
	zoo_vars['subject_set_name'] = new_or_add
	zoo_vars['subject_set_id'] = -1

try:
	zoo_vars = test_zoo_vars(zoo_vars)
except Exception, e:
	print e
	exit(1)

zoo_vars['attribution'] = raw_input("\n -> Enter image attribution metadata: ")
zoo_vars['license'] = raw_input("\n -> Enter image license metadata: ")


#####UPLOAD IMAGES#####

#while upld_stat['UC']['change']!= 0 or upld_stat['SO']['change'] != 0 or sum([us_val['new_total'] for us_val in upld_stat.values()])==0:

print("\nAttempting upload...")
t0 = time.time()

while (upld_stat['UC']['change']!= 0 or upld_stat['SO']['change'] != 0 or sum([us['new_total']for us in upld_stat.values()])==0) and upld_stat['UC']['new_total']+upld_stat['NVI']['new_total'] != len(upload_df):

	upload_df = upload_df.apply(add_capture_as_subject,args=(upld_vars,zoo_vars,),axis=1)

	print("\nTotal captures: "+str(len(upload_df)))
	for us,us_val in upld_stat.iteritems():
		if us in upload_df['uploadstatus'].values:
			us_val['change'] = upload_df['uploadstatus'].value_counts()[us] - us_val['new_total']
			us_val['new_total'] = upload_df['uploadstatus'].value_counts()[us]
		else:
			us_val['change'] = 0 - us_val['new_total']
			us_val['new_total'] = 0
		print("\t"+us_val['status'] + ": " + str(us_val['new_total']))

	print (time.strftime("%H:%M:%S",time.gmtime(time.time()-t0)) + " to save/add "+str(upld_stat['UC']['change'])+" captures.")

	try:
		zoo_vars = test_zoo_vars(zoo_vars)
	except Exception, e:
		print e

#####SAVE OUTPUT MANIFEST#####

upload_df.to_csv(upld_vars['output_manifest_path'],index=False)

