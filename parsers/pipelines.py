import json
import os
from datetime import datetime
from scrapy.exporters import JsonItemExporter


class NewsJsonPipeline:
    """
    Pipeline to export scraped news items to a JSON file
    """
    
    def __init__(self):
        self.files = {}
        self.exporters = {}
        # Ensure the output directory exists
        os.makedirs('output', exist_ok=True)
    
    def open_spider(self, spider):
        """Initialize the JSON file when the spider starts"""
        filename = f"output/{spider.get_output_filename()}"
        self.files[spider] = open(filename, 'wb')
        exporter = JsonItemExporter(self.files[spider], encoding='utf-8', ensure_ascii=False)
        exporter.start_exporting()
        self.exporters[spider] = exporter
        spider.logger.info(f"Created output file: {filename}")
    
    def close_spider(self, spider):
        """Finalize the JSON file when the spider ends"""
        self.exporters[spider].finish_exporting()
        self.files[spider].close()
    
    def process_item(self, item, spider):
        """Process each news item and add it to the JSON file"""
        # Add timestamp if not present
        if 'created_at' not in item:
            item['created_at'] = datetime.now().isoformat()
            
        # Export the item
        self.exporters[spider].export_item(item)
        return item
