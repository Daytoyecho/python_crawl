# -*- coding:utf-8 -*-
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
# scrapy crawl province_laws_148


class ProvinceLaw148Spider(scrapy.Spider):
    name = 'province_laws_148'
    allowed_domains = ['gzrd.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://www.gzrd.gov.cn/dffg/zztldxtl/index_{}.shtml"
        start_url = ['http://www.gzrd.gov.cn/dffg/zztldxtl/index.shtml']

        for i in range(2, 13):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="list-box"]//li/a/@href').extract()
        law_title = response.xpath('//div[@class="list-box"]//li/a/@title').extract()
        law_time = response.xpath('//div[@class="list-box"]//li/span/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "贵州省"
        item["legalCategory"] = "贵州省政府-自治条例单行条例"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="Zoom"]').extract_first()
            fujian = response.xpath('//*[@id="Zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="Zoom"]//a[@href]').xpath('string(.)').extract()

            # 处理文号(绝大部分都没有文号)
            wenhao = response.xpath('//div[@class="content-box"]/div[1]//text()').extract()
            if len(wenhao):
                for i in range(len(wenhao)):
                    if re.search(r'(黔.*?[0-9]{0,4}.*?号)', wenhao[i]):
                        item["legalDocumentNumber"] = re.search(r'(黔.*?[0-9]{0,4}.*?号)', wenhao[i]).group(1)
                    else:
                        item["legalDocumentNumber"] = ""
            else:
                item["legalDocumentNumber"] = ""

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
