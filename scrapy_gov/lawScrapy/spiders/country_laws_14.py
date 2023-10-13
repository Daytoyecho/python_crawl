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
# scrapy crawl country_laws_14


class CountryLaw14Spider(scrapy.Spider):
    name = 'country_laws_14'
    allowed_domains = ['ndrc.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/index_{}.html'
        start_url = ['https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/index.html']

        for i in range(1, 8):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//ul[@class="u-list"]/li/a/@href').extract()
        law_title = response.xpath('//ul[@class="u-list"]/li/a/@title').extract()
        law_time = response.xpath('//ul[@class="u-list"]/li/span/text()').extract()

        for i in range(len(law_url_list)):
            self.count += 1
            print(self.count)
            tmpurl = tools.getpath(law_url_list[i], response.url)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国国家发展和改革委员会"
        item["legalCategory"] = "发改委-发改委令"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'].strip(), "%Y/%m/%d"))

        if re.search(r"\((发.*[0-9]{4}.*)\)", item["legalPolicyName"]):
            item["legalDocumentNumber"] = re.search(r"\((发.*[0-9]{4}.*)\)", item["legalPolicyName"]).group(1)
        elif re.search(r"第[0-9]+号", item["legalPolicyName"]):
            item["legalDocumentNumber"] = "中华人民共和国国家发展和改革委员会令" + re.search(r"(第[0-9]+号)", item["legalPolicyName"]).group(1)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="TRS_Editor"]').extract_first()
            if not content:
                content = response.xpath('//div[contains(@class,"article_con")]').extract_first()

            fujian = response.xpath('//div[@class="TRS_Editor"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="TRS_Editor"]//a[@href]').xpath('string(.)').extract()
            fujian.extend(response.xpath('//div[@class="attachment"]//a/@href').extract())
            fujian_name.extend(response.xpath('//div[@class="attachment"]//a[@href]').xpath('string(.)').extract())

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
