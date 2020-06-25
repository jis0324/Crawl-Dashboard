import re
from html.parser import HTMLParser
import time
parser_result = ''

class MyHTMLParser(HTMLParser):

    def handle_data(self, data):
        global parser_result
        parser_result = parser_result + ' ' + data

parser = MyHTMLParser()

def is_vin_valid(vinList, myDomain):
    try:
        valid_vinList = list()
        for field in vinList:
            POSITIONAL_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
            ILLEGAL_ALL = ['I', 'O', 'Q']
            ILLEGAL_TENTH = ['U', 'Z', '0']
            LETTER_KEY = dict(
                A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8,
                J=1, K=2, L=3, M=4, N=5,    P=7,    R=9,
                S=2, T=3, U=4, V=5, W=6, X=7, Y=8, Z=9,
            )

            if len(field) == 17:
                vin = field.upper()

                for char in ILLEGAL_ALL:
                    if char in vin:
                        continue
                if vin[9] in ILLEGAL_TENTH:
                    continue
                check_digit = vin[8]

                pos = sum = 0
                for char in vin:
                    value = int(LETTER_KEY[char]) if char in LETTER_KEY else int(char)
                    weight = POSITIONAL_WEIGHTS[pos]
                    sum += (value * weight)
                    pos += 1

                calc_check_digit = int(sum) % 11

                if calc_check_digit == 10:
                    calc_check_digit = 'X'

                if str(check_digit) != str(calc_check_digit):
                    continue
                else:
                    if not vin in valid_vinList:
                        valid_vinList.append(vin)
            else:
                continue
        
        if myDomain != 'compasautos.com' and len(valid_vinList) > 9:
            return 0
        elif len(valid_vinList) == 0:
            return 0
        else:
            return valid_vinList[0]
    except:
        return 0

def make_price(price):
    if price == 'N/A':
        return price
    else:
        price = re.sub('\$|\,|\s|[a-zA-Z]', '', price)
        price = price.rsplit('.', 1)[0]
        try:
            return_price = "${:,.0f}".format(int(price))
            return return_price
        except:
            return 'N/A'

def make_mile(mile):
    if mile == 'N/A':
        return mile
    else:
        mile = re.sub('\,|[a-zA-Z]|\s', '', mile)
        mile = mile.rsplit('.', 1)[0]
        try:
            return "{:,.0f}".format(int(mile))
        except:
            return 'N/A'

def find_vin(response, myDomain):
    try:
        vinList = list()
        vin_rex = re.compile(
            r"\>\s*([A-HJ-NPR-Z0-9]{17})\s*\<|\>\s*(VIN:[A-HJ-NPR-Z0-9]{17})|\>(VIN:\s*[A-HJ-NPR-Z0-9]{17})")

        for x in vin_rex.finditer(response):
            foundVin = x.group()
            vin = re.search(r"[A-HJ-NPR-Z0-9]{17}", foundVin).group()
            if vin not in vinList:
                vinList.append(vin)
            
            # if not re.search(r'\d{17}', vin):
            #     vinList.append(vin)

        vin_candidate = re.compile("\>\s*([A-HJ-NPR-Z0-9]{17})")
        for x in vin_candidate.finditer(response):
            foundVin = x.group()
            vin_startpos = x.start()
            vin_range = (response)[vin_startpos - 200:vin_startpos]
            if re.search(r'vin\:?\=?', vin_range, re.I):
                vin = re.search(r"[A-HJ-NPR-Z0-9]{17}", foundVin).group()
                if vin not in vinList:
                    vinList.append(vin)
                                
        vin_rex = re.compile(r"[^a-zA-Z0-9]([A-HJ-NPR-Z0-9]{17})[^a-zA-Z0-9]")

        for x in vin_rex.finditer(response):
            foundVin = x.group()
            vin = re.search(r"[A-HJ-NPR-Z0-9]{17}", foundVin).group()
            if vin not in vinList:
                vinList.append(vin)

        valid_vin = is_vin_valid(vinList, myDomain)

        if valid_vin:
            return valid_vin
        else:
            vin_candidate = re.compile("[^a-zA-Z0-9]([a-hj-npr-z0-9]{17})[^a-zA-Z0-9]")
            for x in vin_candidate.finditer(response):
                foundVin = x.group()
                vin_startpos = x.start()
                vin_range = (response)[vin_startpos - 200:vin_startpos]
                if re.search(r'[^a-zA-Z0-9]vin[^a-zA-Z0-9]|[^a-zA-Z0-9]serial[^a-zA-Z0-9]|[^a-zA-Z0-9]identification[^a-zA-Z0-9]', vin_range, re.I):
                    vin = re.search(r"[a-hj-npr-z0-9]{17}", foundVin).group()
                    valid_vin = is_vin_valid([vin], myDomain)
                    if valid_vin:
                        return valid_vin
    except:
        pass

    return None

def find_price_for_each(response, scope_range, price_pattern_priority, include_pattern, exclude_pattern):
    try:
        for x in price_pattern_priority.finditer(response):
            price_start_pos = x.start()
            price_substring = response[price_start_pos - scope_range : price_start_pos + scope_range]
            if re.search(r'price|pricing|internetvalue|specialvalue|salevalue|askingDetail|\>\s*NOW\s*\<|showroomvalue|car_name_right', price_substring, re.I):
                if exclude_pattern.search(price_substring):
                    continue
                if include_pattern.search(price_substring):
                    price = x.group()[1:]
                    if len(re.sub('\,|\$', '', price.split('.')[0])) > 7:
                        return None
                    return price
        return None
    except: 
        return None

