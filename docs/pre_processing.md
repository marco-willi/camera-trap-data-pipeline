# Pre-Processing Camera-Trap Images

The following codes can be used to:

1. Process and check camera trap images
2. Inspect potential issues to resolve/waive them
3. Obtain an inventory of the processed camera trap images


## Check Import/Directory Structure

The camera trap images to be imported need to be organized according to the following directory structure:

```
root_directory/
  site_directory/
    roll_directory/
      image_files
```

Definitions:
- Site: A specific camera/location.
- Roll: An SD card of a specific location (data from a camera check).

The naming has to adhere to these standards:
- site_directory: alphanumeric followed by two digits, e.g., A01
- roll_directory: site name, followed by 'RX', e.g., A01_R1 (first roll of A01)
- Images: arbitrary names

```
root_directory/
  A01/
    A01_R1/
      *.JPG
```   

The check can be performed using the following script:
```
python3 -m pre_processing.check_input_structure \
--root_dir /home/packerc/shared/albums/ENO/ENO_S1/
```


## Create Input Inventory

The following script generates a inventory of all camera trap images and performs some basic checks. The code is parallelized to speed up the checks -- use the following options to make the most of the parallelization:

```
ssh lab
qsub -I -l walltime=2:00:00,nodes=1:ppn=16,mem=16gb
```

Then run the code:
```
python3 -m pre_processing.create_input_inventory_parallel \
--root_dir /home/packerc/shared/albums/ENO/ENO_S1/ \
--output_csv /home/packerc/shared/season_captures/ENO/ENO_S1_captures_raw.csv \
--n_processes 16
```

## Group Images into Captures -- in developemnt

The following script groups the images into capture events.

```
python3 -m pre_processing.group_inventory_into_captures \
--input_inventory /home/packerc/shared/season_captures/ENO/ENO_S1_captures_raw.csv \
--output_csv /home/packerc/shared/season_captures/ENO/ENO_S1_captures_grouped.csv
```
