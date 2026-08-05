from itemadapter import ItemAdapter


class PricingEnginePipeline:

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Future schema validation will be added here

        return item