import shutil
import os
from src.chat import redis_client
from src.model import pc
import logging

logger=logging.getLogger(__name__)


def cleanup_guest_session(guest_id: str):
    # Delete Redis chat
    redis_client.delete(f"chat:{guest_id}")
    redis_client.delete(f"doc_metadata:{guest_id}")
    redis_client.delete(f"doc_summary:{guest_id}")
    redis_client.delete(f'status:{guest_id}')
    # Delete uploaded files
    folder = os.path.join("items", guest_id)
    if os.path.exists(folder):
        shutil.rmtree(folder)

    #  Delete vectors in pinecone
    pc.delete(filter={"guest_id": guest_id})
    logger.info(f'session for guest_id {guest_id} is cleaned ')
