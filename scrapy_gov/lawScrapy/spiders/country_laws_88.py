from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from selenium import webdriver
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
seleniumLogger.setLevel(logging.WARNING)
option = webdriver.ChromeOptions()
option.add_argument('headless')
option.add_experimental_option('excludeSwitches', ['enable-logging'])
option.add_argument('--no-sandbox')
option.add_argument('--disable-dev-shm-usage')
# scrapy crawl country_laws_88


class CountryLaw88Spider(scrapy.Spider):
    name = 'country_laws_88'
    allowed_domains = ['mee.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'https://www.mee.gov.cn/zcwj/zcjd/index_{}.shtml'
        start_url = ['https://www.mee.gov.cn/zcwj/zcjd/index.shtml']

        for i in range(1, 23):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "https://www.mee.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        driver = webdriver.Chrome(chrome_options=option)
        driver.get(response.url)
        law_url_list = []
        law_title = []
        law_time = []
        for i in driver.find_elements_by_xpath('//div[@class="bd mobile_list"]//ul//li/a'):
            law_url_list.append(i.get_attribute('href'))
            law_title.append(i.text)

        for i in driver.find_elements_by_xpath('//span[@class="date"]'):
            law_time.append(i.text)
        driver.quit()

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国生态环境部"
        item["legalCategory"] = "中华人民共和国生态环境部-政策法规解读"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            driver = webdriver.Chrome(chrome_options=option)
            driver.get(response.url)
            content = ""
            try:
                for i in driver.find_elements_by_xpath('//div[@class="TRS_Editor"]//a'):
                    fujian.append(i.get_attribute('href'))
                    fujian_name.append(i.text)
                content = driver.find_element_by_xpath('//div[@class="TRS_Editor"]').get_attribute('outerHTML')
            except Exception as e:
                print("*******正文提取出错1:{}********".format(e))

            if not content:
                try:
                    for i in driver.find_elements_by_xpath('//div[@class="content_body"]//a'):
                        fujian.append(i.get_attribute('href'))
                        fujian_name.append(i.text)
                    content = driver.find_element_by_xpath('//div[@class="content_body"]').get_attribute('outerHTML')
                except Exception as e:
                    print("*******正文提取出错2:{}********".format(e))
            if not content:
                try:
                    for i in driver.find_elements_by_xpath('//div[@class="neiright_Box"]//a'):
                        fujian.append(i.get_attribute('href'))
                        fujian_name.append(i.text)
                    content = driver.find_element_by_xpath('//div[@class="neiright_Box"]').get_attribute('outerHTML')
                except Exception as e:
                    print("*******正文提取出错3:{}********".format(e))

            tmpn = ""
            if re.search(r'(国[^<>]{0,8}[0-9]{4}[^<>]{0,8}号)', content):
                tmpn = re.search(r'(国[^<>]{0,8}[0-9]{4}[^<>]{0,8}号)', content).group(1)
                item["legalDocumentNumber"] = tools.clean(tmpn)
            if not tmpn:
                if re.search(r'>[^ICP<>]{1,10}[0-9]{4}[^ICP<>]{1,10}号', response.xpath('//body').extract_first()):
                    tmpn = tools.clean(re.search(r'>([^ICP<>]{1,10}[0-9]{4}[^ICP<>]{1,10}号)', response.xpath('//body').extract_first()).group(1))
                    if not re.search(r'[0-9]{8}', tmpn):
                        item["legalDocumentNumber"] = tools.clean(tmpn)

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
