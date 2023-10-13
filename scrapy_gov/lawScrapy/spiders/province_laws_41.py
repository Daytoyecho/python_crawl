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
# scrapy crawl province_laws_41


class ProvinceLaw41Spider(scrapy.Spider):
    name = 'province_laws_41'
    allowed_domains = ['gz.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = "https://www.zj.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=363&perpage=363"

        baseform = "col=1&appid=1&webid=3096&path=%2F&columnid=1229019366&sourceContentType=3&unitid=7509171&webname=%E6%B5%99%E6%B1%9F%E7%9C%81%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C%E9%97%A8%E6%88%B7%E7%BD%91%E7%AB%99&permissiontype=0"
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.zj.gov.cn'
        header['Referer'] = 'http://www.zj.gov.cn/col/col1229093915/index.html'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        header['Cookie'] = "JSESSIONID=F1914D227DC82D6FECB633F43251DA2F; zh_choose_undefined=s; cssstyle=1; ZJYHZXSESSIONID=868061f1-6672-4277-b20c-df52b63f1ed5; session=4104b08deaef4f178a83b45cab729909; cna=wqcKG0usFUoCAf////8f+UNu; SERVERID=b2ba659a0bf802d127f2ffc5234eeeba|1652800150|1652793586"
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        yield scrapy.Request(start_url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        law_url_list = re.findall('href="([^"]+?)"', response.text)
        law_title_list = re.findall('<a title="([^"]+?)"', response.text)
        law_time_list = re.findall('</a><b>([^<>]+?)</b>', response.text)
        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            law_time = tools.clean(law_time_list[i])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "浙江省"
        item["legalCategory"] = "浙江省政府-政策解读"
        item["legalPolicyName"] = response.meta['title']
        item["legalPublishedTime"] = response.meta['time']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            if response.xpath('//*[@class="xxgk-info-wh"]/td/text()').extract_first():
                item["legalDocumentNumber"] = tools.clean(response.xpath('//*[@class="xxgk-info-wh"]/td/text()').extract_first())

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
