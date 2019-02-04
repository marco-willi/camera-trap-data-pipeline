# snapshot_safari_misc
Misc Code for Snapshot Safari.
1. Upload Data to Zooniverse
2. Download Data from Zooniverse
3. Aggregate Data from Zooniverse


## Pre-Requisites


### Prepare Zooniverse-Access (one-time only)

For code that accesses Zooniverse via Panoptes (e.g. requires a password),
a file with Zooniverse credentials should be stored. Default location for that file is:  "~/keys/passwords.ini". It should have the following content:

```
[zooniverse]
username: my_username
password: my_password
```

Set permissions of that file by using this command (remove any access rights other than yours):
```
chmod 600 ~/keys/passwords.ini
```

### Get the codes from GitHub

To execute the following codes we need the most recent version of the GitHub code. We will clone the code into the our home directory. This avoids any conflicts with permissions and will create a directory 'snapshot_safari_misc' in your home directory.

```
cd
git clone https://github.com/marco-willi/snapshot_safari_misc.git
```

If that code / directory already exists you can update it using following command:

```
cd ~/snapshot_safari_misc
git pull
```

Should there be any conflicts / issues, just delete your code and clone again. Any changes you made to the code are lost after this.
```
rm -r -f ~/snapshot_safari_misc
cd
git clone https://github.com/marco-willi/snapshot_safari_misc.git
```


### Prepare Python

Before executing (most of) the code, you need to execute the follwing:
```
ssh lab
module load python3
pip install --upgrade --user panoptes-client
pip install --upgrade --user pillow
cd ~/snapshot_safari_misc
```

### Execute Codes

The easiest way to exectue the following codes is to copy & paste them to a text editor, change the parameters (e.g. paths) and then copy & paste that to the command line to execute them.

## Upload Data to Zooniverse

The following steps are required to upload new data to Zooniverse. The following codes show an example for processing RUA data. These are the steps:

1. Compress Images (Zooniverse has a size limit)
2. Generate Manifest (a file containing all info for the Zooniverse upload)
3. Create Machine Lerning File for Model Input (Optional - create input for machine classifier)
4. Generate new Predictions (Optional - run a machine classifier)
5. Split/Batch Manifest (Optional - Zooniverse recommends not to use too large batches at once)
6. Upload Manifest

The optional steps can simply be skipped.

### Compress Images

The script 'image_compression/compress_images.pbs' compresses images and has to be ADAPTED in the following way (NOT EXECUTED). You can find the script in this directory: '~/snapshot_safari_misc/image_compression/compress_images.pbs'. Image compression is required due to size limits of individual
images on Zooniverse.

```
module load python3

cd $HOME/snapshot_safari_misc

python3 -m image_compression.compress_images \
--captures_csv /home/packerc/shared/season_captures/RUA/cleaned/RUA_S1_cleaned.csv \
--output_image_dir /home/packerc/shared/zooniverse/ToUpload/RUA/RUA_S1_Compressed \
--root_image_path /home/packerc/shared/albums/RUA/
```

After adapting the file 'compress_images.pbs' we have to create the 'output_image_dir' as specified in the file. For the example shown above:

```
mkdir /home/packerc/shared/zooniverse/ToUpload/RUA/RUA_S1_Compressed
```

Then we submit the job by issuing this command:

```
ssh mesabi
cd $HOME/snapshot_safari_misc/image_compression
qsub compress_images.pbs
```

### Generate Manifest

This generates a manifest from the captures csv.

```
python3 -m zooniverse_uploads.generate_manifest \
--captures_csv /home/packerc/shared/season_captures/RUA/cleaned/RUA_S1_cleaned.csv \
--compressed_image_dir /home/packerc/shared/zooniverse/ToUpload/RUA/RUA_S1_Compressed/ \
--output_manifest_dir /home/packerc/shared/zooniverse/Manifests/RUA/ \
--manifest_id RUA_S1 \
--attribution 'University of Minnesota Lion Center + SnapshotSafari + Ruaha Carnivore Project + Tanzania + Ruaha National Park' \
--license 'SnapshotSafari + Ruaha Carnivore Project'
```

The default settings create the following file:
```
RUA_S1__complete__manifest.json
```

### Create Machine Lerning File for Model Input (Optional)

This code creates a 'machine learning file' that has the correct format for the machine learning models to classify the images in the manifest.

