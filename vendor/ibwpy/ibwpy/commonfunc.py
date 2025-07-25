from .constants import TEXT_ENCODE, TEXT_ENCODE_2ND


def decode_unicode(text_buf: bytes):
    try:
        res = text_buf.decode(TEXT_ENCODE)
    except UnicodeDecodeError:
        res = text_buf.decode(TEXT_ENCODE_2ND)
    return res
