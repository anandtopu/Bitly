import string

ALPHABET = string.ascii_lowercase + string.ascii_uppercase + string.digits
BASE = len(ALPHABET)

def encode(num: int) -> str:
    """Encode an integer to a Base62 string."""
    if num == 0:
        return ALPHABET[0]
    
    encoded = []
    while num > 0:
        num, rem = divmod(num, BASE)
        encoded.append(ALPHABET[rem])
    
    return "".join(reversed(encoded))

def decode(short_code: str) -> int:
    """Decode a Base62 string to an integer."""
    num = 0
    for char in short_code:
        num = num * BASE + ALPHABET.index(char)
    return num
