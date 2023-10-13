# coding: utf-8
import scrapy
import csv

headers={
    # cookie 绕过登录
    'cookie': '登录微博后复制cookie即可',
    'Referer': 'https://api.weibo.com/',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,rw;q=0.8',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
}

class HuaWeiCrawlSpider(scrapy.Spider):
    name = 'hua_wei_crawl'
    allowed_domains = ['s.weibo.com']

    def start_requests(self):

        base = "https://s.weibo.com/realtime?q=%23%E5%8D%8E%E4%B8%BAmate60%23&rd=realtime&tw=realtime&Refer=weibo_realtime&page={}"
        start_url = ['https://s.weibo.com/realtime?q=%23%E5%8D%8E%E4%B8%BAmate60%23&rd=realtime&tw=realtime&Refer=weibo_realtime&page=1']
        
        for i in range(2, 51):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=headers)


    def parse_dictionary(self, response):
        # print(response.text)
        user_items = response.xpath('//div[@class="card"]')


        # 创建CSV文件并写入数据
        ## mode='a'，因为如果是w每次循环都会被覆盖而不是在末尾写入
        with open('weibo_data.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # 写入CSV文件的标题行
            writer.writerow(['comment'])  
            
            ##缩进
            for user_item in user_items:
                user_name = user_item.xpath('//a[@class="name"]').xpath('string(.)').extract()
                text = user_item.xpath('//p[@class="txt"]').xpath('string(.)').extract()
                
            ## 打印测试
            # print("分割线——————————————————————-")
            # print(user_name)
            # print(text)
        
            for k in text:
                # print("测试")
                k = k.replace('\u200b','')
                k = k.replace('\n','')
                k = k.replace(' ','')
                # print("清理后")
                # print(k)
                writer.writerow([str(k)])
       
       
