from hashids import Hashids

from config import MIN_LENGTH_FOR_SHORT_URL, SALT


hashids = Hashids(min_length=MIN_LENGTH_FOR_SHORT_URL, salt=SALT)


def get_hashed_short_url(value: int) -> str:
    """Возвращает хешированный url адрес."""
    return hashids.encode(value)


def get_decoded_short_url(value: str):
    """Возвращает декодированный url адрес."""
    return hashids.decode(value)
