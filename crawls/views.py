import os
import csv
import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
import pymongo
import re

mongoclient = pymongo.MongoClient(settings.DB_PATH)
db = mongoclient["dealer_crawl_db"]
daily_log_collection = db['daily_log']
unexpected_urls_collection = db['unexpected_urls']
config_collection = db['config']
input_list_collection = db['input_list']
summary_collection = db['summary_result']
inventory_collection = db['inventory_result']

@login_required
def index(request):

  crawl_log_data = list()
  now = datetime.datetime.now()
  today_date = now.strftime("%Y-%m-%d")

  if request.method == 'POST':
    crawl_date = request.POST['selected_date']
    crawl_log_data = get_data_from_daily_log(crawl_date)
  else:
    crawl_date, crawl_log_data = get_data_from_today_log()

  data = log_to_dict(crawl_log_data)

  return render(request, 'crawl.html', {'data': data, 'today_date': today_date, 'crawl_date': crawl_date})

@login_required
def view_summary(request, host, crawl_date):
  now = datetime.datetime.now()
  today_date = now.strftime("%Y-%m-%d")
  crawl_summary_data = list()
  if request.method == 'POST':
    crawl_date = request.POST['selected_date']
    return redirect('crawl_summary', host=host, crawl_date=crawl_date)
  else:
    crawl_summary_data = get_data_from_summary(host, crawl_date)
  
  data = summary_to_dict(crawl_summary_data, crawl_date)
  return render(request, 'crawler_summary.html', {'data': data, 'today_date': today_date, 'crawl_date': crawl_date, 'host_name': host})

@login_required
def view_inventory(request, host, crawl_date, domain):
  now = datetime.datetime.now()
  today_date = now.strftime("%Y-%m-%d")
  crawl_inventory_data = list()

  # if request.method == 'POST':
  #   crawl_date = request.POST['selected_date']
  #   return redirect('crawl_inventory', host=host, crawl_date=crawl_date, domain=domain)
  # else:
  #   crawl_inventory_data = get_data_from_inventory(host, crawl_date, domain)
  crawl_inventory_data = get_data_from_inventory(host, crawl_date, domain)
  
  data = inventory_to_dict(crawl_inventory_data)
  return render(request, 'crawler_inventory.html', {'data': data, 'today_date': today_date, 'crawl_date': crawl_date, 'host_name': host, 'domain': domain})

@login_required
def total_summary(request, crawl_date):
  now = datetime.datetime.now()
  today_date = now.strftime("%Y-%m-%d")
  crawl_summary_data = list()
  if request.method == 'POST':
    crawl_date = request.POST['selected_date']
    return redirect('total_summary', crawl_date=crawl_date)
  else:
    crawl_summary_data = get_total_summary(crawl_date)

  data = summary_to_dict(crawl_summary_data, crawl_date)

  return render(request, 'total_summary.html', {'data': data, 'today_date': today_date, 'crawl_date': crawl_date, 'host_name': settings.SERVER_HOST})

def get_data_from_daily_log(crawl_date):
  global daily_log_collection

  crawl_log_data = list()

  query = { "Date": { "$regex": "^" + crawl_date } }
  crawl_log_data = list(daily_log_collection.find(query))
  return crawl_log_data
  
def get_data_from_today_log():
  global daily_log_collection

  crawl_log_data = list()
  
  today_date = datetime.date.today()
  yesterday_date = today_date - datetime.timedelta(days=1)

  query = {"Date": {"$regex": "^" + str(today_date)}}
  if daily_log_collection.count_documents(query) > 0:
    crawl_log_data = list(daily_log_collection.find(query))
    return str(today_date), crawl_log_data
  else:
    query = {"Date": {"$regex": "^" + str(yesterday_date)}}
    crawl_log_data = list(daily_log_collection.find(query))
    return str(yesterday_date), crawl_log_data

