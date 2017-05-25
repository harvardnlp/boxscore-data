## for scraping sb nation nba summaries

import datetime
import requests
import scrapy
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import timedelta
import re

ls = []
for l in open("nba_sbnation_links.txt"):
    pieces = l.strip().split("|")
    team, urls = pieces[0], pieces[1]
    urls = urls.split(",")
    if int(pieces[2]) > 0:
        for url in urls:
            for i in range(200):
                ls += [(team, url + ("/%d"%i), False)]
    else: # need more i think
        for url in urls:
            for i in range(600):
                ls += [(team, url + ("/%d"%i), True)]

score_patt = re.compile('(\d\d\d?)-(\d\d\d?)')

def high_prec_recap_title(s):
    if "Recap" in s:
        return True
    scores = score_patt.match(s)
    # i assume there are rarely games w/ < 70 pts
    if len(scores.groups()) == 2 and int(scores.groups()[0]) >= 70 and int(scores.groups()[1]) >= 70:
        return True
    return False

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = ls
    # [
    #     "http://www.pinstripealley.com/yankees-scores-game-recaps/archives/%d"%(i)
    #     #"http://www.federalbaseball.com/washington-nationals-game-recaps/archives/%d"%(i)
    #     for i in range(200)
    # ]
    def request(self, url, callback, meta={}):
        """
        wrapper for scrapy.request
        """
        request = scrapy.Request(url=url, callback=callback, meta=meta)
        request.cookies['over18'] = 1
        request.headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, '
            'like Gecko) Chrome/45.0.2454.85 Safari/537.36')
        return request

    def start_requests(self):
        for i, (team, url, tofilter) in enumerate(self.start_urls):
            yield self.request(url, self.parse, {"team": team, "tofilter": tofilter})

    def parse(self, response):
        for link in response.css('div.m-block__body'):
            next_page = link.css('a::attr("href")').extract_first()
            if not response.meta["tofilter"]: # from a recap-specific link
                yield self.request(next_page, callback=self.parse_game, meta=response.meta)
            else: # from a general archive
                utitle = link.css('a::text').extract_first()
                if high_prec_recap_title(utitle):
                    yield self.request(next_page, callback=self.parse_game, meta=response.meta)

    def parse_game(self, response):
        soup = BeautifulSoup(response.css('div.c-entry-content').extract_first())
        [x.extract() for x in soup.findAll('script')]
        datestring = BeautifulSoup(response.css('time.c-byline__item').extract_first()).get_text().strip()
        dt = parser.parse(datestring)
        if dt.hour < 12:
            dt = dt - timedelta(days=1)
        yield {"title": BeautifulSoup(response.css('h1.c-page-title').extract_first()).get_text().strip(),
               "team": response.meta["team"],
               "datestring": datestring,
               "date" : (dt.year, dt.month, dt.day),
               "content": soup.get_text()}
