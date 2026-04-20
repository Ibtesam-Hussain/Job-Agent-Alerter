import requests

def test_url_reachability(url):
    """Test if URL is reachable with a simple HTTP request"""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code < 400
    except:
        return False