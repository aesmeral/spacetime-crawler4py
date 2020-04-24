import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib.robotparser


visited = set()
stopwords = []
sub_domain_ics = set()

# check if theres any repeating path directory for instance: "https://www.example.com/abc/abc/abc/abc"
def set_unique_page_count():
    ''' Stores number of unique pages visited in a file so count does not reset
    if a crawl is stopped and started at a different time. '''
    global visited
    content = get_unique_page_count()       # Get string page count
    count_file = open('unique_count.txt','w')
    count_file.write(str(int(content)+1))
    count_file.close()

def get_unique_page_count():
    ''' Returns number of unique pages visited, tracked in a text file. '''
    try:
        count_file = open('unique_count.txt','r')   # contains string count of urls visited
        count = count_file.read()
        count_file.close()
        return count
    except FileNotFoundError:
        return '0'       # No file yet means no page counted yet.

def add_visited_url(url):
    ''' Adds the url to the visited list and stores it in unique.txt '''
    global visited
    visited.add(url)
    unique_file = open('unique.txt','a')    # 'a' is file mode to append
    unique_file.write(url+'\n')
    unique_file.close()

def add_sub_domain_url(sub_domain):
    ''' add our unique sub_domain to our sub_domain_list '''
    sub_domain_name = urlparse(sub_domain).netloc.split(".")[0]
    sub_domain_counter(sub_domain_name)
    sub_domain_list = open('sub_domain_list.txt', 'a')
    sub_domain_list.write(sub_domain+'\n')
    sub_domain_list.close()

def sub_domain_counter(sub_domain):
    content = get_sub_domain_counter(sub_domain)
    count_file = open(sub_domain + ".txt", 'w')
    count_file.write(str(int(content) + 1))
    count_file.close()

def get_sub_domain_counter(sub_domain):
    try:
        count_file = open(sub_domain + ".txt", 'r')
        count = count_file.read()
        count_file
        return count
    except FileNotFoundError:
        return '0'

def get_visited_url_record():
    ''' Loads the list of previous urls from before this new session, from unique.txt '''
    global visited
    try:
        unique_file = open('unique.txt','r')
        content = unique_file.readlines()           # Returns list of file contents, split by newline characters. (eg. ['anthony\n','is\n','cool\n'])
        for line in content:
            visited.add(line.split('\n')[0])     # Each visited url is written with a newline, so we only want the first index of the split. (eg. ['ics.uci.edu',''])
        unique_file.close()
    except FileNotFoundError:
        pass        # First time loading, do nothing

def in_web_trap(url):
    parsed = urlparse(url)
    path_list = parsed.path[1:].split('/')
    if len(path_list) != len(set(path_list)):
        return True
    else:
        return False

# we only wanna scrape if our content type is a text or html? (pdf/applications are sometimes links we dont want)
def is_html_text(resp):
    try:
        if re.search("text|html", resp.raw_response.headers['content-type']) is not None:
            return True
        else:
            return False
    except:
        return False

def scraper(url, resp):
    get_visited_url_record()            # Loads visited urls from unique.txt
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.                  
    links = []
    if url in visited or in_web_trap(url) and not is_html_text(resp):
        return links
    add_visited_url(url)                # Add url to visited list and record
    set_unique_page_count()                                         # Keep track of unique urls
    print("Total URLs visited: {}".format(get_unique_page_count()))
    if resp.status in range(200,300):                               # we're getting a successful response from the url.
        content = resp.raw_response.content                         # grab the html content from the url
        ics_subdomain(url)
        soup = BeautifulSoup(content, "html.parser")                # soup the content
        if low_information_page(soup):
            print("low information")
            return links
        for a in soup.find_all('a', href=True):                     # find all links
            potential_url = urllib.parse.urljoin(url,a['href'])
            if is_valid(potential_url) and check_valid_domain(potential_url) and potential_url not in visited and not in_web_trap(potential_url):
                links.append(potential_url)
    return links

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        #encountered a case "http://www.informatics.uci.edu/files/pdf/InformaticsBrochure-March2018" which was a pdf, but still output True
        # so i modified this code a little bit. to where if it was a .extension or the extension existed in the path
        # also added: war and apk ...
        extension_types = "(css|js|bmp|gif|jpe?g|ico|img|" \
                          "png|tiff?|mid|mp2|mp3|mp4|" \
                          "wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|" \
                          "ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|" \
                          "data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|" \
                          "epub|dll|cnf|tgz|sha|apk|" \
                          "thmx|mso|arff|rtf|jar|csv|"\
                          "rm|smil|wmv|swf|wma|zip|rar|gz|war)"

        if re.search("(/)" + extension_types, parsed.path.lower()):
            return False
        if re.search("(.)" + extension_types, parsed.path.lower()):
            return False
        """
            # - is a scroll location
            event - can lead to a calendar
            gallery - can lead to a photo album
            upload - can lead to something with a file that might be missed in extension_type
            index.php - can lead us to getting stuck in some sort of weird trap
        """
        if '#' in url or "event" in url or "gallery" in url or "upload" in url or "index.php" in url:
            return False
        # honestly, it would take forever if we handled every query which can be in the thousands. (mostly news on the given domains)
        if len(parsed.query) != 0:
            return False
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
def check_valid_domain(url):
    # accept domains only from *.ics.uci.edu/ , *.cs.uci.edu , *.informatics.uci.edu , *.stat.uci.edu and the last one
    accepted_domains = "(\.ics\.uci\.edu|\.cs\.uci\.edu|\.informatics\.uci\.edu|\.stat\.uci\.edu|today\.uci\.edu\/department\/information_computer_sciences)"
    if not re.search(accepted_domains,urlparse(url).netloc):
        return False
    return True

def low_information_page(soup):
    global stopwords
    token_list = []
    if stopwords == []:
        with open("stopwords.txt", 'r') as fd:
            for line in fd:
                stopwords.append(line.replace("\n",""))
    try:
        content = " ".join([p.text for p in soup.find_all("p")])                # get all the text within a p tag (meat of the website)
        content = content.split()                                               # split it into a list
        for token in content:                                                   
            if token not in stopwords:                                          # if the token is not a stop word then...
                token_list.append(token)
        if len(content) < 50 or (len(token_list)/len(content) < 0.25):         # if we dont have alot of words then probably dont use it.
            return True
        return False
    except:
        return True
def ics_subdomain(url):
    scheme = urlparse(url).scheme
    domain = urlparse(url).netloc
    parsed_url = scheme + "://" + domain 
    if "ics.uci.edu" in domain:
        domain_list = domain.split(".")
        if  parsed_url not in sub_domain_ics:
            sub_domain_ics.add(parsed_url)
            add_sub_domain_url(parsed_url)
"thinking of implementing this somewhere... "
def robot_checker(url):                                         # robot checker (refer to docs.python.org/3/library/urllib.robotparser.html)
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme                                  # grab our scheme [http/https]
    domain = parsed_url.netloc                                  # our domain (where the robots.txt file will be)
    
    rp = urllib.robotparser.RobotFileParser()                   
    robotFile = scheme + "://" + domain + "/robots.txt"         # [http/https]://[accepted domains]/robots.txt
    rp.set_url(robotFile)
    rp.read()
    return rp.can_fetch("*", url)                               # check if we are allowed to go crawl our given url
