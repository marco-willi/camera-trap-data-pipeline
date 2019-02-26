# Download and Extract Zooniverse Exports

The following codes can be used to:

1. Get Zooniverse Exports (download data through the Python API)
2. Extract Zooniverse Classifications


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

To extract the classification data use the following code:
```
python3 -m zooniverse_exports.get_zooniverse_export \
        --password_file ~/keys/passwords.ini \
        --project_id 5155 \
        --output_file /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications.csv \
        --export_type classifications \
        --new_export 0
```

### Zooniverse Subject Export

To get subject data go to Zooniverse and click 'Request new subject export'. To download the data use:
```
python3 -m zooniverse_exports.get_zooniverse_export \
        --password_file ~/keys/passwords.ini \
        --project_id 5155 \
        --output_file /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_subjects.csv \
        --export_type subjects \
        --new_export 0
```


## Extract Zooniverse Classifications

The following code extracts the relevant fields of a Zooniverse classification csv. It creates a csv file with one line per species identification. Usually, the workflow_id and the workflow_version are specified to extract only the workflow that was used during the 'live-phase' of the project. If neither workflow_id/workflow_version/worfklow_version_min are specified every workflow is extracted. The workflow_id can be found in the project builder when clicking on the workflow. The workflow_version is at the same place slightly further down (e.g. something like 745.34). Be aware that only the 'major' version number is compared against, e.g., workflow_version '45.23' is identical to '45.56'. It is also possible to specify a minimum 'workflow_version_min' in which case all classifications with the same or higher number are extracted. A summary of all extracted workflows and other stats is printed after the extraction.

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
        --workflow_version_min 797
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

### Extract Subject Data from Classifications

This will produce a file containing one record per subject that can be merged with aggregated data in a later step.

```
python3 -m zooniverse_exports.extract_subjects_legacy \
--classifications_extracted /home/packerc/shared/zooniverse/Exports/SER/SER_S1_classifications_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_extracted.csv
```


| Columns   | Description |
| --------- | ----------- |
|capture,roll,season,site | internal ids of the capture
|capture_id| capture-id
|subject_id | zooniverse unique id of the capture (a subject)
|created_at | timestamp when the subject was created on Zooniverse
|filenames | filenames of the images making up the capture, separated by ';'
|timestamps | timestamps of the images making up the capture, separated by ';'
|retirement_reason| Zooniverse generated retirement reason
|retired_at| Zooniverse generated retirement date


Example:
```
capture,capture_id,created_at,filenames,retired_at,retirement_reason,roll,season,site,timestamps,subject_id
1,SER_S1#B04#1#1,2013-01-02 19:45:15 UTC,S1/B04/B04_R1/S1_B04_R1_PICT0001.JPG,,consensus,R1,S1,B04,2010-07-18T16:26:14-05:00,ASG0002kjh
```
