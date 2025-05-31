import logging

from asgiref.sync import sync_to_async
from django.db import transaction, DatabaseError
from dip.models import ScholarRawRecord

logger = logging.getLogger(__name__)

class ScholarPipeline:
    async def process_item(self, item, spider):
        model_instance = ScholarRawRecord(**item)
        await sync_to_async(model_instance.save, thread_sensitive=True)()
        return item
