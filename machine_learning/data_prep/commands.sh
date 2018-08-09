module load python3
cd /home/packerc/shared/scripts/snapshot_safari_misc

python -m machine_learning.data_prep.prep_csv_info_file \
-season 1 \
-season_prefix SER_S

python -m machine_learning.data_prep.prep_csv_info_file \
-season all \
-season_prefix SER_S


cd /home/packerc/shared/machine_learning/will5448/code/camera-trap-classifier
module load python3
source activate ctc

# Create dataset inventory SER
python create_dataset_inventory.py csv -path /home/packerc/will5448/data/season_exports/db_export_season_all_cleaned.csv \
-export_path /home/packerc/will5448/data/inventories/dataset_inventory_season_all.json \
-capture_id_field capture_id \
-image_fields image1 image2 image3 \
-label_fields empty species count standing resting moving eating interacting babies empty \
-meta_data_fields season capturetimestamp location split_name




# Parallel Images Writes Species SER
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_season_all.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_species/SER/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-remove_label_name empty \
-remove_label_value empty \
-image_root_path /home/packerc/shared/albums \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000



# Parallel Images Writes Empty or Not SER
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_season_all.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_empty_or_not/SER/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-balanced_sampling_min \
-balanced_sampling_label empty \
-image_root_path /home/packerc/shared/albums \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000







# Train a model
cd /home/packerc/shared/machine_learning/will5448/code/camera-trap-classifier
module load python3
source activate ctcgpu
python train.py \
-train_tfr_path /home/packerc/will5448/data/tfr_files/all_species/ \
-train_tfr_pattern train \
-val_tfr_path /home/packerc/will5448/data/tfr_files/all_species/ \
-val_tfr_pattern val \
-test_tfr_path /home/packerc/will5448/data/tfr_files/all_species/ \
-test_tfr_pattern test \
-class_mapping_json /home/packerc/will5448/data/tfr_files/all_species/label_mapping.json \
-run_outputs_dir /home/packerc/will5448/data/run_outputs/ \
-model_save_dir /home/packerc/will5448/data/saves/ \
-model ResNet18 \
-labels species count standing resting moving eating interacting babies \
-batch_size 128 \
-n_cpus 24 \
-n_gpus 2 \
-buffer_size 32768 \
-max_epochs 20 \
-starting_epoch 0 \
-color_augmentation fast


# Singularity
singularity pull docker://tensorflow/tensorflow:1.9.0-gpu-py3
singularity exec docker://tensorflow/tensorflow git clone https://github.com/marco-willi/camera-trap-classifier.git
singularity exec docker://tensorflow/tensorflow cd ~/camera-trap-classifier


# Parallel File Writes
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_season_2.json \
-output_dir /home/packerc/will5448/data/tfr_files/s2/ \
-image_save_side_max 500 \
-split_percent 0.9 0.05 0.05 \
-split_names train_s2_species val_s2_species test_s2_species \
-remove_label_name empty \
-remove_label_value 1 \
-image_root_path /home/packerc/shared/albums \
-max_records_per_file 20000 \
-overwrite \
-write_tfr_in_parallel


# Serial Writes
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_season_3.json \
-output_dir /home/packerc/will5448/data/tfr_files/s3/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-remove_label_name empty \
-remove_label_value 1 \
-image_root_path /home/packerc/shared/albums \
-overwrite

###############################################
# RUAHA
###############################################

# Create dataset inventory RUA
python create_dataset_inventory.py csv -path /home/packerc/will5448/data/season_exports/db_export_rua_season_1.csv \
-export_path /home/packerc/will5448/data/inventories/dataset_inventory_rua_season_1.json \
-capture_id_field capture_id \
-image_fields image1 image2 image3 \
-label_fields empty species count standing resting moving eating interacting babies empty \
-meta_data_fields season capturetimestamp location split_name

# Parallel Images Writes Species RUA
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_rua_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_species/RUA/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-remove_label_name empty \
-remove_label_value empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000


# Parallel Images Writes Empty or Not RUA
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_rua_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_empty_or_not/RUA/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-balanced_sampling_min \
-balanced_sampling_label empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000

###############################################
# Grumeti
###############################################

# Create dataset inventory GRU
python create_dataset_inventory.py csv -path /home/packerc/will5448/data/season_exports/db_export_gru_season_1.csv \
-export_path /home/packerc/will5448/data/inventories/dataset_inventory_gru_season_1.json \
-capture_id_field capture_id \
-image_fields image1 image2 image3 \
-label_fields empty species count standing resting moving eating interacting babies empty \
-meta_data_fields season capturetimestamp location split_name


# Parallel Images Writes Species GRU
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_gru_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_species/GRU/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-remove_label_name empty \
-remove_label_value empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000

# Parallel Images Writes Empty or Not GRU
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_gru_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_empty_or_not/GRU/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-balanced_sampling_min \
-balanced_sampling_label empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000


###############################################
# Gondwana
###############################################


cd /home/packerc/shared/machine_learning/will5448/code/camera-trap-classifier
module load python3
source activate ctc

# Create dataset inventory
python create_dataset_inventory.py csv -path //home/packerc/shared/zooniverse/Exports/GON/GON_S1_export.csv \
-export_path /home/packerc/will5448/data/inventories/dataset_inventory_gon_season_1.json \
-capture_id_field capture_id \
-image_fields image1 image2 image3 \
-label_fields empty species count standing resting moving eating interacting babies empty \
-meta_data_fields season capturetimestamp location split_name

# Parallel Images Writes Species
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_gon_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_species/GON/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-remove_label_name empty \
-remove_label_value empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000

# Parallel Images Writes Empty or Not
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_gon_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_empty_or_not/GON/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-balanced_sampling_min \
-balanced_sampling_label empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000


###############################################
# Niassa
###############################################


cd /home/packerc/shared/machine_learning/will5448/code/camera-trap-classifier
module load python3
source activate ctc

# Create dataset inventory
python create_dataset_inventory.py csv -path /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_export.csv \
-export_path /home/packerc/will5448/data/inventories/dataset_inventory_nia_season_1.json \
-capture_id_field capture_id \
-image_fields image1 image2 image3 \
-label_fields empty species count standing resting moving eating interacting babies empty \
-meta_data_fields season capturetimestamp location split_name

# Parallel Images Writes Species
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_nia_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_species/NIA/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-remove_label_name empty \
-remove_label_value empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000

# Parallel Images Writes Empty or Not
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_nia_season_1.json \
-output_dir /home/packerc/will5448/data/tfr_files/all_empty_or_not/NIA/ \
-image_save_side_max 500 \
-split_by_meta split_name \
-balanced_sampling_min \
-balanced_sampling_label empty \
-image_root_path /home/packerc/shared/albums/ \
-process_images_in_parallel \
-process_images_in_parallel_size 320 \
-processes_images_in_parallel_n_processes 8 \
-max_records_per_file 5000
