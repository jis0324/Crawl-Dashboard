import os
import errno
import hashlib
import datetime

base_dir = os.path.abspath('')
def save_page(response_url, res_content, totalCount, myDomain):

    # Build up an MD5 hash for full url
    today = str(datetime.date.today())
    directory =  base_dir + "/ezc/spiders/" + today + '/' + myDomain
    if not os.path.exists(directory):
        os.makedirs(directory)
    url = response_url

    md5Url = hashlib.md5(url.encode())

    # Get last part after /
    page = url.rsplit('/', 1)[-1]

    # Split on "?" only if there
    pageName = page

    if "?" in page:
        pageName, queryString = page.split('?', 1)
    # Split on "." only if there
    pageNameWithoutExt = page
    if "." in page:
        pageNameWithoutExt, Ext = pageName.split('.', 1)
    # prepare file name and write data to it.
    filename = directory + '/' + md5Url.hexdigest() + '_' + \
        str(totalCount) + '.html'
    print(filename)
    try:
        with open(filename, 'w') as f:
            f.write(res_content)
    except Exception as e:
        print(e)
    return filename
