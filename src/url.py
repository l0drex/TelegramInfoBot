import requests


def check_status(url: str) -> bool:
    """Check if opal is online"""
    url_new = str(requests.get(url))
    return "offline" not in url_new
