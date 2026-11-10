from flask import Blueprint, request, jsonify, current_app

from models import db
from models.buyer import Buyer

import requests
import re
import random
import time

from datetime import datetime

from bs4 import BeautifulSoup

from urllib.parse import (
    urljoin,
    urlparse
)

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

scraper_bp = Blueprint(
    "scraper",
    __name__
)


# ============================================================
# Professional Browser Headers
# ============================================================

USER_AGENTS = [

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 Chrome/137.0 Safari/537.36",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/139.0"

]

# ============================================================
# Email Regex
# ============================================================

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)

EMAIL_PRIORITY = [

    "sales@",

    "export@",

    "exports@",

    "marketing@",

    "business@",

    "contact@",

    "info@",

    "support@",

    "office@",

    "admin@"

]


BLOCKED_WORDS = [

    "noreply",

    "no-reply",

    "donotreply",

    "example",

    "localhost",

    "invalid",

    "test"

]

COMMON_PAGES = [

    "",

    "/contact",

    "/contact-us",

    "/about",

    "/about-us",

    "/company",

    "/support",

    "/pages/contact",

    "/pages/about",

    "/wholesale"

]

CONTACT_KEYWORDS = [

    "contact",

    "about",

    "support",

    "help",

    "team",

    "company",

    "dealer",

    "wholesale",

    "sales",

    "reach-us",

    "customer-service"

]


def create_session():

    session = requests.Session()

    retry = Retry(

        total=3,

        backoff_factor=1,

        status_forcelist=[

            429,

            500,

            502,

            503,

            504

        ]

    )

    adapter = HTTPAdapter(

        max_retries=retry

    )

    session.mount(

        "https://",

        adapter

    )

    session.mount(

        "http://",

        adapter

    )

    return session


session = create_session()


# ============================================================
# Random Browser Header
# ============================================================
def browser_headers():

    return {

        "User-Agent": random.choice(USER_AGENTS),

        "Accept":

        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",

        "Accept-Language":

        "en-US,en;q=0.9",

        "Connection":

        "keep-alive"

    }


# ============================================================
# Clean URL
# ============================================================

def clean_url(url):

    if not url:

        return ""

    parsed = urlparse(url)

    return parsed.scheme + "://" + parsed.netloc

# ============================================================
# Country Detection
# ============================================================
def detect_country(url):

    url = url.lower()

    if ".in" in url:
        return "India"

    if ".uk" in url:
        return "United Kingdom"

    if ".au" in url:
        return "Australia"

    if ".ca" in url:
        return "Canada"

    if ".de" in url:
        return "Germany"

    if ".jp" in url:
        return "Japan"

    if ".fr" in url:
        return "France"

    if ".it" in url:
        return "Italy"

    return "USA"

# ============================================================
# Company Name
# ============================================================

def company_name_from_title(title):

    if not title:

        return "Unknown Company"

    title = title.replace("|", "-")

    title = title.split("-")[0]

    return title.strip()


# ============================================================
# Extract Emails From HTML
# ============================================================

def extract_emails(html):

    emails = set()

    soup = BeautifulSoup(

        html,

        "html.parser"

    )

    # -------------------------------
    # mailto:
    # -------------------------------

    for link in soup.find_all(

        "a",

        href=True

    ):

        href = link["href"]

        if href.startswith("mailto:"):

            email = href.replace(

                "mailto:",

                ""

            ).split("?")[0].strip()

            if email:

                emails.add(email)

    # -------------------------------
    # Regex Search
    # -------------------------------

    text = soup.get_text(

        " "

    )

    regex_emails = EMAIL_REGEX.findall(

        text

    )

    for email in regex_emails:

        emails.add(email)

    return list(emails)


# ============================================================
# Download HTML
# ============================================================

def download(url):

    try:

        response = session.get(

            url,

            headers=browser_headers(),

            timeout=10

        )

        if response.status_code == 200:

            return response.text

    except Exception:

        pass

    return None



# ============================================================
# Crawl Website
# ============================================================

