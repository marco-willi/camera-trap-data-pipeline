# Machine Learning

The following codes can be used to generate predictions for season captures.

```
ssh lab
qsub -I -l walltime=02:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd ~/camera-trap-data-pipeline
```

The following examples were run with the following parameters:
```
SITE=SER
SEASON=SER_S1
```

## Prepare Input File for Model

Create an input file for a machine learning model to create predictions for.

```
python3 -m machine_learning.create_machine_learning_file \
--cleaned_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--output_csv /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_machine_learning_input.csv \
--log_dir /home/packerc/shared/zooniverse/MachineLearning/${SITE}/log_files/ \
--log_filename ${SEASON}_create_machine_learning_file
```


## Create Predictions

### Define the Parameters

Run / Define the following commands / parameters:
```
ssh mesabi
cd $HOME/camera-trap-data-pipeline/machine_learning/jobs/

SITE=SER
SEASON=SER_S1

INPUT_FILE=/home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_machine_learning_input.csv

OUTPUT_FILE_EMPTY=/home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_empty_or_not.json

OUTPUT_FILE_SPECIES=/home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_species.json

IMAGES_ROOT=/home/packerc/shared/albums/${SITE}/
```

### Submit the Machine Learning Jobs

Both of the following commands can be run in parallel.

To run the 'Empty or Not' model execute the following command:
```
qsub -v INPUT_FILE=${INPUT_FILE},OUTPUT_FILE=${OUTPUT_FILE_EMPTY},IMAGES_ROOT=${IMAGES_ROOT} ctc_predict_empty_file.pbs
```

To run the 'Species' model execute the following command:
```
qsub -v INPUT_FILE=${INPUT_FILE},OUTPUT_FILE=${OUTPUT_FILE_SPECIES},IMAGES_ROOT=${IMAGES_ROOT} ctc_predict_species_file.pbs
```

NOTE: The script has a walltime of 24h. This was enough to calculate predictions for 187k captures. Should significantly more predictions be required increase the walltime paramter in the script accordingly.

## Flatten ML Predictions (convert JSON to a CSV)

Generate a csv with all machine learning predictions, one record per capture-id.

```
# Create Flattened ML Predictions
python3 -m machine_learning.flatten_ml_predictions \
--predictions_empty /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_empty_or_not.json \
--predictions_species /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_species.json \
--output_csv /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_ml_preds_flat.csv \
--log_dir /home/packerc/shared/zooniverse/MachineLearning/${SITE}/log_files/ \
--log_filename ${SEASON}_flatten_ml_predictions
```

This script may require a lot of memory if the .json files are very large.


## Reporting of Machine Learning Predictions

The following script merges the season captures with the ml predictions.
```
python3 -m reporting.create_ml_report \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--predictions_csv /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_ml_preds_flat.csv \
--export_only_with_predictions \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_ml.csv \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_ml_report
```


Create statistics of current predictions:
```
# Create statistics file
python3 -m reporting.create_ml_report_stats \
--report_path /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_machine_learning.csv \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_ml_overview.csv \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_ml_report_stats
```

## Report Columns

| Columns   | Description |
| --------- | ----------- |
|capture_id | internal identifier of the capture
|season | season id of the capture
|site| site/camera id of the capture
|roll| roll number of the capture
|capture| capture number of the roll
|capture_date_local | local date (YYYY-MM-DD) of the capture
|capture_time_local | local time (HH:MM:SS) of the capture
|machine_topprediction_is_empty| whether the model indicates the image is empty 'empty' or not 'not_empty'
|machine_confidence_is_empty| confidence of the image being empty / blank (0-1)
|machine_topprediction_(label)| the models top prediction for (label), e.g., '5' for the 'count' label
|machine_topconfidence_(label)| the models top confidence for (label), e.g., 0.98 for the 'count' label
|machine_confidence_count_(num) | Confidence of the model of (num) species being present in the image.
|machine_confidence_(behavior) | Confidence of predicted behavior (0-1)
|machine_confidence_species_(species)| Confidence of (species) being present in the image (0-1)


Note: The report is comprised of two models an 'empty or not' model and a 'species' model. Even if the 'empty or not' model classifies the capture as being empty, the 'species' model has to predict a 'species'. Therefore, always consider the species predictions in conjuntion with the 'empty or not' prediction.
