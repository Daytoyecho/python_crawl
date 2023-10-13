# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_3


class CountryLaw3Spider(scrapy.Spider):
    name = 'country_laws_3'
    allowed_domains = ['court.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = ['http://www.court.gov.cn/fabu-gengduo-16.html']

        res = appbk_sql.mysql_com("SELECT legalUrl FROM `law`")
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="sec_list"]/ul/li/a/@href').extract()
        law_title = response.xpath('//div[@class="sec_list"]/ul/li/a/@title').extract()
        law_time = response.xpath('//div[@class="sec_list"]/ul/li/i/text()').extract()
        for i in range(len(law_url_list)):
            self.count += 1
            print(self.count)
            tmpurl = tools.getpath(law_url_list[i], response.url)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

        next_url = response.xpath('//li[@class="next"]/a/@href').extract_first()
        if next_url:
            yield scrapy.Request(tools.getpath(next_url, response.url), self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国最高人民法院"
        item["legalCategory"] = "最高院-权威发布司法解释"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="txt big"]').extract_first()

            if re.search(r'(法[^<]{0,3}〔[0-9]{4}〕[^<]{0,4}号)', re.sub(r'<[^>]+>', r'', content).replace(' ', '').replace('\n', '')):
                item["legalDocumentNumber"] = re.search(r'(法[^<]{0,3}〔[0-9]{4}〕[^<]{0,4}号)', re.sub(r'<[^>]+>', r'', content).replace(' ', '').replace('\n', '')).group(1)
            elif re.search(r'>([^>]{0,4}发[^<]{0,2}〔[0-9]{4}〕[^<]{0,4}号)', content.replace(" ", "")):
                item["legalDocumentNumber"] = re.search(r'>([^>]{0,4}发[^<]{0,2}〔[0-9]{4}〕[^<]{0,4}号)', content.replace(" ", "")).group(1)

            fujian = response.xpath('//div[@class="txt big"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="txt big"]//a[@href]').xpath('string(.)').extract()

            item['legalContent'] = content
            tools.xaizaizw(item["legalPolicyName"], item["legalProvince"], item["legalPublishedTime"], content, pdf_name, response.url)
        else:
            tools.xaizai_not_html_zw(pdf_name, response.body)
        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        legal_enclosure, legal_enclosure_name, legal_enclosure_url = tools.xaizaifujian(fujian, fujian_name, item["legalPolicyName"], response.url)
        if legal_enclosure != "[]":
            item["legalEnclosure"] = legal_enclosure
            item["legalEnclosureName"] = legal_enclosure_name
            item["legalEnclosureUrl"] = legal_enclosure_url
        item['legalScrapyTime'] = tools.getnowtime()
        return item
