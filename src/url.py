import requests


def check_status(url: str) -> bool:
    """Check if url is online"""
    r = requests.get(url)

    # check status code
    if r.status_code[0] < 5:
        return False
    url_new = str(r)

    # check if there is the word offline in the current url, f.e. if it was redirected
    return "offline" not in url_new
