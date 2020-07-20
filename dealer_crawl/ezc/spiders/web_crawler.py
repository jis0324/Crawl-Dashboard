import scrapy
import os
import errno
import hashlib
import datetime
import re
import subprocess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.exceptions import CloseSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.http.request import Request
from scrapy.spidermiddlewares.offsite import OffsiteMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.crawler import CrawlerProcess
import csv
import socket
from tempfile import NamedTemporaryFile
from scrapy.utils.project import get_project_settings
import shutil
import time
import configparser
from scrapy import signals
import psutil
import sys
import time

base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(base_dir))

sys.path.append( base_dir + '/module')
from vehicle_listing import make_vehicle_list, update_csv, make_spider_summary, make_selenium_summary, make_exclude_url, write_summary
from webpages import find_vin, get_rest_data
from websites import save_page

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

import random
import json
import requests
import platform
from bs4 import BeautifulSoup
import pandas
import threading
try:
   import queue
except ImportError:
   import Queue as queue

from dataclasses import dataclass

dealer_ids = list()
dealer_names = list()
dealer_cities = list()
dealer_states = list()
dealer_zips = list()
urls = list()
domains = list()
summary_vin = list()
summary_novin = list()
summary_dynamic_vin = list()
summary_error = list()
deny_domain = list()
searchlist = list()
redirect_dict = dict()
linkSet = list()
csv_name = ''
summary_name = ''
dealerids = list()
dealernames = list()
dealercities = list()
dealerstates = list()
dealerzips = list()
dealerurls = list()
dealerdomains = list()
exceed_list = list()
vinNotFoundCount = 0
totalRequestsCount = 0
former_domain = ""
dealerSet = list()
vinSet = list()
priceSet = list()
titleSet = list()
state_counter = 0
mileageSet = list()
novin_count = 0
slash_except_list = list()

class MySpider(CrawlSpider):

    name = 'webCrawler'

    def __init__(self, dealer_ids, dealer_names, dealer_cities, dealer_states, dealer_zips, urls, domains, searchlist, slash_except_list, inventory_csv_name, summary_csv_name, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        settings = get_project_settings()
        self.allowed_domains = domains
        self.start_urls = urls
        self.handle_httpstatus_all = True
        self.searchlist = searchlist
        self.slash_except_list = slash_except_list
        self.inventory_csv_name = inventory_csv_name
        self.summary_csv_name = summary_csv_name
        global csv_name, summary_name, dealerids, dealernames, dealercities, dealerstates, dealerzips, dealerurls, dealerdomains, summary_vin, summary_novin, summary_dynamic_vin, summary_error, exceed_list, totalRequestsCount, vinSet, vinNotFoundCount, dealerSet, priceSet, mileageSet, titleSet, state_counter, former_domain, novin_count
        csv_name = ""
        summary_name = ""
        dealerids = dealer_ids.copy()
        dealernames = dealer_names.copy()
        dealercities = dealer_cities.copy()
        dealerstates = dealer_states.copy()
        dealerzips = dealer_zips.copy()
        dealerurls = urls.copy()
        dealerdomains = domains.copy()
        dealerSet = list()
        priceSet = list()
        mileageSet = list()
        titleSet = list()
        vinSet = list()
        linkSet = list()
        exceed_list = list()
        totalRequestsCount = 0
        vinNotFoundCount = 0
        state_counter = 0
        novin_count = 0
        former_domain = ""
        slash_except_list = list()
        self.crawl_status = dict()

    rules = (
        Rule(LinkExtractor(), callback='parse_item', process_links="link_filtering", follow=True),
    )
    
    def current_datetime_as_string(self):
        now = datetime.datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        return date_time

    def link_filtering(self, links):

        res = []

        for link in links:
            # exception duplication
            if link.url in linkSet:
                continue

            linkSet.append(link.url)

            flag = True
            myDomain = link.url.split("//")[-1].split("/")[0].split('?')[0]

            if "www" in myDomain:
                myDomain = myDomain[4:]

            if myDomain not in self.allowed_domains:
                continue
            
            if myDomain in self.crawl_status:
                if len(self.crawl_status[myDomain]) == 2:
                    self.crawl_status[myDomain][1] = self.current_datetime_as_string()
            else:
                self.crawl_status[myDomain] = [ self.current_datetime_as_string(), self.current_datetime_as_string() ]
            
            slash_count = len(link.url.split("/"))

            if myDomain not in self.slash_except_list and slash_count > 8:
                flag = False

            if flag == True:
                addsymbol_count = len(link.url.split("&"))

                if addsymbol_count > 4:
                    flag = False

            if flag == True:
                
                search_result_exclude_domain_list = [
                    'lafayettecourtesy.com',
                    'rkchevrolet.com',
                ]
                for searchitem in self.searchlist:
                    if myDomain in search_result_exclude_domain_list and searchitem == 'VehicleSearchResults':
                        continue

                    if searchitem in link.url:
                        flag = False
                        break
                
                if myDomain == 'truckpartsinventory.com':
                    truckpartsinventory_exception_pattern_list = [
                        '/part-types',
                        '/manufacturers',
                        '/proximity',
                        '/company',
                        '/part-request',
                        '/parts',
                    ]

                    for pattern in truckpartsinventory_exception_pattern_list:
                        if pattern in link.url:
                            flag = False
                            break

                if myDomain == 'carsforall.com':
                    if '/search/' in link.url:
                        if len(link.url.split('/search/')[3]) > 0:
                            flag = False
                
            if flag == False:
                continue
            
            with open( base_dir + "/link.csv", "a") as f:
                writer = csv.writer(f)
                writer.writerow([link.url])

            res.append(link)

        return res

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):

        spider = super(MySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):

        global csv_name, summary_name, dealerids, dealernames, dealercities, dealerstates, dealerzips, dealerurls, dealerdomains, summary_vin, summary_novin, summary_dynamic_vin, summary_error
        make_spider_summary(dealerids, dealernames, dealercities, dealerstates, dealerzips, dealerurls, dealerdomains, summary_vin, summary_novin, summary_dynamic_vin, summary_error, self.crawl_status, self.summary_csv_name)

    def parse_item(self, response):

        global csv_name, summary_name, dealerids, dealernames, dealercities, dealerstates, dealerzips, dealerurls, dealerdomains, summary_vin, summary_novin, summary_dynamic_vin, summary_error, exceed_list, totalRequestsCount, vinSet, vinNotFoundCount, dealerSet, priceSet, mileageSet, titleSet, state_counter, former_domain, novin_count

        response_url = response.url
        domain_index = 0
        myDomain = response_url.split("//")[-1].split("/")[0].split('?')[0]

        if "www" in myDomain:
            myDomain = myDomain[4:]

        if myDomain not in dealerdomains:
            return

        if response.status > 400 or response.status == "meta refresh":
            tmp_dict = {}
            tmp_dict[myDomain] = response.status
            summary_error.append(myDomain)
            return
            
        domain_index = dealerdomains.index(myDomain)
        dealer_id = dealerids[domain_index]
        dealer_name = dealernames[domain_index]
        dealer_city = dealercities[domain_index]
        dealer_state = dealerstates[domain_index]
        dealer_zip = dealerzips[domain_index]
        url = dealerurls[domain_index]

        today = str(datetime.date.today())

        try:
            res_content = response.text
        except:
            return
            
        crawl_dict = {}
        final_dict = {}
        csv_name = base_dir + "/output/" + self.inventory_csv_name
        totalRequestsCount += 1

        foundVin = find_vin(res_content, myDomain)
        
        if myDomain == former_domain:
            state_counter += 1
        else:
            state_counter = 0

        former_domain = myDomain

        if foundVin is None:
            vinNotFoundCount += 1

            if "{{VIN}}" in res_content or "{{Vin}}" in res_content or "dws-" in res_content:
                summary_dynamic_vin.append(myDomain)
            else:
                summary_novin.append(myDomain)
            return

        print('VIN : ', foundVin)

        if foundVin not in vinSet:
            summary_vin.append(myDomain)
            crawl_dict['Dealer ID'] = dealer_id
            crawl_dict['Dealer Name'] = dealer_name
            crawl_dict['City'] = dealer_city
            crawl_dict['State'] = dealer_state
            crawl_dict['Zip'] = dealer_zip
            crawl_dict['URL'] = url
            crawl_dict['VIN'] = foundVin
            temp_dict = get_rest_data(res_content, myDomain)
            final_dict = dict(crawl_dict, **temp_dict)
            vinSet.append(foundVin)
            priceSet.append(temp_dict['Price'])
            mileageSet.append(temp_dict['Mileage'])
            titleSet.append(temp_dict['Title'])
            dealerSet.append(dealer_id)
        else:
            vinindex = vinSet.index(foundVin)

            if priceSet[vinindex] != 'N/A' and mileageSet[vinindex] != 'N/A' and titleSet[vinindex] != '':
                return
            crawl_dict = get_rest_data(res_content, myDomain)
            value_list = list()
            value_list.append(dealer_id)
            value_list.append(dealer_name)
            value_list.append(dealer_city)
            value_list.append(dealer_state)
            value_list.append(dealer_zip)
            value_list.append(url)
            value_list.append(foundVin)

            for value in crawl_dict.values():
                value_list.append(value)

            update_csv(csv_name, value_list, foundVin)
            return
        make_vehicle_list(final_dict, csv_name)


