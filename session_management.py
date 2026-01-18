import shutil
import os
from chat import redis_client
from model import pc
import logging

logger=logging.getLogger(__name__)


def cleanup_guest_session(guest_id: str):
    # 1️⃣ Delete Redis chat
    redis_client.delete(f"chat:{guest_id}")

    # 2️⃣ Delete uploaded files
    folder = os.path.join("items", guest_id)
    if os.path.exists(folder):
        shutil.rmtree(folder)

    # 3️⃣ Delete vectors in pinecone
    pc.delete(filter={"guest_id": guest_id})
    logger.info(f'session for guest_id {guest_id} is cleaned ')
