import redis
from datetime import datetime
class Cache:
    def __init__(self):
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, db=1)
        self.expiration_time_seconds = 60
    
    def aquire_lock(self,ip):
        key = f"ip:{ip}"
        lock_key = f"lock:{str(datetime.now())}"  # Define a lock key
        lock_ttl = 5  # Set a reasonable lock time-to-live (in seconds)
        lock_acquired = self.redis_client.setnx(lock_key, "1")
        return lock_acquired,lock_key
    
    def release_lock(self, lock_key):
        self.redis_client.delete(lock_key)