# -------------- subsystem classes start ------------------
@dataclass 
class JDefine:
    # crawl thread states
    CRAWL_STATE_NOTHING_DOING        = 1
    CRAWL_STATE_NOW_DOING            = 2
    CRAWL_STATE_DONE_ERROR_NONE      = 3
    CRAWL_STATE_DONE_ERROR_TIME_OVER = 4
    CRAWL_STATE_DONE_ERROR_OTHER     = 5
    CRAWL_FINAL_END_OK               = False

    # url search states
    PAGE_PROC_NOT_DONE              = 11
    PAGE_PROC_NOW_DOING             = 12
    PAGE_PROC_DONE_OK               = 13
    PAGE_PROC_DONE_ERROR            = 14
    NO_SEARCH_RESULT                = 15

    GET_PROXY_LIST_DONE             = 21 
    GET_PROXY_LIST_ERROR            = 22

class CrawlThread(object):

    def __init__(self, url, proxy_ip=None):
        self.url = url                  # url address
        self.state = JDefine.CRAWL_STATE_NOTHING_DOING        # thread state
        self.start_time = None          # thread processing start time
        self.chrome_opt = None          
        self.proxy = proxy_ip           # proxy_ip
        self.response_queue = queue.Queue() # dict with key: ["page_url", "data"]
        self.res = None                 # list format result
        self.thread = threading.Thread(target=self.crawl_thread_func)

    def start(self):
        self.start_time = time.time()
        if not self.thread.is_alive():
            self.thread.start()
        self.state = JDefine.CRAWL_STATE_NOW_DOING

    def stop(self):
        self.thread.join(2)
        return self.thread.is_alive()

    def restart(self, url, proxy):
        self.url = url
        self.proxy = proxy
        self.result = None
        self.res = None
        self.start_time = None
        self.start()

    def get_thread_state(self):
        return self.state

    def get_result(self):
        data = None
        if not self.response_queue.empty():
            data = self.response_queue.get()
        thread_state = self.state
        if self.state == JDefine.CRAWL_STATE_DONE_ERROR_NONE or self.state == JDefine.CRAWL_STATE_DONE_ERROR_OTHER:
            self.state = JDefine.CRAWL_STATE_NOTHING_DOING
        return self.url, data, thread_state
    
    def crawl_thread_func(self):
        while True:
            if JDefine.CRAWL_FINAL_END_OK:
                break
            if self.state != JDefine.CRAWL_STATE_NOW_DOING:
                time.sleep(0.1)
                continue 
            
            proxy_http = "http://" + self.proxy
            webdriver.DesiredCapabilities.CHROME['proxy']={
                "httpProxy":proxy_http,
                "ftpProxy":proxy_http,
                "sslProxy":proxy_http,
                "proxyType":"MANUAL",
            }
            
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.132 Safari/537.36'
            
            chrome_option = webdriver.ChromeOptions()
            chrome_option.add_argument('--no-sandbox')
            chrome_option.add_argument('--disable-dev-shm-usage')
            chrome_option.add_argument('--ignore-certificate-errors')
            chrome_option.add_argument("--disable-blink-features=AutomationControlled")
            chrome_option.add_argument(f'user-agent={user_agent}')
            chrome_option.headless = True
            
            try:            
                driver = webdriver.Chrome('/usr/local/bin/chromedriver', options = chrome_option) # CentOS
                driver.get(self.url)
                data = WebDriverWait(driver, 20).until(lambda driver: driver.find_element_by_tag_name("html").get_attribute("innerHTML").strip())                 
                driver.quit()
                self.response_queue.put(data)         
                self.state = JDefine.CRAWL_STATE_DONE_ERROR_NONE
            except:
                self.state = JDefine.CRAWL_STATE_DONE_ERROR_OTHER
            time.sleep(0.5)
                
class CrawlThreadManager(object):

    def __init__(self, thread_cnt):
        self.thread_cnt = thread_cnt
        self.url_list = None
        self.page_proc_info = []                # list of dict: (page_num, state)
        self.page_cnt = None
        self.thread_list = []                   #list of class : CrawlThread
        self.proxy_list = None                  # list of proxy ip-> ex:192.168.11.112:3380
        self.start_time = None                  # search start time
        self.search_state = False               # True, False
        self.result_queue = queue.Queue()       # dict (page_num, data)
        self.project_dir =  base_dir + '/' # CentOS
        self.manage_thread = threading.Thread(target=self.manage_thread_func)

    def set_param(self, url_list, proxy_list_path=None):
        self.page_proc_info.clear()
        self.result_queue.queue.clear()
        self.url_list = url_list
        self.start_time = None
        if self.get_proxy_list() == False:
            return JDefine.GET_PROXY_LIST_ERROR
        self.page_cnt = len(url_list)
        if self.page_cnt == 0:
            return JDefine.NO_SEARCH_RESULT
        for page_num in range(self.page_cnt):
            item = dict.fromkeys(['page_url', 'state'])
            item['page_url'] = self.url_list[page_num]
            item['state'] = JDefine.PAGE_PROC_NOT_DONE
            self.page_proc_info.append(item)
        return JDefine.GET_PROXY_LIST_DONE#, len(self.proxy_list)

    def get_proxy_list(self, proxy_list_path=None):
        path = ""
        if proxy_list_path != None:
            path = proxy_list_path
        else:
            path = self.project_dir + "subsystem_patterns/proxies.txt"
        with open(path,"r") as file:
            self.proxy_list = file.readlines()    
            return True
        return False

    def get_ctm_state(self):
        return self.search_state 

    def get_queue_data(self):
        value_data = []
        if not self.result_queue.empty():
            while not self.result_queue.empty():
                data = self.result_queue.get()                
                value_data.append(data)
            return value_data
        else:
            return []

    def start(self):
        self.start_time = time.time()
        if len(self.thread_list) == 0:
            for i in range(self.thread_cnt):
                proxy_ip, page_url = self.get_next_proxy_and_page()
                if page_url is None:
                    break
                crl_thread = CrawlThread(url=page_url, proxy_ip=proxy_ip)
                self.thread_list.append(crl_thread)
            for thrd in self.thread_list:
                thrd.start()
                time.sleep(3)
            self.manage_thread.start()
        self.search_state = True

    def stop(self):
        self.manage_thread.join()
    
    def end_manager(self):
        for thread in self.thread_list:
            if thread.stop():
                del thread
        self.stop()
                    
    def get_next_proxy_and_page(self):
        random_idx = random.randint(1,len(self.proxy_list)-1)
        proxy_ip = self.proxy_list[random_idx]
        for page_info in self.page_proc_info:
            if page_info['state'] == JDefine.PAGE_PROC_NOT_DONE:
                page_info['state'] = JDefine.PAGE_PROC_NOW_DOING
                return proxy_ip, page_info['page_url']
        return None, None
    
    def get_proxy_ip(self):
        random_idx = random.randint(1,len(self.proxy_list)-1)
        proxy_ip = self.proxy_list[random_idx]
        return proxy_ip

    def proc_url_result(self, page_url, data, thread_state):
        if data is not None:
            res = dict.fromkeys(['page_url', 'data'])
            res['page_url'] = page_url
            res['data'] = data
            self.result_queue.put(res)

        if thread_state == JDefine.CRAWL_STATE_NOTHING_DOING:
            return
        if thread_state == JDefine.CRAWL_STATE_DONE_ERROR_NONE:
            self.update_page_state(page_url, JDefine.PAGE_PROC_DONE_OK)
        if thread_state == JDefine.CRAWL_STATE_DONE_ERROR_OTHER:
            self.update_page_state(page_url, JDefine.PAGE_PROC_DONE_ERROR)
            pass
        if thread_state == JDefine.CRAWL_STATE_DONE_ERROR_TIME_OVER:
            pass

    def update_page_state(self, page_url, state):
        for page_info in self.page_proc_info:
            if page_info['page_url'] == page_url:
                page_info['state'] = state
                return

    def manage_thread_func(self):
        no_next_page = False
        while True:
            if no_next_page == True and self.search_state == False:
                time.sleep(2)
                break

            for thread in self.thread_list:
                page_url, data, thread_state = thread.get_result()
                self.proc_url_result(page_url, data, thread_state)
                if thread_state != JDefine.CRAWL_STATE_NOW_DOING:
                    proxy, next_page = self.get_next_proxy_and_page()
                    if next_page is not None:
                        thread.restart(next_page, proxy)
                    else:
                        no_next_page = True
            if no_next_page == True:
                tmp = False
                for thread in self.thread_list:
                    state = thread.get_thread_state()
                    if state == JDefine.CRAWL_STATE_NOW_DOING:
                        tmp = True
                        break
                if tmp == False:
                    self.search_state = False
            time.sleep(0.5)
        return

