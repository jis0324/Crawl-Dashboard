import os
import csv
import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required
def index(request):

  crawl_log_data = list()
  now = datetime.datetime.now()  
  today_date = now.strftime("%Y") + '-' + now.strftime("%m") + '-' + now.strftime("%d")

  if request.method == 'POST':
    crawl_date = request.POST['selected_date']
    if crawl_date == today_date:
      crawl_date, crawl_log_data = get_data_from_today_log()
    else:
      crawl_log_data = get_data_from_daily_log(crawl_date)
  else:
    crawl_date, crawl_log_data = get_data_from_today_log()
    if not crawl_date:
      crawl_date = today_date
      
    ##### if today_log.csv not exist, import data from daily_log_***.csv #####
    if not crawl_log_data:
      crawl_log_data = get_data_from_daily_log(crawl_date)
      
  data = log_to_dict(crawl_log_data)

  return render(request, 'crawl.html', {'data': data, 'today_date' : today_date, 'crawl_date' : crawl_date})

@login_required
def view_summary(request, host, crawl_date):
  now = datetime.datetime.now()  
  today_date = now.strftime("%Y") + '-' + now.strftime("%m") + '-' + now.strftime("%d")
  crawl_summary_data = list()
  if request.method == 'POST':
    crawl_date = request.POST['selected_date']
    return redirect('crawl_summary', host=host, crawl_date=crawl_date)
  else:
    crawl_summary_data = get_data_from_summary(host, crawl_date)
  
  data = summary_to_dict(crawl_summary_data)
  return render(request, 'crawler_summary.html', {'data': data, 'today_date' : today_date, 'crawl_date' : crawl_date, 'host_name' : host})

@login_required
def view_inventory(request, host, crawl_date, domain):
  now = datetime.datetime.now()
  today_date = now.strftime("%Y") + '-' + now.strftime("%m") + '-' + now.strftime("%d")
  crawl_inventory_data = list()

  # if request.method == 'POST':
  #   crawl_date = request.POST['selected_date']
  #   return redirect('crawl_inventory', host=host, crawl_date=crawl_date, domain=domain)
  # else:
  #   crawl_inventory_data = get_data_from_inventory(host, crawl_date, domain)
  crawl_inventory_data = get_data_from_inventory(host, crawl_date, domain)
  
  data = inventory_to_dict(crawl_inventory_data)
  return render(request, 'crawler_inventory.html', {'data': data, 'today_date' : today_date, 'crawl_date' : crawl_date, 'host_name' : host, 'domain' : domain})


def get_data_from_daily_log(crawl_date):
  daliy_log_csv = settings.SERVER_DIR + '/output/daily_log_' + crawl_date.split('-')[0] + crawl_date.split('-')[1] + '.csv'
  daily_log_exist = os.path.isfile(daliy_log_csv)
  crawl_log_data = list()
  if daily_log_exist:
    daily_log_data = list()
    with open(daliy_log_csv, 'r') as daily_log_file:
      daily_log_data = list(csv.DictReader(daily_log_file))
    
    today_log_flag = False
    for row in daily_log_data:
      
      if today_log_flag:
        if row['Date'] == '':
          crawl_log_data.append(row)
        else:
          today_log_flag = False
          break
      
      if crawl_date in row['Date']:
        today_log_flag = True
        crawl_log_data.append(row)

  return crawl_log_data

def get_data_from_today_log():

  crawl_log_data = list()
  crawl_date = ''
  today_log_csv = settings.SERVER_DIR + '/output/today_log.csv'
  today_log_exist = os.path.isfile(today_log_csv)

  ##### if today_log.csv exist, import data from today_log.csv #####
  if today_log_exist:
    with open(today_log_csv, 'r') as today_log_file:
      crawl_log_data = list(csv.DictReader(today_log_file))

    try:
      crawl_date = crawl_log_data[0]['Date'].split('T')[0]
    except:
      pass

  return crawl_date, crawl_log_data

