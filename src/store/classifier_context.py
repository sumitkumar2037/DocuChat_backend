from src.store.redis_config import redis_client
import logging
import json
logger=logging.getLogger(__name__)

def save_metadata_from_doc(guest_id:str,metadata:dict)->None:
    key = f"doc_metadata:{guest_id}"
    redis_client.set(
        key,
        json.dumps(metadata)
    ) 
    logger.info('metadata saved in redis')

def load_metadata(guest_id:str)->list:
    key = f"doc_metadata:{guest_id}"
    stored_metadata=redis_client.get(key)
    return stored_metadata

def save_summary(summary:str,guest_id:str):
    key = f"doc_summary:{guest_id}"
    redis_client.set(
        key,
        json.dumps({"summary": summary})
    )
    logger.info('summary saved in redis')

def load_summary(guest_id:str):
    key = f"doc_summary:{guest_id}"
    stored_summary=redis_client.get(key)
    return stored_summary




if __name__=='__main__':
    save_metadata_from_doc('','')
    load_metadata('')
    save_summary('')
    load_summary('')

