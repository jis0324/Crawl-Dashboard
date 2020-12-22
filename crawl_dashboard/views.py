from django.contrib.auth.models import User
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
import pymongo
import datetime
import configparser
import os
from django.conf import settings
from django.http import FileResponse

mongoclient = pymongo.MongoClient("mongodb://dbUser:AuYbta2211Ac@104.238.234.40:27017/")
db = mongoclient["dealer_crawl_db"]
daily_log_collection = db['daily_log']
unexpected_urls_collection = db['unexpected_urls']


@login_required
def index(request):
  return redirect('crawl_index')


@login_required
def unexpected_urls(request):
  today_date = datetime.date.today()

  if request.method == "POST":
    crawl_date = request.POST['selected_date']
    unexpected_url_data = get_unexpected_url_data_from_crawl_date(crawl_date)
    return render(request, 'unexpected_urls.html',
                  {'data': unexpected_url_data, 'today_date': today_date, 'crawl_date': crawl_date})

  crawl_date, unexpected_url_data = get_unexpected_url_data()
  return render(request, 'unexpected_urls.html',
                {'data': unexpected_url_data, 'today_date': today_date, 'crawl_date': crawl_date})


@login_required
def config_settings(request):
  config = configparser.ConfigParser()
  config_file = settings.SERVER_DIR + "/config.ini"
  config.read(config_file)

  if request.method == "POST":
    try:
      config.set('Server', 'HOST', str(request.POST['host']))
      config.set('Server', 'PORT', str(request.POST['port']))
      config.set('Server', 'INTERVAL_HOURS', str(request.POST['crawler_interval_time']))
      config.set('Server', 'START_TIME', str(request.POST['crawler_start_time']))
      config.set('Server', 'PROCESS_COUNT_OF_EACH_CRAWLERS', str(request.POST['process_per_crawler']))
      config.set('Server', 'NOT_AVAILABLE_REQUEST_REPEAT_COUNT',
                 str(request.POST['not_available_request_repeat_count']))
      config.set('Server', 'BROWSEABLE_PROCESS_NUM', str(request.POST['browseable_process_num']))
      config.set('Server', 'BROWSEABLE_THREAD_COUNT', str(request.POST['browseable_thread_count']))
      config.set('Server', 'CRAWLER_FILE_UPDATING_FLAG', str(request.POST['update_status']))
      config.set('Server', 'DEALER_LIST_REINSERT_FLAG', str(request.POST['dealer_list_reinsert_flag']))
      config.set('Server', 'CRAWLABLE_CRAWLERS_LIST', str(request.POST['crawlable_crawlers'].replace('\n', ',')))
      config.set('Server', 'BROWSEABLE_CRAWLERS_LIST', str(request.POST['browseable_crawlers'].replace('\n', ',')))

      # Writing our configuration file to 'example.ini'
      with open(config_file, 'w') as configfile:
        config.write(configfile)

      return HttpResponse('success')
    except:
      return HttpResponse('failed')

  else:
    return_data = {
      "host": config['Server']['HOST'],
      "port": config['Server']['PORT'],
      "crawler_interval_time": config['Server']['INTERVAL_HOURS'],
      "crawler_start_time": config["Server"]["START_TIME"],
      "process_per_crawler": config['Server']['PROCESS_COUNT_OF_EACH_CRAWLERS'],
      "not_available_request_repeat_count": config['Server']['NOT_AVAILABLE_REQUEST_REPEAT_COUNT'],
      "browseable_process_num": config['Server']['BROWSEABLE_PROCESS_NUM'],
      "browseable_thread_count": config['Server']['BROWSEABLE_THREAD_COUNT'],
      "update_status": config['Server']['CRAWLER_FILE_UPDATING_FLAG'],
      "dealer_list_reinsert_flag": config['Server']['DEALER_LIST_REINSERT_FLAG'],
      "crawlable_crawlers": config['Server']['CRAWLABLE_CRAWLERS_LIST'].split(','),
      "browseable_crawlers": config['Server']['BROWSEABLE_CRAWLERS_LIST'].split(','),
    }

    return render(request, 'settings.html', {'data': return_data})