def get_data_from_summary(host, crawl_date):
  return_data = list()
  summary_path = settings.SERVER_DIR + '/output/' + crawl_date + '/'
  
  if os.path.exists(summary_path):
    summary_csv_prefix = 'summary_' + crawl_date
    crawl_summary_data = list()
    files = []
    files = [i for i in os.listdir(summary_path) if os.path.isfile(os.path.join(summary_path,i)) and summary_csv_prefix in i]
    if files:
      summary_file = files[0]
      with open(summary_path + summary_file, 'r', encoding="latin1", errors="ignore") as summary:
        crawl_summary_data = list(csv.DictReader(summary))
    
    for row in crawl_summary_data:
      if row['Host Address'] == host:
        return_data.append(row)
  return return_data

def get_data_from_inventory(host, crawl_date, domain):
  return_data = list()
  summary_path = settings.SERVER_DIR + '/output/' + crawl_date + '/'
  
  if os.path.exists(summary_path):
    summary_csv_prefix = 'inventory_' + crawl_date
    crawl_inventory_data = list()
    files = []
    files = [i for i in os.listdir(summary_path) if os.path.isfile(os.path.join(summary_path,i)) and summary_csv_prefix in i]
    if files:
      summary_file = files[0]
      
      with open(summary_path + summary_file, 'r', encoding="latin1", errors="ignore") as summary:
        crawl_inventory_data = list(csv.DictReader(summary))
    
    for row in crawl_inventory_data:
      if row['DOMAIN'] == domain:
        return_data.append(row)

  return return_data

def log_to_dict(arg):
  return_data = list()
  for index,row in enumerate(arg):
    temp_dict = dict()
    temp_dict['date'] = row['Date']
    temp_dict['host'] = row['Host']
    temp_dict['start_time'] = row['Start Time']
    temp_dict['completed_time'] = row['Completed Time']
    temp_dict['elapsed_time'] = row['Elapsed Time']
    temp_dict['dealer_count'] = row['Total Dealer Count']
    temp_dict['inventory_count'] = row['Total Inventory Count']
    temp_dict['crawl_type'] = ''
    if index == 0:
      temp_dict['url_count'] = row['URL Range']
    else:
      url_ranges = row['URL Range'].split(':')
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
    return_data.append(temp_dict)
    
  return return_data

def summary_to_dict(arg):
  return_data = list()
  for row in arg:
    temp_dict = dict()
    temp_dict['dealer_id'] = row['Dealer ID']
    temp_dict['dealer_name'] = row['Dealer Name']
    temp_dict['city'] = row['City']
    temp_dict['state'] = row['State']
    temp_dict['zip'] = row['Zip']
    temp_dict['domain'] = row['DOMAIN']
    temp_dict['vin_count'] = row['Vin Count']
    temp_dict['error_state'] = row['Error State']
    temp_dict['host_address'] = row['Host Address']
    start_time = ''
    end_time = ''
    if 'Start Time' in row:
      start_time = row['Start Time']

    if 'End Time' in row:
      end_time = row['End Time']
    
    temp_dict['start_time'] = start_time
    temp_dict['end_time'] = end_time
    
    return_data.append(temp_dict)
    
  return return_data

def inventory_to_dict(arg):
  return_data = list()
  for row in arg:
    temp_dict = dict()
    temp_dict['dealer_id'] = row['Dealer ID']
    temp_dict['dealer_name'] = row['Dealer Name']
    temp_dict['domain'] = row['DOMAIN']
    temp_dict['vin'] = row['VIN']
    temp_dict['price'] = row['Price']
    temp_dict['mileage'] = row['Mileage']
    temp_dict['type'] = row['Type']
    temp_dict['title'] = row['Title']
    temp_dict['year'] = row['Year']
    temp_dict['make'] = row['Make']
    temp_dict['model'] = row['Model']
    temp_dict['trim'] = row['Trim']
    
    return_data.append(temp_dict)
    
  return return_data