def crawl_website(website):

    website = clean_url(website)

    found_emails = set()

    company_name = "Unknown Company"

    for page in COMMON_PAGES:

        try:

            url = urljoin(

                website,

                page

            )

            html = download(url)

            if html is None:
                continue

            soup = BeautifulSoup(

                html,

                "html.parser"

            )

            # -----------------------
            # Title
            # -----------------------

            if company_name == "Unknown Company":

                if soup.title and soup.title.text.strip():

                    company_name = company_name_from_title(

                        soup.title.text

                    )

            # -----------------------
            # mailto + regex emails
            # -----------------------

            emails = extract_emails(html)

            for email in emails:

                email = email.lower().strip()

                if email:

                    found_emails.add(email)

            # -----------------------
            # Contact links
            # -----------------------

            for link in soup.find_all("a", href=True):

                href = link["href"].lower()

                text = link.get_text(" ").lower()

                if any(

                    keyword in href

                    for keyword in [

                        "contact",

                        "about",

                        "support"

                    ]

                ) or any(

                    keyword in text

                    for keyword in [

                        "contact",

                        "about",

                        "support"

                    ]

                ):

                    try:

                        next_url = urljoin(

                            website,

                            link["href"]

                        )

                        next_html = download(next_url)

                        if next_html:

                            emails = extract_emails(

                                next_html

                            )

                            for email in emails:

                                found_emails.add(

                                    email.lower().strip()

                                )

                    except Exception:

                        pass

            time.sleep(0.5)

        except Exception:

            continue

    return {

        "company": company_name,

        "country": detect_country(website),

        "website": website,

        "emails": list(found_emails)

    }


# ============================================================
# Google Search
# ============================================================

def google_search(product):

    api_key = current_app.config.get(

        "GOOGLE_API_KEY"

    )

    search_engine = current_app.config.get(

        "GOOGLE_SEARCH_ENGINE_ID"

    )

    url = "https://www.googleapis.com/customsearch/v1"

    params = {

        "key": api_key,

        "cx": search_engine,

        "q": f"{product} importers",

        "num": 30

    }

    try:

        response = session.get(

            url,

            params=params,

            timeout=20

        )

        data = response.json()

        results = []

        for item in data.get("items", []):

            results.append({

                "title": item.get("title"),

                "link": item.get("link")

            })

        return results

    except Exception as e:

        print(e)

        return []




# ============================================================
# Build Buyer List
# ============================================================



def build_buyers(product):

    buyers = []

    visited = set()

    google_results = google_search(product)

    if not google_results:
        print("No Google search results found.")
        return buyers

    for item in google_results:

        website = clean_url(item.get("link", ""))

        if website == "":
            continue

        if website in visited:
            continue

        visited.add(website)

        print("=" * 70)
        print(f"Scanning Website : {website}")

        try:

            info = scan_website(website)

            print("Company :", info.get("company"))
            print("Emails Found :", info.get("emails", []))
            print("=" * 70)

            emails = info.get("emails", [])

            emails = filter_emails(emails)

            email = best_email(emails)

            buyers.append({

                "company": info.get(
                    "company",
                    "Unknown Company"
                ),

                "country": info.get(
                    "country",
                    "Unknown"
                ),

                "website": info.get(
                    "website",
                    website
                ),

                "email": email,

                "emails": emails

            })

        except Exception as e:

            print(f"Error scanning {website}")
            print(e)

        polite_delay()

    return buyers
# ============================================================
# Validate Email
# ============================================================

def is_valid_email(email):

    if not email:
        return False

    email = email.strip().lower()

    if EMAIL_REGEX.fullmatch(email) is None:
        return False

    invalid_domains = [

        "example.com",
        "example.org",
        "example.net",
        "localhost",
        "test.com"

    ]

    domain = email.split("@")[-1]

    if domain in invalid_domains:
        return False

    return True


# ============================================================
# Remove Duplicate Emails
# ============================================================

def unique_emails(email_list):

    seen = set()

    result = []

    for email in email_list:

        email = email.strip().lower()

        if not is_valid_email(email):
            continue

        if email in seen:
            continue

        seen.add(email)

        result.append(email)

    return result


# ============================================================
# Remove Unwanted Emails
# ============================================================

def filter_emails(email_list):

    filtered = []

    for email in email_list:

        email = email.lower().strip()

        blocked = False

        for word in BLOCKED_WORDS:

            if word in email:

                blocked = True
                break

        if not blocked:

            filtered.append(email)

    return filtered


# ============================================================
# Score Business Emails
# ============================================================

def score_email(email):

    email = email.lower()

    for index, prefix in enumerate(EMAIL_PRIORITY):

        if email.startswith(prefix):

            return 100 - index

    return 10


# ============================================================
# Select Best Email
# ============================================================

def best_email(email_list):

    if len(email_list) == 0:
        return ""

    email_list = sorted(

        email_list,

        key=score_email,

        reverse=True

    )

    return email_list[0]
# ============================================================
# Scan Website
# ============================================================