def get_data_from_summary(host, crawl_date):
  return_data = list()
  summary_query = {"Date": {"$regex": "^" + str(crawl_date)}, "host_address": host}
  if summary_collection.count_documents(summary_query):
    return_data = summary_collection.find(summary_query)
  else:
    summary_path = settings.SERVER_DIR + '/output/' + crawl_date + '/'

    if os.path.exists(summary_path):
      summary_csv_prefix = 'summary_' + crawl_date
      crawl_summary_data = list()
      files = []
      files = [i for i in os.listdir(summary_path) if os.path.isfile(os.path.join(summary_path,i)) and summary_csv_prefix in i]
      if files:
        summary_file = files[-1]
        with open(summary_path + summary_file, 'r', encoding="latin1", errors="ignore") as summary:
          crawl_summary_data = list(csv.DictReader(summary))

      for row in crawl_summary_data:
        if crawl_date > "2020-12-07":
          if row["host_address"] == host:
            return_data.append(row)
        else:
          if row['Host Address'] == host:
            return_data.append(row)
  return return_data

def get_data_from_inventory(host, crawl_date, domain):
  return_data = list()
  inventory_query = {"Date": {"$regex": "^" + str(crawl_date)}, "host_address": host, "domain": domain}
  if inventory_collection.count_documents(inventory_query):
    return_data = inventory_collection.find(inventory_query)
  else:
    inventory_path = settings.SERVER_DIR + '/output/' + crawl_date + '/'

    if os.path.exists(inventory_path):
      summary_csv_prefix = 'inventory_' + crawl_date
      crawl_inventory_data = list()
      files = []
      files = [i for i in os.listdir(inventory_path) if os.path.isfile(os.path.join(inventory_path,i)) and summary_csv_prefix in i]
      if files:
        summary_file = files[-1]

        with open(inventory_path + summary_file, 'r', encoding="latin1", errors="ignore") as summary:
          crawl_inventory_data = list(csv.DictReader(summary))

      for row in crawl_inventory_data:
        if 'doamin' in row:
          if row['doamin'] == domain:
            return_data.append(row)

  return return_data

def get_total_summary(crawl_date):
  return_data = list()
  total_summary_query = {"Date": {"$regex": "^" + str(crawl_date)}}
  if summary_collection.count_documents(total_summary_query):
    return_data = summary_collection.find(total_summary_query)
  else:
    summary_path = settings.SERVER_DIR + '/output/' + crawl_date + '/'

    if os.path.exists(summary_path):
      summary_csv_prefix = 'summary_' + crawl_date
      files = []
      files = [i for i in os.listdir(summary_path) if
               os.path.isfile(os.path.join(summary_path, i)) and summary_csv_prefix in i]
      if files:
        summary_file = files[-1]
        with open(summary_path + summary_file, 'r', encoding="latin1", errors="ignore") as summary:
          return_data = list(csv.DictReader(summary))
  return return_data

def log_to_dict(arg):
  return_data = list()
  for index,row in enumerate(arg):
    temp_dict = dict()
    temp_dict['date'] = row['Date']
    temp_dict['host'] = row['Host']

    if row["Crawler Type"] == "Server":
      temp_dict['start_time'] = row['Date']
    else:
      temp_dict['start_time'] = row['Start Time']

    temp_dict['completed_time'] = row['Completed Time']
    temp_dict['elapsed_time'] = row['Elapsed Time']
    if "Total Dealer Count" in row:
      temp_dict['dealer_count'] = row['Total Dealer Count']
    elif "Completed Dealer Count" in row:
      temp_dict['dealer_count'] = row["Completed Dealer Count"]

    temp_dict['inventory_count'] = row['Total Inventory Count']

    if ':' not in str(row['URL Range']):
      temp_dict['url_count'] = str(row['URL Range'])
    else:
      url_ranges = str(row['URL Range']).split(':')
      total_count = 0
      if len(url_ranges) > 1:
        if url_ranges[0].strip() == 'spider':
          temp_dict['crawl_type'] = 'scrapy'
        elif url_ranges[0].strip() == 'selenium':
          temp_dict['crawl_type'] = 'selenium'
        # temp_dict['crawl_type'] = url_ranges[0]
        urls = url_ranges[1].split(',')
        for url in urls:
          start_url = int(url.split('~')[0])
          end_url = int(url.split('~')[1])
          count = end_url - start_url + 1
          total_count += count
      temp_dict['url_count'] = total_count

    if "crawl_type" not in temp_dict:
      temp_dict['crawl_type'] = row["Crawler Type"]

    return_data.append(temp_dict)
    
  return return_data

