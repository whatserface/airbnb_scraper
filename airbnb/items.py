# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class RoomItem(scrapy.Item):
    hosts = scrapy.Field() # HostItem
    roomTitle = scrapy.Field()
    reviews = scrapy.Field() # ReviewItem
    images = scrapy.Field() # an array of image urls, i.e. strings


class HostItem(scrapy.Item):
    id = scrapy.Field()
    hostName = scrapy.Field()
    profilePictureUrl = scrapy.Field()
    languages = scrapy.Field()
    createdAt = scrapy.Field()
    managedListingsTotalCount = scrapy.Field()
    location = scrapy.Field()

    isSuperhost = scrapy.Field()
    isExperienceHost = scrapy.Field()
    isHomeHost = scrapy.Field()
    isViewerProfileOwner = scrapy.Field()


class ReviewItem(scrapy.Item):
    id = scrapy.Field()
    text = scrapy.Field()
    rating = scrapy.Field()
    createdAt = scrapy.Field()
    originalLanguage = scrapy.Field() # all comments are translated to English
    reviewer = scrapy.Field() # a ReviewerItem instance
    response = scrapy.Field() # a ResponseItem instance


class ResponseItem(scrapy.Item):
    respondentId = scrapy.Field()
    text = scrapy.Field() 
    respondedAt = scrapy.Field()
    originalLanguage = scrapy.Field()


class ReviewerItem(scrapy.Item):
    id = scrapy.Field()
    isAccountDeleted = scrapy.Field()
    name = scrapy.Field()
    avatar = scrapy.Field()


class PhotoItem(scrapy.Item):
    id = scrapy.Field()
    orientation = scrapy.Field()
    url = scrapy.Field()
    aspectRatio = scrapy.Field()
    caption = scrapy.Field()
