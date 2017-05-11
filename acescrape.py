from bs4 import BeautifulSoup
import urllib.request
from re import findall
from flask import Flask
from flask import render_template
import time
import scrapy

tagline = "Scraping only the finest data"

app = Flask(__name__)
title = 'AceScrape'

year = time.strftime("%Y")


class ScrapeSite:

    def __init__(self, url):
        self.url = url
        self.data = urllib.request.urlopen(url)
        self.soup = BeautifulSoup(self.data)
        self.body = self.soup.get_text()

    def regex(self, string):
        return findall(string, self.body)


class Reddit(ScrapeSite):
    """
    Scraper for Reddit
    """

    def __init__(self):
        ScrapeSite.__init__(self, 'http://www.reddit.com')

    # Walks through subreddits and returns a dictionary 
    # with the subs and how many of each are on the front page
    # "raw" flag for debugging
    def subreddits(self, raw=False):
        subreddits_search = self.soup.find_all(
            "a", class_="subreddit hover may-blank")
        subreddits_regex = findall(r'r\/[a-z]+', str(subreddits_search))
        subreddits_seen = set(subreddits_regex)
        subreddits = {}

        for items in subreddits_seen:
            subreddits[items] = 0

        for items in subreddits_regex:
            if items in subreddits:
                subreddits[items] += 1

        if raw is False:
            return subreddits
        else:
            return subreddits_regex

    # Calculates exactly how cute the front page of Reddit is, based on the
    # number of /r/aww submissions that are present
    def cuteness_index(self):
        cuteness_finder = 0
        subreddits = self.subreddits()
        for items in subreddits:
            if 'aww' in items:
                cuteness_finder = subreddits[items]

        return cuteness_finder

    def cuteness(self, level):
        cuteness_levels = [
            'Filthy sloth.', 'Excited corgi!', 'Kitten euphoria!!!']
        return cuteness_levels[level]

    # Returns all of the images that are currently on the front page
    def images(self):
        return self.soup.find_all("a", class_="thumbnail")


class TechCrunch(ScrapeSite):
    """
    Scraper for TechCrunch
    """

    def __init__(self):
        ScrapeSite.__init__(self, 'http://www.techcrunch.com')

    # Number of times VCs are mentioned on TC's front page
    def VCs(self):
        vc_word_search = self.regex(r'(?:VC[s]?|[Vv]enture [Cc]apital[ist]?)')
        return len(vc_word_search)

    # Measures how disruptive, innovative and/or Twittergasmic TC is at the
    # time
    def disruption(self, level):
        disruption_levels = [
            '2014 MySpace.', 'Getting Googley!', 'Twittergasm!!!']
        return disruption_levels[level]

    # Shows who is getting articles published on the front page of TC
    def writers(self, raw=False):
        writers_regex = self.soup.find_all('a', {"rel": "author"})
        writers_list = []
        writers_seen = set()

        for authors in writers_regex:
            writers_list.append(authors.get_text())
            writers_seen.add((authors.get_text(), authors.get('href')))

        writers = {}

        for authors in writers_seen:
            writers[authors] = 0

        for authors in writers_regex:
            if authors.get_text() in writers_list:
                writers[authors.get_text(), authors.get('href')] += 1

        if raw is False:
            return writers

        else:
            return writers_regex


class WaBar(scrapy.Spider):
    name = "barSpider"
    
    
    
    def start_requests(self):
        crawl_limit = 10
        y = 0 
        crawl_counter = 0
        for x in range(0, crawl_limit):
            y = y +1
            url = 'https://www.mywsba.org/LawyerDirectory/LawyerProfile.aspx?Usr_ID={0}'.format(y)
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        for lawyer in response.css('#content-left'):
            yield {
                'name': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblMemberName::text').extract_first(),
                'admitted': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblAdmitDate::text').extract_first(),
                'status': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblStatus::text').extract_first(),
                'addresss': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblAddress::text').extract_first(),
                'phone': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblPhone::text').extract_first(),
                'TDD:' : lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblTDD::text').extract_first(),
                'email' : lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblEmail::text').extract_first(),
                'website' : lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_hlWebsite::text').extract_first(),
                'practice areas': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblPracticeAreas::text').extract_first(),
                'private practice': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblPrivatePractice::text').extract_first(),
                'has insurance?': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblHasInsurance::text').extract_first(),
                'languages': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblLanguages::text').extract_first(),
                'memberships': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblCommittees::text').extract_first(),
                'discipline': lawyer.css('#dnn_ctr671_MyWSBA_LawyerProfile_lblNodiscipline::text').extract_first(),
            }

# Instances
RedditScraper = Reddit()
TCScraper = TechCrunch()
BMScraper = BloombergMarkets()


@app.context_processor
def site_info():
    return {'title': title, 'tagline': tagline, 'year': year}


@app.route('/')
def front_page():
    return render_template('index.html',
                           subreddits=RedditScraper.subreddits(),
                           images=RedditScraper.images(),
                           VCs=TCScraper.VCs(),
                           disruption_levels=TCScraper.disruption,
                           cuteness_levels=RedditScraper.cuteness,
                           cuteness_index=RedditScraper.cuteness_index(),
                           writers=TCScraper.writers())


@app.route('/finance')
def finance_page():
    return render_template('finance.html',
                           stock_markets=BMScraper.lawyer('name'),
                           futures=BMScraper.lawyer('admitted'),
                           currencies=BMScraper.lawyer('status'))

if __name__ == '__main__':
    app.run(debug=True)