```
python3 -m zooniverse_uploads.create_machine_learning_file \
--manifest /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__complete__manifest.json
```

The default settings create the following file:
```
RUA_S1__complete__machine_learning_input.csv
```

### Generate new Predictions (Optional)

The following steps describe how to run the machine learning models. Note that the files 'ctc_predict_species.pbs' and 'ctc_predict_empty.pbs' have to be adapted. The predictions process is split into two parts: predict the presence of an animal (empty or not) and predict the animal species. Both of the following scripts can be run in parallel. The scripts process approximately 300 capture events / minute on a CPU queue so it can take several hours for large manifests to process. Please note that the following codes will create a file in your home directory 'camera-trap-classifier-latest-cpu.simg', you can safely delete that after the scripts have finished (it contains the machine learning software).

#### Generating 'Empty or Not' Predictions

The following file needs to be adapted:
```
$HOME/snapshot_safari_misc/machine_learning/jobs/ctc_predict_empty.pbs
```
Adapt the following parameters:
```
SITE=RUA
SEASON=RUA_S1
```

Optionally -- if choosing a specific batch to create predictions for, also adapt the batch name (derived from the manifest file name, default is 'complete', could be 'batch_1'):
```
BATCH=complete
```

After that we can run the script using this command:
```
ssh mesabi
cd $HOME/snapshot_safari_misc/machine_learning/jobs
qsub ctc_predict_empty.pbs
```

The default settings create the following file:
```
RUA_S1__complete__predictions_empty_or_not.json
```

#### Generating 'Species' Predictions

The following file needs to be adapted:
```
$HOME/snapshot_safari_misc/machine_learning/jobs/ctc_predict_species.pbs
```

Adapt the following parameters:
```
SITE=RUA
SEASON=RUA_S1
```

Optionally -- if choosing a specific batch to create predictions for, also adapt the batch name (derived from the manifest file name, default is 'complete', could be 'batch_1'):
```
BATCH=complete
```

After that we can run the script using this command:
```
ssh mesabi
cd $HOME/snapshot_safari_misc/machine_learning/jobs
qsub ctc_predict_species.pbs
```

The default settings create the following file:
```
RUA_S1__complete__predictions_species.json
```

#### Add Model Predictions to Manifest (Optional)

This code adds the aggregated predictions into the manifest.

```
cd $HOME/snapshot_safari_misc
python3 -m zooniverse_uploads.add_predictions_to_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__complete__manifest.json
```

Note: If the script is 'killed' the most likely reason is memory usage. In that case use this command to launch a session with more memory and try again:

```
qsub -I -l walltime=01:00:00,nodes=1:ppn=4,mem=16gb
module load python3
```

### Split/Batch Manifest (Optional)

This codes splits the manifest into several batches that can be uploaded separately. Additionally, the machine scores can be updated for individual batches (usually batches that have not yet been uploaded). Either the number of batches 'number_of_batches' or the 'max_batch_size' can be specified. Default is to randomly split the manifest into the batches.

```
cd $HOME/snapshot_safari_misc
python3 -m zooniverse_uploads.split_manifest_into_batches \
--manifest /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__complete__manifest.json \
--max_batch_size 20000
```

This creates the following files:
```
RUA_S1__batch_1__manifest.json
RUA_S1__batch_2__manifest.json
...
```

### Upload Manifest

This code uploads a manifest to Zooniverse. Note that the Zooniverse credentials have to be available in '~/keys/passwords.ini' and that it is better to use the .qsub version of this code due to the (very!) long potential run-time. Make sure that your account has enough allowance on how many subjects can be uploaded to Zooniverse.

Adapt the following file:
```
$HOME/snapshot_safari_misc/zooniverse_uploads/upload_manifest.pbs
```

Change the paths analogue to this example:
```
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__complete__manifest.json \
--project_id 5155 \
--password_file ~/keys/passwords.ini
```

Note: to upload a specific batch instead use something analogue to:
```
--manifest /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__batch_1__manifest.json \
```

To submit the job use the following command:

```
ssh lab
cd $HOME/snapshot_safari_misc/zooniverse_uploads/
qsub upload_manifest.pbs
```

This code can run for a long time, i.e. multiple days.


#### In case of a failure

