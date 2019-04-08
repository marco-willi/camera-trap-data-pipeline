# Machine Learning

The following codes can be used to generate predictions for season captures.

```
ssh lab
qsub -I -l walltime=02:00:00,nodes=1:ppn=4,mem=8gb
module load python3
cd ~/camera-trap-data-pipeline
```

The following examples were run with the following paramters:
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
qsub -v INPUT_FILE=${INPUT_FILE},OUTPUT_FILE=${OUTPUT_FILE_SPECIES},IMAGES_ROOT=${IMAGES_ROOT} ctc_predict_empty_file.pbs
```
