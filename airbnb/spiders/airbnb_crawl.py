import scrapy
import json
import unicodedata # needed to replace \xa0 with a space

class AirbnbCrawlSpider(scrapy.Spider):
    name = "airbnb_crawl"
    allowed_domains = ["airbnb.cz"]
    start_urls = [r"https://airbnb.cz//s/%C4%8Cesk%C3%A1-republika/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=5&channel=EXPLORE&query=%C4%8Cesk%C3%A1%20republika&place_id=ChIJQ4Ld14-UC0cRb1jb03UcZvg&date_picker_type=calendar&source=structured_search_input_header"]

    def parse(self, response):
        data = json.loads(unicodedata.normalize("NFKD", response.xpath("//script[@id='data-deferred-state']/text()").get()))
        floats = data['niobeMinimalClientData'][0][1]['data']['presentation']['explore']['sections']['sectionIndependentData']['staysSearch']['searchResults']
        for float in floats:
            rating = float['listing']['avgRatingLocalized']
            rating = rating[:rating.find(' ')].replace(',' , '.')
            city = float['listing']['city']
            price = float['pricingQuote']['primaryLine']['price'][:-3].replace(' ', '')
            period = float['pricingQuote']['primaryLine']['qualifier']
