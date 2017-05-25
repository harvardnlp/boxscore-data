import os, sys
import datetime
import urllib2
import codecs
import subprocess


def scrape_rotowire():
    try:
        os.makedirs("rotowire_raw")
    except OSError as ex:
        if "File exists" in ex:
            print ex
        else:
            raise ex

    start_day = datetime.date(2014, 1, 1)
    day = datetime.date(2017, 3, 29)

    while day >= start_day:
        url = "http://www.rotowire.com/basketball/game-recaps.htm?date=%s" % day.strftime("%m/%d/%Y")
        response = urllib2.urlopen(url)
        html = response.read().decode('utf-8', 'ignore')
        with codecs.open("rotowire_raw/games_%s" % day.strftime("%m_%d_%y"), "w+", "utf-8") as f:
            f.write(html)
        day = day - datetime.timedelta(days=1)

def scrape_sbnation():
    subprocess.call("scrapy runspider scrape_base.py -o sbnba.json --logfile sbnba.log", shell=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sbnation":
        scrape_sbnation()
    else:
        scrape_rotowire()