def find_price(response):
    try:
        price_dismatch_pattern1 = re.compile(r'(\>\s*call\s+for\s+price)', re.I)
        price_dismatch_pattern2 = re.compile(r'(\>\s*get\s+eprice)', re.I)
        body_start_pos = response.find('<body')
        body_end_pos = response.find('</body>')
        if body_start_pos < 0 or body_end_pos < 0:
            if price_dismatch_pattern1.search(response) or price_dismatch_pattern2.search(response):
                return None
        else:
            # if price_dismatch_pattern2.search(response):
            #     return None
            pass
    except:
        pass

    try:
        price_pattern_priority_list = [
            re.compile(r'[\s\"\'\>\:](\$\d+\s?\,\d{3}\.\d{2})|[\s\"\'\>\:](\$\d+\s?\,\d{3})|[\s\"\'\>\:](\$\d+\s?\d{3})'),
            re.compile(r'[\s\"\'\>\:](\d+\,\d{3}\.\d{2})|[\s\"\'\>\:](\d+\,\d{3})|[\s\"\'\>\:](\d+\d{3})')
        ]
        exclude_pattern1 = re.compile(r'original|MSRP|Month|under\s|Less\s|\-\s*\$|saving|related|recommended|similar|Listed|endprice|startprice|priceIncrement|Retail|\scash|\sfee|\sBonus|discount|\scustomer|pricerange|slideshow|Enganche|\<del\>|\-extra|\>was\<|Get\s*Sale\s*Price|data\-year|[\s\"\']offer|\<meta|\sdown|increases|http|engine|href|year', re.I)
        exclude_pattern = re.compile(r'original|MSRP|Month|under\s|Less\s|\-\s*\$|saving|related|recommended|similar|Listed|endprice|startprice|priceIncrement|\scash|\sfee|\sBonus|discount|\scustomer|pricerange|slideshow|Enganche|\<del\>|\-extra|\>was\<|Get\s*Sale\s*Price|data\-year|[\s\"\']offer|\<meta|\sdown|increases|http|engine|href|year', re.I)
        exclude_pattern2 = re.compile(r'original|Month|under|Less\s|\-\s*\$|saving|related|recommended|similar|Listed|endprice|startprice|priceIncrement|\scash|\sfee|\sBonus|discount|\scustomer|pricerange|slideshow|Enganche|\<del\>|\-extra|\>was\<|Get\s*Sale\s*Price|data\-year|[\s\"\']offer|\<meta|\sdown|increases|http|engine|href|year', re.I)
        include_pattern_list = [
            re.compile(r'discount[\s\'\"]', re.I),
            re.compile(r'Your Killer Deal', re.I),
            re.compile(r'(Schumacher.?Price)(Ctabox.?Price)', re.I),
            re.compile(r'Manager\'s.?Special', re.I),
            re.compile(r'Price.?Now', re.I),
            re.compile(r'Today\'s.?price', re.I),
            re.compile(r'price\-1', re.I),
            re.compile(r'price\-2', re.I),
            re.compile(r'price\-3', re.I),
            re.compile(r'price\-font', re.I),
            re.compile(r'Special.?Price', re.I),
            re.compile(r'Final.?Price', re.I),
            re.compile(r'priceCurrency', re.I),
            re.compile(r'Lowest.?Price', re.I),
            re.compile(r'low.?Price', re.I),
            re.compile(r'unit.?Price', re.I),
            re.compile(r'lbl.?Price', re.I),
            re.compile(r'item__.?Price', re.I),
            re.compile(r'priceSpecification', re.I),
            re.compile(r'Sale.?Price', re.I),
            re.compile(r'Selling.?Price', re.I),
            re.compile(r'base.?Price', re.I),
            re.compile(r'price.?tag', re.I),
            re.compile(r'reduce.?Price', re.I),
            re.compile(r'inventory.?Price', re.I),
            re.compile(r'internet.?Price', re.I),
            re.compile(r'detail.?Price', re.I),
            re.compile(r'asking.?price', re.I),
            re.compile(r'vehicle.?cost', re.I),
            re.compile(r'vehicle.?Price', re.I),
            re.compile(r'gp.?veh.?intprice', re.I),
            re.compile(r'our.?price', re.I),
            re.compile(r'page.?price', re.I),
            re.compile(r'vdp.?price', re.I),
            re.compile(r'pricing.?value', re.I),
            re.compile(r'internetvalue', re.I),
            re.compile(r'specialvalue', re.I),
            re.compile(r'salevalue', re.I),
            re.compile(r'showroomvalue', re.I),
            re.compile(r'website.?price', re.I),
            re.compile(r'\>\s*now\s*\<', re.I),
            re.compile(r'value.?price', re.I),
            re.compile(r'Best.?Price', re.I),
            re.compile(r'Obaugh.?E-Price', re.I),
            re.compile(r'Cox.?Price', re.I),
            re.compile(r'Classic.?Price', re.I),
            re.compile(r'Net.?Price', re.I),
            re.compile(r'Ctabox.?Price', re.I),
            re.compile(r'discounted.?price', re.I),
            re.compile(r'price.?display', re.I),
            re.compile(r'Exclusive', re.I),
            re.compile(r'clearCut.?price', re.I),
            re.compile(r'Retail.?price', re.I),
            re.compile(r'hit.?price', re.I),
            re.compile(r'[\s\'\"\>]price[\s\'\"\<]', re.I),
            re.compile(r'regular.?price', re.I),
            re.compile(r'price\s?\:', re.I),
            re.compile(r'high.?price', re.I),
            re.compile(r'askingDetail', re.I),
        ]
    

        for index, price_pattern_priority in enumerate(price_pattern_priority_list):

            scope_range = 50
            while scope_range < 101:
                
                include_pattern = re.compile(r'AAg.?Price', re.I)
                real_price = find_price_for_each(response, scope_range, price_pattern_priority, include_pattern, exclude_pattern1)
                if real_price:
                    return real_price

                scope_range += 50

            for include_pattern in include_pattern_list:
                scope_range = 50
                while scope_range < 101:
                    if index == 0:
                        exclude_pattern = re.compile(r'finance|original|MSRP|Month|under\s|Less\s|\-\s*\$|saving|related|recommended|similar|Listed|endprice|startprice|priceIncrement|\scash|\sfee|\sBonus|discount|\scustomer|pricerange|slideshow|Enganche|\<del\>|\-extra|\>was\<|Get\s*Sale\s*Price|data\-year|[\s\"\']offer|\<meta|\sdown|increases|http|engine|href', re.I)
                    
                    real_price = find_price_for_each(response, scope_range, price_pattern_priority, include_pattern, exclude_pattern)
                    if real_price:
                        return real_price

                    scope_range += 50

            scope_range = 50
            while scope_range < 101:

                include_pattern = re.compile(r'MSRP', re.I)
                real_price = find_price_for_each(response, scope_range, price_pattern_priority, include_pattern, exclude_pattern2)
                if real_price:
                    return real_price

                scope_range += 50

    except:
        pass
    
    return None

