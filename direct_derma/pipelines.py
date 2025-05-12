class PricePipeline:
    def process_item(self, item, spider):
        # Clean and validate the price data
        if 'price' in item:
            item['price'] = item['price'].replace('EUR', '').strip()
        return item