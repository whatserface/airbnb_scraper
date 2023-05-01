'''

Manual:

- To obey the robots.txt file, type in terminal:
"scrapy crawl airbnb_crawl -s ROBOTSTXT_OBEY=True"
By default it's ignored.

- To specify the ID of the crawled room, type in terminal:
"scrapy crawl airbnb_crawl -a ID=your_id"

- To specify the output directory and name, type in terminal: scrapy crawl airbnb_crawl -o your/output.json
This will go to the root directory, make a "your" directory and create an "output.json" file.

- Note:
  With image urls there are some parameters that change the size of pictures
(these are specified after (?) the question mark), such as: 
  - "aki_policy=profile_x_medium, poster or profile_large"
  - "im_w=240, 480, 720 or 1200"

'''

import logging
import scrapy
from scrapy.utils.project import get_project_settings
import json
import unicodedata # needed to replace \xa0 with a space
import pandas as pd
from ..items import HostItem, PhotoItem, ResponseItem, ReviewItem, ReviewerItem, RoomItem
from urllib.parse import urlencode
import math

class AirbnbCrawlSpider(scrapy.Spider):
    name = "airbnb_crawl"
    allowed_domains = ["airbnb.com"]
    start_urls = ["THIS IS CONFIGURED BELOW"]

    # IDs: 18081993, 1016153
    def __init__(self, ID=1016153,**kwargs):
        super().__init__(**kwargs)
        self.sections: dict = None
        self.my_df: pd.DataFrame = None

        AirbnbCrawlSpider.ID = ID
        AirbnbCrawlSpider.start_urls = [f"https://www.airbnb.com/rooms/{ID}"]
        
        # for hosts
        self.host_number = 0

        # for reviews
        self.iterations = 0 # number of iterations to go through
        self.curr_i = 0 # current iteration 

        self.headers = {
            'x-airbnb-api-key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
        }
        
        self.review_params = {
            'operationName': 'PdpReviews',
            'locale': 'en',
            'variables': '{"request":{"fieldSelector":"for_p3_translation_only","forPreview":false,"limit":7,"listingId":"%s"}}' \
                % self.ID,
            'extensions': '{"persistedQuery":{"sha256Hash":"22574ca295dcddccca7b9c2e3ca3625a80eb82fbdffec34cb664694730622cab"}}'
        }

        #for photos
        self._photos_request: scrapy.Request = None


    def parse(self, response):
        room = RoomItem() # this will contain all info about the room

        # setup, loading data
        data = json.loads(unicodedata.normalize("NFKD", response.xpath("//script[@id='data-deferred-state']/text()").get()))
        self.sections = data["niobeMinimalClientData"][0][1]['data']['presentation']['stayProductDetailPage']['sections']['sections']
        self.my_df = pd.json_normalize(self.sections)
        ignore_robotstxt = not self.settings.getbool('ROBOTSTXT_OBEY')

        # getting api key (in case it changes over a period of time)
        self.headers['x-airbnb-api-key'] = (json.loads(response.xpath("//script[@id='data-state']/text()").get())
            ['bootstrapData']['layout-init']['api_config']['key'])

        # hosts
        hosts_list = self._get_section("HOST_PROFILE_DEFAULT")


        ad_hosts = hosts_list['additionalHosts']
        room['hosts'] = [self._get_host(host, False, ignore_robotstxt) for host in ad_hosts]  if ad_hosts else\
                        [self._get_host(hosts_list['hostAvatar'], True, ignore_robotstxt)]
        
        self.host_number = len(room['hosts'])
        
        # name of the apartment
        room['roomTitle'] = self._get_section('TITLE_DEFAULT')['title']
        
        # photos, DRYing request
        stays_id = json.loads(data["niobeMinimalClientData"][0][0][17:])['id']

        params = {
            'operationName': 'StaysPdpSections',
            'locale': 'en',
            'variables': '{"id":"%s","pdpSectionsRequest":{"layouts":["SIDEBAR","SINGLE_COLUMN"]}}' % stays_id,
            'extensions': '{"persistedQuery":{"sha256Hash":"3aebb59d292ede4bb8fa8b61528d50b5f55fcf40cae4034fc09e0b632ca9fbb8"}}',
        }

        self._photos_request = scrapy.Request(
                            url=f'https://www.airbnb.com/api/v3/StaysPdpSections?{urlencode(params)}',
                            cb_kwargs={'room': room},
                            headers=self.headers,
                            callback=self.parse_photos
                            )

        # get additional info about host, if possible
        if ignore_robotstxt:
            yield scrapy.Request(url=f'https://www.airbnb.com/users/show/{room["hosts"][0]["id"]}',
                             cb_kwargs={'room': room,
                                        'viewed_hosts': room['hosts']},
                             callback=self.parse_hosts
                             )
        else:
            yield self._photos_request

    def parse_hosts(self, response, room, viewed_hosts: list):
        data = json.loads(unicodedata.normalize("NFKD", response.xpath("//script[@id='data-state']/text()").get()))

        curr_host = self.host_number - len(viewed_hosts)

        host: HostItem = viewed_hosts[0]
        profile_info = data['niobeMinimalClientData'][2][1]['data']['presentation']['userProfileContainer']['userProfile']
        self.copy_dictionary_pairs(profile_info, host, ['isSuperhost', 'isExperienceHost',
                                                        'isHomeHost', 'isViewerProfileOwner',
                                                        'location', 'languages',
                                                        'managedListingsTotalCount', 'profilePictureUrl',
                                                        'createdAt'])
        host['hostName'] = profile_info['smartName']
        host['profilePictureUrl'] = host['profilePictureUrl'].split('?')[0]
        # Exclude __typename values
        host['languages'] = [{k: d[k] for k in d if k != '__typename'} for d in host['languages']]

        room['hosts'][curr_host] = host

        # if the current host isn't last
        if len(viewed_hosts) > 1:
            curr_host += 1
            yield scrapy.Request(url=f'https://www.airbnb.com/users/show/{room["hosts"][curr_host]["id"]}',
                                 cb_kwargs={'room': room,
                                        'viewed_hosts': viewed_hosts[1:]},
                                callback=self.parse_hosts)
        else:
            yield self._photos_request

    def parse_photos(self, response, room):
        js = response.json()

        self.sections = js["data"]["presentation"]["stayProductDetailPage"]["sections"]["sections"]
        self.my_df = pd.json_normalize(self.sections)
        images = self._get_section("PHOTO_TOUR_SCROLLABLE")["mediaItems"]

        room['images'] = []
        for i in images:
            img = PhotoItem()
            self.copy_dictionary_pairs(i, img, ['orientation', 'id', 'aspectRatio'])
            img['url'] = i['baseUrl']
            img['caption'] = i['imageMetadata']['caption']
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

        for review in js['data']['merlin']['pdpReviews']['reviews']:
            item = ReviewItem()
            self.copy_dictionary_pairs(review, item, ['rating', 'id', 'createdAt'])

            if review['language'] != 'en' and review['language'] != 'und': # und is undetermined
                item['text'] = review['localizedReview']['comments']
            else:
                item['text'] = review['comments']
            item['originalLanguage'] = review['language']


            if not review['response']:
                item['response'] = None
            else:
                item['response'] = ResponseItem()
                item['response']['respondedAt'] = review['localizedRespondedDate']
                item['response']['text'] = (review['localizedReview'] if review['localizedReview'] else review)\
                                            ['response']
                item['response']['respondentId'] = review['reviewee']['id']

            item['reviewer'] = ReviewerItem()
            reviewer = review['reviewer']
            item['reviewer']['id'] = reviewer['id']
            item['reviewer']['name'] = reviewer['firstName']
            item['reviewer']['isAccountDeleted'] = reviewer['deleted']
            item['reviewer']['avatar'] = reviewer['pictureUrl'].split('?')[0]

            room['reviews'].append(item)

        if self.curr_i < self.iterations - 1:
            self.curr_i += 1
            self.review_params['variables'] = '{"request":{"fieldSelector":"for_p3_translation_only","forPreview":false,"limit":7,"listingId":"%s","offset":"%s"}}' \
                % (self.ID, (7*self.curr_i)) # configures offset parameter
            yield scrapy.Request(url="https://www.airbnb.com/api/v3/PdpReviews?" + urlencode(self.review_params),
                        callback=self.parse_reviews,
                        headers=self.headers,
                        dont_filter=True,
                        cb_kwargs={'room': room})
        else:
            yield room

    # helper functions

    def copy_dictionary_pairs(self, copy_from: dict, copy_to: scrapy.Item | dict, copy_what: list) -> scrapy.Item | dict:
        '''
        This function updates the copy_to with key-value pairs of copy_from.
        Note that this function only modifies a scrapy.Item and returns None
        '''
        copy_to.update({k:copy_from[k] for k in copy_what})

    def _get_section(self, section_name: str) -> dict:
        return self.sections[self.my_df[self.my_df['sectionComponentType'] == section_name].index[0]]['section']

    def _get_host(self, host: dict, is_superhost = False, get_only_ids=True) -> HostItem:
        avatar = host if is_superhost else host['avatar']
        item = HostItem()
        item['id'] = avatar['userId']
        if not get_only_ids:
            label = avatar['avatarImage']['accessibilityLabel']
            item['isSuperhost'] = is_superhost or 'superhost' in label
            item['hostName'] = host.get('name') or label[label.rfind("Learn more about")+17:-1]
            item['profilePictureUrl'] = avatar['avatarImage']['baseUrl'].split('?')[0]
        return item
    
