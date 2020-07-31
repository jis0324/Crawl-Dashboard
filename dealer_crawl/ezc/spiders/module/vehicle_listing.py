import csv
import os
import datetime
import requests
from tempfile import NamedTemporaryFile
import shutil
import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def make_vehicle_list(final_dict, csv_name):

    file_exists = os.path.isfile(csv_name)
    with open(csv_name, 'a', newline='') as file:
            fieldnames = ['Dealer ID', 'Dealer Name', 'City', 'State', 'Zip', 'Domain', 'URL', 'VIN', 'Price',
                                    'Mileage', 'Type', 'Title', 'Year', 'Make', 'Model', 'Trim']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                    writer.writeheader()
            writer.writerow(final_dict)

def update_csv(csv_name, value_list, foundVin):
    rows = list()
    fields = ['Dealer ID', 'Dealer Name', 'City', 'State', 'Zip', 'Domain', 'URL', 'VIN', 'Price', 'Mileage', 'Type', 'Title', 'Year', 'Make', 'Model', 'Trim', ]

    with open(csv_name, 'r') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fields)

        for row in reader:
            if row['VIN'] == foundVin:
                if row['Price'] == 'N/A':
                    row['Price'] = value_list[8]
                if row['Mileage'] == 'N/A':
                    row['Mileage'] = value_list[9]
                row['Type'] = value_list[10]
                if row['Title'] == '':
                    row['Title'] = value_list[11]
                if row['Year'] == '':
                    row['Year'] = value_list[12]
                if row['Make'] == '':
                    row['Make'] = value_list[13]
                if row['Model'] == '':
                    row['Model'] = value_list[14]
                if row['Trim'] == '':
                    row['Trim'] = value_list[15]
            row = {'Dealer ID': row['Dealer ID'], 'Dealer Name': row['Dealer Name'], 'City' : row['City'], 'State' : row['State'], 'Zip' : row['Zip'], 'Domain': row['Domain'], 'URL': row['URL'], 'VIN': row['VIN'], 'Price': row['Price'], 'Mileage': row['Mileage'], 'Type': row['Type'], 'Title': row['Title'], 'Year': row['Year'], 'Make': row['Make'], 'Model': row['Model'], 'Trim': row['Trim']}
            rows.append(row)

    os.remove(csv_name)

    with open(csv_name, "a", newline="") as newfile:
        writer = csv.DictWriter(newfile, fieldnames=fields)
        for row in rows:
            writer.writerow(row)

