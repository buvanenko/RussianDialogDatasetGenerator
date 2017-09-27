#######################################################################
# Author Name: Oruj Ahmadov, Fred Glozman
# Author Student ID: 260523568, 260635610
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
#   scrapy runspider RussianRususaCrawler.py -o items.json
#
# Pre-reqs: 
# - you must have Scrappy and language-detector installed on your 
# system. To do so, run the following command in your terminal:
#
#   pip install scrapy
#   pip install language-detector
#
# Result:
# - this script will generate a JSON file titled items.json 
# containing all the dialogs on otvet.i.ua. 
# And the same content formated as an XML file.
#######################################################################
 
import scrapy
import re
from language_detector import detect_language

class RussianSpider(scrapy.Spider):
    name = 'russian'
    allowed_domains = ['rususa.com']
    start_urls = ['http://www.rususa.com/forum/forum.asp-forumid-22','http://www.rususa.com/forum/forum.asp-forumid-57','http://www.rususa.com/forum/forum.asp-forumid-52','http://www.rususa.com/forum/forum.asp-forumid-60','http://www.rususa.com/forum/forum.asp-forumid-36','http://www.rususa.com/forum/forum.asp-forumid-92786','http://www.rususa.com/forum/forum.asp-forumid-93444','http://ru.rususa.com/forum/forum.asp-forumid-188','http://ru.rususa.com/forum/forum.asp-forumid-77','http://ru.rususa.com/forum/forum.asp-forumid-59','http://ru.rususa.com/forum/forum.asp-forumid-73','http://ru.rususa.com/forum/forum.asp-forumid-191','http://ru.rususa.com/forum/forum.asp-forumid-74','http://ru.rususa.com/forum/forum.asp-forumid-54','http://ru.rususa.com/forum/forum.asp-forumid-75','http://www.rususa.com/forum/forum.asp-forumid-34', 'http://ru.rususa.com/forum/forum.asp-forumid-55', 'http://ru.rususa.com/forum/forum.asp-forumid-6559']

    speakers_dict = {}
    speaker_uuid = 6985
    text_file = open("output.txt", "w")
    pager = 2

    def clean_utterance(self, utterance):
        cleaned_utterance = re.sub(r"\r\n", " ", utterance)
        cleaned_utterance = cleaned_utterance.encode('utf-8')
        cleaned_utterance = re.sub(r'\&', '&amp;', cleaned_utterance)
        cleaned_utterance = re.sub(r'\<', '&lt;', cleaned_utterance)
        cleaned_utterance = re.sub(r'\>', '&gt;', cleaned_utterance)
        cleaned_utterance = re.sub(r'\"', '&apos;', cleaned_utterance)
        cleaned_utterance = re.sub(r'\"', '&quot;', cleaned_utterance)
        return cleaned_utterance

    def generate_uid(self, speaker_name):
        if (speaker_name in self.speakers_dict):
            return self.speakers_dict[speaker_name]
        else:
            self.speaker_uuid+=1
            self.speakers_dict[speaker_name] = self.speaker_uuid

        return self.speaker_uuid

    def parse(self, response):
        # visit all posts on the current page
        urls = response.css('body > div.container > div.menu_border > form.flatForm > table > tr > td > a::attr(href)').extract()
        # Create output text file to dump results into
        self.text_file = open("output.txt", "w")
        for url in urls:
            url = response.urljoin(url)
            yield scrapy.Request(url=url, callback=self.parse_conversation)

    def parse_conversation(self, response):
        speakers = response.css('body > div.container > div.msgBlock > table > tr > td > b').extract()
        utterances = filter(lambda x: x!='\r' and '[Message edited by' not in x, response.css('td[id=post]::text').extract())
        clean_utterances_count = 0
        # Check if conversation contains more than 1 utterance
        if (len(utterances) > 1):
            corpus ="<s>"
            for index in range(len(speakers)):
                parsed_clean_utterance = self.clean_utterance(utterances[index])
                # Check if utterance is not empty
                if (parsed_clean_utterance.isspace() is False):
                    # Check utterance language
                    if detect_language(parsed_clean_utterance) != 'English':
                        clean_utterances_count+=1
                        corpus+='<utt uid="' + str(self.generate_uid(speakers[index])) + '">' + parsed_clean_utterance + '</utt>'
            if (clean_utterances_count > 1):
                corpus+="</s>\n"
                self.text_file.write(corpus)

        # Visit all pages of the current post
        next_page_urls = response.css('body > div.container > div.msgBlock > table > tr.msgHeader > td > div.fnavhead > div.fnavnum > a::attr(href)').extract()
        for next_url in next_page_urls:
            next_url = response.urljoin(next_url)
            yield scrapy.Request(url=next_url, callback=self.parse_conversation)
