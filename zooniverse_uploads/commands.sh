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

# Merge Predictions with Manifest
cd $HOME/snapshot_safari_misc

python3 -m zooniverse_uploads.merge_predictions_with_manifest \
-manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_manifest.json \
-predictions_empty /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_empty_or_not.json \
-predictions_species /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_species.json \
-output_file /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_manifest1.json



###################################
# KAR
###################################

SITE=KAR
SEASON=KAR_S1

# Create Prediction File
python3 -m zooniverse_uploads.create_predict_file_from_manifest \
-manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_manifest.json \
-prediction_file /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_machine_learning_input.csv

# Merge Predictions with Manifest
cd $HOME/snapshot_safari_misc

python3 -m zooniverse_uploads.merge_predictions_with_manifest \
-manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_manifest.json \
-predictions_empty /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_empty_or_not.json \
-predictions_species /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_species.json \
-output_file /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_manifest1.json
