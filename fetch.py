
# standard
import requests


#############
# Functions #
#############

def download_url_data(url: str) -> str:
    response = requests.get(url)
    if not response:
        raise requests.HTTPError(f"Data download failed with {response.status_code} ({response.reason}). Url: {url}.")
    return response.text
