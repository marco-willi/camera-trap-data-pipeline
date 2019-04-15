# Upload Data to Zooniverse

The following steps are required to upload new data to Zooniverse. The following codes show an example for processing RUA data. These are the steps:

1. Generate Manifest (a file containing all info for the Zooniverse upload)
2. Create Machine Learning File for Model Input (Optional - create input for machine classifier)
3. Generate new Predictions (Optional - run a machine classifier)
4. Split/Batch Manifest (Optional - Zooniverse recommends not to use too large batches at once)
5. Upload Manifest

The optional steps can simply be skipped.

For most scripts we use the following ressources (unless indicated otherwise):
```
ssh lab
qsub -I -l walltime=12:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd ~/camera-trap-data-pipeline
```

The following examples were run with the following paramters:
```
SITE=RUA
SEASON=RUA_S1
PROJECT_ID=5155
ATTRIBUTION='University of Minnesota Lion Center + SnapshotSafari + Ruaha Carnivore Project + Tanzania + Ruaha National Park'
LICENSE='SnapshotSafari + Ruaha Carnivore Project'
```

Make sure to create the following folders:
```
Manifests/${SITE}/
Manifests/${SITE}/log_files/
```


## Generate Manifest

This generates a manifest from the captures csv. A manifest contains all the information required to upload data to Zooniverse.

```
python3 -m zooniverse_uploads.generate_manifest \
--captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--output_manifest_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--images_root_path /home/packerc/shared/albums/${SITE}/ \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/log_files/ \
--log_filename ${SEASON}_generate_manifest \
--manifest_id ${SEASON} \
--attribution "${ATTRIBUTION}" \
--license "${LICENSE}"
```

The default settings create the following file:
```
${SEASON}__complete__manifest.json
```

The 'image_root_path' has to be specified if the 'captures_csv' contains relative paths to the images -- the manifest creation code checks for file existence.

### Cleaned Captures File

The 'captures_csv' input is a csv file with one row per image and with (at least) the following columns:

| Column   | Description |
| --------- | ----------- |
|season | season identifier (typically identical for the whole file)
|site | site/camera identifier
|roll | roll identifier (SD card of a camera)
|capture | capture number (e.g. '1' for the first capture in a specific roll)
|path or image_path_rel | Absolute or relative path of the image
|invalid| (legacy column) -- excludes images from the manifest if value is '1' or '2'

It is expected that the input is ordered by: season, site, roll, capture, image (ordered by sequence in the capture).

Example:
```
season,site,roll,capture,image,path,timestamp,oldtime,sr,imname,invalid,timez,J
GRU_S1,J05,1,14,1,GRU_S1/J05/J05_R1/GRU_S1_J05_R1_IMAG0036.JPG,2017:06:06 03:56:50,2017:06:06 03:56:50,J05_R1,GRU_S1_J05_R1_IMAG0036.JPG,1,,
GRU_S1,J06,1,17,1,GRU_S1/J06/J06_R1/GRU_S1_J06_R1_IMAG0043.JPG,2017:06:09 22:28:38,2017:06:09 22:28:38,J06_R1,GRU_S1_J06_R1_IMAG0043.JPG,0,,
```

## Machine Learning (Optional)

It is assumed that the machine predictions have already been created using: [Machine Learning](docs/machine_learning.md).

```
cd $HOME/camera-trap-data-pipeline
python3 -m zooniverse_uploads.add_predictions_to_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--predictions_empty /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_empty_or_not.json \
--predictions_species /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_species.json \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/log_files/ \
--log_filename ${SEASON}_add_predictions_to_manifest
```

Note: If the script is 'killed' the most likely reason is memory usage. In that case use this command to launch a session with more memory and try again:

```
qsub -I -l walltime=01:00:00,nodes=1:ppn=4,mem=16gb
module load python3
```

## Split/Batch Manifest (Optional)

This codes splits the manifest into several batches that can be uploaded separately. Additionally, the machine scores can be updated for individual batches (usually batches that have not yet been uploaded). Either the number of batches 'number_of_batches' or the 'max_batch_size' can be specified. Default is to randomly split the manifest into the batches.