If the upload fails (which can happen if the connection to Zooniverse crashes) you can add the missing subjects to the already (partially) uploaded set by specifying the SUBJECT_SET_ID of the already created set. DO NOT specify the parameter '-subject_set_name', instead use '-subject_set_id' and use the id on the 'Subject Sets' page after clicking on the name of the set of your project on Zooniverse.


Adapt the following file:
```
$HOME/snapshot_safari_misc/zooniverse_uploads/upload_manifest.pbs
```

Change the paths analogue to this example:
```
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__complete__manifest.json \
--project_id 5155 \
--subject_set_id 7845 \
--password_file ~/keys/passwords.ini
```

To submit the job use the following command:

```
ssh lab
cd $HOME/snapshot_safari_misc/zooniverse_uploads/
qsub upload_manifest.pbs
```

## Get and Extract Zooniverse Exports

Some of the scripts used for different sites can be found here: [zooniverse_exports/scripts.sh](zooniverse_exports/scripts.sh). The following steps are required:

1. Get Zooniverse Exports (download data through the Python API)
2. Extract Zooniverse Classifications
3. Aggregate Extracted Zooniverse Classifications (on capture-event aggregation - work-in-progress)
4. Add Meta-Data to Aggregated Classifications (work-in-progress)

### Get Zooniverse Exports

Download Zooniverse exports. Requires Zooniverse account credentials and
collaborator status with the project. The project_id can be found in the project builder
in the top left corner. To create a 'fresh' export it is easiest to go on Zooniverse, to the project page,
click on 'Data Exports', and click on new 'Request new classification export'. After receiving an e-mail confirming the export was completed, execute the following script (do not download data via e-mail):

```
python3 -m zooniverse_exports.get_zooniverse_export \
        --password_file ~/keys/passwords.ini \
        --project_id 5155 \
        --output_file /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications.csv \
        --export_type classifications \
        --new_export 0
```

#### Structure of Zooniverse Data

1. One classification contains 1:N tasks
2. One task contains 1:N identifications (for survey task), or 1:N answers (for question tasks)
3. One identification contains 1:N questions (for survey task)
4. One question has 0:N answers (for survey task)

Example:
1. A task is to identify animals (survey task)
2. One task contains two animal identifications, e.g, zebra and wildebeest
3. One identification has multiple questions, e.g., species name and behavior
4. One question may have multiple answres, e.g, different behaviors for the behavior question


### Extract Zooniverse Classifications (subject to changes)

The following code extracts the relevant fields of a Zooniverse classification file. It creates a csv file with one line per annotation/species identification. Normally, you would
want to specify the workflow_id and the workflow_version to extract only the workflow that was used
during the 'live-phase' of the project. If neither workflow_id/workflow_version are not specified every workflow is extracted (and can be separated later). The workflow_id can be found in the project builder when clicking on the workflow. The workflow_version is at the same place slightly further down (e.g. something like 745.34).

Use a machine with enough memory - for example:

```
ssh lab
qsub -I -l walltime=2:00:00,nodes=1:ppn=4,mem=16gb
```

```
cd $HOME/snapshot_safari_misc
python3 -m zooniverse_exports.extract_classifications \
        --classification_csv /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications.csv \
        --output_csv /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_extracted.csv \
        --workflow_id 4889 \
        --workflow_version 797.34
```

The resulting file may have the following column headers:

| Columns   | Description |
| --------- | ----------- |
|season,site,roll,capture | internal descriptors/ids of the subject
|capture_event_id| internal capture id (legacy format)
|capture_id| internal capture id (new format)
|user_name,user_id | user information (user_id null for anonymous users)
|created_at | when the classification was created
|subject_id | zooniverse unique id of the capture (a subject)
|workflow_id,workflow_version | workflow info
|classification_id | classification_id (multiple annotations possible)
|retirement_reason| Zooniverse generated retirement reason
|question__count, question__eating | question answers
|question__interacting | question answers
|question__lyingdown, question__moving | question answers
|question__standing  | question answers
|question__young_present,question__species | question answers
|question__antlers_visible  | question answers


One record may look like:
```
XYZ,2012-12-11 07:40:53 UTC,ASG000aau3,495255,consensus,S3,K03,R12,
IMAG0275.JPG;IMAG0276.JPG;IMAG0274.JPG,2011-11-14T15:10:37-06:00;2011-11-14T15:
10:37-06:00;2011-11-14T15:10:37-06:00,50c6e3859177d033f6000330,
SER_S3#K03#R12#114,114,wildebeest,11-50,0,0,0,1,0,0
```

