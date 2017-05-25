This directory provides scripts for creating the rotowire and sbnation data

# Python Files
* grab_summaries.py - contains functions scrape_rotowire() and scrape_sbnation() for scraping raw summaries.
* align_summaries.py - contains functions write_intermediate_json(), align_rotowire(), and align_sbnation() for aligning scraped summaries with NBA boxscore data.
* preproc.py - contains functions prep_roto() and prep_sb() for tokenizing, normalizing, and splitting aligned data.
* run_pipeline.py - a convenience script that executes functions from the three files above serially (in the correct order).
* scrape_base.py - used by grab_summaries.py within scrape_sbnation()

# Running
Each script can simply be run as `python <script_name>.py [sbnation]`. If the first (sbnation) argument is left out, or if it is anything other than "sbnation", the script will execute under the rotowire setting.

# Other Files
* nba_sbnation_links.txt - used by scrape_sbnation()
* roto_split_keys.txt - associates unique keys associated with each rotowire summary into one of train, valid, test
* sb_split_keys.txt - associates unique keys associated with each sbnation summary into one of train, valid, test
