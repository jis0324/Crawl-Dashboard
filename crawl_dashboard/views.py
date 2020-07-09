from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import pymongo
import datetime

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
  today_date = now.strftime("%Y") + '-' + now.strftime("%m") + '-' + now.strftime("%d")
  
  if request.method == "POST":
    crawl_date = request.POST['selected_date']
    unexpected_url_data = get_data_from_crawl_date(crawl_date)
    return render(request, 'unexpected_urls.html', {'data': unexpected_url_data, 'today_date' : today_date, 'crawl_date' : crawl_date})

  crawl_date, unexpected_url_data = get_data()
  return render(request, 'unexpected_urls.html', {'data': unexpected_url_data, 'today_date' : today_date, 'crawl_date' : crawl_date})

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
