# -*- coding:utf-8 -*-
from copy import deepcopy
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl province_laws_68


class ProvinceLaw68Spider(scrapy.Spider):
    name = 'province_laws_68'
    allowed_domains = ['fujian.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://kjt.fujian.gov.cn/was5/web/search?channelid=229105&templet=advsch.jsp&sortfield=-pubdate&classsql=docpuburl%3D%27%25http%3A%2F%2Fkjt.fujian.gov.cn%2Fxxgk%2Fzfxxgkzl%2Fzfxxgkml%2F%25%27&prepage=100&page={}"

        header = deepcopy(tools.header)
        header['Referer'] = 'http://kjt.fujian.gov.cn/xxgk/zfxxgkzl/zfxxgkml/'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 83):
            time.sleep(2)
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary,  dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        time.sleep(5)
        text = re.sub(r'<br>\n', '', response.text)
        text = re.sub(r'[^, {\[\}]\n', '', text)
        text = re.sub(r'	', '', text)
        data = json.loads(text, strict=False)['docs']
        for item in data:
            tmpurl = item["url"]
            law_title = item["title"]
            if law_title == "文章标题":
                continue
            law_time = item["pubtime"][:10]
            law_number = item["fileno"]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "福建省"
        item["legalCategory"] = "福建省科学技术厅-公开内容"
        item["legalPolicyName"] = tools.clean(response.meta['title'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            tim = ""
            try:
                tim = response.xpath('//p[@class="fl"]/text()').extract_first()
                if tim:
                    tim = re.search("发布时间：([0-9]{4}-[0-9]{2}-[0-9]{2})", tim).group(1)
                    item["legalPublishedTime"] = tim
                else:
                    tim = response.xpath('//*[@class="xl_tit6_l"]/span/text()').extract_first()
                    tim = re.search("([0-9]{4}-[0-9]{2}-[0-9]{2})", tim).group(1)
                    item["legalPublishedTime"] = tim
            except:
                pass
            try:
                if not tim:
                    tim = response.xpath('//*[contains(@class,"article_time")]/text()').extract_first()
                    tim = re.search("([0-9]{4}-[0-9]{2}-[0-9]{2})", tim).group(1)
                    item["legalPublishedTime"] = tim
            except:
                pass
            if not tim:
                tim = response.xpath('//*[@id="conter"]').extract_first()
                tim = re.search(r"时间：[ ]*([0-9]{4}-[0-9]{2}-[0-9]{2})", tim).group(1)
                item["legalPublishedTime"] = tim
            content = response.xpath('//div[@class="TRS_Editor"]').extract_first()
            fujian = response.xpath('//*[@id="conter"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="conter")]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[contains(@class,"tit_ml_BOx")]').extract_first()
                fujian = response.xpath('//*[contains(@class,"tit_ml_BOx")]//a/@href').extract()
                fujian_name = response.xpath('//*[contains(@class,"tit_ml_BOx")]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//div[contains(@id,"detailCont")]').extract_first()
                fujian = response.xpath('//div[contains(@id,"detailCont")]//a/@href').extract()
                fujian_name = response.xpath('//div[contains(@id,"detailCont")]//a[@href]').xpath('string(.)').extract()
            wenhao = tools.clean(response.meta["number"])
            if wenhao:
                item["legalDocumentNumber"] = wenhao

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
