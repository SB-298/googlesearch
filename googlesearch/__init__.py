"""googlesearch is a Python library for searching Google, easily."""
from time import sleep
from bs4 import BeautifulSoup
from requests import get
from .user_agents import get_useragent
from urllib.parse import urlparse


def _req(term, results, lang, start, proxies, timeout):
    resp = get(
        url="https://www.google.com/search",
        headers={
            "User-Agent": get_useragent()
        },
        params={
            "q": term,
            "num": results + 2,  # Prevents multiple requests
            "hl": lang,
            "start": start,
        },
        proxies=proxies,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp


class SearchResult:
    def __init__(self, url, title, description):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"


def search(term, num_results=10, lang="en", proxy=None, advanced=False, sleep_interval=0, timeout=5):
    """Search the Google search engine"""

    escaped_term = term.replace(" ", "+")

    # Proxy
    proxies = None
    if proxy:
        if proxy.startswith("https"):
            proxies = {"https": proxy}
        else:
            proxies = {"http": proxy}

    # Fetch
    start = 0
    while start < num_results:
        # Send request
        resp = _req(escaped_term, num_results - start,
                    lang, start, proxies, timeout)

        # Parse
        soup = BeautifulSoup(resp.text, "html.parser")
        result_block = soup.find_all("div", attrs={"class": "g"})
        for result in result_block:
            # Find link, title, description
            link = result.find("a", href=True)
            title = result.find("h3")
            description_box = result.find(
                "div", {"style": "-webkit-line-clamp:2"})
            if description_box:
                description = description_box.text
                if link and title and description:
                    start += 1
                    if advanced:
                        yield SearchResult(link["href"], title.text, description)
                    else:
                        yield link["href"]
        sleep(sleep_interval)

def url_contains_domain(url, domain_list):
    parsed_url = urlparse(url)
    url_domain = parsed_url.netloc.lower()
    for domain in domain_list:
        if domain.lower() in url_domain:
            return True
    return False

def search_desired(term, num_results=100, lang="en", proxy=None, advanced=False, sleep_interval=0, timeout=5, filetype="pdf", whitelist=["gov"], to_download=20):
    """Search the Google search engine for desired file types from specific domains"""

    import requests
    from bs4 import BeautifulSoup
    from time import sleep

    escaped_term = term.replace(" ", "+")

    # Proxy
    proxies = None
    if proxy:
        if proxy.startswith("https"):
            proxies = {"https": proxy}
        else:
            proxies = {"http": proxy}

    # Track total downloads obtained so far
    total_downloads = 0

    # Set to store unique URLs
    unique_urls = set()

    # Counter for consecutive attempts with no new downloads
    consecutive_no_downloads = 0

    # Fetch until desired number of downloads is reached or stop condition met
    while total_downloads < to_download:
        # Calculate number of results to fetch in this request
        remaining_downloads = to_download - total_downloads
        results_to_fetch = min(remaining_downloads, num_results)

        # Send request
        print("Sending request")
        resp = requests.get(
            f"https://www.google.com/search?q={escaped_term}+filetype:{filetype}",
            params={"start": total_downloads * results_to_fetch},
            proxies=proxies,
            timeout=timeout
        )

        # Parse the response
        soup = BeautifulSoup(resp.text, "html.parser")
        result_block = soup.find_all("div", attrs={"class": "g"})
        
        # Initialize flag for new downloads in this attempt
        new_downloads_in_attempt = False

        for result in result_block:
            # Find link, title, description
            link = result.find("a", href=True)
            title = result.find("h3")
            description_box = result.find("div", {"style": "-webkit-line-clamp:2"})
            if description_box:
                description = description_box.text
                if link and title and description:
                    if link["href"].endswith(f'.{filetype}') and url_contains_domain(link["href"], whitelist):
                        if link["href"] not in unique_urls:
                            print("Adding link: ", link["href"])
                            unique_urls.add(link["href"])
                            total_downloads += 1
                            new_downloads_in_attempt = True  # Set flag to true when a new download is obtained
                            if advanced:
                                yield SearchResult(link["href"], title.text, description)
                            else:
                                yield link["href"]

                            # Check if desired number of downloads is reached
                            if total_downloads >= to_download:
                                break  # Exit loop if reached desired number of downloads

        # Update consecutive_no_downloads counter based on whether new downloads were obtained
        if new_downloads_in_attempt:
            consecutive_no_downloads = 0  # Reset counter if new downloads were obtained
        else:
            consecutive_no_downloads += 1  # Increment counter if no new downloads were obtained

        # Check if consecutive_no_downloads counter reaches 3, indicating no consistent results
        if consecutive_no_downloads >= 3:
            print("No consistent results found for 3 attempts in a row, stopping.")
            break
        
        # Wait for specified interval before next request
        print("Sleeping...")
        sleep(sleep_interval)





