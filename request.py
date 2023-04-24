import requests
from time import sleep
import json
from math import ceil

headers = {
	'x-airbnb-api-key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
}

params = {
    'operationName': 'PdpReviews',
    'locale': 'en',
    'variables': '{"request":{"fieldSelector":"for_p3_translation_only","forPreview":false,"limit":7,"listingId":"18081993","showingTranslationButton":false,"numberOfAdults":"1","numberOfChildren":"0","numberOfInfants":"0"}}',
    'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"22574ca295dcddccca7b9c2e3ca3625a80eb82fbdffec34cb664694730622cab"}}',
}

# params['variables'] = '{"request":{"fieldSelector":"for_p3_translation_only","forPreview":false,"limit":7,"listingId":"18081993","offset":"%s","showingTranslationButton":false,"numberOfAdults":"1","numberOfChildren":"0","numberOfInfants":"0"}}'\
#  % 252


req = requests.get('https://www.airbnb.com/api/v3/PdpReviews', headers=headers, params=params)
js = json.loads(req.content)
iterations = ceil(js['data']['merlin']['pdpReviews']['metadata']['reviewsCount'] / 7)

ret = []
for i in range(1, iterations):
	params['variables'] = '{"request":{"fieldSelector":"for_p3_translation_only","forPreview":false,"limit":7,"listingId":"18081993","offset":"%s","showingTranslationButton":false,"numberOfAdults":"1","numberOfChildren":"0","numberOfInfants":"0"}}' % (7*i)
	req = requests.get('https://www.airbnb.com/api/v3/PdpReviews', headers=headers, params=params)
	js = json.loads(req.content)
	rs = js['data']['merlin']['pdpReviews']['reviews']
	for r in rs:
		ret.append({"id": r['id'], "comment": r['localizedReview']['comments'], "rating": r["rating"]})

	print(i)
	sleep(1)

with open('test.json', 'w') as f:
	json.dump(ret, f, ensure_ascii=False)

print("END")
