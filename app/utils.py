import random
import string

BASE62 = string.ascii_letters + string.digits
CODE_LENGTH = 7

def generate_short_code() -> str:
    return "".join(random.choice(BASE62) for _ in range(CODE_LENGTH))