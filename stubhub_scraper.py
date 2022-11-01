import requests
from tqdm import tqdm
import math



def get_events(league = 'NBA', start = "2022-09-09", end = "9999-12-31"):

    event_category = {'NBA':{'grouping':'115','categoryid': "6453"}}

    url = "https://www.stubhub.com/nba-tickets/grouping/{}/".format(event_category[league]['grouping'])

    querystring = {"pageIndex":"1",
                "gridFilterType":"0",
                "sortBy":"0",
                "method":"GetFilteredEvents",
                "categoryId": event_category[league]['categoryid'],
                "from": start,
                "to": end}

    response = requests.request("POST", url, params=querystring).json()

    total_pages = math.ceil((response['totalCount'] - 2*response['pageSize'])/response['pageSize'])
    events = response['items']
    event_dicts = []
    with tqdm(total=total_pages) as pbar:
        while response['remaining'] > 0:
            event_dicts.append(events)

            querystring['pageIndex'] = int(querystring['pageIndex']) + 1
            response = requests.request("POST", url, params=querystring).json()
            events = response['items']
            pbar.update(1)

    return event_dicts

def main():
    evs = get_events()



if __name__ == '__main__':
    main()