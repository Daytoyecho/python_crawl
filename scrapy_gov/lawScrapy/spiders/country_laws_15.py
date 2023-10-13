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
# scrapy crawl country_laws_15


class CountryLaw15Spider(scrapy.Spider):
    name = 'country_laws_15'
    allowed_domains = ['most.gov.cn']
    url_list = []
    count = 0
    wrong = 0

    def start_requests(self):
        base = 'http://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/fgzc/gfxwj/index_{}.html'
        start_url = ['http://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/fgzc/gfxwj/index.html']

        for i in range(1, 46):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_list = response.xpath('//ul[@id="data_list"]/li')
        for i in law_list:
            self.count += 1
            print(self.count)
            tmpurl = i.xpath('./a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)

            title = i.xpath('./a/@title').extract_first()
            time = i.xpath('./div[@class="list-main-li-item tac w_list_rq"]/text()').extract_first()
            number = i.xpath('./div[@class="list-main-li-item tac w_list_fwzh"]/text()').extract_first()

            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": title, "time": time, "number": number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        if re.search(r'/404\.', response.url) or response.url == "http://www.most.gov.cn/index.html":
            print("页面不存在")
            self.wrong += 1
            print("*****", self.wrong, "*****")
            0/0

        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国科学技术部"
        item["legalCategory"] = "科学技术部-法规政策规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'].strip(), "%Y年%m月%d日"))

        if response.meta['number']:
            item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="Zoom"]').extract_first()
            # if not content:
            #     content = response.xpath('//*[contains(@class,"article_con")]').extract_first()

            fujian = response.xpath('//*[@class="xxgk_detail_content"]//a/@href').extract()
            fujian_name = response.xpath('//*[@class="xxgk_detail_content"]//a[@href]').xpath('string(.)').extract()

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
