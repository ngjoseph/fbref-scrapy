import scrapy
from scrapy.loader import ItemLoader
from fbref_scrapy.items import MatchDetailsItem

class MatchSpider(scrapy.Spider):
    name = 'fbref_match'
    
    # TODO Replace with start_requests() method after initial tests
    # TODO Need additional test URLs (available/not on Wayback Machine) for middleware test
    start_urls = [
        'https://fbref.com/en/matches/85624e5e/Arsenal-Leeds-United-February-14-2021-Premier-League'
    ]
    
    def parse(self, response):
        loader = ItemLoader(item= MatchDetailsItem(), response= response)
        
        # Team IDs
        team_ids = (
            response.xpath('//div[@itemprop="performer"]//a/@href')
                    .re('(?<=\/squads\/)[a-zA-Z0-9]+')
        )
        loader.add_value('team_ids', team_ids)
        
        # Officials
        officials = {} # empty dict
        for item in response.xpath('//div[@class = "scorebox_meta"]/div[contains(./strong//text(), "Officials")]//span'):
            text = item.xpath('.//text()').re('([\w\s]+)\((\w+)\)')
            offtype = 'official_' + text[1].lower()
            offname = text[0]
            officials[offtype] = offname
        loader.add_value('officials', officials)
        
        
        return loader.load_item()