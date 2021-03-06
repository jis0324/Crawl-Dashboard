import os
import csv
from datetime import datetime
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Test
import json
import subprocess
import psutil

@login_required
def index(request):
  now = datetime.now()
  today_date = now.strftime("%Y-%m-%d")

  domain_list = list()
  if os.path.isfile(settings.SERVER_DIR + '/input.csv'):
    with open(settings.SERVER_DIR + '/input.csv', 'r', encoding="latin1", errors="ignore") as summary:
      domain_list = list(csv.DictReader(summary))
  
  data = input_to_dict(domain_list)

  return render(request, 'domain.html', {'data': data, 'today_date': today_date})

@login_required
def domain_summary(request, domain, crawl_date):
  now = datetime.now()  
  today_date = now.strftime("%Y-%m-%d")
  domain_summary_data = list()
  if request.method == 'POST':
    crawl_date = request.POST['selected_date']
    return redirect('domain_summary', domain=domain, crawl_date=crawl_date)
  else:
    domain_summary_data = get_data_from_summary(domain, crawl_date)
  
  data = summary_to_dict(domain_summary_data)
  return render(request, 'domain_summary.html', {'data': data, 'today_date' : today_date, 'crawl_date' : crawl_date, 'domain' : domain})

@login_required
def test_domain(request):
  if request.method == 'POST':
    try:
      # Test.objects.all().delete()
      test_list = Test.objects.all()
      for item in test_list:
        if item.status == 'crawling':
          return_data = {
            'user' : item.user.username,
            'status' : 'crawling',
          }
          return HttpResponse(json.dumps(return_data))
      
      now = datetime.now()
      start_time = now.strftime("%Y-%m-%d-%H-%M-%S")
      save_data = Test( dealer = request.POST['dealer_id'], start_time = start_time, status = 'crawling', user = request.user)
      save_data.save()

      input_csv_path = settings.BASE_DIR + '/dealer_crawl/ezc/spiders/input.csv'

      input_dict = {
        "Dealer ID" : request.POST['dealer_id'],
        "Dealer Name" : request.POST['dealer_name'],
        "City" : request.POST['dealer_city'],
        "State" : request.POST['dealer_state'],
        "Zip" : request.POST['dealer_zip'],
        "Website" : make_url(request.POST['dealer_website']),
        "Category" : request.POST['dealer_category'],
        "Crawl Type" : request.POST['dealer_type'],
        "Redirect URLs" : request.POST['dealer_redirect'],
        "id" : save_data.id
      }

      if os.path.isfile(input_csv_path):
        os.remove(input_csv_path)
      
      with open(input_csv_path, 'w', newline="") as input_file:
        fieldnames = ["Dealer ID", "Dealer Name", "City", "State", "Zip", "Website", "Category", "Crawl Type", "Redirect URLs", "id",]
        writer = csv.DictWriter(input_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(input_dict)
      
      os.chdir(settings.BASE_DIR + "/dealer_crawl/ezc/spiders/")
      output = subprocess.Popen("python3 web_crawler.py", shell=True, universal_newlines=True)
      os.chdir(settings.BASE_DIR)
      
      return_data = {
        'user': request.user.username,
        'status' : 'success'
      }
      return HttpResponse(json.dumps(return_data))
    except:
      return HttpResponse(json.dumps({'status' : 'failed'}))

@login_required
def test_cancel(request):
  if request.method == 'POST':
    now = datetime.now()
    end_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    try:
      record = get_object_or_404(Test, dealer=request.POST['dealer_id'], status = 'crawling')
    except:
      record = None
      
    if record:
      record.status = 'cancel'
      record.end_time = end_time
      record.save()
    
      try:
        PROCNAME = "python3"
        for proc in psutil.process_iter():
          if proc.name() == PROCNAME:
            if proc.cmdline() == ['python3', 'web_crawler.py']:
                proc.kill()
      except :
          pass

      return HttpResponse('success')
    else:
      return HttpResponse('complete')

@login_required
def view_test(request, dealer_id):
  test_data = Test.objects.filter( dealer = dealer_id )
  return render(request, 'view_test.html', {'data': test_data, 'dealer': dealer_id})

@login_required
def test_detail(request, dealer_id, id):
  test_detail_data = Test.objects.get( id = id )
  summary_data = list()
  inventory_data = list()

  if test_detail_data:
    if test_detail_data.summary_file:
      summary_path = settings.BASE_DIR + '/dealer_crawl/ezc/spiders/output/' + test_detail_data.summary_file
      if os.path.isfile(summary_path):
        with open(summary_path, 'r') as summary_file:
          summary_data = list(csv.DictReader(summary_file))

    if test_detail_data.inventory_file:
      inventory_path = settings.BASE_DIR + '/dealer_crawl/ezc/spiders/output/' + test_detail_data.inventory_file
      if os.path.isfile(inventory_path):
        with open(inventory_path, 'r') as inventory_file:
          inventory_data = list(csv.DictReader(inventory_file))

  summary_data = summary_to_dict(summary_data)
  inventory_data = inventory_to_dict(inventory_data)

  return render(request, 'test_detail.html', { 'summary_data' : summary_data, 'inventory_data' : inventory_data, 'id':id, 'dealer':dealer_id})

@login_required
def get_dealer(request):
  if request.method == 'POST':
    try:
      domain = request.POST['domain']
      if os.path.isfile(settings.SERVER_DIR + '/input.csv'):
        with open(settings.SERVER_DIR + '/input.csv', 'r', encoding="latin1", errors="ignore") as summary:
          dealer_list = csv.DictReader(summary)
          for dealer in dealer_list:
            if dealer['domain'] == domain:
              return_dict = {
                'domain': dealer['domain'],
                'website': dealer['website'],
                'domain_inputdata': dealer['domain_inputdata'],
                'dealer_type': dealer['crawl_type'],
                'dealer_type_reason': dealer['comment'],
                'dealer_redirect': dealer['redirect_urls'],
                'makes': dealer['makes'],
                'get_description': dealer['get_description'],
              }
              return HttpResponse(json.dumps(return_dict))
      return HttpResponse('not_found')
    except Exception as err:
      print(err)
      return HttpResponse('failed')

@login_required
def update_input(request):
  if request.method == 'POST':
    try:
      domain = request.POST['domain']
      website = request.POST['website']
      inputdata = request.POST['inputdata']
      redirect_urls = request.POST['redirect_urls']
      crawl_type = request.POST['crawl_type']
      comment = request.POST['crawl_type_reason']
      makes = request.POST['makes']
      get_description = request.POST['get_description']

      if os.path.isfile(settings.SERVER_DIR + '/input.csv'):
        temp_list = list()
        with open(settings.SERVER_DIR + '/input.csv', 'r', encoding="latin1", errors="ignore") as input_file:
          temp_list = list(csv.DictReader(input_file))

        with open(settings.SERVER_DIR + '/input.csv', 'w', encoding="latin1", errors="ignore") as input_file:
          fieldnames = ["domain", "website", "domain_inputdata", "makes", "crawl_type", "comment", "redirect_urls", "get_description"]
          writer = csv.DictWriter(input_file, fieldnames=fieldnames)
          writer.writeheader()
          for row_dict in temp_list:
            if row_dict["domain"] == domain:
              row_dict["website"] = website
              row_dict["domain_inputdata"] = inputdata
              row_dict["crawl_type"] = crawl_type
              row_dict["comment"] = comment
              row_dict["redirect_urls"] = redirect_urls
              row_dict["makes"] = makes
              if get_description == "Y":
                row_dict["get_description"] = "Y"
              else:
                row_dict["get_description"] = ""

            writer.writerow(row_dict)
      return HttpResponse('success')
    except Exception as err:
      print(err)
      return HttpResponse('failed')

def input_to_dict(arg1):
  return_data = list()
  for row in arg1:
    temp_dict = dict()
    temp_dict['domain'] = row['domain']
    temp_dict['website'] = row['website']
    temp_dict['domain_inputdata'] = row['domain_inputdata']
    temp_dict['makes'] = row['makes']
    temp_dict['crawl_type'] = row['crawl_type']
    temp_dict['comment'] = row['comment']
    temp_dict['get_description'] = make_url(row['get_description'])

    redirect_list = list()
    if row['redirect_urls']:
      for item in row['redirect_urls'].split(','):
        redirect_list.append(make_url(item))
    temp_dict['redirect_url_list'] = redirect_list

    # test_status = 'notcrawling'
    # history_status = 'nothistory'
    # for item in arg2:
    #   if item.dealer == row['Dealer ID']:
    #     if item.status == 'crawling':
    #       test_status = 'crawling'
    #     if item.status == 'complete' or item.status == 'cancel':
    #       history_status = 'history'
    #
    # temp_dict['test_status'] = test_status
    # temp_dict['history_status'] = history_status

    if temp_dict["domain"]:
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
    try:
      temp_dict['url'] = row['URL']
    except:
      temp_dict['domain'] = row['DOMAIN']
    temp_dict['vin_count'] = row['Vin Count']
    temp_dict['error_state'] = row['Error State']
    try:
      temp_dict['host_address'] = row['Host Address']
    except:
      pass
    
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
    temp_dict['city'] = row['City']
    temp_dict['state'] = row['State']
    temp_dict['zip'] = row['Zip']
    try:
      temp_dict['url'] = row['URL']
    except:
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

def get_data_from_summary(domain, crawl_date):
  return_data = list()
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
      if row['DOMAIN'] == domain:
        return_data.append(row)
  return return_data

def make_domain(url):
  if "http" in url:
      url = url.split("//")[-1].split("/")[0].split('?')[0]
  if "www" in url:
      url = url[4:]
  return url

def make_url(url):
  if not "http" in url and url:
    url = "http://" + url
  return url
