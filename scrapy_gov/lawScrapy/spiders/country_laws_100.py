# -*- coding:utf-8 -*-
'''
中国证券监督管理委员会
证监会-监管规则适用指引
'''
import scrapy
import datetime
from lawScrapy.items import LawscrapyItem
import re
import pdfkit
import json
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools

# scrapy crawl country_laws_100

header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,rw;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36'
}


class CountryLaw100Spider(scrapy.Spider):
    name = 'country_laws_100'
    allowed_domains = ['csrc.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = 'http://www.csrc.gov.cn/searchList/a646cc4ea60542d081bd38eab9494c92?_isAgg=true&_isJson=true&_pageSize=10&_template=index&_rangeTimeGte=&_channelName=&page={}'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 3):
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['data']['results']

        for i in data_list:

            law_url = i['url']
            law_title = i['title']
            law_time = i['publishedTimeStr']
            law_url = tools.getpath(law_url, response.url)
            self.count += 1
            print(self.count)
            if law_url not in self.url_list:
                yield scrapy.Request(law_url, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "中国证券监督管理委员会"
        item["legalCategory"] = "证监会-监管规则适用指引"

        item["legalPolicyName"] = response.meta['title'].replace('\n', '').replace('\t', '').replace('&nbsp;', ' ')
        item["legalPublishedTime"] = response.meta['time'][:10]
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)

        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            #########文章正文的html，附件，和附件名字#########################
            content = response.xpath('//div[@class="detail-news"]').extract_first()
            fujian = response.xpath('//div[@class="detail-news"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="detail-news"]//a[@href]').xpath('string(.)').extract()
            # -------------------------------------------------------------#

            #########如果时间或者文号需要用到xpath或者re，请放到这儿来#########

            # -------------------------------------------------------------#

            content = re.sub(r'<div class="xxgk-down-box">[\s\S]+?<div class="clear"></div>[\s\S]+?</div>', r"",
                             content, flags=re.I)

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
