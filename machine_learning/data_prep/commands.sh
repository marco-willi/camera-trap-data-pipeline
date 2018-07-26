cd /home/packerc/shared/machine_learning/will5448/code/camera-trap-classifier
module load python3
source activate ctc

python create_dataset_inventory.py csv -path /home/packerc/will5448/data/season_exports/db_export_season_all_cleaned.csv \
-export_path /home/packerc/will5448/data/inventories/dataset_inventory_season_all.json \
-capture_id_field capture_id \
-image_fields image1 image2 image3 \
-label_fields species count standing resting moving eating interacting babies empty \
-meta_data_fields season capturetimestamp


# Serial Writes
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_season_3.json \
-output_dir /home/packerc/will5448/data/tfr_files/s3/ \
-image_save_side_max 500 \
-split_percent 0.9 0.05 0.05 \
-split_names train_s3_species val_s3_species test_s3_species \
-remove_label_name empty \
-remove_label_value 1 \
-image_root_path /home/packerc/shared/albums \
-overwrite


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
-write_tfr_in_parallel \


# Parallel Images Writes
python create_dataset.py -inventory /home/packerc/will5448/data/inventories/dataset_inventory_season_3.json \
-output_dir /home/packerc/will5448/data/tfr_files/s3/ \
-image_save_side_max 500 \
-split_percent 0.9 0.05 0.05 \
-split_names train_s3_species val_s3_species test_s3_species \
-remove_label_name empty \
-remove_label_value 1 \
-image_root_path /home/packerc/shared/albums \
-overwrite \
-process_images_in_parallel \
-process_images_in_parallel_size 100 \
-processes_images_in_parallel_n_processes 4


# Train a model
python train.py \
-train_tfr_path /home/packerc/will5448/data/tfr_files/s2/ \
-train_tfr_pattern train \
-val_tfr_path /home/packerc/will5448/data/tfr_files/s2/ \
-val_tfr_pattern val \
-test_tfr_path /home/packerc/will5448/data/tfr_files/s2/ \
-test_tfr_pattern test \
-class_mapping_json /home/packerc/will5448/data/tfr_files/s2/label_mapping.json \
-run_outputs_dir /home/packerc/will5448/data/run_outputs/ \
-model_save_dir /home/packerc/will5448/data/saves/ \
-model ResNet18 \
-labels species count standing resting moving eating interacting babies \
-batch_size 128 \
-n_cpus 8 \
-n_gpus 2 \
-buffer_size 512 \
-max_epochs 20 \
-starting_epoch 0


# Singularity
singularity exec docker://tensorflow/tensorflow git clone https://github.com/marco-willi/camera-trap-classifier.git
singularity exec docker://tensorflow/tensorflow cd ~/camera-trap-classifier