def find_mileage(response):
    try:
        except_pattern = re.compile(r'location|consignment|month|range|[^a-zA-Z]max[^a-zA-Z]|[^a-zA-Z]min[^a-zA-Z]|[^a-zA-Z]EPA[^a-zA-Z]|Year|distance|basic\s|lease|https|\<option|highway|\stotal|freycon|http|under\s', re.I)
    
        # **,*** mi(le)
        mile_rex = re.compile(r"(\d+\,\d{3})\s*mi", re.I)
        for x in mile_rex.finditer(response):
            foundMile = x.group()
            miles_pos = x.start()
            miles_range = (response)[miles_pos - 100 : miles_pos + 100]
            if except_pattern.search(miles_range):
                continue
            mileageMatch = re.findall(r"(\d+\,\d{3})", foundMile)
            if len(mileageMatch) > 0:
                return mileageMatch[0]

        mileage_rex = re.compile(r'Mileage\:',re.I)
        for x in mileage_rex.finditer(response):
            miles_pos = x.start()
            miles_range = (response)[miles_pos - 100 : miles_pos + 100]
            if except_pattern.search(miles_range):
                continue
            real_mile_range = response[x.end() : x.end() + 100]
            mileageMatch_pattern_list = [
                re.compile("(\d+\,\s*\d{3})"),
                re.compile("(\d+\d{3})"),
                re.compile("([^\d\,]\d{3}[^\d]\,)"),
                re.compile("(\d+)\s?(km|mile|miles|mi)")
            ]
            
            for mileageMatch_pattern in mileageMatch_pattern_list:
                for z in mileageMatch_pattern.finditer(real_mile_range):
                    mile = z.group()
                    if mileageMatch_pattern == mileageMatch_pattern_list[3]:
                        if 'km' in mile:
                            mile = int(int(re.search('\d+', mile).group()) / 1.6)
                    return str(mile)

        mile_rex = re.compile(r"(\d{3}|\d+)\s*Miles", re.I)
        for x in mile_rex.finditer(response):
            foundMile = x.group()
            miles_pos = x.start()
            miles_range = (response)[miles_pos - 100 : miles_pos + 100]
            if except_pattern.search(miles_range):
                continue
            mileageMatch = re.findall(r"(\d+|\d{3})", foundMile)
            if len(mileageMatch) > 0:
                return mileageMatch[0]

        mileage_rex = re.compile("MILEAGE", re.I)
        for x in mileage_rex.finditer(response):
            miles_pos = x.end()
            miles_range = (response)[miles_pos - 100 : miles_pos + 100]
            if except_pattern.search(miles_range):
                continue

            mileageMatch_pattern1 = re.compile("[\s\:\"\'\>](\d+\,\s*\d{3})")
            mileageMatch_pattern2 = re.compile("[\s\:\"\'\>](\d+\d{3})")
            for z in mileageMatch_pattern1.finditer(miles_range):
                mile = z.groups()[0]
                return mile
            
            for z in mileageMatch_pattern2.finditer(miles_range):
                mile = z.groups()[0]
                return mile
            

        mileage_rex = re.compile("Miles", re.I)
        for x in mileage_rex.finditer(response):
            miles_pos = x.end()
            miles_range = (response)[miles_pos - 100 : miles_pos + 50]
            if except_pattern.search(miles_range):
                continue
            mileageMatch_pattern1 = re.compile("[\"\>\'](\d+\,\s*\d{3})")
            mileageMatch_pattern2 = re.compile("[\"\>\'](\d+\d{3})")
            mileageMatch_pattern3 = re.compile("[\"\>\'](\d+)K[\s\<]")
            for z in mileageMatch_pattern1.finditer(miles_range):
                mile = z.groups()[0]
                return mile
            
            for z in mileageMatch_pattern2.finditer(miles_range):
                mile = z.groups()[0]
                return mile

            for z in mileageMatch_pattern3.finditer(miles_range):
                mile = z.groups()[0] + '000'
                return mile
    except:
        pass
    return None

