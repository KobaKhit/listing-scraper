import requests
from requests.adapters import HTTPAdapter, Retry

from tqdm import tqdm
import math
import itertools
import json
import time
import os


def get_events(league = 'NBA', start = "2022-09-09", end = "9999-12-31"):
    '''
    Get all league events on stubhub.
    '''

    event_category = {'NBA':{'path':'nba-tickets','categoryid': "6453"},
                      'NFL':{'path':'nfl-tickets','categoryid': "5084"}}


    url = f"https://www.stubhub.com/{event_category[league]['path']}"

    querystring = {"pageIndex":"0",
                "gridFilterType":"0",
                "sortBy":"0",
                "method":"GetFilteredEvents",
                "categoryId": event_category[league]['categoryid'],
                "from": start,
                "to": end}

    response = requests.request("POST", url, params=querystring).json()

    total_pages = math.ceil((response['totalCount'] - 2*response['pageSize'])/response['pageSize'])
    items = response['items']
    for i in items:
        i['eventid_from_url'] = int(i['url'].strip('/').split('/')[-1])
    item_dicts = []
    with tqdm(total=total_pages) as pbar:
        while response['remaining'] > 0:
            item_dicts.append(items)

            querystring['pageIndex'] = int(querystring['pageIndex']) + 1
            response = requests.request("POST", url, params=querystring).json()
            items = response['items']
            for i in items:
                i['eventid_from_url'] = int(i['url'].strip('/').split('/')[-1])
            pbar.update(1)
            
        # append last page
        item_dicts.append(items)

    return list(itertools.chain.from_iterable(item_dicts))

class EnhancedSession(requests.Session):
    '''
    Set timeout at the session level .
    '''
    def __init__(self, timeout=(3.05, 4)):
        self.timeout = timeout
        return super().__init__()

    def request(self, method, url, **kwargs):
        # print("EnhancedSession request")
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        return super().request(method, url, **kwargs)

def prepare_session():
    '''
    Prepare requests session with default timeout and retry.
    '''
    s = EnhancedSession(timeout=10)
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    method_whitelist=["POST", "GET"])
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    return s

def get_listings(eventid):
    '''
    Get all event listings.
    '''
    s = prepare_session()
    
    url = f"https://www.stubhub.com/event/{eventid}"
    url = s.request("POST", url,allow_redirects=True).url
    response = s.request("POST", url)


    if response.status_code == 404:
        print('404, Probably, no listings for event {}'.format(eventid))
        # print(url)
        return None

    respjson= response.json()
    querystring = {"CurrentPage":"1"}
    total_pages = math.ceil((respjson['TotalCount'] - 2*respjson['PageSize'])/respjson['PageSize'])
    items = respjson['Items']
    item_dicts = []
    with tqdm(total=total_pages, desc=f'Event Id: {eventid}', leave=False) as pbar:
        while respjson['ItemsRemaining'] > 0:
            item_dicts.append(items)

            querystring['CurrentPage'] = int(querystring['CurrentPage']) + 1
            respjson = s.request("POST", url, params=querystring).json()
            items = respjson['Items']
            pbar.set_description(f'Code: {response.status_code} Event Id: {eventid}')
            pbar.update(1)
            
        # append last page
        item_dicts.append(items)

    return list(itertools.chain.from_iterable(item_dicts))

def parse_listing(l):
    '''
    Parse listing by extracting relevant columns.
    '''
    listing = {}
    for c in columns:
        listing[c] = columns[c]
    pass