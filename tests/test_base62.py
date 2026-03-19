from app.utils.base62 import encode, decode

def test_encode_decode():
    for i in range(1000):
        # Base62 encode/decode should be reversible
        assert decode(encode(i)) == i

def test_specific_values():
    assert encode(0) == 'a' # a is the first char in alphabet
    assert encode(61) == '9' # 9 is the last char in alphabet
    assert encode(62) == 'ba' # 1 * 62 + 0 -> 'b' + 'a'

def test_decode_specific():
    assert decode('a') == 0
    assert decode('9') == 61
    assert decode('ba') == 62