def find_used(response, mileage):
    try:
        if mileage != None:
            mile = float(mileage.replace(",", ""))
            if mile > 100:
                return "Used"
            else:
                return "New"
        else:
            return "New"
    except:
        return "New"

def find_title_info(response, domain):
    global parser_result, parser

    result_dict = {
        'Title': '',
        'Year':  '',
        'Make': '',
        'Model': '',
        'Trim': ''
    }
    try:
        # get title
        title_exception_pattern = re.compile(r'weight\s|EPA\s|\=|\sConfirm|\sMobile|\sFax|Please|All right|Feature\s|Since\s|Copyright\s|Search\s|Text\sUs|Click\s|Check\s|offer\s|Make\s|Model\s|Request\s|more\s|Today\'s|What\'s|Photos\s|Compare\s|Contact\s|Website\s|\sDetails|Phone\s|http|Service\s|Select\s|Sales\s|month\s|Watch\s|Inventory\s|\sInventory|Text.?us|\sShop')
        ymmt_exception_pattern = re.compile(r'\sVIN|bodystyle|with|mileage|door|miles|\||\sTrain', re.I)
        title_pattern_array = [
            # from claesses of DIV tag
            re.compile(r'class\s*\=*\s*[\"\']\s*\w*(car\_name\_kia|gp\-veh\-make\-model|titleDetail|title[\s\'\"])', re.I),
            # from classes of H tag
            re.compile(r'<(h\d).*(((class|id)\=\"*\'*.*(vehicle.?title|vehicle.?name|vehicle.?details.?title|vehicleNameWrap|entry.?title|detailVehicleName|Vehicle.?info|PageTitle|DetailsTitleText|vehicleTitle|page.?heading|post.?title|title|GenCarInfo|ar_vehtitle))|(itemprop\=\"*\'*.*name))', re.I),
            # from classes of P tag
            re.compile(r'\<p.*class\s*\=\s*[\'\"].*(captionSerios|vehicle-year-make-model).*[\'\"].*\>.*(20\d{2}|19\d{2})[^\d].*\<\/p\>', re.I),
            # from all H tag finally
            re.compile(r'\<h\d.*[^\d](20\d{2}|19\d{2})[^\d].*\<\/h\d\>', re.I),

        ]

        if 'workmansnv.com' in domain :
            title_pattern = re.compile(r'\<div\sclass\=\"[\s\w\d]*\svehicle\_title\"\>([\w\s\+\-\=\"\'\/\,\.\!\@\#\%\^\&\*\(\)\;]*)', re.I)
            if title_pattern.search(response):
                substring = title_pattern.search(response)
                result_dict['Title'] = substring.groups()[0]
        elif 'w1w024.financeexpress.com' in domain:
            title_pattern = re.compile(r'\<b\>(20\d{2}|19\d{2})', re.I)
            if title_pattern.search(response):
                substring = response[ title_pattern.search(response).start() + 3 : title_pattern.search(response).start() + 200 ]
                title = substring.split('</b>', 1)[0]
                result_dict['Title'] = re.sub('&nbsp;', ' ', title)
        elif 'desertmotor.com' in domain:
            title_pattern = re.compile(r'\<span\sitemprop\=\"name\"\>', re.I)
            if title_pattern.search(response):
                substring = title_pattern.search(response)
                start_pos = substring.span()[0]
                end_pos = substring.span()[1] + 200
                substring = response[start_pos: end_pos]
                substring = substring.rsplit('</span>', 1)[0]
                parser_result = ''
                parser.feed(substring)
                parser_result = re.sub('\s+', ' ', parser_result)
                parser_result = re.sub('^\s+|\s+$', '', parser_result)
                result_dict['Title'] = parser_result
        else:
            for title_tag_pattern in title_pattern_array:
                if result_dict['Title']:
                    break
                
                if title_tag_pattern == title_pattern_array[1]:
                    response = re.sub('\<\/h1\>', '</h1>\n', response)
                    response = re.sub('\<\/h2\>', '</h2>\n', response)
                    response = re.sub('\<\/h3\>', '</h3>\n', response)
                    response = re.sub('\<\/h4\>', '</h4>\n', response)
                    response = re.sub('\<\/h5\>', '</h5>\n', response)
                    response = re.sub('\<\/h6\>', '</h6>\n', response)
                elif title_tag_pattern == title_pattern_array[2]:
                    response = re.sub('\<\/p\>', '</p>\n', response)
                    
                for title in title_tag_pattern.finditer(response):
                    try:
                        if title_tag_pattern == title_pattern_array[0]:
                            substring = response[ title.start() : title.start() + 300 ]
                            substring = substring.split('</div>')[0]
                        else:
                            if title_tag_pattern == title_pattern_array[1]:
                                substring = response[ title.start() : title.start() + 300 ]
                                substring = substring.split('</'+title.groups()[0]+'>')[0]
                            else:
                                substring = title.group()

                        parser_result = ''
                        parser.feed(substring)
                        parser_result = re.sub('\s+', ' ', parser_result)
                        parser_result = re.sub('^\s+|\s+$', '', parser_result)

                        # exception processing
                        if re.search(r'\>', parser_result):
                            parser_result = re.split(r'\>', parser_result)[1]

                        if title_exception_pattern.search(parser_result):
                            continue
                        
                        if "price" in re.split('20\d{2}|19\d{2}', parser_result)[0] or "$" in re.split('20\d{2}|19\d{2}', parser_result)[0]:
                            parser_result = re.search('20\d{2}|19\d{2}', parser_result).group() + re.split('20\d{2}|19\d{2}', parser_result)[1]
                            
                        if len(parser_result) < 200 and re.search('20\d{2}|19\d{2}', parser_result) and len(re.split('\s', parser_result)) > 2:
                            result_dict['Title'] = parser_result
                            break
                    except :
                        continue

            if result_dict['Title'] == '':
                try:
                    check_title_pattern = re.compile('\<title.+\<\/title\>')
                    if check_title_pattern.search(response):
                        substring = check_title_pattern.search(response)
                        substring = substring.group()
                        parser_result = ''
                        parser.feed(substring)
                        parser_result = re.sub('\s+', ' ', parser_result)
                        parser_result = re.sub('^\s+|\s+$', '', parser_result)

                        split_pattern = re.compile(r'\||\sFor\s|-For-|_For_|\sIn\s|-In-|_In_', re.I)
                        parser_result = split_pattern.split(parser_result)[0]
                    
                        if not title_exception_pattern.search(parser_result) and not len(re.findall(r'20\d{2}|19\d{2}', parser_result)) > 1:
                            if len(parser_result) < 200 and re.search('20\d{2}|19\d{2}', parser_result) and len(re.split('\s', parser_result)) > 2:
                                result_dict['Title'] = parser_result
                except:
                    pass

            if result_dict['Title'] == '':
                try:
                    response = re.sub('\<\/a\>', '</a>\n', response)
                    check_title_pattern_array = [
                        re.compile(r'\<a [\w \<\>\+\-\=\"\'\/\,\.\!\@\#\%\^\&\*\(\)\;\?\:]*(20\d{2}|19\d{2})[\w \<\>\+\-\=\"\'\/\,\.\!\@\#\%\^\&\*\(\)\;\?\:]*\<\/a\>'),
                        re.compile(r'\<a [\w \<\>\+\-\=\"\'\/\,\.\!\@\#\%\^\&\*\(\)\;\?\:]*(20\d{2}|19\d{2})[ \w\d\.]*\<\/a\>'),
                    ]
                    for check_title_pattern in check_title_pattern_array:
                        if result_dict['Title']:
                            break

                        for title_a_tag in check_title_pattern.finditer(response):
                            substring = title_a_tag.group()
                            parser_result = ''
                            parser.feed(substring)
                            parser_result = re.sub('\s+', ' ', parser_result)
                            parser_result = re.sub('^\s+|\s+$', '', parser_result)
                            duplicate_list = re.findall('20\d{2}|19\d{2}', parser_result)
                            if len(duplicate_list) >= 2:
                                if duplicate_list[0] == duplicate_list[1]:
                                    parser_result = duplicate_list[0] + parser_result.split(duplicate_list[0])[-1]
                            
                            # exception processing
                            if re.search(r'\>', parser_result):
                                parser_result = re.split(r'\>', parser_result)[1]

                            if title_exception_pattern.search(parser_result):
                                continue

                            if not title_exception_pattern.search(parser_result) and not len(re.findall(r'20\d{2}|19\d{2}', parser_result)) > 1:
                                if len(parser_result) < 200 and re.search('20\d{2}|19\d{2}', parser_result) and len(re.split('\s', parser_result)) > 2:
                                    result_dict['Title'] = parser_result
                                    break
                except:
                    pass

            if result_dict['Title'] == '':
                try:
                    check_year_pattern = re.compile(r'class\s*=\s*[\'\"](CarYearTitle)')
                    check_mmt_pattern = re.compile(r'id\s*=\s*[\'\"](DataList1_LblItemCarName)')
                    for x in check_year_pattern.finditer(response):
                        year_string = response[ x.start() : x.end() + 50 ]
                        if re.search('20\d{2}|19\d{2}', year_string):
                            year = re.search('20\d{2}|19\d{2}', year_string).group()
                            for y in check_mmt_pattern.finditer(response):
                                mmt =  response[ y.start() : y.end() + 150 ]
                                parser_result = ''
                                parser.feed(mmt)
                                parser_result = re.sub('\s+', ' ', parser_result)
                                parser_result = re.sub('^\s+|\s+$', '', parser_result)
                                parser_result = re.sub('^\s+|\s+$', '', parser_result)

                                if re.search('\>', parser_result):
                                    parser_result = re.split(r'\>', parser_result)[1]

                                title = year + ' ' + parser_result

                                # exception processing
                                if re.search(r'\>', title):
                                    title = re.split(r'\>', title)[1]

                                if title_exception_pattern.search(title):
                                    continue

                                if not title_exception_pattern.search(parser_result) and not len(re.findall(r'20\d{2}|19\d{2}', parser_result)) > 1:
                                    if len(title) < 200 and re.search('20\d{2}|19\d{2}', title) and len(re.split('\s', title)) > 2:
                                        result_dict['Title'] = title
                except:
                    pass

            if result_dict['Title'] == '':
                try:
                    parser_start_data = ''
                    parser_data = ''
                    parser_end_data = ''
                    td_value_list = list()
                    

                    class MyHTMLParser1(HTMLParser):
                        td_tag_flag = False
                        def handle_starttag(self, tag, attrs):
                            if tag == 'td':
                                self.td_tag_flag = True

                        def handle_endtag(self, tag):
                            if tag == 'td':
                                self.td_tag_flag = False

                        def handle_data(self, data):
                            if self.td_tag_flag == True:
                                td_value_list.append(data)

                    parser1 = MyHTMLParser1()
                    parser1.feed(response)
                    
                    for x in td_value_list:
                        
                        
                        x = re.sub('\s+', ' ', x)
                        x = re.sub('^\s+|\s+$', '', x)
                        x = re.sub('^\s+|\s+$', '', x)
                        # exception processing
                        if re.search(r'\>', x):
                            x = re.split(r'\>', x)[1]

                        if title_exception_pattern.search(x):
                            continue

                        if not title_exception_pattern.search(x) and not len(re.findall(r'20\d{2}|19\d{2}', x)) > 1:
                            if len(x) < 200 and re.search('20\d{2}|19\d{2}', x) and len(re.split('\s', x)) > 2:
                                result_dict['Title'] = x
                                break
                except:
                    pass

            if result_dict['Title'] == '':
                try:
                    if not re.search(r'\<\/body\>', response):
                        check_title_pattern = re.compile('\<b.+\<\/b\>')
                        if check_title_pattern.search(response):
                            substring = check_title_pattern.search(response)
                            substring = substring.group()
                            parser_result = ''
                            parser.feed(substring)
                            parser_result = re.sub('\s+', ' ', parser_result)
                            parser_result = re.sub('^\s+|\s+$', '', parser_result)

                            if not title_exception_pattern.search(parser_result) and not len(re.findall(r'20\d{2}|19\d{2}', parser_result)) > 1:
                                if len(parser_result) < 200 and re.search('20\d{2}|19\d{2}', parser_result) and len(re.split('\s', parser_result)) > 2:
                                    result_dict['Title'] = parser_result

                except:
                    pass
                
        ymmt_pattern_array = [
            [ re.compile('\>(\s*Year:?\s*)\<', re.I), re.compile('\>(\s*Make:?\s*)\<', re.I), re.compile('\>(\s*Model:?\s*)\<', re.I), re.compile('\>(\s*Trim:?\s*)\<', re.I)],
            [ re.compile('(data-year)\s*[\=\:]\s*\"*\'*', re.I), re.compile('(data-make)\s*[\=\:]\s*\"*\'*', re.I), re.compile('(data-model)\s*[\=\:]\s*\"*\'*', re.I), re.compile('(data-trim)\s*[\=\:]\s*\"*\'*', re.I)],
            [ re.compile('(ff_year)\s*[\=\:]\s*\"*\'*', re.I), re.compile('(ff_make)\s*[\=\:]\s*\"*\'*', re.I), re.compile('(ff_model)\s*[\=\:]\s*\"*\'*', re.I), re.compile('(ff_trim)\s*[\=\:]\s*\"*\'*', re.I)],
            [ re.compile('([\"\']year[\"\'])\s*[\=\:]\s*\"*\'*', re.I), re.compile('([\"\']make[\"\'])\s*[\=\:]\s*\"*\'*', re.I), re.compile('([\"\']model[\"\'])\s*[\=\:]\s*\"*\'*', re.I), re.compile('([\"\']trim[\"\'])\s*[\=\:]\s*\"*\'*', re.I)],
            [ re.compile('(itemprop\s*\=*\s*\"*\'*vehicleModelDate\"*\'*)', re.I), re.compile('(itemprop\s*\=*\s*\"*\'*manufacturer\"*\'*)', re.I), re.compile('(itemprop\s*\=*\s*\"*\'*model\"*\'*)', re.I), re.compile('(itemprop\s*\=*\s*\"*\'*vehicleConfiguration\"*\'*)', re.I)],
        ]

        response = re.sub('\r|\n', '', response)       
        response = re.sub('\>\s*\<', '><', response)      # remove all \n

        for sample in ymmt_pattern_array:
            for match_string in sample[0].finditer(response):
                match_string_start_pos = match_string.span()[0] - 100
                match_string_end_pos = match_string.span()[1] + 1000
                substring = response[match_string_start_pos:match_string_end_pos]   # select string scope 
                if all(item.search(substring) for item in sample):
                    if sample == ymmt_pattern_array[0]:
                        if '<' in substring:
                            substring = '<' + substring.split('<', 1)[1]    # trim string start position
                        if '>' in substring:
                            substring = substring.rsplit('>', 1)[0] + '>'   # trim string end position
                        substring = re.sub('\>\s*\<', '><', substring)  # remove spaces between tags
                        
                        value_year = substring[(sample[0].search(substring)).span()[0] + len((sample[0].search(substring)).groups()[0]) + 1 : (sample[1].search(substring)).span()[0] + 1]        # select 'Year:' scope 
                        value_make = substring[(sample[1].search(substring)).span()[0] + len((sample[1].search(substring)).groups()[0]) + 1 : (sample[2].search(substring)).span()[0] + 1]       # select 'Make:' scope 
                        value_model = substring[(sample[2].search(substring)).span()[0] + len((sample[2].search(substring)).groups()[0]) + 1 : (sample[3].search(substring)).span()[0] + 1]      # select 'Model:' scope 
                        value_trim = substring[(sample[3].search(substring)).span()[0] + len((sample[3].search(substring)).groups()[0]) + 1 : ]        # select 'Trim:' scope 
                        
                        parser_result = ''
                        parser.feed(value_year)
                        value_year = re.split('\s\s+', re.sub('^\s*', '', parser_result))[0]
                        value_year = ymmt_exception_pattern.split(value_year)[0]

                        parser_result = ''
                        parser.feed(value_make)
                        value_make = re.split('\s\s+', re.sub('^\s*', '', parser_result))[0]
                        value_make = ymmt_exception_pattern.split(value_make)[0]

                        parser_result = ''
                        parser.feed(value_model)
                        value_model = re.split('\s\s+', re.sub('^\s*', '', parser_result))[0]
                        value_model = ymmt_exception_pattern.split(value_model)[0]

                        parser_result = ''
                        parser.feed(value_trim)
                        value_trim = re.split('\s\s+', re.sub('^\s*', '', parser_result))[0]
                        value_trim = ymmt_exception_pattern.split(value_trim)[0]

                        if re.search('20\d{2}|19\d{2}', value_year):
                            value_year = (re.search('20\d{2}|19\d{2}', value_year)).group()
                            
                            if result_dict['Title'] == '':
                                result_dict['Title'] = value_year + ' ' +  value_make + ' ' + value_model + ' ' + value_trim
                                result_dict['Year'] = value_year
                                result_dict['Make'] = value_make
                                result_dict['Model'] = value_model
                                result_dict['Trim'] = value_trim
                            else:
                                if value_year in result_dict['Title'] and value_make in result_dict['Title'] and value_model in result_dict['Title']:  
                                    result_dict['Year'] = value_year
                                    result_dict['Make'] = value_make
                                    result_dict['Model'] = value_model
                                    result_dict['Trim'] = value_trim
                            return result_dict
                    
                    if sample == ymmt_pattern_array[1] or sample == ymmt_pattern_array[2] or sample == ymmt_pattern_array[3]:
                        try:
                            value_year = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[0].search(substring)).span()[0] + len((sample[0].search(substring)).groups()[0]) + 1 : (sample[1].search(substring)).span()[0]])[0]
                            value_make = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[1].search(substring)).span()[0] + len((sample[1].search(substring)).groups()[0]) + 1 : (sample[2].search(substring)).span()[0]])[0]
                            value_model = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[2].search(substring)).span()[0] + len((sample[2].search(substring)).groups()[0]) + 1 : (sample[3].search(substring)).span()[0]])[0]
                            value_trim = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[3].search(substring)).span()[0] + len((sample[3].search(substring)).groups()[0]) + 1 : ])[0]
                        except:
                            value_year = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[0].search(substring)).span()[0] + len((sample[0].search(substring)).groups()[0]) + 1 : (sample[0].search(substring)).span()[0] + len((sample[0].search(substring)).groups()[0]) + 51])[0]
                            value_make = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[1].search(substring)).span()[0] + len((sample[1].search(substring)).groups()[0]) + 1 : (sample[1].search(substring)).span()[0] + len((sample[1].search(substring)).groups()[0]) + 51])[0]
                            value_model = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[2].search(substring)).span()[0] + len((sample[2].search(substring)).groups()[0]) + 1 : (sample[2].search(substring)).span()[0] + len((sample[2].search(substring)).groups()[0]) + 51])[0]
                            value_trim = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\s\,]', substring[(sample[3].search(substring)).span()[0] + len((sample[3].search(substring)).groups()[0]) + 1 : (sample[3].search(substring)).span()[0] + len((sample[3].search(substring)).groups()[0]) + 51])[0]
                        
                        value_year = ymmt_exception_pattern.split(value_year)[0]
                        value_make = ymmt_exception_pattern.split(value_make)[0]
                        value_model = ymmt_exception_pattern.split(value_model)[0]
                        value_trim = ymmt_exception_pattern.split(value_trim)[0]

                        if re.search('20\d{2}|19\d{2}', value_year):
                            value_year = (re.search('20\d{2}|19\d{2}', value_year)).group()
                            value_make = re.sub('\"|\'|\,', '', value_make)
                            value_model = re.sub('\"|\'|\,', '', value_model)
                            value_trim = re.sub('\"|\'|\,', '', value_trim)

                            if result_dict['Title'] == '':
                                result_dict['Title'] = value_year + ' ' +  value_make + ' ' + value_model + ' ' + value_trim
                                result_dict['Year'] = value_year
                                result_dict['Make'] = value_make
                                result_dict['Model'] = value_model
                                result_dict['Trim'] = value_trim
                            else:
                                if value_year in result_dict['Title'] and value_make in result_dict['Title'] and value_model in result_dict['Title'] and value_trim in result_dict['Title']:  
                                    result_dict['Year'] = value_year
                                    result_dict['Make'] = value_make
                                    result_dict['Model'] = value_model
                                    result_dict['Trim'] = value_trim
                            return result_dict

                    if sample == ymmt_pattern_array[4]:
                        try:
                            value_year = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\<]', substring[(sample[0].search(substring)).span()[0] + len((sample[0].search(substring)).groups()[0]) : (sample[0].search(substring)).span()[0] + len((sample[0].search(substring)).groups()[0]) + 51])[0]
                            value_make = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\<]', substring[(sample[1].search(substring)).span()[0] + len((sample[1].search(substring)).groups()[0]) : (sample[1].search(substring)).span()[0] + len((sample[1].search(substring)).groups()[0]) + 51])[0]
                            value_model = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\<]', substring[(sample[2].search(substring)).span()[0] + len((sample[2].search(substring)).groups()[0]) : (sample[2].search(substring)).span()[0] + len((sample[2].search(substring)).groups()[0]) + 51])[0]
                            value_trim = re.findall('\"*\'*[\w\s\.\,\-\_\!\@\#\$\%\*\(\)\&]+\"*\'*[\<]', substring[(sample[3].search(substring)).span()[0] + len((sample[3].search(substring)).groups()[0]) : (sample[3].search(substring)).span()[0] + len((sample[3].search(substring)).groups()[0]) + 51])[0]
                        except:
                            continue    
                        value_year = re.split('\<', re.sub('^\s*', '', value_year))[0]
                        value_make = re.split('\<', re.sub('^\s*', '', value_make))[0]
                        value_model = re.split('\<', re.sub('^\s*', '', value_model))[0]
                        value_trim = re.split('\<', re.sub('^\s*', '', value_trim))[0]

                        if re.search('20\d{2}|19\d{2}', value_year):
                            value_year = (re.search('20\d{2}|19\d{2}', value_year)).group()

                            if result_dict['Title'] == '':
                                result_dict['Title'] = value_year + ' ' +  value_make + ' ' + value_model + ' ' + value_trim
                                result_dict['Year'] = value_year
                                result_dict['Make'] = value_make
                                result_dict['Model'] = value_model
                                result_dict['Trim'] = value_trim
                            else:
                                if value_year in result_dict['Title'] and value_make in result_dict['Title'] and value_model in result_dict['Title'] :  
                                    result_dict['Year'] = value_year
                                    result_dict['Make'] = value_make
                                    result_dict['Model'] = value_model
                                    result_dict['Trim'] = value_trim
                            return result_dict

    except:
        pass

    return result_dict
        