class BrowseableSubsystem(object):
    
    def __init__(self, dealer_ids, dealer_names, dealer_cities, dealer_states, dealer_zips, urls, domains, searchlist, slash_except_list, inventory_csv_name, summary_csv_name,):
        self.proxy_list = []
        self.browseable_domains = domains
        self.browseable_urls = urls
        self.dealer_ids = dealer_ids
        self.dealer_names = dealer_names
        self.dealer_cities = dealer_cities
        self.dealer_states = dealer_states
        self.dealer_zips = dealer_zips
        self.detail_page_urls = []
        self.detail_wrapper = []
        self.inventory_page_url_patterns = []
        self.inventory_directly_patterns = []
        self.not_detail_url_match_patterns = []
        self.exclude_page_url_patterns = []
        self.pagination_patterns = []
        self.predefined_inventory_url_patterns = []
        self.inventory_csv_name = inventory_csv_name
        self.summary_csv_name = summary_csv_name
        global dealerids, dealernames, dealerurls, dealerdomains, dealercities, dealerstates, dealerzips
        dealerids = dealer_ids.copy()
        dealernames = dealer_names.copy()
        dealercities = dealer_cities.copy()
        dealerstates = dealer_states.copy()
        dealerzips = dealer_zips.copy()
        dealerurls = urls.copy()
        dealerdomains = domains.copy() 
        self.log_file = ''
        self.project_dir =  base_dir + '/'         
        self.initialize()
    
    def initialize(self):
        self.get_detail_page_url_patterns()
        self.get_inventory_page_url_patterns()
        self.get_not_detail_page_url_patterns()
        self.get_pagination_pattern()
        self.get_proxy_list()
        self.create_log_file()
        self.get_inventory_directly_pattern()
        self.get_exclude_page_url_patterns()
        self.get_predefined_inventory_pattern()
        self.get_detail_wrapper_patterns()
        
    def set_driver(self):
        random_proxy_ip = "http://" + self.get_random_proxy()        
        webdriver.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy":random_proxy_ip,
            "ftpProxy":random_proxy_ip,
            "sslProxy":random_proxy_ip,
            "proxyType":"MANUAL",
        }    
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.132 Safari/537.36'
        chrome_option = webdriver.ChromeOptions()
        chrome_option.add_argument('--no-sandbox')
        chrome_option.add_argument('--disable-dev-shm-usage')
        chrome_option.add_argument('--ignore-certificate-errors')
        chrome_option.add_argument(f'user-agent={user_agent}')
        chrome_option.headless = True
        
        driver = webdriver.Chrome('/usr/local/bin/chromedriver', options = chrome_option)
        return driver

    def get_proxy_list(self):
        path = self.project_dir + "subsystem_patterns/proxies.txt"
        with open(path) as file_object:
            self.proxy_list = [row.rstrip('\n') for row in file_object]
            
    def get_random_proxy(self):
        random_idx = random.randint(1, len(self.proxy_list) - 1)
        proxy_ip = self.proxy_list[random_idx]
        return proxy_ip

    def current_datetime_as_string(self):
        now = datetime.datetime.now()
        date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        return date_time

    def remove_duplicated_inventory_url(self):
        self.tmp_inventory_href_list = list(set(self.tmp_inventory_href_list))
        inventory_urls = self.tmp_inventory_href_list
        
        for inventory_url in self.tmp_inventory_href_list:
            for other_inventory_url in self.tmp_inventory_href_list:
                if inventory_url != other_inventory_url and inventory_url in inventory_urls:
                    inventory_urls.remove(inventory_url)
        self.tmp_inventory_href_list = inventory_urls
    
    # ----------------------------------- necessary patterns start ------------------------------------- #
    def get_detail_page_url_patterns(self):
        path = self.project_dir + "subsystem_patterns/subsys_detail_page_url_pattern.txt"
        with open(path) as file_object:
            self.detail_page_urls = [row.rstrip('\n') for row in file_object]
    
    def get_detail_wrapper_patterns(self):
        path = self.project_dir + "subsystem_patterns/subsys_detail_wrapper.csv"
        with open(path, 'r', encoding='latin1') as file_object:
            self.detail_wrapper = list(csv.reader(file_object))
            self.detail_wrapper.pop(0)
            
    def get_inventory_page_url_patterns(self):
        path = self.project_dir + "subsystem_patterns/subsys_inventory_url_match_pattern.txt"
        with open(path) as file_object:
            self.inventory_page_url_patterns = [row.rstrip('\n') for row in file_object]
    
    def get_exclude_page_url_patterns(self):
        path = self.project_dir + "subsystem_patterns/subsys_exclude_url_pattern.txt"
        with open(path) as file_object:
            self.exclude_page_url_patterns = [row.rstrip('\n') for row in file_object]
            
    def get_inventory_directly_pattern(self):
        path = self.project_dir + "subsystem_patterns/subsys_inventory_directly_pattern.csv"
        with open(path, 'r', encoding='latin1') as file_object:
            self.inventory_directly_patterns = list(csv.reader(file_object))
            self.inventory_directly_patterns.pop(0)

    def get_predefined_inventory_pattern(self):
        path = self.project_dir + "subsystem_patterns/subsys_predefined_inventory_url.csv"
        with open(path, 'r', encoding='latin1') as file_object:
            self.predefined_inventory_url_patterns = list(csv.reader(file_object))
            self.predefined_inventory_url_patterns.pop(0)

    def get_not_detail_page_url_patterns(self):
        path = self.project_dir + "subsystem_patterns/subsys_not_detail_url_match_pattern.txt"
        with open(path) as file_object:
            self.not_detail_url_match_patterns = [row.rstrip('\n') for row in file_object]

    def get_pagination_pattern(self):
        path = self.project_dir + "subsystem_patterns/subsys_pagination_pattern.csv"
        with open(path, "r", encoding='latin1') as file_object:
            self.pagination_patterns = list(csv.reader(file_object))
            self.pagination_patterns.pop(0)
    
    def create_log_file(self):
        log_path = self.project_dir + 'subsystem_log/'
        now = datetime.datetime.now()
        date = now.strftime("%Y_%m_%d")
        if os.path.isdir(log_path) == False:
            os.mkdir(log_path)
        self.log_file = log_path + date + '.txt'
        
    def extract_href(self, matched_result):
        if isinstance(matched_result, str):
            matched_result_as_string = matched_result
        else:
            matched_result_as_string = matched_result[1]
            
        space_removed_result = matched_result_as_string.replace(' ', '')
        wrapped_character_start = space_removed_result[5]
        space_removed_result = space_removed_result[6:]
        wrapped_character_end_position = space_removed_result.find(wrapped_character_start)
        href = space_removed_result[:wrapped_character_end_position].replace('amp;', '')
        return href
    
    def real_protocol(self, url, page_url):
        http_protocol = url[:url.find('/')]
        page_http_protocol = page_url[:page_url.find('/')]
        if http_protocol != page_http_protocol:
            page_url = page_url.replace(page_http_protocol, http_protocol)
        return page_url
    
    def extract_inventory_page_urls(self, html):
        html_content = html
        html_content = re.sub('\s+', '', html_content)
        html_content = re.sub('\<\/a\>', '</a>\n', html_content)
        html_content = re.sub('\<\/script\>', '</script>\n', html_content)
        html_content = re.sub('\<script.*\<\/script\>', '', html_content)
        matched_result_pattern = re.compile('\<a\s*.*(href\s*\=\s*\"*\'*.*\"*\'*.*\>.*\<\/a\>)')     
        all_patterns = []  
        for item in matched_result_pattern.finditer(html_content):
            matched_result = item.groups()[0]
            for inventory_page_pattern in self.inventory_page_url_patterns:
                space_removed_pattern = inventory_page_pattern.replace(' ', '')
                space_removed_matched_result = matched_result.replace(' ', '')
                if space_removed_pattern in space_removed_matched_result:
                    inventory_href = self.extract_href(space_removed_matched_result)
                    inventory_href = self.check_inventory_page_urls(inventory_href)
                    if inventory_href not in self.tmp_inventory_href_list and inventory_href != '#':
                        if 'all' in space_removed_pattern.lower():
                            all_patterns.append(inventory_href)        
                        self.tmp_inventory_href_list.append(inventory_href)
        
        if len(all_patterns) > 0:
            self.tmp_inventory_href_list = all_patterns
        
    def check_inventory_page_urls(self, inventory_href):
        if inventory_href == "/used-cars":
            inventory_href = "/cars-for-sale/Used+Cars"
        elif inventory_href == "/new-cars":
            inventory_href = "/cars-for-sale/New+Cars"
        return inventory_href
    
    def extract_detail_page_urls(self, inventory_href, vehicle_html, detail_url_in_each_inventory):
        html_content = vehicle_html
        html_content = re.sub('\s+', ' ', html_content)
        html_content = re.sub('\<\/a\>', '</a>\n', html_content)
        html_content = re.sub('\<\/script\>', '</script>\n', html_content)
        html_content = re.sub('\<script.*\<\/script\>', '', html_content)        
        # regex to get like '<a href="/170974/2009-Toyota-Matrix-S-5-Speed-At">'
        matched_result_pattern1 = re.compile('\<a\s*.*(href\s*\=\s*\"*\'*\/\d+\"*\'*.*\>.*\<\/a\>)')
        # regex to get the content of href
        matched_result_pattern2 = re.compile('href\s*\=\s*\"*\'*([\w\d\/\:\;\!\@\#\$\%\^\&\*\-\+\_\=\.\,\?]+)\"*\'*')
        detail_urls_each_inventory = detail_url_in_each_inventory
        new_item_appended = False
        # for matched_result in matched_result_list2:
        for item in matched_result_pattern1.finditer(html_content):            
            matched_result = item.groups()[0]
            href = self.extract_href(matched_result)            
            if href != inventory_href and href not in detail_urls_each_inventory:
                new_item_appended = True
                detail_urls_each_inventory.append(href)
        for item in matched_result_pattern2.finditer(html_content):
            href = item.groups()[0].replace('amp;', '')            
            for detail_page in self.detail_page_urls:
                if href != inventory_href and detail_page in href:
                    if any(not_detail_pattern in href for not_detail_pattern in self.not_detail_url_match_patterns):
                        pass
                    else:
                        if detail_page == 'Detail.asp?':
                            href = 'http://weblot.walkthelot.com/Inventory/v5/' + href
                        if href not in detail_urls_each_inventory:
                            new_item_appended = True
                            detail_urls_each_inventory.append(href)
        return new_item_appended, detail_urls_each_inventory
    
    def extract_front_href(self, pattern, html):
        end_position = html.find(pattern)
        start_position = html[:end_position].rfind('href')
        exact_pattern = html[start_position:end_position]
        return self.extract_href(exact_pattern)
    
    def extract_behind_href(self, pattern, html):
        pattern_start_position = html.find(pattern)
        behind_text = html[pattern_start_position:]
        end_position = behind_text.find('>')
        href_start_position = html[pattern_start_position:].find('href')
        exact_pattern = html[href_start_position:end_position]
        return self.extract_href(exact_pattern)

    def extract_pagination_attribute(self, html):
        html_removed_space_and_enter = re.sub('\s+', '', html)
        for row in self.pagination_patterns:
            try:
                p_pattern = row[0].strip()
                p_attr = row[1].strip()
                p_value = row[2].strip()
                p_state = row[3].strip()
                p_child_tag = row[4].strip()
                p_condition = row[5].strip()
                p_pattern_removed_space = re.sub('\s+', '', p_pattern)
                if p_pattern_removed_space in html_removed_space_and_enter and p_pattern != 'pattern':
                    return p_attr, p_value, p_state, p_child_tag, p_condition
            except:
                return None, None, None, None, None
        return None, None, None, None, None
        
    def process_dynamic_loading_page(self, dynamic_loading_page):
        url_type_1 = dynamic_loading_page + '&results='
        url_type_2 = dynamic_loading_page + '?results='
        type_1, type_2 = False, False
        response_1 = requests.get(url_type_1)
        response_2 = requests.get(url_type_2)
        try:
            soup = BeautifulSoup(response_1.text, 'html.parser')
            jsonStr = soup.find('div',{'id':'ds-vehicles-json'})['data-json']
            jsonData = json.loads(jsonStr)
            df_1 = pandas.json_normalize(jsonData)
            type_1 = True
        except:
            pass
        try:
            soup = BeautifulSoup(response_2.text, 'html.parser')
            jsonStr = soup.find('div',{'id':'ds-vehicles-json'})['data-json']
            jsonData = json.loads(jsonStr)
            df_2 = pandas.json_normalize(jsonData)
            type_2 = True
        except:
            pass
        if type_1 and type_2:
            count_df_1 = df_1['Vin'].count()
            count_df_2 = df_2['Vin'].count()
            df = df_1 if count_df_1 > count_df_2 else df_2
        else:
            df = df_1 if type_1 else df_2
        return df
    
    def remove_not_detail_url(self, urls):
        detail_url_list = urls
        for url in urls:
            if url[-2:] == '/#':
                detail_url_list.remove(url)
            contains_count = 0
            for other_url in urls:
                # only check other url contains url or not, (not the same)
                if url in other_url and url != other_url: 
                    contains_count += 1
            if contains_count >= 1 and url in detail_url_list:
                detail_url_list.remove(url)        
        return detail_url_list
    
    def get_redirect_domain_inventory(self, inventory_url):
        domain = re.sub(r'(.*://)?([^/?]+).*', '\g<1>\g<2>', inventory_url)
        return domain
        
    def get_redirect_domain_inventory(self, inventory_url):
        domain = re.sub(r'(.*://)?([^/?]+).*', '\g<1>\g<2>', inventory_url)
        return domain
    
    def remove_duplicated_item_from_list(self, duplicated_list):
        unique_urls = list(set(duplicated_list))
        ret_urls = []
        # remove similar urls ('/used' == '/used/' )
        for url in unique_urls:
            if url[:-1] in unique_urls:
                pass
            else:
                ret_urls.append(url)
        return ret_urls
    
    def check_list_selected(self, inventory_html):
        html_content = inventory_html
        html_content = re.sub('\<\/script\>', '</script>\n', html_content)
        html_content = re.sub('\<script.*\<\/script\>', '', html_content)
        if 'class="dws-list-view btn"' in html_content and 'class="dws-grid-view btn hidden"' in html_content:
            return True
        else:
            return False
            
    def parse_item(self, response):
        global csv_name, summary_name, dealerids, dealernames, dealerurls, dealerdomains, summary_vin, summary_novin, summary_dynamic_vin, summary_error, exceed_list, totalRequestsCount, vinSet, vinNotFoundCount, dealerSet, priceSet, mileageSet, titleSet, state_counter, former_domain, novin_count
        response_url = response['url']
        domain_index = 0
        myDomain = response_url.split("//")[-1].split("/")[0].split('?')[0]
        if "www" in myDomain:  # revised
            myDomain = myDomain[4:]  # revised
        if myDomain not in dealerdomains:
            return
        if response['status'] > 400 or response['status'] == "meta refresh":
            tmp_dict = {}
            tmp_dict[myDomain] = response['status']
            summary_error.append(myDomain)
            return
            
        domain_index = dealerdomains.index(myDomain)
        dealer_id = dealerids[domain_index]
        dealer_name = dealernames[domain_index]
        dealer_city = dealercities[domain_index]
        dealer_state = dealerstates[domain_index]
        dealer_zip = dealerzips[domain_index]
        url = dealerurls[domain_index]

        today = str(datetime.date.today())

        res_content = response['text']
        crawl_dict = {}
        final_dict = {}
        csv_name =  base_dir + "/output/" + self.inventory_csv_name
        totalRequestsCount += 1

        foundVin = find_vin(res_content, myDomain)
        
        if myDomain == former_domain:
            state_counter += 1
        else:
            state_counter = 0

        former_domain = myDomain

        if foundVin is None:
            vinNotFoundCount += 1
            summary_novin.append(myDomain)
            return

        if foundVin not in vinSet:
            summary_vin.append(myDomain)
            crawl_dict['Dealer ID'] = dealer_id
            crawl_dict['Dealer Name'] = dealer_name
            crawl_dict['City'] = dealer_city
            crawl_dict['State'] = dealer_state
            crawl_dict['Zip'] = dealer_zip
            crawl_dict['URL'] = url
            crawl_dict['VIN'] = foundVin
            temp_dict = get_rest_data(res_content, myDomain)
            final_dict = dict(crawl_dict, **temp_dict)
            vinSet.append(foundVin)
            priceSet.append(temp_dict['Price'])
            mileageSet.append(temp_dict['Mileage'])
            titleSet.append(temp_dict['Title'])
            dealerSet.append(dealer_id)
        else:
            vinindex = vinSet.index(foundVin)

            if priceSet[vinindex] != 'N/A' and mileageSet[vinindex] != 'N/A' and titleSet[vinindex] != '':
                return
            crawl_dict = get_rest_data(res_content, myDomain)
            value_list = list()
            value_list.append(dealer_id)
            value_list.append(dealer_name)
            value_list.append(dealer_city)
            value_list.append(dealer_state)
            value_list.append(dealer_zip)
            value_list.append(url)
            value_list.append(foundVin)

            for value in crawl_dict.values():
                value_list.append(value)

            update_csv(csv_name, value_list, foundVin)
            return
        make_vehicle_list(final_dict, csv_name)

    def extract_inventory_directly_pattern(self, vehicle_html, domain):        
        html_content = vehicle_html
        html_content = re.sub('\<\/script\>', '</script>\n', html_content)
        html_content = re.sub('\<script.*\<\/script\>', '', html_content)
        for row in self.inventory_directly_patterns:
            d_exclude_domain = row[8].strip()
            if domain in d_exclude_domain:
                return None, None, None, None, ''
            d_special_string = row[2].strip()
            d_tag = row[3].strip()
            d_attr = row[4].strip()
            d_value = row[5].strip()
            d_state = row[6].strip()
            d_child_tag = row[7].strip()
            if d_special_string in html_content and d_special_string != 'special_strings':
                return d_tag, d_attr, d_value, d_state, d_child_tag
        return None, None, None, None, ''

    def insert_log(self, content):
        date_time = self.current_datetime_as_string()
        content = date_time + ' :  ' + content
        with open(self.log_file, 'a') as file_object:
            file_object.write(content)
            file_object.write('\n')
            
    def insert_time_log_for_no_template(self, content):
        date_time = self.current_datetime_as_string()
        content = date_time + ' :  ' + content
        path = self.log_file[:-4] + '_time.txt'
        with open(path, 'a') as file_object:
            file_object.write(content)
            file_object.write('\n')
           
    def make_inventory_url_as_full(self, inventory_href, url):
        prefixs = ['http', 'www.']
        if any(prefix in inventory_href for prefix in prefixs):                                                
            inventory_full_url = inventory_href
        else:
            if 'orangeparktrucks.com' in url:
                url = 'https://www.orangeparktrucks.com'
            inventory_full_url = url + inventory_href
            inventory_full_url = inventory_full_url.replace('//', '/')
            inventory_full_url = inventory_full_url.replace(':/', '://')
            inventory_full_url = self.real_protocol(url, inventory_full_url)
        return inventory_full_url
        
    def get_predefined_inventory_href(self, url):
        for row in self.predefined_inventory_url_patterns:
            domain = row[0].strip()
            if domain in url:
                inventory_url = row[1].split(',')    
                self.tmp_inventory_href_list = [row.strip() for row in inventory_url]
                return True
        return False

    def extract_detail_wrapper(self, domain):
        w_tag, w_attr, w_value, w_state = None, None, None, None
        for row in self.detail_wrapper:
            if row[0].strip() in domain:
                w_tag, w_attr, w_value, w_state = row[1].strip(), row[2].strip(), row[3].strip(), row[4].strip()
                break
        return w_tag, w_attr, w_value, w_state
    
    def is_exclude_url(self, url):
        state = any(exclude_pattern in url for exclude_pattern in self.exclude_page_url_patterns)
        return state
    
    def is_exclude_pattern(self, pattern):
        state = any(pattern in exclude_pattern for exclude_pattern in self.exclude_page_url_patterns)
        return state

    def sub_process(self):
        global csv_name, summary_name, dealerids, dealernames, dealerurls, dealerdomains, summary_vin, summary_novin, summary_dynamic_vin, summary_error
        i = 1
        crawl_status = {}
        loading_count = 0
        count_browseable_urls = len(self.browseable_domains)
        execution_time = 0
        while True:
            domain_start_time = self.current_datetime_as_string()
            print ('------------- start -------------')
            if (count_browseable_urls <= i - 1):
                break
            start_time = time.time()
            domain = self.browseable_domains[i - 1]
            url = self.browseable_urls[i - 1]
            dealer_id = self.dealer_ids[i - 1]
            dealer_name = self.dealer_names[i - 1]
            dealer_city = self.dealer_cities[i - 1]
            dealer_state = self.dealer_states[i - 1]
            dealer_zip = self.dealer_zips[i - 1]
            dynamic_loading_page = False
            self.insert_log("-------------------------------------------- start --------------------------------------------")
            print (domain + ' : ' + url)
            self.insert_log(domain + ' : ' + url)
            
            if url[0] != 'h':
                url = 'http://' + url
        
            self.tmp_inventory_href_list = [] # inventory page url list of each websites (new or used)
            detail_url_list_each_site = []
            pagination = False
            redirect_url = True
            vehicle_info_outHtml = []
            dynamic_vehicle_info = []
            next_page_attr, next_page_value, next_page_state, next_page_child_tag, next_page_condition = None, None, None, None, None
            inventory_direct_site = False
            tag, attr, value, state, child_tag = None, None, None, None, None
            w_tag, w_attr, w_value, w_state = None, None, None, None
            page_no = 0 # for no next page attr
            
            try:
                w_tag, w_attr, w_value, w_state = self.extract_detail_wrapper(domain)                
                inventory_url_predefined = True
                inventory_url_predefined = self.get_predefined_inventory_href(url)
                
                if inventory_url_predefined == False:
                    if pagination == False:     
                        try:
                            self.driver = self.driver.quit()
                        except:
                            pass                   
                        try:
                            self.driver = self.set_driver()
                            self.driver.get(url)

                            time.sleep(3)
                            if redirect_url:
                                real_url = self.driver.current_url
                                if real_url != url:
                                    # first page is inventory page
                                    if 'alleghenytruckspa.com' in url:
                                        self.tmp_inventory_href_list.append(real_url)
                                    url = real_url

                                    try:
                                        self.driver.quit()
                                    except:
                                        pass

                                    self.driver = self.set_driver()
                                    self.driver.get(url)
                                    self.insert_log('redireted to ' + url)
                                redirect_url = False
                            pagination_url = url
                            
                            content = url + ' ' + 'Page loaded'
                            self.insert_log(content)
                        except TimeoutException:
                            content = url + ' ' + 'Page load Timeout Occured. Loading again ...'
                            self.insert_log(content)
                            loading_count += 1
                            if loading_count > 2:
                                i += 1
                                loading_count = 0
                                content = 'Tried to load page 3 times, but can not load this page !!!'
                                self.insert_log(content)
                            continue    
                        except:
                            content = 'site connection error'
                            print (content)
                            self.insert_log(content)
                            i += 1
                            continue
                    try:
                        inventory_html = WebDriverWait(self.driver, 20).until(lambda driver: driver.find_element_by_tag_name("html").get_attribute("innerHTML").strip())                 
                    except:
                        inventory_html = ''
                        pass
                    if pagination == False:
                        try:
                            self.extract_inventory_page_urls(inventory_html)
                        except:
                            pass                            
                    else:
                        if self.is_exclude_pattern(pagination_url) == False:
                            self.tmp_inventory_href_list.append(pagination_url)
                
                if len(self.tmp_inventory_href_list) != 0:
                    if inventory_url_predefined == False:
                        iframe_src_list = []
                        for inventory_href in self.tmp_inventory_href_list:
                            dynamic_loading_inventory_page = False
                            # append iframe src
                            if 'iframe' in inventory_html and dynamic_loading_inventory_page == False:
                                elements = self.driver.find_elements_by_tag_name('iframe')
                                for element in elements:
                                    try:
                                        iframe_src = element.get_attribute('src')
                                        if self.is_exclude_url(iframe_src) == False:
                                            iframe_src_list.append(iframe_src)
                                    except:
                                        pass
                        for item in iframe_src_list:
                            self.tmp_inventory_href_list.append(item)
                            
                        self.tmp_inventory_href_list = self.remove_duplicated_item_from_list(self.tmp_inventory_href_list)   
                        self.tmp_inventory_href_list.sort(reverse=True)                     
                        self.insert_log('--- possible inventory page start ---')
                        print (self.tmp_inventory_href_list)
                        for item in self.tmp_inventory_href_list:
                            self.insert_log(item)
                        self.insert_log('--- possible inventory page end ---')
                    
                    analyzed_count = 0
                    print (self.tmp_inventory_href_list)
                    for inventory_href in self.tmp_inventory_href_list:         

                        next_page_enable = True 
                        page_next_tag_click_again = 0                 
                        detail_url_in_each_inventory = []                          
                        page_count = 1            
                        inventory_url = self.make_inventory_url_as_full(inventory_href, url) 
                        dynamic_loading_inventory_page = False
                        try:
                            self.driver.quit()
                        except:
                            pass
                        try:
                            self.driver = self.set_driver()
                            self.driver.get(inventory_url)
                            inventory_html = WebDriverWait(self.driver, 20).until(lambda driver: driver.find_element_by_tag_name("html").get_attribute("innerHTML").strip())                 
                            element = self.driver.find_element_by_id("ds-vehicle-listing")
                            dynamic_vehicle_details_df = self.process_dynamic_loading_page(inventory_url)
                            dynamic_vehicle_info.append(dynamic_vehicle_details_df)
                            dynamic_loading_page = True
                            dynamic_loading_inventory_page = True
                        except:
                            pass
                        
                        if dynamic_loading_inventory_page == False:
                            if inventory_url != inventory_href and inventory_url in self.tmp_inventory_href_list:
                                content = 'inventory url duplicated. so passed...'
                                self.insert_log(content)
                            else:
                                content = 'inventory URL is [%s]' % inventory_url
                                self.insert_log(content)
                                redirect_domain_inventory = self.get_redirect_domain_inventory(inventory_url)
                                pagination_url = inventory_url
                                page_url_changed = True                            
                                
                                # inventory page with "Show_xxx" button (one page) 
                                inventory_pagination_link_count = 0
                                script_elements = []
                                try:
                                    print (inventory_url)
                                    vehicle_html = WebDriverWait(self.driver, 20).until(lambda driver: driver.find_element_by_tag_name("html").get_attribute("innerHTML").strip())                 
                                    next_page_attr, next_page_value, next_page_state, next_page_child_tag, next_page_condition = self.extract_pagination_attribute(vehicle_html)
                                except:
                                    next_page_value = None
                                    
                                if next_page_value == 'inventory-pagination_link js-pagination-btn':
                                    next_page_link_script = '//*[@class="inventory-pagination_link js-pagination-btn"]'
                                    while True:
                                        try:
                                            next_page_link = self.driver.find_element_by_xpath(next_page_link_script)
                                            self.driver.execute_script("arguments[0].click();", next_page_link)
                                            time.sleep(3)
                                            inventory_pagination_link_count += 1
                                        except:
                                            break
                                    print ('----  click count ------')
                                    print (inventory_pagination_link_count)
                                    script_elements = self.driver.find_elements_by_tag_name("script")
                                    for element in script_elements:
                                        try:
                                            outhtml = element.get_attribute('outerHTML')
                                            if outhtml not in vehicle_info_outHtml and "window.inlineJS.push(function() { Moff.modules.get('DataLayer').pushData('VehicleObject_" in outhtml:
                                                vehicle_info_outHtml.append(outhtml)
                                        except:
                                            pass
                                
                                # if 'truckmax.com' not in url:
                                if len(vehicle_info_outHtml) == 0:
                                    while True:           
                                        vehicle_html = ''     
                                        try:

                                            if page_url_changed == True:
                                                try:  
                                                    self.driver.quit()
                                                except:
                                                    self.insert_log('can not quit driver')

                                                try:
                                                    self.driver = self.set_driver()
                                                    self.driver.get(pagination_url)
                                                    time.sleep(3)
                                                except:
                                                    self.insert_log('can not create new driver')
                                                    break
                                            # Get scroll height.
                                            last_height = 0
                                            try:
                                                last_height = self.driver.execute_script("return document.body.scrollHeight")
                                                scroll_down_count = 1
                                            except:
                                                pass
                                            
                                            while True:
                                                try:
                                                    # Scroll down to the bottom.
                                                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                                    # Wait to load the page.
                                                    time.sleep(2)
                                                    # Calculate new scroll height and compare with last scroll height.
                                                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                                                    if new_height == last_height:
                                                        break
                                                    last_height = new_height      
                                                    scroll_down_count += 1        
                                                except:
                                                    break
                                            try:
                                                if w_tag == None:
                                                    vehicle_html = WebDriverWait(self.driver, 20).until(lambda driver: driver.find_element_by_tag_name("html").get_attribute("innerHTML").strip())                 
                                                    content = 'get html code inside <html>'
                                                else:
                                                    if w_state == 'equal':
                                                        vehicle_html = WebDriverWait(self.driver, 20).until(lambda driver: driver.find_element_by_xpath("//" + w_tag + "[@" + w_attr + "='" + w_value + "']").get_attribute("innerHTML").strip())                 
                                                    elif w_state == 'contain':
                                                        vehicle_html = WebDriverWait(self.driver, 20).until(lambda driver: driver.find_element_by_xpath("//" + w_tag + "[contains(@" + w_attr + ", '" + w_value + "')]").get_attribute("innerHTML").strip())                 
                                                    else:
                                                        vehicle_html = ''
                                                    content = 'get html code inside <%s>, %s, %s tag' % (w_tag, w_attr, w_value)
                                            except:
                                                vehicle_html = ''
                                            self.insert_log(pagination_url + ' : ' + content)
                                            if inventory_direct_site == False:
                                                tag, attr, value, state, child_tag = self.extract_inventory_directly_pattern(vehicle_html, domain)
                                            content = 'inventory directly : tag, attr, value, state, child_tag are [%s], [%s], [%s], [%s], [%s]' % (tag, attr, value, state, child_tag)
                                            
                                            self.insert_log(content)
                                            special_domain_list_for_direclty = ['lkqheavytruck.com', 'daystarrmotors.com', 'rydemore.com', 'vicjenkins.com']
                                            if any(special_domain in domain for special_domain in special_domain_list_for_direclty):
                                                tag = 'special_domain_list_for_direclty'
                                            
                                            if tag != None:
                                                inventory_direct_site = True
                                                try:
                                                    if 'vicjenkins.com' in domain or 'daystarrmotors.com' in domain:
                                                        elements = self.driver.find_elements_by_xpath("//table/tbody/*") 
                                                        content = 'template : vicjenkins.com or daystarrmotors.com'
                                                    elif 'rydemore.com' in domain:
                                                        elements = self.driver.find_elements_by_xpath("//div[@id='body-content-inner']/div/*")
                                                        content = 'template : rydemore.com'
                                                    elif 'lkqheavytruck.com' in domain:
                                                        elements = self.driver.find_elements_by_xpath("//div[@id='searchResult']/table/tbody/tr/td/center/table/tbody/*")
                                                        content = 'template : lkqheavytruck.com'
                                                    else:
                                                        if state == 'equal' and child_tag == '':
                                                            elements = self.driver.find_elements_by_xpath("//" + tag + "[@" + attr + "='" + value + "']/*")
                                                        elif state == 'equal' and child_tag != '':
                                                            elements = self.driver.find_elements_by_xpath("//" + tag + "[@" + attr + "='" + value + "']/" + child_tag + "/*")
                                                        elif state == 'contain' and child_tag == '':
                                                            elements = self.driver.find_elements_by_xpath("//" + tag + "[contains(@" + attr + ", '" + value + "')]/*")
                                                        elif state == 'contain' and child_tag != '':
                                                            elements = self.driver.find_elements_by_xpath("//" + tag + "[contains(@" + attr + ", '" + value + "')]/" + child_tag + "/*")
                                                        content = 'template : ' + value
                                                        
                                                    self.insert_log(content + ' count: ' + str(len(elements)))
                                                except:
                                                    elements = []
                                                
                                                directly_vehicle_info_count = 0
                                                for element in elements:
                                                    try:
                                                        outhtml = element.get_attribute('outerHTML')
                                                        if outhtml not in vehicle_info_outHtml:
                                                            directly_vehicle_info_count += 1
                                                            vehicle_info_outHtml.append(outhtml)
                                                            next_page_enable = True
                                                    except:
                                                        pass
                                                content = 'extracted [%s] vehicles info directly' % str(directly_vehicle_info_count)
                                                self.insert_log(content)
                                            
                                            next_page_enable, detail_url_in_each_inventory = self.extract_detail_page_urls(inventory_href, vehicle_html, detail_url_in_each_inventory)                                        
                                            print ('---------------------------')
                                            print ('next_page_enable ? ', next_page_enable)
                                            print ('---------------------------')
                                            if page_url_changed:
                                                next_page_enable = True
                                            if len(detail_url_in_each_inventory) != 0 or len(vehicle_info_outHtml) != 0:
                                                for detail_href in detail_url_in_each_inventory:
                                                    prefixs = ['http', 'www.']
                                                    if any(prefix in detail_href for prefix in prefixs):
                                                        if detail_href[:2] == '//':
                                                            detail_href = detail_href[2:]
                                                        elif detail_href[0] == '/':
                                                            detail_href = detail_href[1:]
                                                        detail_url = detail_href
                                                    else:
                                                        if detail_href[0] != "/":
                                                            redirect_domain_inventory = redirect_domain_inventory + "/"
                                                        if detail_href[0] == "#":
                                                            if inventory_url[-1:] == "/":
                                                                redirect_domain_inventory = inventory_url[:-1]
                                                            else:
                                                                redirect_domain_inventory = inventory_url
                                                            
                                                        detail_url = redirect_domain_inventory + detail_href
                                                        detail_url = self.real_protocol(url, detail_url)
                                                        detail_url = detail_url.replace('//', '/')
                                                        detail_url = detail_url.replace(':/', '://')
                                                    
                                                    if detail_url not in detail_url_list_each_site and inventory_url != detail_url:
                                                        detail_url_list_each_site.append(detail_url)
                                                
                                                # if next_page_value != 'inventory-pagination_link js-pagination-btn':
                                                next_page_attr, next_page_value, next_page_state, next_page_child_tag, next_page_condition = self.extract_pagination_attribute(vehicle_html)
                                                content = 'next_page_attr, next_page_value, next_page_state, next_page_child_tag, next_page_condition are [%s], [%s], [%s], [%s], [%s]' % (next_page_attr, next_page_value, next_page_state, next_page_child_tag, next_page_condition)
                                                self.insert_log(content)
                                                page_not_changed = False
                                            
                                                if next_page_attr != None:
                                                    if next_page_attr == 'option': 
                                                        # select box                                                        
                                                        try:
                                                            find_option_text_script = 'return document.getElementsByName("page")[0].getElementsByTagName("option")[1].getElementsByTagName("a")[' + str(page_count - 1) + '].textContent'
                                                            option_text = self.driver.execute_script(find_option_text_script)
                                                            self.driver.find_element_by_xpath("//select[@name='page']/option[text()='" + option_text + "']").click()
                                                            content = option_text + ' is clicked'
                                                            self.insert_log(content) 
                                                            page_not_changed = False
                                                        except:
                                                            content = 'not clicked'
                                                            self.insert_log(content)
                                                            pass
                                                    elif next_page_value == 'paging':
                                                        try:
                                                            self.driver.find_elements_by_class_name("convertUrl ")[page_no].click()
                                                            content = 'a[%s] is clicked' % str(page_no)
                                                            self.insert_log(content)
                                                            page_not_changed = False
                                                            page_no += 1
                                                        except:
                                                            pass
                                                    else:
                                                        next_page_link_script = '--- nothing ---'
                                                        general_attr = ['class', 'id', 'rel']
                                                        # ----------- pagination for unavaliable next link start ----------
                                                        if next_page_value == 'pagination custom-pagination-top right':                                                        
                                                            page_no += 1
                                                            next_page_link_script = '//ul[@class="pagination custom-pagination-top right"]/li[@id="' + str(page_no + 1) + '"]/a'
                                                            
                                                        elif next_page_value == 'page_number pagination':
                                                            next_page_link_script = '//ul[@class="' + next_page_value + '"]' + next_page_child_tag 
                                                        # ----------- pagination for unavaliable next link end ----------
                                                        
                                                        elif next_page_attr in general_attr:
                                                            if next_page_condition != '':
                                                                next_page_link_script = '//*[@' + next_page_attr + '="' + next_page_value + '"]' + next_page_child_tag + '[contains(text(),"' + next_page_condition + '")]' 
                                                            else:
                                                                next_page_link_script = '//*[@' + next_page_attr + '="' + next_page_value + '"]' + next_page_child_tag 
                                                            
                                                        elif next_page_attr == 'text':
                                                            if next_page_state == 'equal':
                                                                next_page_link_script = '//*[.="' + next_page_value + '"]'
                                                            elif next_page_state == 'contain':
                                                                next_page_link_script = '//*[contains(text(),"' + next_page_value + '")]'
                                                            
                                                        elif next_page_attr == 'refreshData': 
                                                            # div onclick="refreshData()"
                                                            next_page_link_script = '//div[@id="' + next_page_value + '"]/div[.="Next"]'
                                                            
                                                        try:
                                                            next_page_link = self.driver.find_element_by_xpath(next_page_link_script)
                                                            self.driver.execute_script("arguments[0].click();", next_page_link)
                                                            pages_not_change = ['ImageButtonNext']
                                                            if next_page_value in pages_not_change:
                                                                page_not_changed = True                                                
                                                            else:
                                                                page_not_changed = False                                                
                                                            content = 'clicked ' + next_page_link_script
                                                        except:
                                                            content = 'not clicked ' + next_page_link_script
                                                            page_count -= 1
                                                            next_page_enable = False
                                                            pagination = False
                                                            pass
                                                        
                                                        self.insert_log(content)
                                                    
                                                    content = 'page click count : ' + str(page_count) + ' clicked by ' + next_page_attr + ' ' + next_page_value 
                                                    print (content)
                                                    page_count += 1
                                                    time.sleep(5)
                                                    current_url = pagination_url
                                                    if page_not_changed == False and 'isaacsautosalesbkf.com' not in domain:
                                                        try:
                                                            current_url = self.driver.current_url
                                                        except:
                                                            break
                                                        
                                                    if pagination_url != current_url:
                                                        pagination_url = current_url
                                                        try:
                                                            page_url_changed = True
                                                        except TimeoutException:
                                                            content = pagination_url + ' ' + 'Page load Timeout Occured.'
                                                            self.insert_log(content)
                                                            break
                                                    else:
                                                        page_url_changed = False
                                                    pagination = True
                                                else:
                                                    next_page_enable = False
                                                    pagination = False
                                                # print ('----------- nex page click again  ---------', page_next_tag_click_again)
                                                # print ('pagination_url : ', pagination_url)
                                                # print ('current_url : ', current_url)
                                                # print ('--------------------')
                                                if next_page_enable == False:
                                                    if page_next_tag_click_again >= 1:
                                                        pagination = False
                                                        if next_page_attr != None:
                                                            page_count -= 1
                                                        break
                                                    else:
                                                        page_next_tag_click_again += 1
                                                
                                                    
                                            else:
                                                content = inventory_url + ' ' + 'no vehicle'
                                                self.insert_log(content)
                                                break
                                        except TimeoutException:
                                            content = inventory_url + ' ' + 'Inventory Page load Timeout Occured.'
                                            self.insert_log(content)
                                            break
                        analyzed_count += 1
                        print ('analyzed inventory group ' + str(analyzed_count) + '/' + str(len(self.tmp_inventory_href_list)))
                else:
                    content = 'no inventory page match'
                    self.insert_log(content)
                
                try:
                    real_detail_url_list_each_site = self.remove_not_detail_url(detail_url_list_each_site)
                    count_real_detail_url_list_each_site = len(real_detail_url_list_each_site)
                    content = url + ' : page count is ' + str(count_real_detail_url_list_each_site)
                    self.insert_log(content)
                except:
                    count_real_detail_url_list_each_site = 0
                    pass
                processed_count_detail_page = 0
                if dynamic_loading_page == False:
                    count_vehicle_info_outHtml = len(vehicle_info_outHtml)
                    if count_vehicle_info_outHtml != 0 and count_real_detail_url_list_each_site / 3 < count_vehicle_info_outHtml:
                        for res_content in vehicle_info_outHtml:
                            response = {
                                'url':domain,
                                'status': 200,
                                'text': res_content
                            }
                            self.parse_item(response)
                            processed_count_detail_page += 1
                        content = 'directly -> summary count is ' + str(count_vehicle_info_outHtml)
                        print (content)
                        self.insert_log(content)
                    else:
                        if count_real_detail_url_list_each_site > 0:
                            try:
                                ctm = CrawlThreadManager(3)
                                ret = JDefine.GET_PROXY_LIST_ERROR  
                                ret = ctm.set_param(url_list=real_detail_url_list_each_site)
                                if ret != JDefine.GET_PROXY_LIST_ERROR:
                                    JDefine.CRAWL_FINAL_END_OK = False
                                    ctm.start()
                                    while True:
                                        data = ctm.get_queue_data()
                                        if ctm.get_ctm_state() == False and len(data) == 0:
                                            ctm.end_manager()
                                            break
                                        else:
                                            if len(data) != 0:
                                                response = {
                                                    'url':domain,
                                                    'status': 200,
                                                    'text': data[0]['data']
                                                }
                                                self.parse_item(response)
                                                processed_count_detail_page += 1
                                        time.sleep(1)
                                content = 'original -> summary count is ' + str(len(real_detail_url_list_each_site))
                                self.insert_log(content)
                                JDefine.CRAWL_FINAL_END_OK = True
                                execution_time = round(time.time() - start_time, 2)
                                self.insert_time_log_for_no_template(domain + ' ' + url)
                                self.insert_time_log_for_no_template(content)
                                content = 'processed in [%s] seconds\n' % str(execution_time)
                                self.insert_time_log_for_no_template(content)
                            except:
                                pass
            except KeyboardInterrupt:
                break
            except requests.exceptions.RequestException:
                content = 'site connection error'
                self.insert_log(content)
            
            if dynamic_loading_page:
                dynamic_vehicle_count = 0
                for vehicle_info in dynamic_vehicle_info:
                    try:
                        mileage = vehicle_info['Mileage'].values.tolist()
                        vin = vehicle_info['Vin'].values.tolist()
                        title = vehicle_info['VehicleName'].values.tolist()
                        year = vehicle_info['Year'].values.tolist()
                        make = vehicle_info['Make'].values.tolist()
                        model = vehicle_info['Model'].values.tolist()
                        trim = vehicle_info['Trim'].values.tolist()
                        price = vehicle_info['FinalPrice'].values.tolist()
                        
                        for j in range(len(vin)):
                            if vin[j] != 'Vin':
                                if mileage[j] > 100:
                                    type_of_vehicle = 'used'
                                else:
                                    type_of_vehicle = 'new'

                                final_dict = {
                                    'Dealer ID':dealer_id,
                                    'Dealer Name':dealer_name,
                                    'City':dealer_city,
                                    'State':dealer_state,
                                    'Zip':dealer_zip,
                                    'URL':domain,
                                    'VIN':vin[j],
                                    'Price':price[j],
                                    'Mileage':mileage[j],
                                    'Type': type_of_vehicle,
                                    'Title':title[j],
                                    'Year':year[j],
                                    'Make':make[j],
                                    'Model':model[j],
                                    'Trim':trim[j]
                                }
                                csv_name_inventory =  base_dir + "/output/" + self.inventory_csv_name
                                make_vehicle_list(final_dict, csv_name_inventory)
                                summary_vin.append(domain)
                                dynamic_vehicle_count += 1
                        content = url + ' : dynamic loading page ' +  str(dynamic_vehicle_count)
                        self.insert_log(content)
                    except:
                        pass
                            
            i += 1
            content = "--------------------------------------- end -------------------------------------------------------\n"
            self.insert_log(content)
            execution_time = round(time.time() - start_time, 2)
            domain_end_time = self.current_datetime_as_string()
            crawl_status[domain] = [domain_start_time, domain_end_time]
        try:
            self.driver = self.driver.quit()
        except:
            pass   
        content = 'finished subsystem'
        self.insert_log(content)
        make_selenium_summary(dealerids, dealernames, dealercities, dealerstates, dealerzips, dealerurls, dealerdomains, summary_vin, summary_novin, summary_error, crawl_status, self.summary_csv_name)
        content = 'summary file updated...'
        self.insert_log(content)
        content = '----------- final end [%s] seconds -----------\n\n' % str(execution_time)
        self.insert_log(content)
        print('------------- end --------------222222')

