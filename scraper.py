import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib.robotparser


visited = set()

def least_split_length(url1, url2):
    ''' Returns the smallest length between two split urls'''
    return min(len(url1), len(url2))


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.                                  
    links = []
    if resp.status in range(200,300):                       # we're getting a successful response from the url.
        visited.add(url)                                    # add the url into our visited list
        content = resp.raw_response.content                 # grab the html content from the url
        soup = BeautifulSoup(content, "html.parser")        # soup the content
        for a in soup.find_all('a', href=True):             # find all links
            potential_url = define_url(url,a['href'])
            if is_valid(potential_url) and check_valid_domain(potential_url) and potential_url not in visited:
                links.append(potential_url)
    return links

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        #encountered a case "http://www.informatics.uci.edu/files/pdf/InformaticsBrochure-March2018" which was a pdf, but still output True
        # so i modified this code a little bit. to where if it was a .extension or the extension existed in the path
        extension_types = "(css|js|bmp|gif|jpe?g|ico|" \
                          "png|tiff?|mid|mp2|mp3|mp4|" \
                          "wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|" \
                          "ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|" \
                          "data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|" \
                          "epub|dll|cnf|tgz|sha|" \
                          "thmx|mso|arff|rtf|jar|csv|"\
                          "rm|smil|wmv|swf|wma|zip|rar|gz)"

        if re.search("(/)" + extension_types, parsed.path.lower()):
            return False
        if re.search("(.)" + extension_types, parsed.path.lower()):
            return False
        
        return True

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
        new_base = base_parsed.scheme + "://" + base_parsed.netloc
        return new_base + path
    elif path_parsed.scheme == "" and path_parsed.netloc is not "":
        return base_parsed.scheme + ":" + path
    else:
        return path

def ok_status(url):
    r = requests.get(url)
    if r.status_code in range(200,300):
        return True
    else:
        return False

def check_valid_domain(url):
    accepted_domains = "(\.ics\.uci\.edu|\.cs\.uci\.edu|informatics\.uci\.edu|\.stat\.uci\.edu|today\.uci\.edu\/department\/information_computer_sciences)"
    if not re.search(accepted_domains,urlparse(url).netloc):
        return False
    return True

def robot_checker(url):                                         # robot checker (refer to docs.python.org/3/library/urllib.robotparser.html)
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme                                  # grab our scheme [http/https]
    domain = parsed_url.netloc                                  # our domain (where the robots.txt file will be)
    
    rp = urllib.robotparser.RobotFileParser()                   
    robotFile = scheme + "://" + domain + "/robots.txt"         # [http/https]://[accepted domains]/robots.txt
    rp.set_url(robotFile)
    rp.read()
    return rp.can_fetch("*", url)                               # check if we are allowed to go crawl our given url