@login_required
def crawl_status(request):
  today_date = datetime.date.today()

  if request.method == "POST":
    crawl_date = request.POST['selected_date']
    crawl_status_data = get_crawl_status_data_from_crawl_date(crawl_date)
    return render(request, 'crawl_status.html',
                  {'data': crawl_status_data, 'today_date': str(today_date), 'crawl_date': str(crawl_date)})

  crawl_date, crawl_status_data = get_crawl_status_data()
  return render(request, 'crawl_status.html',
                {'data': crawl_status_data, 'today_date': str(today_date), 'crawl_date': str(crawl_date)})


def get_crawl_status_data():
  global daily_log_collection
  temp_dict = dict()
  today_date = datetime.date.today()
  yesterday_date = today_date - datetime.timedelta(days=1)

  query = {"Date": {"$regex": "^" + str(today_date)}, "Crawler Type": "Server"}
  if daily_log_collection.count_documents(query) > 0:
    crawl_status_data = daily_log_collection.find_one(query)

    return str(today_date), modify_crawl_status_data(crawl_status_data, today_date)
  else:
    query = {"Date": {"$regex": "^" + str(yesterday_date)}, "Crawler Type": "Server"}
    crawl_status_data = daily_log_collection.find_one(query)
    return str(yesterday_date), modify_crawl_status_data(crawl_status_data, yesterday_date)


def get_crawl_status_data_from_crawl_date(crawl_date):
  global daily_log_collection
  temp_dict = dict()

  query = {"Date": {"$regex": "^" + str(crawl_date)}, "Crawler Type": "Server"}
  crawl_status_data = daily_log_collection.find_one(query)
  if crawl_status_data:
    return modify_crawl_status_data(crawl_status_data, crawl_date)
  else:
    return {}


def modify_crawl_status_data(crawl_status_data, crawling_date):
  global unexpected_urls_collection, daily_log_collection
  yesterday_date = datetime.datetime.date(
    datetime.datetime.strptime(str(crawling_date), '%Y-%m-%d')) - datetime.timedelta(days=1)

  temp_dict = dict()
  query = {"date": {"$regex": "^" + str(crawling_date)}}
  temp_dict['incompleted_dealer_count'] = unexpected_urls_collection.count_documents(query)

  query = {"Date": {"$regex": "^" + str(yesterday_date)}, "Crawler Type": "Server"}
  if daily_log_collection.count_documents(query):
    temp_dict['yesteday_invendory_count'] = dict(daily_log_collection.find_one(query)).get("Total Inventory Count")
  else:
    temp_dict['yesteday_invendory_count'] = ''

  if "Start Time" in crawl_status_data:
    temp_dict['start_time'] = crawl_status_data["Start Time"]

  if "Completed Time" in crawl_status_data:
    temp_dict['end_time'] = crawl_status_data["Completed Time"]

  if "Elapsed Time" in crawl_status_data:
    temp_dict['elapsed_time'] = crawl_status_data["Elapsed Time"]

  if "Total Dealer Count" in crawl_status_data:
    temp_dict['completed_dealer_count'] = crawl_status_data["Total Dealer Count"]

  if "Whole Dealer Count" in crawl_status_data:
    temp_dict['whole_dealer_count'] = crawl_status_data["Whole Dealer Count"]

  if "Filtered Dealer Count" in crawl_status_data:
    temp_dict['filtered_dealer_count'] = crawl_status_data["Filtered Dealer Count"]

  if "Crawlable Dealer Count" in crawl_status_data:
    temp_dict['crawlable_dealer_count'] = crawl_status_data["Crawlable Dealer Count"]

  if "Browseable Dealer Count" in crawl_status_data:
    temp_dict['browseable_dealer_count'] = crawl_status_data["Browseable Dealer Count"]

  if "NoVin Dealer Count" in crawl_status_data:
    temp_dict['novin_dealer_count'] = crawl_status_data["NoVin Dealer Count"]

  if "NoInventory Dealer Count" in crawl_status_data:
    temp_dict['noinventory_dealer_count'] = crawl_status_data["NoInventory Dealer Count"]

  if "NotActive Dealer Count" in crawl_status_data:
    temp_dict['notactive_dealer_count'] = crawl_status_data["NotActive Dealer Count"]

  if "Exclude Dealer Count" in crawl_status_data:
    temp_dict['exclude_dealer_count'] = crawl_status_data["Exclude Dealer Count"]

  if "Total Inventory Count" in crawl_status_data:
    temp_dict['today_invendory_count'] = crawl_status_data["Total Inventory Count"]

  return temp_dict


