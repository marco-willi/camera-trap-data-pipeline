 # Aggregate Zooniverse Classifications

The following codes aggregate extracted classifications per subject / capture-event and species identification.

The general aggregation logic is as follows:

1. Group / collect all classifications of a specific subject (synonym to a capture event)
2. For each species (incl. blanks) calculate the following stats:
  - how many users identified it (and the proportion of all users)
  - calculate among the users who identified the species the proportions of users who identified a certain characteristic (e.g. 0.9 may identified a 'moving' behavior)
  - calculate among the users who identified the species the median number of counts (round up)
  - characteristics that were not asked for or no user answered are indicated by an empty string: ''
3. Calculate the median over the number of different species identified by each user (round up)
4. Flag the top N species (number of different species identified) with 'species_is_plurality_consensus'. Choose a random species on ties.
5. Export the full dataset including species without consensus, blanks, and additional information.

## Output Fields

| Columns   | Description |
| --------- | ----------- |
|season, roll, site, capture  | internal identifiers of the capture
|subject_id | Zooniverse subject_id (per capture)
|retirement_reason | Zooniverse retirement reason
|retired_at | Zooniverse date when retired
|url1, url2, url3 | Zooniverse image links of the capture
|question__* | Aggregated question answers
|n_users_identified_this_species | Number of users that identified 'question__species'
|p_users_identified_this_species | Proportion of users that identified 'question__species'
|n_species_ids_per_user_median | Median number of different species identified among users for this capture
|n_users_classified_this_subject | Number of users that classified this subject
|species_is_plurality_consensus | Flag indicating a plurality consensus for this species (normally only species with a 1 are relevant)


## Get Zooniverse Subject Data

This is an example to download subject data from Zooniverse. This data can be used to extract useful meta-data for reports.

```
cd $HOME/snapshot_safari_misc
SITE=GRU
SEASON=GRU_S1
PROJECT_ID=5115

# Get Zooniverse Subject Data
python3 -m zooniverse_exports.get_zooniverse_export \
        --password_file ~/keys/passwords.ini \
        --project_id $PROJECT_ID \
        --output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
        --export_type subjects \
        --new_export 0
```      
