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
# scrapy crawl province_laws_42


class ProvinceLaw42Spider(scrapy.Spider):
    name = 'province_laws_42'
    allowed_domains = ['hangzhou.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = "http://www.hangzhou.gov.cn/module/xxgk/xxgk_rulebase_search.jsp?q=&xxgkjd=&searchfields=0&currpage={}"

        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.hangzhou.gov.cn'
        header['Referer'] = 'http://www.hangzhou.gov.cn/module/xxgk/xxgk_rulebase_search.jsp?xxgkjd='

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 10):
            time.sleep(0.2)
            yield scrapy.Request(start_url.format(str(i)), body="", method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//div[@class="zc_list"]//tbody/tr/td[2]')

        for item in data_list:
            tmpurl = item.xpath("./a/@href").extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath("./a/text()").extract_first()
            text = tools.clean(item.xpath("./p/text()").extract_first())
            law_time = re.search("[（\(]([\S]+?日)", text).group(1)
            law_number = re.search("[（\(][\S]+?日([\S]+?号)", text).group(1)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "杭州市"
        item["legalCategory"] = "杭州市政府-政府规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'], "%Y年%m月%d日"))
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@class="zc_article_con"]').extract_first()
            fujian = response.xpath('//*[@class="zc_article_con"]//a/@href').extract()
            fujian_name = response.xpath('//*[@class="zc_article_con"]//a[@href]').xpath('string(.)').extract()
            content = re.sub(r'<div class="zc_artice_tit">[^<>]+?</div>', '', content)

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
