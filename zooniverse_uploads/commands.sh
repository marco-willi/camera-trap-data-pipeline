# Preparation
ssh lab
module load python3
pip install --upgrade --user panoptes-client
cd ~/snapshot_safari_misc


###################################
# GRU
###################################

SITE=GRU
SEASON=GRU_S1

# compress images
python3 -m image_compression.compress_images \
--captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--output_image_dir /home/packerc/shared/zooniverse/ToUpload/${SITE}/${SEASON}_Compressed \
--root_image_path /home/packerc/shared/albums/${SITE}/

# generate manifest
python3 -m zooniverse_uploads.generate_manifest \
--captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--compressed_image_dir /home/packerc/shared/zooniverse/ToUpload/${SITE}/${SEASON}_Compressed/ \
--output_manifest_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--manifest_id ${SEASON} \
--attribution 'University of Minnesota Lion Center + Snapshot Safari + Singita Grumeti + Tanzania' \
--license 'Snapshot Safari + Singita Grumeti'

# Create machine learning file
python3 -m zooniverse_uploads.create_machine_learning_file \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json

# add machine scores to batch
python3 -m zooniverse_uploads.add_predictions_to_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json

# Split into batches
python3 -m zooniverse_uploads.split_manifest_into_batches \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--max_batch_size 10000

# Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_1__manifest.json \
--project_id 5115 \
--password_file ~/keys/passwords.ini


# Retry Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_1__manifest.json \
--project_id 5115 \
--subject_set_id 72185 \
--password_file ~/keys/passwords.ini

###################################
# SER
###################################

SITE=SER
SEASON=SER_S11

# Create machine learning file
python3 -m zooniverse_uploads.create_machine_learning_file \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_6__manifest.json

# add machine scores to batch
python3 -m zooniverse_uploads.add_predictions_to_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_5__manifest.json

# Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_5__manifest.json \
--project_id 4996 \
--password_file ~/keys/passwords.ini

###################################
# MTZ
###################################

SITE=MTZ
SEASON=MTZ_S1

# Split manifest into batches
python3 -m zooniverse_uploads.split_manifest_into_batches \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--max_batch_size 20000


# Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_1__manifest.json \
--project_id 5124 \
--password_file ~/keys/passwords.ini


# Re-Try Uploading manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_1__manifest.json \
--project_id 5124 \
--subject_set_id 72374 \
--password_file ~/keys/passwords.ini

###################################
# KAR
###################################

SITE=KAR
SEASON=KAR_S1


###################################
# PLN
###################################

SITE=PLN
SEASON=PLN_S1

# Split manifest into batches
python3 -m zooniverse_uploads.split_manifest_into_batches \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--max_batch_size 20000


# Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_1__manifest.json \
--project_id 6190 \
--password_file ~/keys/passwords.ini
