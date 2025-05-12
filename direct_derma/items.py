class ProductPriceItem(scrapy.Item):
    product_url = scrapy.Field()
    price = scrapy.Field()