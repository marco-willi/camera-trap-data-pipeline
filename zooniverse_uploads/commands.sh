# Preparation
ssh lab
module load python3
pip install --upgrade --user panoptes-client
cd ~/snapshot_safari_misc


###################################
# MTZ
###################################

SITE=MTZ
SEASON=MTZ_S1

# Create Prediction File
python3 -m zooniverse_uploads.create_predict_file_from_manifest \
-manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_manifest.json \
-prediction_file /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_machine_learning_input.csv
