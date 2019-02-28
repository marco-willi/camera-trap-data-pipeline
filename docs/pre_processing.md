# Pre-Processing Camera-Trap Images

The following codes can be used to:

1. Process and check camera trap images
2. Inspect potential issues to resolve/waive them
3. Obtain a cleaned inventory of the processed camera trap images
4. Re-name all images


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
- site_directory: alphanumeric
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
--root_dir /home/packerc/shared/albums/ENO/ENO_S1/ \
--log_dir /home/packerc/shared/season_captures/ENO/captures/
```

A log file will be created in 'log-dir' if 'log-dir' is specified.


## Create Input Inventory

The following script generates an inventory of all camera trap images and performs some basic checks. The code is parallelized to speed up the checks -- use the following options to make the most of the parallelization:

```
ssh lab
qsub -I -l walltime=2:00:00,nodes=1:ppn=16,mem=16gb
```

Then run the code:
```
python3 -m pre_processing.create_input_inventory_parallel \
--root_dir /home/packerc/shared/albums/ENO/ENO_S1/ \
--output_csv /home/packerc/shared/season_captures/ENO/captures/ENO_S1_captures_raw.csv \
--n_processes 16
```

The idea is to directly run the next code.

## Group Images into Captures

The following script groups the images into capture events.

```
python3 -m pre_processing.group_inventory_into_captures \
--input_inventory /home/packerc/shared/season_captures/ENO/captures/ENO_S1_captures_raw.csv \
--output_csv /home/packerc/shared/season_captures/ENO/captures/ENO_S1_captures_grouped.csv
```

## Export Potential Issues -- in development

The following script updates the grouped_inventory, and creates a csv with all images that have a potential issue. Optinally, a timeseries plot can be generated for the number of captures over time for each roll to find suspicious patterns.

```
python3 -m pre_processing.export_checks_for_inspection \
--inventory_grouped /home/packerc/shared/season_captures/ENO/captures/ENO_S1_captures_grouped.csv \
--issues_csv /home/packerc/shared/season_captures/ENO/captures/ENO_S1_potential_issues.csv \
--no_older_than_year 2017 \
--no_newer_than_year 2019 \
--plot_timelines
```