def scan_website(website):

    website = clean_url(website)

    html = download(website)

    if html is None:

        return {

            "company": "Unknown Company",

            "country": detect_country(website),

            "website": website,

            "emails": []

        }

    soup = BeautifulSoup(html, "html.parser")

    # -----------------------
    # Company Name
    # -----------------------

    if soup.title and soup.title.text.strip():

        company = company_name_from_title(

            soup.title.text

        )

    else:

        company = urlparse(

            website

        ).netloc.replace(

            "www.", ""

        )

    found_emails = set()

    # -----------------------
    # Homepage Emails
    # -----------------------

    homepage_emails = extract_emails(html)

    for email in homepage_emails:

        if is_valid_email(email):

            found_emails.add(

                email.lower()

            )

    # -----------------------
    # Contact/About Links
    # -----------------------

    for link in soup.find_all(

        "a",

        href=True

    ):

        href = link["href"]

        text = link.get_text(

            " ",

            strip=True

        )

        if not is_contact_page(

            href,

            text

        ):

            continue

        try:

            contact_url = urljoin(

                website,

                href

            )

            contact_html = download(

                contact_url

            )

            if contact_html is None:

                continue

            emails = extract_emails(

                contact_html

            )

            for email in emails:

                if is_valid_email(email):

                    found_emails.add(

                        email.lower()

                    )

            polite_delay()

        except Exception:

            pass

    # -----------------------
    # Common Pages
    # -----------------------

    for page in COMMON_PAGES:

        try:

            page_url = urljoin(

                website,

                page

            )

            page_html = download(

                page_url

            )

            if page_html is None:

                continue

            emails = extract_emails(

                page_html

            )

            for email in emails:

                if is_valid_email(email):

                    found_emails.add(

                        email.lower()

                    )

            polite_delay()

        except Exception:

            pass

    emails = unique_emails(

        filter_emails(

            list(found_emails)

        )

    )

    return {

        "company": company,

        "country": detect_country(

            website

        ),

        "website": website,

        "emails": emails

    }
# ============================================================
# Small Delay Between Requests
# ============================================================

def polite_delay():

    time.sleep(

        random.uniform(

            0.8,

            1.5

        )

    )
    # ============================================================
# Save Buyers to Database
# ============================================================

def save_buyers_to_database(buyers):

    saved = 0
    skipped = 0

    for buyer in buyers:

        website = buyer.get("website", "").strip()
        email = buyer.get("email", "").strip().lower()

        # Skip empty website
        if website == "":
            continue

        # Check duplicate website
        existing = Buyer.query.filter_by(
            website=website
        ).first()

        if existing:
            skipped += 1
            continue

        new_buyer = Buyer(

            company_name=buyer.get(
                "company",
                "Unknown Company"
            ),

            country=buyer.get(
                "country",
                "Unknown"
            ),

            website=website,

            email=email

        )

        db.session.add(new_buyer)

        saved += 1

    db.session.commit()

    return {

        "saved": saved,

        "skipped": skipped

    }


# ============================================================
# Logger
# ============================================================

def log_scraper(message):

    print(

        f"[SCRAPER] {datetime.now()} : {message}"

    )


# ============================================================
# Professional Search
# ============================================================

def professional_search(product):

    log_scraper(

        f"Searching buyers for {product}"

    )

    buyers = build_buyers(product)

    log_scraper(

        f"{len(buyers)} buyers found."

    )

    return buyers


# ============================================================
# Search Buyers API
# ============================================================

@scraper_bp.route(
    "/api/search-buyers",
    methods=["POST"]
)

def search_buyers():

    data = request.get_json()

    product = data.get(
        "product",
        ""
    ).strip()

    if product == "":

        return jsonify({

            "success": False,

            "error": "Please enter product name."

        }), 400

    try:

        buyers = professional_search(product)

        return jsonify({

            "success": True,

            "buyers": buyers,

            "count": len(buyers)

        })

    except Exception as e:

        print(e)

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ============================================================
# Save Buyers API
# ============================================================

@scraper_bp.route(
    "/api/save-buyers",
    methods=["POST"]
)

def save_buyers():

    data = request.get_json()

    buyers = data.get(
        "buyers",
        []
    )

    if len(buyers) == 0:

        return jsonify({

            "success": False,

            "error": "No buyers found."

        }), 400

    result = save_buyers_to_database(
        buyers
    )

    return jsonify({

        "success": True,

        "saved": result["saved"],

        "skipped": result["skipped"]

    })


# ============================================================
# Status API
# ============================================================

@scraper_bp.route(
    "/api/scraper/status",
    methods=["GET"]
)

def scraper_status():

    return jsonify({

        "success": True,

        "service": "Professional Buyer Scraper",

        "status": "Running"

    })