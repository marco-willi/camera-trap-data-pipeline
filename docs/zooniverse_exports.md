# Download and Extract Zooniverse Exports

The following codes can be used to:

1. Get Zooniverse Exports (download data through the Python API)
2. Extract Annotations from Zooniverse Classifications
3. Handle Legacy (S1-S10 Serengeti) Data

The following example was run with the following paramters:

```
SITE=RUA
SEASON=RUA_S1
PROJECT_ID=5155
WORKFLOW_ID=4889
WORKFLOW_VERSION_MIN=797
```

## Get Zooniverse Exports

Download Zooniverse exports. Requires Zooniverse account credentials and
collaborator status with the project. The project_id can be found in the project builder
in the top left corner. To create a 'fresh' export it is easiest to go on Zooniverse, to the project page, click on 'Data Exports', and request the appropriate export (see below). After receiving an e-mail confirming the export was completed, execute the following scripts (do not download data via e-mail).

### Zooniverse Classifications Export

Click on 'Request new classification export' to get the classifications. The structure of a classification is as follows:

1. One classification contains 1:N tasks
2. One task contains 1:N identifications (for survey task), or 1:N answers (for question tasks)
3. One identification contains 1:N questions (for survey task)
4. One question has 0:N answers (for survey task)

Example:
1. A task is to identify animals (survey task)
2. One task contains two animal identifications, e.g, zebra and wildebeest
3. One identification has multiple questions, e.g., species name and behavior
4. One question may have multiple answres, e.g, different behaviors for the behavior question

We refer to an identification/answer by a volunteer as an annotation.

To extract the classification data use the following code:
```
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--export_type classifications \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/
```

### Zooniverse Subject Export

To get subject data go to Zooniverse and click 'Request new subject export'. To download the data use:
```
# Get Zooniverse Subject Data
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--export_type subjects \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/
```


## Extract Zooniverse Annotations from Classifications

The following code extracts the relevant fields of a Zooniverse classification csv. It creates a csv file with one line per species identification/annotation. Usually, the workflow_id and the workflow_version are specified to extract only the workflow that was used during the 'live-phase' of the project. If neither workflow_id/workflow_version/worfklow_version_min are specified every workflow is extracted. The workflow_id can be found in the project builder when clicking on the workflow. The workflow_version is at the same place slightly further down (e.g. something like 745.34). Be aware that only the 'major' version number is compared against, e.g., workflow_version '45.23' is identical to '45.56'. It is also possible to specify a minimum 'workflow_version_min' in which case all classifications with the same or higher number are extracted. A summary of all extracted workflows and other stats is printed after the extraction.

Use a machine with enough memory - for example:

```
ssh lab
qsub -I -l walltime=2:00:00,nodes=1:ppn=4,mem=16gb
```

If WORKFLOW_ID / WORFKLOW_VERSION_MIN are unknown run the script like this:
```
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv
```

Then investiage the output of the script in the terminal to determine which workflows to use and then re-run the code with the specified workflows:

```
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--workflow_id $WORKFLOW_ID \
--workflow_version_min $WORFKLOW_VERSION_MIN
```


The resulting file may have the following column headers:

| Columns   | Description |
| --------- | ----------- |
|user_name,user_id | user information (user_id null for anonymous users)
|created_at | when the classification was created
|subject_id | zooniverse unique id of the capture (a subject)
|workflow_id,workflow_version | workflow info
|classification_id | classification_id (multiple annotations possible)
|retirement_reason| Zooniverse generated retirement reason
|retired_at| Zooniverse generated retirement date
|question__count, question__eating | question answers
|question__interacting | question answers
|question__lyingdown, question__moving | question answers
|question__standing  | question answers
|question__young_present,question__species | question answers
|question__antlers_visible  | question answers


One record may look like:
```
XYZ,,2018-02-06 17:09:43 UTC,
17530583,4979,275.13,88921948,consensus,2018-11-21T19:16:34.362Z,
4,0,1,0,0,1,1,wildebeest,
```

