cd /home/packerc/shared/machine_learning/will5448/code/camera-trap-classifier
source activate ctc

python create_dataset_inventory.py csv -path /home/packerc/will5448/test_export_season_1_cleaned.csv \
-export_path /home/packerc/will5448/dataset_inventory_s1.json \
-capture_id_field capture_id \
-image_fields image1 image2 image3 \
-label_fields species count standing resting moving eating interacting babies empty \
-meta_data_fields season capturetimestamp


python create_dataset.py -inventory /home/packerc/will5448/dataset_inventory_s1.json \
-output_dir /home/packerc/will5448/tfr_files/ \
-image_save_side_max 500 \
-split_percent 0.9 0.05 0.05 \
-split_names train_s1 val_s1 test_s1 \
-remove_label_name empty \
-remove_label_value 1 \
-image_root_path /home/packerc/shared/albums \
-max_records_per_file 100000 \
-overwrite
