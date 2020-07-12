from django.contrib.auth.models import User
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
import pymongo
import datetime
import configparser
from django.conf import settings

mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["dealer_crawl_db"]
unexpected_urls_collection = db['unexpected_urls']

@login_required
def index(request):
  print(request.user)
  return redirect('crawl_index')

@login_required
def unexpected_urls(request):
  unexpected_url_data = list()
  now = datetime.datetime.now()  
  today_date = now.strftime("%Y-%m-%d")
  
  if request.method == "POST":
    crawl_date = request.POST['selected_date']
    unexpected_url_data = get_data_from_crawl_date(crawl_date)
    return render(request, 'unexpected_urls.html', {'data': unexpected_url_data, 'today_date' : today_date, 'crawl_date' : crawl_date})

  crawl_date, unexpected_url_data = get_data()
  return render(request, 'unexpected_urls.html', {'data': unexpected_url_data, 'today_date' : today_date, 'crawl_date' : crawl_date})

@login_required
def config_settings(request):
  config = configparser.ConfigParser()
  config_file = settings.SERVER_DIR + "/config.ini"
  config.read( config_file )

  if request.method == "POST":
    try:
      config.set('Server', 'HOST', str(request.POST['host']))
      config.set('Server', 'PORT', str(request.POST['port']))
      config.set('Server', 'START_TIME', str(request.POST['crawler_start_time']))
      config.set('Server', 'INTERVAL_HOURS', str(request.POST['crawler_interval_time']))
      config.set('Server', 'URLS_PER_SPIDER_CLIENT', str(request.POST['url_per_spider_crawler']))
      config.set('Server', 'URLS_PER_SELENIUM_CLIENT', str(request.POST['url_per_selenium_crawler']))
      config.set('Server', 'SPIDER_CLIENTS', str(request.POST['spider_crawlers'].replace('\n', ',')))
      config.set('Server', 'SELENIUM_CLIENTS', str(request.POST['selenium_crawlers'].replace('\n', ',')))
      config.set('Server', 'UPDATE_STATUS', str(request.POST['update_status']))
      config.set('Server', 'PROCESS_NUM_FOR_SPIDER_CLIENTS', str(request.POST['process_per_crawler']))

      # Writing our configuration file to 'example.ini'
      with open( config_file, 'w' ) as configfile:
          config.write(configfile)

      return HttpResponse('success')
    except:
      return HttpResponse('failed')

  else:
    return_data = {
      "host" : config['Server']['HOST'],
      "port" : config['Server']['PORT'],
      "crawler_start_time" : config["Server"]["START_TIME"],
      "crawler_interval_time" : config['Server']['INTERVAL_HOURS'],
      "url_per_spider_crawler" : config['Server']['URLS_PER_SPIDER_CLIENT'],
      "url_per_selenium_crawler" : config['Server']['URLS_PER_SELENIUM_CLIENT'],
      "spider_crawlers" : config['Server']['SPIDER_CLIENTS'].split(','),
      "selenium_crawlers" : config['Server']['SELENIUM_CLIENTS'].split(','),
      "update_status" : config['Server']['UPDATE_STATUS'],
      "process_per_crawler" : config['Server']['PROCESS_NUM_FOR_SPIDER_CLIENTS'],
    }

    return render(request, 'settings.html', {'data' : return_data})

def get_data():
  global unexpected_urls_collection

  unexpected_urls_data = list()
  
  today_date = datetime.date.today()
  yesterday_date = today_date - datetime.timedelta(days=1)
  
  query = { "date": { "$regex": "^" + str(today_date) } }
  if unexpected_urls_collection.count_documents(query) > 0:
    unexpected_urls_data = list(unexpected_urls_collection.find(query))
    return str(today_date), unexpected_urls_data
  else:
    query = { "date": { "$regex": "^" + str(yesterday_date) } }
    unexpected_urls_data = list(unexpected_urls_collection.find(query))
    return str(yesterday_date), unexpected_urls_data

def get_data_from_crawl_date(crawl_date):
  global unexpected_urls_collection

  unexpected_urls_data = list()
  query = { "date": { "$regex": "^" + crawl_date } }
  unexpected_urls_data = list(unexpected_urls_collection.find(query))
  return unexpected_urls_data