# -------------- subsystem classes end ------------------

# Convert Inventory List To String
def inventorylisttostring(s):
    str = "inventory@#$%"
    for i in s:
        str = str + i + "@#$%"
    str = str + "\n"
    return str

# Convert Summary List To String
def summarylisttostring(s):
    str = "summary@#$%"
    for i in s:
        str = str + i + "@#$%"
    str = str + "\n"
    return str

# Get Domain From URL
def make_domain(url):
    try:
        if "http" in url:
            url = url.split("//", 1)[1].split("/", 1)[0].split('?', 1)[0]
        if "www" in url:
            url = url[4:]
        return url
    except:
        print('Error in Make Domain Function!')

def main():
    global searchlist, slash_except_list, dealer_ids, dealer_names, dealer_cities, dealer_states, dealer_zips, urls, domains
    data = ""
    dealer_ids = list()
    dealer_names = list()
    dealer_cities = list()
    dealer_states = list()
    dealer_zips = list()
    urls = list()
    domains = list()
    crawl_type = ''
    row_id = ''

    filename1 = base_dir + "/exclude_patterns.csv"
    file_exists = os.path.isfile( filename1 )
    if file_exists:
        with open(filename1, "r") as exclude_patterns_file:
            searchlist_data = list(csv.reader(exclude_patterns_file))
        exclude_patterns_file.close()

        for item in searchlist_data:
            searchlist.append(item[0])

    filename2 = base_dir + "/slash_except_list.csv"
    file_exists = os.path.isfile( filename2 )
    if file_exists:
        with open(filename2, "r") as slash_except_file:
            slash_except_list_data = list(csv.reader(slash_except_file))
        slash_except_file.close()

        for item in slash_except_list_data:
            slash_except_list.append(item[0])

    filename3 = base_dir + "/input.csv"
    file_exists = os.path.isfile( filename3 )
    if file_exists:
        with open(filename3, "r") as input_file:
            input_data = csv.DictReader(input_file)
            for row in input_data:
                print
                if row['Redirect URLs'].strip() == '':
                    print('***************************')
                    crawl_type =row['Crawl Type']
                    dealer_ids.append(row['Dealer ID'])
                    dealer_names.append(row['Dealer Name'])
                    dealer_cities.append(row['City'])
                    dealer_states.append(row['State / Province'])
                    dealer_zips.append(row['Zip'])
                    urls.append(row['Website'])
                    domains.append(make_domain(row['Website']))
                    row_id = row['id']
                else:
                    print('#########################')
                    print(row['Redirect URLs'])
                    print(len(row['Redirect URLs']))
                    redirect_urls = row['Redirect URLs'].split(',')
                    for item in redirect_urls:
                        if item != '':
                            crawl_type =row['Crawl Type']
                            dealer_ids.append(row['Dealer ID'])
                            dealer_names.append(row['Dealer Name'])
                            dealer_cities.append(row['City'])
                            dealer_states.append(row['State / Province'])
                            dealer_zips.append(row['Zip'])
                            urls.append(item)
                            domains.append(make_domain(item))
                            row_id = row['id']

    now = datetime.datetime.now()
    now_time = now.strftime("%Y-%m-%d-%H-%M-%S")

    inventory_csv_name = 'inventory-' + now_time + '.csv'
    summary_csv_name = 'summary-' + now_time + '.csv'

    if len(dealer_ids) != 0:
        if crawl_type == "Browseable":
            browseable_subsystem = BrowseableSubsystem(dealer_ids, dealer_names, dealer_cities, dealer_states, dealer_zips, urls, domains, searchlist, slash_except_list, inventory_csv_name, summary_csv_name)
            browseable_subsystem.sub_process()
            
        elif crawl_type == "Crawlable":
            process = CrawlerProcess(get_project_settings())
            process.crawl("webCrawler", dealer_ids, dealer_names, dealer_cities, dealer_states, dealer_zips, urls, domains, searchlist, slash_except_list, inventory_csv_name, summary_csv_name)
            process.start()
        
        else:
            pass

    
    import sqlite3

    #Connecting to sqlite
    conn = sqlite3.connect( os.path.dirname(os.path.dirname(os.path.dirname(base_dir))) + '/crawl_dashboard.sqlite3')

    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    
    now = datetime.datetime.now()
    end_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    #Updating the records
    sql = "UPDATE domains_test SET end_time = '" + str(end_time) + "', status = 'complete', summary_file='" + str(summary_csv_name) + "', inventory_file='" + str(inventory_csv_name) + "' WHERE id=" + row_id
    
    cursor.execute(sql)

    #Commit your changes in the database
    conn.commit()

    #Closing the connection
    conn.close()
    return
    
if __name__ == '__main__':
    
    file_exists = os.path.isfile( base_dir + "/link.csv")
    if file_exists:
        os.remove( base_dir + "/link.csv")

    main()
