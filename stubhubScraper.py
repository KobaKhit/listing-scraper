import requests
import base64

import pandas as pd
from tqdm import tqdm
from time import gmtime, strftime

import json

# authorization
# https://developer.stubhub.com/docs/StubHub+API+Developers+Guide.html
# http://ozzieliu.com/2016/06/21/scraping-ticket-data-with-stubhub-api/
# https://stubhubapi.zendesk.com/hc/en-us/articles/220922687-Inventory-Search

class St(object):
	def __init__(self,app_token,consumer_key,consumer_secret,stubhub_username,stubhub_password):
		# create authorization request
		combo = consumer_key + ':' + consumer_secret 
		basic_authorization_token = base64.b64encode(combo.encode('utf-8')).decode() # create authorization token

		url = 'https://api.stubhub.com/login'
		headers = {
	        'Content-Type':'application/x-www-form-urlencoded',
	        'Authorization':'Basic '+ basic_authorization_token,}
		body = {
	        'grant_type':'password',
	        'username':stubhub_username,
	        'password':stubhub_password,
	        'scope':'PRODUCTION'}

		r = requests.post(url, headers=headers, data=body)
		print(r.content) # print response

		token_response = r.json()
		access_token = token_response['access_token']
		user_GUID = r.headers['X-StubHub-User-GUID']


		self.headers = {'Authorization': 'Bearer ' + access_token,
						'Accept': 'application/json',
						'Accept-Encoding': 'application/json'}

	def process_listings(self,listings, event_id):
		'''
		Process listings obtained from Stubhub API
		Args:
		- listings - a list of stubhub listings
		'''

		# Process listings obtained from Stubhub API
		# Args:
		# - listings - a list of stubhub listings

		fields = ['listingId','sectionId','row','quantity','sellerSectionName','sectionName',\
		'zoneId','zoneName','dirtyTicketInd','score']
		l = [] # listings list
		for k in listings: # for a listing in list
			ret = {}
			for f in fields: # for a field in fields
				if f in k: 
					ret[f] = k[f] # if field in listing grab value
				else:
					ret[f] = 'NA' # else NA

			ret['currentPrice'] = k['currentPrice']['amount'] # get current price
			ret['listingPrice'] = k['listingPrice']['amount'] # get listing price
			# get seatnumbers if those are in listing
			ret['seatNumbers'] = k['seatNumbers'].replace(',',';') if 'seatNumbers' in k else 'NA'
			ret['retrieveTime'] = strftime("%Y-%m-%d %H:%M:%S", gmtime()) # time of request
			ret['event id'] = event_id # add event id
			l.append(ret) # append to list

		return(l)

	def get_listings(self,eventid,pages=False):
		'''
		Get listings using Stubhub API
		Args:
		- eventid: integer - eventid taken from the Stubhub event url
		- pages: bool - paginate to get all listings
		
		'''
		

		req_count = 0 # api limit count
		inventory_url = 'https://api.stubhub.com/search/inventory/v2'
		data = {'eventid':eventid,'rows':200,'start':0}

		# make request to get the first page
		inventory = requests.get(inventory_url, headers=self.headers, params=data).json()
		if 'description' in inventory:
			print(inventory['description'],'- Event ID: ',eventid)
			return
		elif 'totalListings' in inventory and inventory['totalListings'] == 0:
			print('Event: ',eventid, 'has 0 listings')
			return

		event_id = inventory['eventId']
		total_listings = inventory['totalListings']

		if pages is True: # loop through all pages 
			start = 200 # first page already requested
			while start < total_listings:
				data = {'eventid':eventid,'rows':200,'start':start}
				inv_temp = requests.get(inventory_url, headers=self.headers, params=data).json()
				inventory['listing'].extend(inv_temp['listing'])
				start+=200 # go to next page

		inventory['rows'] = total_listings # total number of listings
		if 'minQuantity' in inventory: del inventory['minQuantity'] # remove unnecessary key value pairs
		if 'maxQuantity' in inventory: del inventory['maxQuantity']
		inv = self.process_listings(inventory['listing'], event_id) # process listings

		return(inv)

	def get_listings_by_event(self,events):
		'''
		Given the list of events and event ids retrieve all the listings for each event 
		Args:
		- events - a dataframe of events and event ids on stubhub
		
		'''
	
		listings = []
		t = tqdm(events[['Event','Eventid']].itertuples(index=False))
		for event, eid in t:
			t.set_description("Event: {}".format(event)) # update event name
			inv = self.get_listings(eventid=eid,pages=True)

			df = pd.DataFrame(inv)
			df['Event'] = event
			df['Date'] = event.split(' ')[-1]
			listings.append(df)
		print('Done getting listings by event.')
		return(pd.concat(listings))


def main():
	# Enter user's API key, secret, and Stubhub login
	app_token = ''
	consumer_key = ''
	consumer_secret = ''
	stubhub_username = ''
	stubhub_password = ''

	st = St(app_token,consumer_key,consumer_secret,stubhub_username,stubhub_password)

	events = pd.read_csv('flyers events 2018.csv')

	listings = st.get_listings_by_event(events)
	listings.to_csv('flyers listings.csv')

	return


if __name__ == '__main__':
	main()