```
cd $HOME/camera-trap-data-pipeline
python3 -m zooniverse_uploads.split_manifest_into_batches \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/log_files/ \
--log_filename ${SEASON}_split_manifest_into_batches \
--max_batch_size 20000
```

This creates the following files:
```
${SEASON}__batch_1__manifest.json
${SEASON}__batch_2__manifest.json
...
```

## Upload Manifest

This code uploads a manifest to Zooniverse. Note that Zooniverse credentials have to be available in '~/keys/passwords.ini' and that it is better to use the .qsub version of this code due to the (very!) long potential run-time (especially for manifests with > 50k subjects). Make sure that your account has enough allowance on how many subjects can be uploaded to Zooniverse.

### Run in Terminal

Define the parameters:
```
SITE=RUA
SEASON=RUA_S1
PROJECT_ID=5155
BATCH=complete
```

Change the paths analogue to this example:
```
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__${BATCH}__manifest.json \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/log_files/ \
--log_filename ${SEASON}_upload_manifest \
--project_id ${PROJECT_ID} \
--password_file ~/keys/passwords.ini \
--image_root_path /home/packerc/shared/albums/${SITE}/
```

To upload a specific batch instead use:
```
BATCH=batch_1
```

### Run via qsub (if not via Terminal) - Recommended if connection issues

Run the script in the following way:
```
ssh lab
cd $HOME/camera-trap-data-pipeline/zooniverse_uploads/

SITE=RUA
SEASON=RUA_S1
PROJECT_ID=5155
BATCH=batch_0

qsub -v SITE=${SITE},SEASON=${SEASON},PROJECT_ID=${PROJECT_ID},BATCH=${BATCH} upload_manifest.pbs
```

### Upload Tracker File

The code creates an upload 'tracker' file that tracks which captures have already been uploaded successfully. This allows for resuming uploads upon connection failures while avoiding to upload duplicates. This file is automatically deleted after the manifest has been completely uploaded.

Important: If, for some reason, one uploads a manifest incompletely, deletes the subject-set on Zooniverse, and at some point starts over with the upload, the upload-tracker file needs to be manually deleted, else it's content is inconsistent with what is already on Zooniverse.

Example file:
```
RUA_S1__batch_1__upload_tracker_file.txt
```


### Image Compression Options

Per default the images are being compressed during the upload process. Use the following paramters to change that behavior:

```
--save_quality 50 \
--n_processes 3 \
--max_pixel_of_largest_side 1440
```

Or disable image compression with:
```
--dont_compress_images
```

### In case of a failure

If the upload fails (which can happen if the connection to Zooniverse crashes) you can add the missing subjects to the already (partially) uploaded set by specifying the SUBJECT_SET_ID of the already created set. DO NOT specify the parameter '-subject_set_name', instead use '-subject_set_id' and use the id on the 'Subject Sets' page after clicking on the name of the set of your project on Zooniverse.

Change the paths analogue to this example:
```
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/log_files/ \
--log_filename ${SEASON}_upload_manifest \
--project_id ${PROJECT_ID} \
--subject_set_id 7845 \
--image_root_path /home/packerc/shared/albums/${SITE}/ \
--password_file ~/keys/passwords.ini
```

Alternatively, use the qsub system:
```
ssh lab
cd $HOME/camera-trap-data-pipeline/zooniverse_uploads/

SITE=RUA
SEASON=RUA_S1
PROJECT_ID=5155
BATCH=batch_0
SUBJECT_SET_ID=7845

qsub -v SITE=${SITE},SEASON=${SEASON},PROJECT_ID=${PROJECT_ID},BATCH=${BATCH},SUBJECT_SET_ID=${SUBJECT_SET_ID} upload_manifest.pbs
```

### Notes

1. It is possible to add subjects to a subject-set that is linked to a workflow and is itself in an active project volunteers are currently working on.
2. It can happen that the script crashes frequently and early. So far, such phases have been temporary hence the advise: "keep trying!". Typically, the error message for connetion issues looks similar to:
```
INFO:Error occurred for capture_id: PLN_S1#D05#2#3345
INFO:Details of error: Received HTTP status code 504 from API
```
The script tries to re-try on connection issues, however, it can take a long time until connection issues are detected. It is thus useful to use the 'qsub' version of the script with a long runtime and be patient until everything is uploaded.
