# Download and Extract Zooniverse Exports

The following codes can be used to:

1. Get Zooniverse Exports (download data through the Python API)
2. Extract Annotations from Zooniverse Classifications


For most scripts we use the following ressources (unless indicated otherwise):
```
ssh lab
qsub -I -l walltime=02:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd ~/camera-trap-data-pipeline
```

The following examples were run with the following parameters (non-legacy):
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

Note: Currently (April 2019) the export contains all historical data from a particular project -- it is only possible to filter by workflow_id.

### Zooniverse Subject Export

To get subject data go to Zooniverse and click 'Request new subject export'. To download the data use:
```
# Get Zooniverse Subject Data
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--export_type subjects \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_get_subject_export
```

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

To donwload the classification data from Zooniverse use the following code:
```
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--export_type classifications \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_get_classification_export
```

## Extract Zooniverse Subject Data

The following codes extract subject data from the subject exports that Zooniverse provides. The 'filter_by_season' argument selects only subjects from the specified season.

```
python3 -m zooniverse_exports.extract_subjects \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--filter_by_season ${SEASON} \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_subjects
```

The resulting file may have the following column headers:

| Columns   | Description |
| --------- | ----------- |
|capture_id, capture,roll,season,site | internal id's of the capture (uploaded to Zooniverse)
|subject_id | zooniverse unique id of the capture (a subject)
|zooniverse_created_at| Datetime of when the subject was created/uploaded on/to Zooniverse
|zooniverse_retired_at| Datetime of when the subject was retired on Zooniverse (empty if not)
|zooniverse_retirement_reason| Zooniverse system-generated retirement-reason (empty if none / not)
|zooniverse_url_*| Zooniverse URLs to images of the capture / subject

Note: The 'season' attribute is guessed for records without that data in the subject export based on the name of the 'output_csv'. This is to deal with legacy data that had no 'season' field.

## Extract Zooniverse Annotations from Classifications

The following code extracts the relevant fields of a Zooniverse classification csv. It creates a csv file with one line per species identification/annotation.

Use a machine with enough memory - for example:

```
ssh lab
qsub -I -l walltime=2:00:00,nodes=1:ppn=4,mem=16gb
```

### Option 1) Filtering Classifications by Worfklow-ID

Usually, the workflow_id and the workflow_version are specified to extract only the workflow that was used during the 'live-phase' of the project. If neither workflow_id/worfklow_version_min are specified every workflow is extracted. The workflow_id can be found in the project builder when clicking on the workflow. The workflow version is at the same place slightly further down (e.g. something like 745.34). Be aware that only the 'major' version number is compared against, e.g., workflow version '45.23' is identical to '45.56'. To extract specific workflow versions we can specify a minimum version 'workflow_version_min' in which case all classifications with the same or higher number are extracted. A summary of all extracted workflows and other stats is printed after the extraction.

If WORKFLOW_ID / WORKFLOW_VERSION_MIN are unknown run the script like this:
```
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv
```

Then investigate the output of the script in the terminal to determine which workflows to use and then re-run the code with the specified workflows. Example output:
```
INFO:Workflow id: 4655    Workflow version: 4.4        -- counts: 2
INFO:Workflow id: 4655    Workflow version: 173.7      -- counts: 1
INFO:Workflow id: 4655    Workflow version: 209.17     -- counts: 2
INFO:Workflow id: 4655    Workflow version: 226.18     -- counts: 2
INFO:Workflow id: 4655    Workflow version: 303.22     -- counts: 277
INFO:Workflow id: 4655    Workflow version: 304.23     -- counts: 1377468
INFO:Workflow id: 4655    Workflow version: 362.24     -- counts: 405
INFO:Workflow id: 4655    Workflow version: 363.25     -- counts: 842646
```

In that case we would choose 'WORKFLOW_ID=4655' and 'WORKFLOW_VERSION_MIN=304.23' since this seems to be the 'real' start of the season with many annotations. Later changes hopefully were only minor.

```
WORKFLOW_ID=4655
WORKFLOW_VERSION_MIN=304.23
```

```
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--workflow_id $WORKFLOW_ID \
--workflow_version_min $WORKFLOW_VERSION_MIN \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_annotations
```


### Option 2) Filtering Classifications by Date Range

If is is known when the project went live a start-date can be specified such that no classifications made prior to that date are being extracted. There is also the option to specify an end-date: no classification made past that date will be extracted. It is possible to specify only one of the dates. Note: The dates are compared against UTC time.

```
EARLIEST_DATE=2000-01-01
LAST_DATE=2099-01-01
```

```
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--no_earlier_than_date $EARLIEST_DATE \
--no_later_than_date $LAST_DATE \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_annotations
```

### Option 3) No Filtering

No filtering of any classifications.

```
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_annotations
```

### Option 4) Combine Filters

Workflow and date range filters can be applied at the same time.

```
EARLIEST_DATE=2000-01-01
WORKFLOW_ID=4655
WORKFLOW_VERSION_MIN=304.23
```

```
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--no_earlier_than_date $EARLIEST_DATE \
--workflow_id $WORKFLOW_ID \
--workflow_version_min $WORKFLOW_VERSION_MIN \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_annotations
```


### Output File


The resulting file may have the following column headers:

| Columns   | Description |
| --------- | ----------- |
|user_name,user_id | user information (user_id null for anonymous users)
|subject_id | zooniverse unique id of the capture (a subject)
|workflow_id,workflow_version | workflow info
|classification_id | classification_id (multiple annotations possible)
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

## Filter Annotations with Subject Data

To retain only annotations of a specific set of subjects (for example a season) run the following code:

```
python3 -m zooniverse_exports.select_annotations \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--subjects /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_select_annotations
```

## Processing Snapshot Serengeti S1-S10 data (legacy format)

See [Legacy Extractions](../docs/zooniverse_exports_legacy.md)
