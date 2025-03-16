from datetime import datetime,timedelta
from django.core.cache import cache
import random
import string 

MAX_ATTEMPTS = 5
BLOCK_TIME = 300
COOLDOWN_TIME = 30


def generate_otp(length = 6):
    return ''.join(random.choices(string.digits,k=length))

def store_otp(email):
    otp =  generate_otp()
    cache.set(f'otp:{email}',otp,timeout=300)
    
    if cache.get(f'otp_attempts:{email}') is None:
        cache.set(f'otp_attempts:{email}', 0, timeout=BLOCK_TIME)
        
    if cache.get(f'otp_resend_cooldown:{email}') is None:
         cache.set(f'otp_resend_cooldown:{email}', 0, timeout=COOLDOWN_TIME)

    return otp

