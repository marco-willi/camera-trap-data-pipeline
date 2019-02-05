# Upload Data to Zooniverse

The following steps are required to upload new data to Zooniverse. The following codes show an example for processing RUA data. These are the steps:

1. Compress Images (Zooniverse has a size limit)
2. Generate Manifest (a file containing all info for the Zooniverse upload)
3. Create Machine Lerning File for Model Input (Optional - create input for machine classifier)
4. Generate new Predictions (Optional - run a machine classifier)
5. Split/Batch Manifest (Optional - Zooniverse recommends not to use too large batches at once)
6. Upload Manifest

The optional steps can simply be skipped.


## Compress Images

The script [image_compression](image_compression/compress_images.pbs) compresses images and has to be ADAPTED in the following way (NOT EXECUTED). You can find the script in this directory: '~/snapshot_safari_misc/image_compression/compress_images.pbs'. Image compression is required due to size limits of individual
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

## Generate Manifest

This generates a manifest from the captures csv. A manifest contains all the information required to upload data to Zooniverse.

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

## Create Machine Lerning File for Model Input (Optional)

This code creates a 'machine learning file' that has the correct format for the machine learning models to classify the images in the manifest.

```
python3 -m zooniverse_uploads.create_machine_learning_file \
--manifest /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1__complete__manifest.json
```

The default settings create the following file:
```
RUA_S1__complete__machine_learning_input.csv
```

## Generate new Predictions (Optional)

The following steps describe how to run the machine learning models. Note that the files 'ctc_predict_species.pbs' and 'ctc_predict_empty.pbs' have to be adapted. The predictions process is split into two parts: predict the presence of an animal (empty or not) and predict the animal species. Both of the following scripts can be run in parallel. The scripts process approximately 300 capture events / minute on a CPU queue so it can take several hours for large manifests to process. Please note that the following codes will create a file in your home directory 'camera-trap-classifier-latest-cpu.simg', you can safely delete that after the scripts have finished (it contains the machine learning software).

### Generating 'Empty or Not' Predictions

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

### Generating 'Species' Predictions

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

### Add Model Predictions to Manifest (Optional)

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

## Split/Batch Manifest (Optional)

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

## Upload Manifest

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


### In case of a failure

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

### Notes

1. It is possible to add subjects to a subject-set that is linked to a workflow and is itself in an active project volunteers are currently working on.
2. It can happen that the upload_manifest.pbs script crashes frequently and early. So far, such phases have been temporary hence the advise: "keep trying!".
