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
# scrapy crawl province_laws_34


class ProvinceLaw34Spider(scrapy.Spider):
    name = 'province_laws_34'
    allowed_domains = ['gz.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = "http://www.zj.gov.cn/module/xxgk/search.jsp?standardXxgk=0&isAllList=1&texttype=1&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=b_settop:0,compaltedate:0"

        baseform = "infotypeId=A0203&jdid=3096&area=&divid=div1229498488&vc_title=&vc_number=&sortfield=b_settop:0,compaltedate:0&currpage={}&vc_filenumber=&vc_all=&texttype=1&fbtime=-1&standardXxgk=0&isAllList=1&texttype=1&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=b_settop:0,compaltedate:0"
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.zj.gov.cn'
        header['Referer'] = 'http://www.zj.gov.cn/col/col1545734/index.html'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        header['Cookie'] = "zh_choose_undefined=s; cssstyle=1; ZJYHZXSESSIONID=3cc6ecb7-3717-471e-a3d6-849009fcb451; SERVERID=b2ba659a0bf802d127f2ffc5234eeeba|1652793645|1652793586"
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 14):
            data = baseform.format(str(i), str(i))
            yield scrapy.Request(start_url.format(str(i)), body=data, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        dta_list = response.xpath('//*[@class="zcwj-con-right_list"]/div')
        for item in dta_list:
            tmpurl = item.xpath('./span[1]/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(item.xpath('./span[1]/a/text()').extract_first())
            law_time = tools.clean(item.xpath('./span[contains(@class,"cont_right_from4")]/text()').extract_first())
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "浙江省"
        item["legalCategory"] = "浙江省政府-政府规章"
        item["legalPolicyName"] = response.meta['title']
        item["legalPublishedTime"] = response.meta['time']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@class="zc_article_con"]').extract_first()
            fujian = response.xpath('//*[@class="zc_article_con"]//a/@href').extract()
            fujian_name = response.xpath('//*[@class="zc_article_con"]//a[@href]').xpath('string(.)').extract()

            tmpn = response.xpath('//*[@class="zc_artice_tit1"]').xpath('string(.)').extract_first()
            if tmpn:
                if re.search(r'日([\s\S]+?第[0-9]+号)', tmpn):
                    item["legalDocumentNumber"] = re.search(r'日([\s\S]+?第[0-9]+号)', tmpn).group(1)

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
