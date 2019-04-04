#!/bin/bash -l
#PBS -l walltime=12:00:00,nodes=1:ppn=12
#PBS -j oe
#PBS -m abe
#PBS -q small
#PBS -N eval_empty
#PBS -o ${HOME}/job_ml_output_eval_empty_${PBS_JOBID}.log
#PBS -e ${HOME}/job_ml_error_eval_empty_${PBS_JOBID}.log


INPUT_PATH=/home/packerc/shared/machine_learning/data/info_files/SNAPSHOT_SAFARI/
INPUT_FILE=SNAPSHOT_SAFARI_data_blank_species_balanced_test.csv


OUTPUT_ROOT=/home/packerc/shared/machine_learning/data/predictions/
OUTPUT_PATH=${OUTPUT_ROOT}empty_or_not/PANTHERA_SNAPSHOT_SAFARI/ResNet18_448_v1/predictions.json

# Parameters Static
IMAGES_ROOT=/home/packerc/shared/albums/
TO_PREDICT_PATH=${INPUT_PATH}${INPUT_FILE}

# MODEL PATHS
MODEL_ROOT_PATH=/home/packerc/shared/machine_learning/data/models/PANTHERA_SNAPSHOT_SAFARI/empty_or_not/
MODEL_NAME=ResNet18_448_v1
MODEL_PATH=${MODEL_ROOT_PATH}${MODEL_NAME}/best_model.hdf5
MODEL_CLASS_MAPPING=${MODEL_ROOT_PATH}${MODEL_NAME}/label_mappings.json
MODEL_PRE_PROCESSING=${MODEL_ROOT_PATH}${MODEL_NAME}/image_processing.json


# Log Parameters
echo "TO_PREDICT_PATH: $TO_PREDICT_PATH"
echo "IMAGES_ROOT: $IMAGES_ROOT"
echo "OUTPUT_PATH: $OUTPUT_PATH"

echo "MODEL_ROOT_PATH: $MODEL_ROOT_PATH"
echo "MODEL_NAME: $MODEL_NAME"
echo "MODEL_PATH: $MODEL_PATH"
echo "MODEL_CLASS_MAPPING: $MODEL_CLASS_MAPPING"
echo "MODEL_PRE_PROCESSING: $MODEL_PRE_PROCESSING"


# modules
module load singularity
module load python3

# download container and code
cd $HOME
singularity pull docker://will5448/camera-trap-classifier:latest-cpu

# run the script
singularity exec -B /home/packerc/shared:/home/packerc/shared ./camera-trap-classifier-latest-cpu.simg \
  ctc.predict \
    -csv_path $TO_PREDICT_PATH \
    -csv_id_col capture_id \
    -csv_images_cols image1 image2 image3 \
    -csv_images_root_path $IMAGES_ROOT \
    -export_file_type json \
    -results_file $OUTPUT_PATH \
    -model_path $MODEL_PATH \
    -class_mapping_json $MODEL_CLASS_MAPPING \
    -pre_processing_json $MODEL_PRE_PROCESSING \
    -aggregation_mode min

chmod g+rw $OUTPUT_PATH