def make_exclude_url(url):
    with open("exclude.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(url)

def sort_summary(vinList):
    tmp_dict = dict()
    while len(vinList) != 0:
        vin = vinList[0]
        count = vinList.count(vin)
        tmp_dict[vin] = count
        for i in range(count):
            vinList.remove(vin)
    return tmp_dict

def write_summary(tmp_dict, summary_csv_name):
    summary_name =  base_dir + "/output/" + summary_csv_name
    file_exists = os.path.isfile(summary_name)
    with open(summary_name, 'a', newline='') as file:
        fieldnames = ['Dealer ID', 'Dealer Name', 'City', 'State', 'Zip', 'URL', 'Vin Count', 'Error State', 'Start Time', 'End Time']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(tmp_dict)

def default_time_format(arg):
    if len(arg) == 1:
        arg = '0' + arg
    return arg

def calc_elapsed_time(arg):
    start_time = arg['start_time']
    end_time = arg['end_time']
    start_time_obj = datetime.datetime.strptime(
        start_time, '%Y-%m-%dT%H:%M:%S')
    end_time_obj = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
    elapsed_time = (end_time_obj - start_time_obj).seconds
    elapsed_hour = int(elapsed_time/3600)
    rest_time = elapsed_time - elapsed_hour * 3600
    elapsed_minute = int(rest_time/60)
    rest_time = rest_time - elapsed_minute * 60
    elapsed_secs = rest_time
    result = default_time_format(str(elapsed_hour)) + "h " + " " + default_time_format(
        str(elapsed_minute)) + "m " + " " + default_time_format(str(elapsed_secs)) + "s"
    return result

def make_spider_summary(dealer_ids, dealer_names, dealer_cities, dealer_states, dealer_zips, urls, domains, summary_vin, summary_novin, summary_dynamic_vin, summary_error, crawl_status, sumamry_csv_name):
    blocksite_dict = dict()
    remove_domains = list()
    summary_dict = dict()
    error_list = list()
    remove_domains = domains.copy()
    found_vindict = sort_summary(summary_vin)
    no_vindict = sort_summary(summary_novin)
    dynamic_vindict = sort_summary(summary_dynamic_vin)
    http_error = sort_summary(summary_error)

    # remove the domain both in found_vindic and no_vindict from no_vindict
    for foundvin_key in found_vindict:
        for novin_key in no_vindict:
            if foundvin_key == novin_key:
                no_vindict.pop(novin_key)
                break

    # remove the domain both in found_vindic and dynamic_vindict from dynamic_vindict
    for foundvin_key in found_vindict:
        for dynamicvin_key in dynamic_vindict:
            if foundvin_key == dynamicvin_key:
                dynamic_vindict.pop(dynamicvin_key)
                break

    # remove the domain both in dynamic_vindict and no_vindict from no_vindict
    for dynamicvin_key in dynamic_vindict:
        for novin_key in no_vindict:
            if novin_key == dynamicvin_key:
                no_vindict.pop(novin_key)
                break

    # remove the domains in found_vindict from remove_domains
    for foundvin_key in found_vindict:
        if foundvin_key in remove_domains:
            remove_domains.remove(foundvin_key)

    # remove the domains in no_vindict from remove_domains
    for novin_key in no_vindict:
        if novin_key in remove_domains:
            remove_domains.remove(novin_key)

    # remove the domains in dynamic_vindict from remove_domains
    for dynamicvin_key in dynamic_vindict:
        if dynamicvin_key in remove_domains:
            remove_domains.remove(dynamicvin_key)

    # remove the domains in http_error from remove_domains
    for http_key in http_error:
        if http_key in remove_domains:
            error_list.append(http_key)
            remove_domains.remove(http_key)

    # remain the domains have not response
    for domain in remove_domains:
        domain_index = domains.index(domain)
        state = "Not Available"
        blocksite_dict[domain] = str(state)

    # crawling successfully
    for key, value in found_vindict.items():
        tmp_dict = dict()
        i = domains.index(key)
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = value
        tmp_dict['Error State'] = 'Crawlable'

        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time

        write_summary(tmp_dict, sumamry_csv_name)
    
    # crawling successfully but not got vin
    for key in no_vindict:
        tmp_dict = dict()
        i = domains.index(key)
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = 'N/A'
        tmp_dict['Error State'] = 'No Inventory'

        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time

        write_summary(tmp_dict, sumamry_csv_name)

    # crawling successfully but not got vin because of dynamic site
    for key in dynamic_vindict:
        tmp_dict = dict()
        i = domains.index(key)
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = 'N/A'
        tmp_dict['Error State'] = 'Browseable'

        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time
        write_summary(tmp_dict, sumamry_csv_name)

    # not got response from request
    for key, values in blocksite_dict.items():
        tmp_dict = dict()
        i = domains.index(key)
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = 'N/A'
        tmp_dict['Error State'] = values

        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time
        write_summary(tmp_dict, sumamry_csv_name)

    # got response from request but response is http error (400 ~ 500)
    for j in range(len(error_list)):
        tmp_dict = dict()
        i = domains.index(error_list[j])
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = 'N/A'
        tmp_dict['Error State'] = "Not Available"

        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time
        write_summary(tmp_dict, sumamry_csv_name)

    csv_name =  base_dir + "/dealer_crawl_inventory.csv"
    file_exists = os.path.isfile(csv_name)
    if file_exists:
        update_csv(csv_name, [], "")

def make_selenium_summary(dealer_ids, dealer_names, dealer_cities, dealer_states, dealer_zips, urls, domains, summary_vin, summary_novin, summary_error, crawl_status, sumamry_csv_name):
    blocksite_dict = dict()
    remove_domains = list()
    summary_dict = dict()
    error_list = list()
    remove_domains = domains.copy()
    found_vindict = sort_summary(summary_vin)
    no_vindict = sort_summary(summary_novin)
    http_error = sort_summary(summary_error)

    # remove the domain both in found_vindic and no_vindict from no_vindict
    for foundvin_key in found_vindict:
        for novin_key in no_vindict:
            if foundvin_key == novin_key:
                no_vindict.pop(novin_key)
                break

    # remove the domains in found_vindict from remove_domains
    for foundvin_key in found_vindict:
        if foundvin_key in remove_domains:
            remove_domains.remove(foundvin_key)

    # remove the domains in no_vindict from remove_domains
    for novin_key in no_vindict:
        if novin_key in remove_domains:
            remove_domains.remove(novin_key)

    # remove the domains in http_error from remove_domains
    for http_key in http_error:
        if http_key in remove_domains:
            error_list.append(http_key)
            remove_domains.remove(http_key)

    # remain the domains have not response
    for domain in remove_domains:
        domain_index = domains.index(domain)
        state = "Not Available"
        blocksite_dict[domain] = str(state)

    # crawling successfully
    for key, value in found_vindict.items():
        tmp_dict = dict()
        i = domains.index(key)
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = value
        tmp_dict['Error State'] = 'Browseable'

        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time
        write_summary(tmp_dict, sumamry_csv_name)
    
    # crawling successfully but not got vin
    for key in no_vindict:
        tmp_dict = dict()
        i = domains.index(key)
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = 'N/A'
        tmp_dict['Error State'] = 'No Inventory'
        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time
        write_summary(tmp_dict, sumamry_csv_name)

    # not got response from request
    for key, values in blocksite_dict.items():
        tmp_dict = dict()
        i = domains.index(key)
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = 'N/A'
        tmp_dict['Error State'] = values
        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time
        write_summary(tmp_dict, sumamry_csv_name)

    # got response from request but response is http error (400 ~ 500)
    for j in range(len(error_list)):
        tmp_dict = dict()
        i = domains.index(error_list[j])
        dealer_id = dealer_ids[i]
        dealer_name = dealer_names[i]
        dealer_city = dealer_cities[i]
        dealer_state = dealer_states[i]
        dealer_zip = dealer_zips[i]
        url = urls[i]
        tmp_dict['Dealer ID'] = dealer_id
        tmp_dict['Dealer Name'] = dealer_name
        tmp_dict['City'] = dealer_city
        tmp_dict['State'] = dealer_state
        tmp_dict['Zip'] = dealer_zip
        tmp_dict['URL'] = url
        tmp_dict['Vin Count'] = 'N/A'
        tmp_dict['Error State'] = "Not Available"
        start_time = ''
        end_time = ''
        if domains[i] in crawl_status:
            start_time = crawl_status[domains[i]][0]
            end_time = crawl_status[domains[i]][1]

        tmp_dict['Start Time'] = start_time
        tmp_dict['End Time'] = end_time
        write_summary(tmp_dict, sumamry_csv_name)

    csv_name =  base_dir + "/dealer_crawl_inventory.csv"
    file_exists = os.path.isfile(csv_name)
    if file_exists:
        update_csv(csv_name, [], "")

