# snapshot_safari_misc
Misc Code for Snapshot Safari

## Get Zooniverse Exports

Download Zooniverse exports. Requires Zooniverse account credentials and
collaborator status with the project.

```
python3 zooniverse_exports/get_zooniverse_export.py -username user \
        -password 1234 \
        -project_id 4715 \
        -output_file classifications.csv \
        -export_type classifications \
        -new_export 0
```


## Extract Zooniverse Classifications

This extracts the relevant fields of a Zooniverse classification file
and creates a csv with one line per annotation. All classifications have to
be from the same workflow with the same workflow version.

```
python3 extract_classifications.py \
        -classification_csv classifications.csv \
        -output_csv classifications_extracted.csv \
        -workflow_id 4655 \
        -workflow_version 304
```


## Aggregate Extracted Zooniverse Classifications

This aggregates the extracted Zooniverse classifications using the
plurality algorithm to get one single label per species detection for each
subject.

```
python3 aggregate_extractions.py \
        -classifications_extracted classifications_extracted.csv \
        -output_csv classifications_aggregated.csv
```
