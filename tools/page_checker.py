
import requests

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

