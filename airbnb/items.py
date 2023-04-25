# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class RoomItem(scrapy.Item):
    hosts = scrapy.Field()
    room_title = scrapy.Field()
    reviews = scrapy.Field()
    images = scrapy.Field() 

class HostItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    host_name = scrapy.Field()
    is_superhost = scrapy.Field()
    avatar = scrapy.Field()


class ReviewItem(scrapy.Item):
    id = scrapy.Field()
    text = scrapy.Field()
    rating = scrapy.Field()


class PhotoItem(scrapy.Item):
    orientation = scrapy.Field()
    url = scrapy.Field()
    id = scrapy.Field()
    aspectRatio = scrapy.Field()