def defalt_format(arg):
    if len(arg) == 1:
        arg = '0' + arg
    return arg

def calc_elapsed_time(start_time, end_time):
  try:
    start_time_obj = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time_obj = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    elapsed_time = (end_time_obj - start_time_obj).seconds
    elapsed_hour = int(elapsed_time/3600)
    rest_time = elapsed_time - elapsed_hour * 3600
    elapsed_minute = int(rest_time/60)
    rest_time = rest_time - elapsed_minute * 60
    elapsed_secs = rest_time
    return defalt_format(str(elapsed_hour)) + "h " + " " + defalt_format(str(elapsed_minute)) + "m " + " " + defalt_format(str(elapsed_secs)) + "s"
  except:
    return ''

def make_domain(url):
  try:
    if "#" in url:
      url = url.split("#")[0]
    if re.search(r"http\:\/+|https\:\/+", url):
      url = url.split(re.search(r"http\:\/+|https\:\/+", url).group(), 1)[1].split("/", 1)[0].split('?', 1)[0]
    if "www" in url:
      url = url[4:]

    return url.lower()
  except:
    return url.lower()

def summary_to_dict(arg, crawl_date):
  return_data = list()
  for row in arg:
    temp_dict = dict()
    if crawl_date > "2020-12-07":
      temp_dict['domain'] = row['domain']
      temp_dict['website'] = row['website']
      temp_dict['domain_inputdata'] = row['domain_inputdata']
      temp_dict['makes'] = row['makes']

      if row['vin_count'] == "N/A":
        temp_dict['vin_count'] = '0'
      else:
        temp_dict['vin_count'] = row['vin_count']
      if 'comment' in row:
        temp_dict['comment'] = row['comment']
      else:
        temp_dict['comment'] = ''
      temp_dict['error_state'] = row['error_state']
      if 'elapsed_time' in row:
        temp_dict['elapsed_time'] = row['elapsed_time']
        temp_dict['request_count'] = row['request_count']
      else:
        temp_dict['elapsed_time'] = calc_elapsed_time(row['Date'], row['End Time'])
        temp_dict['request_count'] = ''

      temp_dict['crawler'] = row['host_address']

      if "crawl_success_page_count" in row:
        temp_dict['crawl_success_page_count'] = row['crawl_success_page_count']
      else:
        temp_dict["crawl_success_page_count"] = ""
    else:
      temp_dict['domain'] = make_domain(row['Website'])
      temp_dict['website'] = row['Website']
      temp_dict['domain_inputdata'] = ""
      temp_dict['makes'] = ""

      if row['Vin Count'] == "N/A":
        temp_dict['vin_count'] = '0'
      else:
        temp_dict['vin_count'] = row['Vin Count']
      if 'Comment' in row:
        temp_dict['comment'] = row['Comment']
      else:
        temp_dict['comment'] = ''
      temp_dict['error_state'] = row['Error State']
      temp_dict['host_address'] = row['Host Address']
      if 'Elapsed Time' in row:
        temp_dict['elapsed_time'] = row['Elapsed Time']
        temp_dict['request_count'] = row['Request Count']
      else:
        temp_dict['elapsed_time'] = calc_elapsed_time(row['Date'], row['End Time'])
        temp_dict['request_count'] = ''

      temp_dict['crawler'] = row['Host Address']
      temp_dict['crawl_success_page_count'] = ""

      if not temp_dict["domain"]:
        continue


    return_data.append(temp_dict)

  return return_data

def inventory_to_dict(arg):
  return_data = list()
  for row in arg:
    try:
      temp_dict = dict()
      temp_dict['domain'] = row['domain']
      temp_dict['website'] = row['website']
      temp_dict['inputdata'] = row['domain_inputdata']
      temp_dict['link'] = row['link']
      temp_dict['vin'] = row['vin']
      temp_dict['price'] = row['price']
      temp_dict['mileage'] = row['mileage']
      temp_dict['type'] = row['type']
      temp_dict['title'] = row['title']
      temp_dict['year'] = row['year']
      temp_dict['make'] = row['make']
      temp_dict['model'] = row['model']
      temp_dict['trim'] = row['trim']
      temp_dict['description'] = row['description']

      return_data.append(temp_dict)
    except Exception as err:
      print(err)
      print(row)

  return return_data
