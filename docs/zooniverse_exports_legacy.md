# Extract Zooniverse Legacy (Serengeti S1-S10) Exports

Data for Snapshot Serengeti (S1-S10) has been collected via an old Zooniverse platform (Oruboros) and has a different format than the newer Snapshot Safari data. Therefore, a separate processing script was implemented to generate csv files.

For most scripts we use the following ressources (unless indicated otherwise):
```
ssh lab
qsub -I -l walltime=02:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd ~/camera-trap-data-pipeline
```

### Data

The data has been saved to MSI shared drives:
/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv

### Processing Codes

The following codes take as input the full export from Zooniverse. Note that the data is quite large (over 6GB and more than 25 mio records).

The scripts can be found here:
[Scripts for S1-S10](../zooniverse_exports/legacy/)

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

SITE=SER
SEASON=SER_S3
SEASON_STRING=S3

python3 -m zooniverse_exports.legacy.extract_legacy_serengeti \
--classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
--output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
--season_to_process ${SEASON_STRING} \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_legacy_serengeti
```

Specify the following to split the raw file into seasons (otherwise, the script assumes this was done):
```
--split_raw_file
```

Available seasons (season_string):
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
|zooniverse_retirement_reason | string defining the retirement reason as defined by Zooniverse
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
user_name,created_at,subject_id,capture_event_id,zooniverse_retirement_reason,season,site,roll,filenames,timestamps,classification_id,capture_id,capture,question__species,question__count,question__young_present,question__standing,question__resting,question__moving,question__eating,question__interacting
XYZ,2012-12-11 01:39:51 UTC,ASG00019km,61592,consensus,S1,I06,R2,PICT0344.JPG;PICT0345.JPG;PICT0346.JPG,2010-08-20T13:34:44-05:00;2010-08-20T13:34:46-05:00;2010-08-20T13:34:4605:00,50c68ee79177d0298c0002da,SER_S1#I06#2#116,116,gazelleThomsons,1,0,1,0,0,0,0
```

### Extract Subject Data from Classifications

This will produce a file containing one record per subject that can be merged with aggregated data in a later step.

```
python3 -m zooniverse_exports.legacy.extract_subjects_legacy \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted_prelim.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_subjects_legacy_prelim
```


| Columns   | Description |
| --------- | ----------- |
|capture,roll,season,site | internal ids of the capture (some are missing)
|capture_id| capture-id
|subject_id | zooniverse unique id of the capture (a subject)
|filenames | filenames of the images making up the capture, separated by ';' (some are missing)
|timestamps | timestamps of the images making up the capture, separated by ';' (some are missing)
|zooniverse_retirement_reason| Zooniverse generated retirement reason ('' if not available)
|zooniverse_retired_at| Zooniverse generated retirement date of the subject ('' if not available)
|zooniverse_created_at| Zooniverse generated creation date of the subject ('' if not available)

Example:
```
capture,capture_id,created_at,filenames,retired_at,zooniverse_retirement_reason,roll,season,site,timestamps,subject_id
1,SER_S1#B04#1#1,2013-01-02 19:45:15 UTC,S1/B04/B04_R1/S1_B04_R1_PICT0001.JPG,,consensus,R1,S1,B04,2010-07-18T16:26:14-05:00,ASG0002kjh
```

### Get Subject URLs from Zooniverse API (warning - takes a long time)

The following code queries the Ouroboros API from Zooniverse to get legacy subject data. The code can run a very long time (many hours per season). Resumes on failures by re-reading from file from disk.

```
# Get Subject URLs from Zooniverse API (warning - takes a long time)
python3 -m zooniverse_exports.legacy.get_legacy_ouroboros_data \
--subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--subjects_ouroboros /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_ouroboros.json
```

The following code extracts urls from the Ouroboros exports and saves them to a csv.
```
# Extract Zooniverse URLs from Oruboros Exports
python3 -m zooniverse_exports.legacy.extract_legacy_subject_urls \
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

The code relies on various input files:
1. LILA/Dryad publication (S1-S6)
2. MSI DB exports (S1-S8)
3. SX_cleaned.csv files

The code is suppoed to be run manually at only once. Details can be found here:

[Build Cleaned CSV](../zooniverse_exports/legacy/build_cleaned_csv.py)

| Columns   | Description |
| --------- | ----------- |
|capture_id| capture-id
|season, site, roll, capture| internal ids of the capture
|image_rank_in_capture| rank/order of image in a capture (may be missing)
|image_path_rel| relative (to season root) image path after re-naming
|datetime| datetime of image (default Y-m-d H:M:S) -- after any datetime corrections applied
|datetime_exif| datetime as extrated from EXIF data (default Y-m-d H:M:S, '' if none)
|datetime_file_creation| file creation date (is missing - just for consistency)
|image_is_invalid| flag if image was invalidated (1, '' otherwise) -- derived from 'invalid' column (values 1,2,3)
|image_datetime_uncertain| flag if image was marked for uncertain datetime (1, '' otherwise) -- derived from 'invalid' column (values 1,2,3)
|invalid| legacy column referring to timestamp status ('1' = 'Not recoverable', '2'= 'Fix is hard', '3'='Fix is hard but timestamp likely close'),
|include| legacy flag referring whether to 'include' (='1') the image (='1' only were published)


Examples:
```
capture_id,season,site,roll,capture,image_rank_in_capture,image_path_rel,datetime,datetime_exif,datetime_file_creation,invalid,include,image_is_invalid,image_datetime_uncertain
SER_S10#B03#1#1,S10,B03,1,1,1,S10/B03/B03_R1/S10_B03_R1_IMAG0001.JPG,2015-01-16 11:31:41,2015-01-16 11:31:41,,0,1,0,0
SER_S10#B03#1#1,S10,B03,1,1,2,S10/B03/B03_R1/S10_B03_R1_IMAG0002.JPG,2015-01-16 11:31:41,2015-01-16 11:31:43,,0,1,0,0
SER_S10#B03#1#2,S10,B03,1,2,1,S10/B03/B03_R1/S10_B03_R1_IMAG0003.JPG,2015-01-16 11:31:46,2015-01-16 11:31:46,,0,1,0,0
```

### Add Zooniverse URLs to subjec exports

The following code appends the Zooniverse Urls of each subject.

```
# Extract subjects without filename/timestamp cols
python3 -m zooniverse_exports.legacy.extract_subjects_legacy \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_subjects_legacy \
--exclude_colums timestamps filenames

# Add subject urls to subject extracts
python3 -m zooniverse_exports.merge_csvs \
--base_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--to_add_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subject_urls.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--key subject_id \
--add_new_cols_to_right
```


### Aggregations

Aggregations can be created with the usual aggregation code.