## Extract Zooniverse Subject Data

The following codes extract subject data from the subject exports that Zooniverse provides.

```
python3 -m zooniverse_exports.extract_subjects \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv
```


## Processing Snapshot Serengeti S1-S10 data (legacy format)

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
cd $HOME/camera-trap-data-pipeline

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

The output is on level annotation. There is no hard unique identifier for an annotation. Logically, an annotation is defined by subject_id, user_name and question_species (the main question). However, duplicates exist which the extraction process merges or discards.

The data has the following columns:

| Columns   | Description |
| --------- | ----------- |
|user_name | dispaly name of user (if logged in, else 'not-logged-in..')
|created_at | when the classification was made
|subject_id | zooniverse subject_id (unique id per capture event)
|capture_event_id | old capture_event_id as uploaded to zooniverse
|retirement_reason | string defining the retirement reason as defined by Zooniverse
|season,site,roll,capture | internal id for season, site, roll and capture
|filenames | image names, separated by ; if multiple (some are missing)
|timestamps | image timestamps, separated by ; if multiple (some are missing)
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
user_name,created_at,subject_id,capture_event_id,retirement_reason,season,site,roll,filenames,timestamps,classification_id,capture_id,capture,question__species,question__count,question__young_present,question__standing,question__resting,question__moving,question__eating,question__interacting
XYZ,2012-12-11 01:39:51 UTC,ASG00019km,61592,consensus,S1,I06,R2,PICT0344.JPG;PICT0345.JPG;PICT0346.JPG,2010-08-20T13:34:44-05:00;2010-08-20T13:34:46-05:00;2010-08-20T13:34:4605:00,50c68ee79177d0298c0002da,SER_S1#I06#2#116,116,gazelleThomsons,1,0,1,0,0,0,0
```

### Extract Subject Data from Classifications

This will produce a file containing one record per subject that can be merged with aggregated data in a later step.

```
python3 -m zooniverse_exports.extract_subjects_legacy \
--classifications_extracted /home/packerc/shared/zooniverse/Exports/SER/SER_S1_classifications_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_extracted.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/SER/
```


| Columns   | Description |
| --------- | ----------- |
|capture,roll,season,site | internal ids of the capture (some are missing)
|capture_id| capture-id
|subject_id | zooniverse unique id of the capture (a subject)
|created_at | timestamp when the subject was created on Zooniverse
|filenames | filenames of the images making up the capture, separated by ';' (some are missing)
|timestamps | timestamps of the images making up the capture, separated by ';' (some are missing)
|retirement_reason| Zooniverse generated retirement reason
|retired_at| Zooniverse generated retirement date


Example:
```
capture,capture_id,created_at,filenames,retired_at,retirement_reason,roll,season,site,timestamps,subject_id
1,SER_S1#B04#1#1,2013-01-02 19:45:15 UTC,S1/B04/B04_R1/S1_B04_R1_PICT0001.JPG,,consensus,R1,S1,B04,2010-07-18T16:26:14-05:00,ASG0002kjh
```

### Get Subject URLs from Zooniverse API (warning - takes a long time)

The following code queries the Ouroboros API from Zooniverse to get legacy subject data. The code can run a very long time (many hours per season). Resumes on failures by re-reading from file from disk.

```
# Get Subject URLs from Zooniverse API (warning - takes a long time)
python3 -m zooniverse_exports.get_legacy_ouroboros_data \
--subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--subjects_ouroboros /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_ouroboros.json
```

The following code extracts urls from the Ouroboros exports and saves them to a csv.
```
# Extract Zooniverse URLs from Oruboros Exports
python3 -m zooniverse_exports.extract_legacy_subject_urls \
--oruboros_export /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_ouroboros.json \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subject_urls.csv
```

Example:
```
subject_id,zooniverse_url_0,zooniverse_url_1,zooniverse_url_2
ASG0000001,http://www.snapshotserengeti.org/subjects/standard/50c210188a607540b9000001_0.jpg,,
ASG0000002,http://www.snapshotserengeti.org/subjects/standard/50c210188a607540b9000002_0.jpg,http://www.snapshotserengeti.org/subjects/standard/50c210188a60754
0b9000002_1.jpg,
```

### Re-Create Season Captures

For processing with later codes the following code re-creates season capture files according to the new process. This file has one row per image and is normally the end-product of pre-processing camera trap images.

```
python3 -m zooniverse_exports.recreate_legacy_season_captures \
--subjects_extracted /home/packerc/shared/zooniverse/Exports/SER/S1_subjects_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/SER/S1_cleaned.csv
```

| Columns   | Description |
| --------- | ----------- |
|capture,roll,season,site | internal ids of the capture (some are missing)
|capture_id| capture-id
|image| rank of the image in the capture (1=first image)
|path| relative path of the image
|timestamp| date time of when the image was taken (YYYY-MM-DD HH:MM:SS)


Examples:
```
capture_id,season,site,roll,capture,image,path,timestamp
SER_S1#B04#1#1,S1,B04,R1,1,1,S1/B04/B04_R1/S1_B04_R1_PICT0001.JPG,2010-07-18 16:26:14
SER_S1#B04#1#2,S1,B04,R1,2,1,S1/B04/B04_R1/S1_B04_R1_PICT0002.JPG,2010-07-18 16:26:30
SER_S1#B04#1#3,S1,B04,R1,3,1,S1/B04/B04_R1/S1_B04_R1_PICT0003.JPG,2010-07-20 06:14:06
```

### Add Zooniverse URLs to subjec exports

The following code appends the Zooniverse Urls of each subject.

```
# Add subject urls to subject extracts
python3 -m zooniverse_exports.merge_csvs \
--base_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--to_add_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subject_urls.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted_url.csv \
--key subject_id \
--add_new_cols_to_right
```


### Aggregations

Aggregations can be created with the usual aggregation code.

Additionally, the following codes append subject into:


The following code merges the subject_url infos with the aggregtions:

```
# Add subject data to Aggregations
python3 -m zooniverse_exports.merge_csvs \
--base_cs /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated.csv \
--to_add_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted_url.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--key subject_id
```

```
# Add subject data to Aggregations (samples)
python3 -m zooniverse_exports.merge_csvs \
--base_cs /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_samples.csv \
--to_add_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted_url.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info_samples.csv \
--key subject_id
```

Example:

```
capture_id,season,site,roll,capture,created_at,filenames,retired_at,retirement_reason,timestamps,zooniverse_url_0,zooniverse_url_1,zooniverse_url_2,subject_id,
question__species,question__count,question__young_present,question__standing,question__resting,question__moving,question__eating,question__interacting,n_users_
identified_this_species,p_users_identified_this_species,n_species_ids_per_user_median,n_users_classified_this_subject,n_users_saw_a_species,n_users_saw_no_spec
ies,p_users_saw_a_species,pielous_evenness_index,species_is_plurality_consensus
SER_S1#K11#1#205,S1,K11,R1,205,2012-12-14 22:33:50 UTC,S1/K11/K11_R1/S1_K11_R1_PICT0611.JPG;S1/K11/K11_R1/S1_K11_R1_PICT0612.JPG;S1/K11/K11_R1/S1_K11_R1_PICT06
13.JPG,,blank,2010-09-10T05:17:40-05:00;2010-09-10T05:17:40-05:00;2010-09-10T05:17:42-05:00,http://www.snapshotserengeti.org/subjects/standard/50c2115c8a607540
b9011370_0.jpg,http://www.snapshotserengeti.org/subjects/standard/50c2115c8a607540b9011370_1.jpg,http://www.snapshotserengeti.org/subjects/standard/50c2115c8a6
07540b9011370_2.jpg,ASG0001ieo,blank,,,,,,,,5,1.00,0,5,0,5,0.00,0.00,1
```
