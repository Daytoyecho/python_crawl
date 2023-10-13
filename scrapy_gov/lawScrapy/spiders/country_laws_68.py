# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import time
import json
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_68


class CountryLaw68Spider(scrapy.Spider):
    name = 'country_laws_68'
    allowed_domains = ['mofcom.gov.cn']
    url_list = []
    count = 0
    wrong = 0

    def start_requests(self):
        base_url = [['http://www.mofcom.gov.cn/article/zqyj/yjzc/yjzcxbb/?{}', 2], ['http://www.mofcom.gov.cn/article/zqyj/yjzc/yjzcnzd/?{}', 6], ['http://www.mofcom.gov.cn/article/zqyj/yjhwh/?{}', 10],
                    ['http://www.mofcom.gov.cn/article/zqyj/yjghbz/?{}', 1], ['http://www.mofcom.gov.cn/article/zqyj/yjbz/?{}', 4], ['http://www.mofcom.gov.cn/article/zqyj/yjqt/?{}', 1]]
        start_url = ['http://www.mofcom.gov.cn/article/zqyj/yjzc/yjzcxbb/', 'http://www.mofcom.gov.cn/article/zqyj/yjzc/yjzcnzd/', 'http://www.mofcom.gov.cn/article/zqyj/yjhwh/',
                     'http://www.mofcom.gov.cn/article/zqyj/yjghbz/', 'http://www.mofcom.gov.cn/article/zqyj/yjbz/', 'http://www.mofcom.gov.cn/article/zqyj/yjqt/']

        for data in base_url:
            for i in range(2, data[1]+1):
                start_url.append(data[0].format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in start_url:
            time.sleep(0.3)
            yield scrapy.Request(i, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//ul[@class="txtList_01"]/li[count(@class)=0]')

        for item in data_list:
            tmpurl = item.xpath('./a[1]/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)

            self.count += 1
            print(self.count)
            law_title = item.xpath('./a[1]/@title').extract_first()
            law_time = item.xpath('./span/text()').extract_first()

            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.redirect, meta={"title": law_title, 'time': law_time}, dont_filter=False, headers=tools.header)

    def redirect(self, response):
        if not re.search(r'}var _cofing1={href:"', response.xpath('//body').extract_first()):
            time.sleep(0.2)
            yield scrapy.Request(response.url, self.parse_article, meta={"title": response.meta['title'], 'time': response.meta['time']}, dont_filter=False, headers=tools.header)
        else:
            tmpurl = re.search(r'}var _cofing1={href:"([^"]+)"', response.xpath('//body').extract_first()).group(1)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": response.meta['title'], 'time': response.meta['time']}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        if re.search(r'/404\.s?htm', response.url):
            self.wrong += 1
            print(self.wrong)
            0/0
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "中华人民共和国商务部"
        item["legalCategory"] = "商务部-征求意见"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = response.meta['time'][:10]

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            rt = response.xpath('//body').extract_first()
            rt = tools.clean(re.sub(r"<[^<>]+?>", "", rt))
            tmpn = ""
            try:
                tmpn = re.search(r"([^号]+?号)", item["legalPolicyName"]).group(1)
                item["legalDocumentNumber"] = tools.clean(tmpn)
            except:
                pass
            if not tmpn:
                try:
                    tmpn = re.search(r"[\[【]发布文号[】\]](.+?号)", rt).group(1)
                    item["legalDocumentNumber"] = tools.clean(tmpn)
                except:
                    pass
            if not tmpn:
                if re.search(r'>[^ICP<>]{1,10}[0-9]{4}[^ICP<>]{1,10}号', response.xpath('//body').extract_first()):
                    tmpn = tools.clean(re.search(r'>([^ICP<>]{1,10}[0-9]{4}[^ICP<>]{1,10}号)', response.xpath('//body').extract_first()).group(1))
                    if not re.search(r'[0-9]{8}', tmpn):
                        item["legalDocumentNumber"] = tools.clean(tmpn)

            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[contains(@class,"art-con")]').extract_first()
            if not fujian:
                fujian = response.xpath('//*[contains(@class,"art-con")]//a/@href').extract()
                fujian_name = response.xpath('//*[contains(@class,"art-con")]//a[@href]').xpath('string(.)').extract()
            if not fujian:
                fujian = response.xpath('//*[@class="TRS_Editor"]//a/@href').extract()
                fujian_name = response.xpath('//*[@class="TRS_Editor"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = re.search(r'<!\-\-文章正文\-\->([\s\S]+?)<script', response.xpath('//body').extract_first()).group(1)

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
