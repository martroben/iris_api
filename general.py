
# standard
import random
import requests


def download_url_data(url: str) -> str:
    response = requests.get(url)
    if not response:
        raise requests.HTTPError(f"Data download failed with {response.status_code} ({response.reason}). Url: {url}.")
    return response.text


def generate_random_hex(length: int) -> str:
    """
    Generate random hexadecimal string with given length.
    Alternative: f"{16 ** 8 - 1:08x}"). Has limited length, because of maximum int size.
    :param length: Length of the hex string.
    :return: A string representation of a hex with the requested length
    """
    decimals = random.choices(range(16), k=length)
    hexadecimal = "".join(["{:x}".format(decimal) for decimal in decimals])
    return hexadecimal
