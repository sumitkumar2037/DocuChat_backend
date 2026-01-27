import redis
import os

redis_client=redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)
#production
# REDIS_URL = os.getenv("REDIS_URL")

# redis_client = redis.from_url(
#     REDIS_URL,
#     decode_responses=True
# )