import sys
from grab_summaries import scrape_sbnation, scrape_rotowire
from align_summaries import align_sbnation, write_intermediate_json, align_rotowire
from preproc import prep_sb, prep_roto

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sbnation":
        scrape_sbnation()
        align_sbnation()
        prep_sb()
    else:
        scrape_rotowire()
        write_intermediate_json("rotowire_raw")
        align_rotowire()
        prep_roto()
