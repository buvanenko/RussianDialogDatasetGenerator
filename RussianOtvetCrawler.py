#######################################################################
# Author Name: Fred Glozman
# Author Student ID: 260635610
# University: McGill
# Course: COMP-551: Applied Machine Learning
# Instructor: Joelle Pineau
# Project 1: A multilingual dialogue dataset
# Due Date: September 27th 2017
# Team:     Fred Glozman - fred.glozman@mail.mcgill.ca - 260635610 
#           Raihan Seraj  -raihan.seraj@mail.mcgill.ca - 260752605
#           Oruj Ahmadov - oruj.ahmadov@mail.mcgill.ca - 260523568
#
# Description: This script crawls the Russian forum otvet.i.ua and 
# extracts the Russian human dialogs which it contains.
# Note of warning, the execution runtime is approximately 14 minutes
#
# Instructions: 
# - to run this scrypt, execute the following command in your terminal:
# 
#   scrapy runspider RussianOtvetCrawler.py -o items.json
#
# Pre-reqs: 
# - you must have Scrappy installed on your system. 
#   to do so, run the following command in your terminal:
#
#   pip install scrapy
#
# Result:
# - this script will generate a JSON file titled items.json 
# containing all the dialogs on otvet.i.ua
#######################################################################

# -*- coding: utf-8 -*-
import scrapy
import re

class RussianSpider(scrapy.Spider):
    name = 'russian'
    allowed_domains = ['otvet.i.ua']
    start_urls = ['http://otvet.i.ua/search?_subm=search&words=&type=tags&commID=&userID=&subm=1&sort=popular']

    def clean_utterances(self, utterances):
        cleaned_utterances = []
        for utterance in utterances:
            # remove anchor tags and replace with the url it references in plain text
            pattern =r'<(a|/a).*?>'
            result = re.sub(pattern , "", utterance)

            cleaned_utterances.append(result)
        return cleaned_utterances

    def parse(self, response):
        # visit all posts on the current page
        urls = response.css('body > div.body_container > div.Body.clear > div.Left > div.Wrap > ul.search_result.list_underlined > li > h4 > a::attr(href)').extract()
        for url in urls:
            url = response.urljoin(url)
            yield scrapy.Request(url=url, callback=self.parse_conversation)

        # visit the next page
        next_page_url = response.css('a.forward::attr(href)').extract_first()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_conversation(self, response):
        # username of the creator of the post
        originalSpeaker = response.css('body > div.body_container > div.Body.clear > div.Left > div.Wrap > div.post_container.clear > div.author > p').extract_first()

        # usernames of all responders
        speakers = response.css('body > div.body_container > div.Body.clear > div.Left > div.Wrap > dl.navigation_tabs > dd[id^=page] > div[id=commentsContainer] > div.comments > div.comment_container.clear > div.author > p').extract()

        # title of the post
        title = response.css('body > div.body_container > div.Body.clear > div.Left > div.Wrap > div.post_container.clear > div.post > div.Wrap > div.post_title > h2::text').extract_first()

        # content of the post
        body = response.css('body > div.body_container > div.Body.clear > div.Left > div.Wrap > div.post_container.clear > div.post > div.Wrap > div.entry::text').extract_first()

        # content of all the responses
        comments = response.css('body > div.body_container > div.Body.clear > div.Left > div.Wrap > dl.navigation_tabs > dd[id^=page] > div[id=commentsContainer] > div.comments > div.comment_container.clear > div.post > div.Wrap > p[id^=comment]').extract()
        comments = [re.sub(r'<p id="comment[0-9]+">', '', comment).replace('</p>', '').replace('<br>', '\n') for comment in comments]

        url = response.url
        isFirstPage = not bool(re.search('\?p=[0-9]+', url))
        url = re.sub('\?p=[0-9]+', '', url)

        # all speakers on this page and their corresponding utterances
        speakers = ([originalSpeaker] if isFirstPage else []) + speakers;
        utterances = self.clean_utterances(([title + '\n' + body] if isFirstPage else []) + comments);

        yield { 
            "url": url,
			"speakers": speakers,
        	"utterances": utterances, 
        }

        # visit all pages of the current post
        next_page_url = response.css('body > div.body_container > div.Body.clear > div.Left > div.Wrap > dl.navigation_tabs > dd[id^=page] > div[id=commentsContainer] > div.comments > div.clear.pager > dl > dd > a.arr.forward::attr(href)').extract_first()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse_conversation)