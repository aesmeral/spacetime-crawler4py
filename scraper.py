import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.
    links = []
    if resp.status in range(200,300):                       # we're getting a successful response from the url.
        content = resp.raw_response.content                 # grab the html content from the url
        soup = BeautifulSoup(content, "html.parser")        # soup the content
        for a in soup.find_all('a', href=True):             # find all links
            links.append(a['href'])
        for i in range(len(links)):                         # reformat all found links if needed
            links[i] = define_url(url, links[i])
        for link in links:
            if is_valid(link) == False:
                links.remove(link)
    return links

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

"""
    base -> the url given from the frontier
    path -> url(s) from the frontier's html code
    
    (1) if ... it has no scheme and it has no netloc, meaning that it must be in form --- /xyz --- (meaning that it is a path from the base url)
    (2) elif ... it has no scheme but is in form --- //*.asdfasdf.* (meaning that it might be another website but formated wrong)
    (3) it takes on the form of http://www.somewebsite.com/random... so just return it as is.
"""
def define_url(base, path):
    base_parsed = urlparse(base)
    path_parsed = urlparse(path)
    if path_parsed.scheme == "" and path_parsed.netloc == "":
        return base + path
    elif path_parsed.scheme == "" and path_parsed.netloc is not "":
        return base_parsed.scheme + ":" + path
    else:
        return path