# -*- coding:utf-8 -*-
'''
中国证券监督管理委员会
证监会-政策
'''
import scrapy
import datetime
from lawScrapy.items import LawscrapyItem
import re
import pdfkit
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools

# scrapy crawl country_laws_99

header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,rw;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36'
}


class CountryLaw99Spider(scrapy.Spider):
    name = 'country_laws_99'
    allowed_domains = ['csrc.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = 'http://www.csrc.gov.cn/searchList/d5c69b3f67334ed984a43e864f42f1ab?_isAgg=true&_isJson=true&_pageSize=10&_template=index&_rangeTimeGte=&_channelName=&page={}'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 10):
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['data']['results']

        for i in data_list:

            law_url = i['url']
            law_title = i['title']
            law_subtitle = i['subTitle']
            law_url = tools.getpath(law_url, response.url)
            self.count += 1
            print(self.count)
            if law_url not in self.url_list:
                yield scrapy.Request(law_url, self.parse_article, meta={"title": law_title, "time": law_subtitle}, dont_filter=False)

    def parse_article(self, response):

        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "中国证券监督管理委员会"
        item["legalCategory"] = "证监会-政策"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = re.search(r'[（\(]([^"]{8,12}日)', response.meta['time']).group(1)
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(item["legalPublishedTime"], "%Y年%m月%d日"))
        item["legalDocumentNumber"] = re.search(r'日([\S\s]+?)公', response.meta['time']).group(1)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)

        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = response.xpath('//div[@class="content-body"]').extract_first()
            fujian = response.xpath('//div[@class="content-body"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="content-body"]//a[@href]').xpath('string(.)').extract()

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
