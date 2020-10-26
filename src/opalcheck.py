import requests


def get_url() -> str:
    """Returns the url redirected to"""
    r = requests.get("https://bildungsportal.sachsen.de/opal/")
    return r.url


def check_status() -> bool:
    """Check if opal is online"""
    return "offline" not in str(get_url())