def get_rest_data(response, domain):
    temp_dict = {}
    response = re.sub(r'\s\s+|\n', '  ', response)             # replace all \n, \r, \s, \t to \s
    response = re.sub(r'\<\/style\>', '</style>\n', response)
    response = re.sub(r'\<style.*\<\/style\>', '', response)        # remove all style content
    response = re.sub(r'\>\s*\<', '><', response)            
    response = re.sub(r'\&colon\;', ':', response)
    response = re.sub(r'\&dollar\;', '$', response)
    response = re.sub(r'\&minus\;', '-', response)
    response = re.sub(r'\&\#39\;', '\'', response)
    response = re.sub(r'\%20', ' ', response)
    response = re.sub(r'\%3E', '>', response)
    response = re.sub(r'\%3C', '<', response)
    response = re.sub(r'\%2F', '/', response)            

    try:
        if domain == "truckmax.com":
            price_pattern_list = [ 
                re.compile(r'sellingprice', re.I), 
                re.compile(r'internetPrice', re.I), 
                re.compile(r'originalPrice', re.I)
            ]
            for pattern in price_pattern_list:
                for substring in pattern.finditer(response):
                    end = substring.end()
                    substring = response[end : end + 20]
                    if re.search(r'\d+\d{3}', substring):
                        price = re.search(r'\d+\d{3}', substring).group()
                        temp_dict['Price'] = make_price(str(price))
            
            mileage_pattern_list = [
                re.compile(r'mileage', re.I)
            ]
            for pattern in mileage_pattern_list:
                for substring in pattern.finditer(response):
                    end = substring.end()
                    substring = response[end : end + 20]
                    if re.search(r'\d+\d{3}', substring):
                        mileage = re.search(r'\d+\d{3}', substring).group()
                        temp_dict['Mileage'] = make_mile(str(mileage))

            if 'Price' not in temp_dict:
                temp_dict['Price'] = 'N/A'
            if 'Mileage' not in temp_dict:
                temp_dict['Mileage'] = 'N/A'
            
        else:
            foundPrice = find_price(response)
            if foundPrice == None:
                foundPrice = "N/A"

            foundMileage = find_mileage(response)
            
            if foundMileage == None:
                foundMileage = "N/A"
        
            temp_dict['Price'] = make_price(str(foundPrice))
            temp_dict['Mileage'] = make_mile(str(foundMileage))

        foundTitelInfo = find_title_info(response, domain)
        
        new_type_pattern = re.compile(r'new[\s\-\_]', re.I)
        used_type_pattern = re.compile(r'used[\s\-\_]|pre\-owned|Certified[\s\-\_]', re.I)

        if foundTitelInfo['Title'] and new_type_pattern.search(foundTitelInfo['Title']):
            foundUsed = 'New'
        elif foundTitelInfo['Title'] and used_type_pattern.search(foundTitelInfo['Title']):
            foundUsed = 'Used'
        else:
            foundUsed = find_used(response, temp_dict['Mileage'])

        if foundUsed == "New":
            temp_dict['Mileage'] = 'N/A'

        temp_dict['Type'] = foundUsed
        temp_dict.update(foundTitelInfo)
        
        return temp_dict
    except:
        pass
