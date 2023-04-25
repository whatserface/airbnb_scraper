import logging
import scrapy
import json
import unicodedata # needed to replace \xa0 with a space
import pandas as pd
from ..items import HostItem, PhotoItem, ReviewItem, RoomItem
from urllib.parse import urlencode
import math

class AirbnbCrawlSpider(scrapy.Spider):
    name = "airbnb_crawl"
    allowed_domains = ["airbnb.com"]
    ID = 18081993 # 18081993 1016153
    start_urls = [f"https://www.airbnb.com/rooms/{ID}"]

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.sections: dict = None
        self.my_df: pd.DataFrame = None
        # for reviews
        self.iterations = 0 # number of iterations to go through
        self.curr_i = 0 # current iteration 

        self.headers = {
            'x-airbnb-api-key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
        }
        
        self.review_params = {
            'operationName': 'PdpReviews',
            'locale': 'en',
            'variables': '{"request":{"forPreview":false,"limit":7,"listingId":"%s"}}' \
                % self.ID,
            'extensions': '{"persistedQuery":{"sha256Hash":"22574ca295dcddccca7b9c2e3ca3625a80eb82fbdffec34cb664694730622cab"}}'
        }


    def parse(self, response):
        room = RoomItem() # this will contain all info about the room

        # loading data
        data = json.loads(unicodedata.normalize("NFKD", response.xpath("//script[@id='data-deferred-state']/text()").get()))
        self.sections = data["niobeMinimalClientData"][0][1]['data']['presentation']['stayProductDetailPage']['sections']['sections']
        self.my_df = pd.json_normalize(self.sections)
        
    
        # hosts
        hosts_list = self._get_section("HOST_PROFILE_DEFAULT")

        ad_hosts = hosts_list['additionalHosts']
        room['hosts'] = [self._get_host(host) for host in ad_hosts]  if ad_hosts else\
                        [self._get_host(hosts_list['hostAvatar'], True)]
        
        
        # name of the apartment

        room['room_title'] = self._get_section('TITLE_DEFAULT')['title']
        
        # photos
        stays_id = json.loads(data["niobeMinimalClientData"][0][0][17:])['id']
        params = {
            'operationName': 'StaysPdpSections',
            'locale': 'en',
            'variables': '{"id":"%s","pdpSectionsRequest":{"layouts":["SIDEBAR","SINGLE_COLUMN"]}}' % stays_id,
            'extensions': '{"persistedQuery":{"sha256Hash":"3aebb59d292ede4bb8fa8b61528d50b5f55fcf40cae4034fc09e0b632ca9fbb8"}}',
        }

        yield scrapy.Request(url='https://www.airbnb.com/api/v3/StaysPdpSections?' + urlencode(params),
                             cb_kwargs={'room': room},
                             headers=self.headers,
                             callback=self.parse_photos)

    def parse_photos(self, response, room):
        js = response.json()

        self.sections = js["data"]["presentation"]["stayProductDetailPage"]["sections"]["sections"]
        self.my_df = pd.json_normalize(self.sections)
        images = self._get_section("PHOTO_TOUR_SCROLLABLE")["mediaItems"]

        if not room.get('images'):
            room['images'] = []

        for i in images:
            img = PhotoItem({k:i[k] for k in ['orientation', 'id', 'aspectRatio']})
            img['url'] = i['baseUrl']
            room['images'].append(img)

        # reviews
        yield scrapy.Request(url="https://www.airbnb.com/api/v3/PdpReviews?" + urlencode(self.review_params),
                      callback=self.parse_reviews,
                      headers=self.headers,
                      dont_filter=True,
                      cb_kwargs={'room': room})

    def parse_reviews(self, response, room):
        js = response.json()
        if not self.iterations:
            self.iterations = math.ceil(js['data']['merlin']['pdpReviews']['metadata']['reviewsCount'] / 7)

        if not room.get('reviews'):
            room['reviews'] = []

        for r in js['data']['merlin']['pdpReviews']['reviews']:
            item = ReviewItem()
            item['rating'] = r['rating']
            if r['language'] != 'en' and r['language'] != 'und': # und is undetermined
                item['text'] = r['localizedReview']['comments']
            else:
                item['text'] = r['comments']
            item['id'] = r['id']
            room['reviews'].append(item)

        if self.curr_i < self.iterations-1:
            self.curr_i += 1
            self.review_params['variables'] += ',"offset":"%s"}}' % (7*self.curr_i) # adds offset parameter
            yield scrapy.Request(url="https://www.airbnb.com/api/v3/PdpReviews?" + urlencode(self.review_params),
                        callback=self.parse_reviews,
                        headers=self.headers,
                        dont_filter=True,
                        cb_kwargs={'room': room})
        else:
            yield room


    def _get_section(self, section_name: str) -> dict:
        return self.sections[self.my_df[self.my_df['sectionComponentType'] == section_name].index[0]]['section']

    def _get_host(self, host: dict, is_superhost = False) -> HostItem:
        avatar = host if is_superhost else host['avatar']
        item = HostItem()
        label = avatar['avatarImage']['accessibilityLabel']
        item['is_superhost'] = is_superhost or 'superhost' in label
        item['host_name'] = host.get('name') or label[label.rfind("Learn more about")+17:-1]
        item['id'] = avatar['userId']
        item['avatar'] = avatar['avatarImage']['baseUrl']
        return item
