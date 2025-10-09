
import sys
import os
import requests
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import dectools.decors as decorate


def url_valid(url: str, timeout: int=5) -> bool:
    '''
    Check if a URL is valid based on the internal criteria defined.
    Return True if valid, False otherwise
    '''

    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        status = response.status_code

        if 200 <= status < 300:
            return True # Valid
        elif 300 <= status < 400:
            return True  # Consider redirects as valid
        else:
            return False # Invalid

    except requests.exceptions.Timeout:
        return False # Timeout treated as invalid url to be safe (makese sense when slow or unresponsive pages nor useful)
    except requests.exceptions.ConnectionError:
        return False # Connections errors (albeit temporary) treated as invalid to be safe

@decorate.assert_notifier
def multi_url_validation(url: Dict[str, List[str]]) -> Dict[str, List[str]]:
    '''
    Validate a list of URLs and return only the valid ones.
    '''

    # In case of an assertion error in this function, the decorator 'decorate.assert_notifier" will catch assertion errors and print a message and will reprint the assertion error
    assert "candidate_urls" in url, "Input dictionary must contain 'candidate_urls' key."

    valid_urls = [u for u in url["candidate_urls"] if url_valid(u)]
    return {"validated_urls": valid_urls}  # returning a JSON object (dictionary)