def get_unexpected_url_data():
  global unexpected_urls_collection

  unexpected_urls_data = list()

  today_date = datetime.date.today()
  yesterday_date = today_date - datetime.timedelta(days=1)

  query = {"date": {"$regex": "^" + str(today_date)}}
  if unexpected_urls_collection.count_documents(query) > 0:
    unexpected_urls_data = list(unexpected_urls_collection.find(query))
    return str(today_date), unexpected_urls_data
  else:
    query = {"date": {"$regex": "^" + str(yesterday_date)}}
    unexpected_urls_data = list(unexpected_urls_collection.find(query))
    return str(yesterday_date), unexpected_urls_data


def get_unexpected_url_data_from_crawl_date(crawl_date):
  global unexpected_urls_collection

  unexpected_urls_data = list()
  query = {"date": {"$regex": "^" + crawl_date}}
  unexpected_urls_data = list(unexpected_urls_collection.find(query))
  return unexpected_urls_data


# send server files to crawlers
def download_crawler_files(request):
  if request.method == "POST":
    passw = request.POST['passw']
    pattern = request.POST['pattern']
    if passw == "jis_passw":
      if pattern == "need_webcrawler_file":
        file_path = settings.SERVER_DIR + "/client_files/web_crawler.py"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_webpages_file":
        file_path = settings.SERVER_DIR + "/client_files/webpages.py"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_vehicle_file":
        file_path = settings.SERVER_DIR + "/client_files/vehicle_listing.py"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_exclude_patterns_file":
        file_path = settings.SERVER_DIR + "/client_files/exclude_patterns.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_slash_except_file":
        file_path = settings.SERVER_DIR + "/client_files/slash_except_list.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_detail_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_detail_page_url_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_detail_wrapper_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_detail_wrapper.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_exclude_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_exclude_url_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_inventory_directly_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_inventory_directly_pattern.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_inventory_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_inventory_url_match_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_not_detail_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_not_detail_url_match_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_pagination_not_next_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_pagination_not_next_page_pattern.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_pagination_pattern_file":
        file_path = settings.SERVER_DIR + \
                    "/client_files/subsys_pagination_pattern.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_predefined_inventory_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_predefined_inventory_url.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)

    else:
      return HttpResponse("wrong_auth")

  elif request.method == "GET":
    passw = request.GET['passw']
    pattern = request.GET['pattern']
    if passw == "jis_passw":
      if pattern == "need_webcrawler_file":
        file_path = settings.SERVER_DIR + "/client_files/web_crawler.py"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_webpages_file":
        file_path = settings.SERVER_DIR + "/client_files/webpages.py"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_vehicle_file":
        file_path = settings.SERVER_DIR + "/client_files/vehicle_listing.py"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_exclude_patterns_file":
        file_path = settings.SERVER_DIR + "/client_files/exclude_patterns.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_slash_except_file":
        file_path = settings.SERVER_DIR + "/client_files/slash_except_list.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_detail_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_detail_page_url_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_detail_wrapper_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_detail_wrapper.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_exclude_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_exclude_url_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_inventory_directly_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_inventory_directly_pattern.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_inventory_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_inventory_url_match_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_not_detail_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_not_detail_url_match_pattern.txt"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_pagination_not_next_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_pagination_not_next_page_pattern.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_pagination_pattern_file":
        file_path = settings.SERVER_DIR + \
                    "/client_files/subsys_pagination_pattern.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)
      elif pattern == "need_subsys_predefined_inventory_file":
        file_path = settings.SERVER_DIR + "/client_files/subsys_predefined_inventory_url.csv"
        if os.path.isfile(file_path):
          file = open(file_path, 'rb')
          return FileResponse(file)

    else:
      return HttpResponse("wrong_auth")

  return HttpResponse("Raised Error!")
