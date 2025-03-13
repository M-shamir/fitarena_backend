from datetime import datetime,timedelta
from django.core.cache import cache
import random
import string 

BLOCK_TIME = 600 

def generate_otp(length = 6):
    return ''.join(random.choices(string.digits,k=length))

def store_otp(email):
    otp =  generate_otp()
    cache.set(f'otp:{email}',otp,timeout=300)
    attempts = cache.get(f'otp_attempts:{email}',0)
    if attempts == 0:
        cache.set(f'otp_attempts:{email}',attempts,timeout=BLOCK_TIME)
    return otp

