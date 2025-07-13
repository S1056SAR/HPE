import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin
import json
import os
import tempfile
import random
import re
from environment import SCRAPE_DELAY
import pickle
import io
import PyPDF2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from datetime import datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkDocScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://arubanetworking.hpe.com/"
        })
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
        ]
        
        self.setup_selenium()
    def setup_selenium(self):
        """Initialize Selenium WebDriver with improved configuration"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--ignore-certificate-errors")  
            chrome_options.add_argument("--ignore-ssl-errors") 
            chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("Selenium WebDriver initialized successfully")
            self.use_selenium = True
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {str(e)}")
            self.use_selenium = False
        
        self.use_selenium = True
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.url_cache_file = os.path.join(self.cache_dir, "url_cache.pkl")
        self.content_cache_file = os.path.join(self.cache_dir, "content_cache.pkl")
        
        if os.path.exists(self.url_cache_file):
            with open(self.url_cache_file, 'rb') as f:
                self.url_cache = pickle.load(f)
        else:
            self.url_cache = set()
            
        if os.path.exists(self.content_cache_file):
            with open(self.content_cache_file, 'rb') as f:
                self.content_cache = pickle.load(f)
        else:
            self.content_cache = {}
    
    def process_pdf_without_downloading(self, url):
        """Stream PDF and extract text without saving to disk"""
        try:
            # Get cookies from Selenium session
            selenium_cookies = self.driver.get_cookies()
            
            # Create a new requests session and add cookies
            session = requests.Session()
            for cookie in selenium_cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/pdf,application/x-pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://arubanetworking.hpe.com/techdocs/',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin'
            }
            

            logger.info(f"Streaming PDF from: {url}")
            response = session.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verify it's a PDF
            if 'application/pdf' in response.headers.get('Content-Type', ''):
                # Read content into memory
                pdf_content = io.BytesIO(response.content)
                
                # Extract text directly
                text = self.extract_text_from_memory(pdf_content)
                logger.info(f"Successfully extracted text from: {url}")
                return text
            else:
                logger.error(f"Downloaded content is not a PDF: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing PDF {url}: {str(e)}")
            return None
        
    def extract_text_from_memory(self, pdf_bytes):
        """Extract text content from a PDF file in memory"""
        reader = PyPDF2.PdfReader(pdf_bytes)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
        return text
    
    # Enhance the existing extract_pdf_content method with the improved version
    def extract_pdf_content(self, url):
        """Extract content from PDF files using improved method"""
        return self.process_pdf_without_downloading(url)


    def get_page(self, url):
        # if url in self.content_cache:
        #     logger.info(f"Using cached content for: {url}")
        #     return self.content_cache[url]
        html = None
        
        try:
            logger.info(f"Fetching: {url}")
            time.sleep(SCRAPE_DELAY + random.uniform(1.0, 3.0))
            
            if self.use_selenium:
                try:
                    self.driver.get(url)
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    logger.info(f"Explicitly refreshing page: {url}")
                    self.driver.refresh()
                    # Wait again after refresh to ensure content is loaded
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    html = self.driver.page_source
                    logger.info(f"Successfully fetched {url} using Selenium.")
                except Exception as e:
                    logger.warning(f"Selenium fetch failed for {url}: {str(e)}. Falling back to requests.")
                    html = None
            
            if not html:
                logger.info(f"Attempting fetch for {url} using requests.")
                # Use a specific User-Agent for the request
                headers = {
                    "User-Agent": random.choice(self.user_agents),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                }
                response = self.session.get(url, headers=headers, timeout=20) # Added timeout
                response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
                html = response.text
                logger.info(f"Successfully fetched {url} using requests.")

            # --- Caching is disabled ---
            # The original code would save to self.content_cache here.
            # We skip saving to the cache to ensure freshness on next call.
            # if html:
            #      self.content_cache[url] = html
            #      self.url_cache.add(url)
            #      self._save_cache()
            # --- End Caching Disabled ---

            return html

        except requests.exceptions.RequestException as e:
            # Handle errors specifically from the requests library
            logger.error(f"Requests error fetching {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def _save_cache(self):
        with open(self.url_cache_file, 'wb') as f:
            pickle.dump(self.url_cache, f)
        with open(self.content_cache_file, 'wb') as f:
            pickle.dump(self.content_cache, f)
    
    def parse_cisco_release_notes(self, url):
        """Parse Cisco release notes page and extract links and metadata"""
        html = self.get_page(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find all links in the document list
        for link in soup.select("a[href*='release-notes']"):
            title = link.text.strip()
            href = link.get('href')
            if href and title:
                # Get the date if available (usually in a nearby td)
                date_element = link.find_parent('tr').find('td', class_='dateColumn')
                date = date_element.text.strip() if date_element else "Unknown"
                
                # Construct absolute URL
                absolute_url = urljoin(url, href)
                
                results.append({
                    "title": title,
                    "url": absolute_url,
                    "date": date,
                    "vendor": "Cisco",
                    "doc_type": "Release Notes"
                })
        
        return results
    
    def parse_cisco_config_guides(self, url):
        """Parse Cisco configuration guides page and extract links and metadata"""
        html = self.get_page(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find all links to configuration guides
        for link in soup.select("a[href*='configuration']"):
            title = link.text.strip()
            href = link.get('href')
            if href and title:
                # Get the date if available
                date_element = link.find_parent('tr').find('td', class_='dateColumn')
                date = date_element.text.strip() if date_element else "Unknown"
                
                # Construct absolute URL
                absolute_url = urljoin(url, href)
                
                results.append({
                    "title": title,
                    "url": absolute_url,
                    "date": date,
                    "vendor": "Cisco",
                    "doc_type": "Configuration Guide"
                })
        
        return results
    
    def parse_document(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {
            "url": url,
            "vendor": self.extract_vendor(url, soup),
            "product_line": self.extract_product_line(url, soup),
            "release": self.extract_release(url, soup),
            "features": self.extract_features(url, soup),
            "categories": self.extract_categories(url, soup),
            "deployment": self.extract_deployment(url, soup)
        }
        content = self.extract_content(soup)
        return metadata, content
    
    def extract_vendor(self, url, soup):
        vendors = {
            "cisco": r"cisco\.com",
            "juniper": r"juniper\.net",
            "aruba": r"arubanetworks\.com",
            "arista": r"arista\.com",
            "hpe": r"hpe\.com"
        }
        for vendor, pattern in vendors.items():
            if re.search(pattern, url, re.IGNORECASE):
                return vendor.capitalize()
        return "Unknown"
    
    def extract_product_line(self, url, soup):
        product_patterns = {
            "Nexus": r"nexus[-\s]?\d+",
            "Catalyst": r"catalyst[-\s]?\d+",
            "MX Series": r"mx[-\s]?\d+",
            "EX Series": r"ex[-\s]?\d+",
            "CX Series": r"cx[-\s]?\d+"
        }
        content = soup.get_text()
        for line, pattern in product_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return f"{line}: {match.group()}"
        return "Unknown"
    
    def extract_release(self, url, soup):
        release_pattern = r"(Release|Version)\s+([\d\.]+)"
        match = re.search(release_pattern, soup.get_text(), re.IGNORECASE)
        return match.group(2) if match else "Unknown"
    
    def extract_features(self, url, soup):
        features = []
        hw_patterns = ["hardware", "physical", "port", "interface", "chassis"]
        sw_patterns = ["software", "firmware", "os", "operating system", "configuration"]
        
        content = soup.get_text().lower()
        if any(pattern in content for pattern in hw_patterns):
            features.append("Hardware")
        if any(pattern in content for pattern in sw_patterns):
            features.append("Software")
        
        return features if features else ["Unknown"]
    
    def extract_categories(self, url, soup):
        categories = []
        category_patterns = {
            "Switching": ["switch", "vlan", "spanning tree", "stp", "lacp", "trunk"],
            "Routing": ["rout", "ospf", "bgp", "eigrp", "rip", "static route"],
            "VPN": ["vpn", "ipsec", "ssl", "tunnel"]
        }
        
        content = soup.get_text().lower()
        for category, patterns in category_patterns.items():
            if any(pattern in content for pattern in patterns):
                categories.append(category)
        
        return categories if categories else ["Unknown"]
    
    def extract_deployment(self, url, soup):
        deployments = []
        deployment_patterns = {
            "Datacenter": ["data center", "rack", "server", "virtualization"],
            "Campus": ["campus", "office", "building", "enterprise"],
            "WAN": ["wan", "wide area network", "branch", "remote"]
        }
        
        content = soup.get_text().lower()
        for deployment, patterns in deployment_patterns.items():
            if any(pattern in content for pattern in patterns):
                deployments.append(deployment)
        
        return deployments if deployments else ["Unknown"]

    def extract_document_content(self, doc_meta):
        # """Extract the actual content from a document page"""
        # html = self.get_page(url)
        # if not html:
        #     return None
        
        # soup = BeautifulSoup(html, 'html.parser')
        
        # # Remove navigation, headers, footers
        # for element in soup.select('nav, header, footer, script, style'):
        #     element.decompose()
        
        # # Get the main content
        # main_content = soup.select_one('main, article, .content, #content')
        # if main_content:
        #     return main_content.get_text(separator='\n', strip=True)
        
        # # Fallback to body if no main content identified
        # return soup.body.get_text(separator='\n', strip=True)
        """Extract content based on document type"""
        url = doc_meta["url"]
        time.sleep(random.uniform(3, 7))
        # For PDF files, use the PDF extraction method
        if url.endswith(".pdf") or doc_meta.get("type") == "pdf":
            logger.info(f"Extracting content from PDF: {url}")
            return self.process_pdf_without_downloading(url)
        else:
            # For HTML files, use the regular extraction method
            logger.info(f"Extracting content from HTML: {url}")
            html = self.get_page(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation, headers, footers
            for element in soup.select('nav, header, footer, script, style'):
                element.decompose()
            
            # Get the main content
            main_content = soup.select_one('main, article, .content, #content')
            if main_content:
                return main_content.get_text(separator='\n', strip=True)
            
            # Fallback to body if no main content identified
            return soup.body.get_text(separator='\n', strip=True)
    
    
    def save_to_json(self, data, filename):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved data to {filename}")

    def parse_aruba_documentation(self, url):
        """Parse Aruba AOS-CX documentation page and extract all links with improved PDF handling"""
        html = self.get_page(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        pdf_links = soup.select("a[href$='.pdf']")
        for link in pdf_links:
            title = link.get_text(strip=True) or link.get('title', '') or "Untitled Document"
            href = link.get('href')
            if href:
                version = "Unknown"
                version_match = re.search(r'AOS-CX\s+(\d+\.\d+)', title)
                if version_match:
                    version = version_match.group(1)
                else:
                    parent_text = link.parent.get_text()
                    version_match = re.search(r'AOS-CX\s+(\d+\.\d+)', parent_text)
                    if version_match:
                        version = version_match.group(1)
                
                absolute_url = urljoin(url, href)
                results.append({
                    "title": title,
                    "url": absolute_url,
                    "version": version,
                    "vendor": "Aruba",
                    "doc_type": "AOS-CX Documentation",
                    "type": "pdf"  
                })
        
        html_links = soup.select("a[href$='.htm'], a[href$='.html']")
        for link in html_links:
            title = link.get_text(strip=True) or link.get('title', '') or "Untitled Document"
            href = link.get('href')
            if href:
                absolute_url = urljoin(url, href)
                results.append({
                    "title": title,
                    "url": absolute_url,
                    "vendor": "Aruba",
                    "doc_type": "AOS-CX Documentation",
                    "type": "html"
                })
        
        return results

    def scrape_dropdown_options(self, url):
        """Scrape all options from the dropdown selector and visit each page"""
        html = self.get_page(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        all_results = []
        
        dropdown = soup.select_one("select")
        if not dropdown:
            dropdown = soup.select_one("select[name*='other'], select[id*='other']")
        
        if dropdown:
            options = dropdown.select("option")
            
            for option in options:
                option_value = option.get("value")
                if option_value and not option_value.startswith("#"):
                    option_url = urljoin(url, option_value)
                    
                    logger.info(f"Visiting dropdown option page: {option_url}")
                    option_results = self.parse_aruba_documentation(option_url)
                    all_results.extend(option_results)
        
        return all_results

    def extract_pdf_content(self, url):
        """Extract content from PDF files"""
        try:
            logger.info(f"Downloading PDF: {url}")
            response = self.session.get(url)
            response.raise_for_status()
            
            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            # Extract text from the PDF
            text = ""
            try:
                # Using PyPDF2 to extract text
                with open(temp_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(reader.pages)):
                        text += reader.pages[page_num].extract_text() + "\n"
            finally:
                # Clean up the temporary file
                os.unlink(temp_path)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF content from {url}: {str(e)}")
            return None
        
    def parse_hacker_news(self, url):
        """Parse Hacker News front page and extract story links and metadata"""
        html = self.get_page(url)
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        # Find all story rows (identified by class 'athing')
        story_rows = soup.select("tr.athing")
        
        for row in story_rows:
            title_link = row.select_one('td.title > span.titleline > a')
            if title_link:
                title = title_link.text.strip()
                href = title_link.get('href')
                
                # Make sure href is an absolute URL if it's internal
                if href and not href.startswith(('http://', 'https://')):
                    href = urljoin(url, href) # Need 'from urllib.parse import urljoin' at the top

                if href and title:
                    # Use current time as the 'date' for testing update detection
                    current_time_str = datetime.now().isoformat()
                    
                    results.append({
                        "title": title,
                        "url": href,
                        "date": current_time_str, # Using current time for testing
                        "vendor": "HackerNews", # Assign a vendor name
                        "doc_type": "posts" # Assign a document type
                    })
                
        logger.info(f"Parsed {len(results)} stories from Hacker News: {url}")
        return results
    
            
    def __del__(self):
        if self.use_selenium and hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("Selenium WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing Selenium WebDriver: {str(e)}")
