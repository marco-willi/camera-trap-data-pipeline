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
