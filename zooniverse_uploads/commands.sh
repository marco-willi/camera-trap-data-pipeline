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
--captures_csv /home/packerc/shared/season_captures/RUA/cleaned/${SEASON}_cleaned.csv \
--compressed_image_dir /home/packerc/shared/zooniverse/ToUpload/${SITE}/${SEASON}_Compressed/ \
--output_manifest_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--manifest_id ${SEASON} \
--attribution 'University of Minnesota Lion Center + SnapshotSafari + Singita Grumeti' \
--license 'SnapshotSafari'

###################################
# SER
###################################

SITE=SER
SEASON=SER_S11

# Create machine learning file
python3 -m zooniverse_uploads.create_machine_learning_file \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_5__manifest.json


###################################
# MTZ
###################################

SITE=MTZ
SEASON=MTZ_S1


###################################
# KAR
###################################

SITE=KAR
SEASON=KAR_S1