### Aggregate Extracted Zooniverse Classifications (in development)

This aggregates the extracted Zooniverse classifications using the
plurality algorithm to get one single label per species detection for each
subject.

```
python3 -m zooniverse_exports.aggregate_extractions \
        -classifications_extracted /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_extracted.csv \
        -output_csv /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_aggregated.csv
```

### Add Meta-Data to Aggregated Classifications (in development)

This function adds meta-data to aggregated classifications, like location, timestamp, and
other data currently used for input to machine learning models. This function is unfinished
and currently only works with the 'old' manifest formats.

```
python3 -m zooniverse_exports.add_meta_data_to_aggregated_class \
-classifications_aggregated /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated.csv \
-season_cleaned /home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv \
-output_csv /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_export.csv \
-season GRU_S1 \
-site GRU \
-manifest_files_old /home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1_manifest_v1 \
-max_n_images 3
```

#### Notes

1. It is possible to add subjects to a subject-set that is linked to a workflow and is itself in an active project volunteers are currently working on.
2. It can happen that the upload_manifest.pbs script crashes frequently and early. So far, such phases have been temporary hence the advise: "keep trying!".

## Processing Snapshot Serengeti S1-S10 data (legacy format) - (in development)

Data for Snapshot Serengeti (S1-S10) has been collected via an old Zooniverse platform (Oruboros) and has a different format than the newer Snapshot Safari data. Therefore, a separate processing script was implemented to generate csv files.

### Data

The data has been saved to MSI shared drives:
/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv

### Processing Codes

The following codes take as input the full export from Zooniverse. Note that the data is quite large (over 6GB and more than 25 mio records).

The scripts can be found here:
[Scripts for S1-S10](zooniverse_exports/extract_legacy_serengeti.py)

The script is a re-implementation of the following code:
https://github.com/mkosmala/SnapshotSerengetiScripts/

Reimplemented due to:
- dealing with additional seasons with different format
- efficiency reasons
- getting rid of certain undocumented pre-processing steps

The script does the following:
1. Split the raw file into seasons
2. Extract annotations and do some cleaning and mapping
3. Write extracted annotations to a file


To run the code use the following command:
```
cd $HOME/snapshot_safari_misc

python3 -m zooniverse_exports.extract_legacy_serengeti \
--classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
--output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
--season_to_process 'S3'
```

Specify the following to split the raw file into seasons (otherwise, the script assumes this was done):
```
--split_raw_file
```

Available seasons:
```
'S1', 'S2', 'S3', 'S4', 'S5', 'S6',
'S7', 'S8', 'S9', '10', 'WF1', 'tutorial'
```

### Output

The output is on level annotation. There is no unique identifier for an annotation.
The data has the following columns:

| Columns   | Description |
| --------- | ----------- |
|user_name | dispaly name of user (if logged in, else 'not-logged-in..')
|created_at | when the classification was made
|subject_id | zooniverse subject_id (unique id per capture event)
|capture_event_id | old capture_event_id as uploaded to zooniverse
|retirement_reason | string defining the retirement reason as defined by Zooniverse
|season,site,roll | internal id for season, site, roll
|filenames | image names, separated by ; if multiple
|timestamps | image timestamps, separated by ; if multiple
|classification_id | unique id per classification
|capture_id | new-style capture_id
|question__species | task-answer
|question__count | task-answer
|question__young_present | task-answer
|question__standing | task-answer
|question__resting | task-answer
|question__moving | task-answer
|question__eating | task-answer
|question__interacting | task-answer


```
user_name,created_at,subject_id,capture_event_id,retire_reason,season,site,roll,filenames,timestamps,classification_id,capture_id,question__species,question__count,question__young_present,question__standing,question__resting,question__moving,question__eating,question__interacting
XYZ,2012-12-11 06:27:56 UTC,ASG0004fwr,221374,consensus,S2,E04,R3,IMAG1524.JPG;IMAG1523.JPG;IMAG1522.JPG,2011-07-14T17:27:04-05:00;2011-07-14T17:27:04-05:00;2011-07-14T17:27:04-05:00,50c6d26c9177d0340a0001c5,SER_S2#E04#R3#570,zebra,3,0,0,0,1,1,0
```
