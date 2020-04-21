import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib.robotparser

accepted_domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stats.uci.edu"]

prev_url = ""

def web_trap_handler(url):
    prev_url_parse = urlparse(prev_url)
    url_parse = urlparse(url)
    prev_url_path = prev_url_parse.path.split()
    current_url_path = url_parse.path.split()
    counter = 0
    for i in range(len(prev_url_path)):
        if prev_url_path[i] == current_url_path[i]:             
            counter += 1                                        
    if counter >= 3:                                            # if we encounter this problem 3 times, we're definitely trapped.
        return True
    else:
        return False

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.
    if web_trap_handler(url):
        return []
    prev_url = url                                          
    links = []
    if resp.status in range(200,300):                       # we're getting a successful response from the url.
        content = resp.raw_response.content                 # grab the html content from the url
        soup = BeautifulSoup(content, "html.parser")        # soup the content
        for a in soup.find_all('a', href=True):             # find all links
            links.append(a['href'])
        for i in range(len(links)):                         # reformat all found links if needed
            links[i] = define_url(url, links[i])
        for link in links:
            if check_valid_domain(url) == False or robot_checker(url) == False:
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

def check_valid_domain(url):
    parsed_url = urlparse(url)                                      
    domain = parsed_url.netloc
    path = parsed_url.path
    if domain == "www.today.uci.edu":                               # check if our domain is www.today.uci.edu
        if "/department/information_computer_science" in path:      # if it is.. only check if our /department/information_computer_science is a substring of our path
            return True
    else:
        for d in accepted_domains:                  # check if one of the accepted domains is a substring of our url's domain
            if d in domain:                         # since we are crawling through *.[accepted domains]/*
                return True
    return False

def robot_checker(url):                                         # robot checker (refer to docs.python.org/3/library/urllib.robotparser.html)
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme                                  # grab our scheme [http/https]
    domain = parsed_url.netloc                                  # our domain (where the robots.txt file will be)
    
    rp = urllib.robotparser.RobotFileParser()                   
    robotFile = scheme + "://" + domain + "/robots.txt"         # [http/https]://[accepted domains]/robots.txt
    rp.set_url(robotFile)
    rp.read()
    return rp.can_fetch("*", url)                               # check if we are allowed to go crawl our given url