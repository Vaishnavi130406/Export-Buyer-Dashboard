"""
services/buyer_search_service.py

FAST Google Maps / Local-first B2B buyer discovery service.

Design goals:
- Only 3 Google Maps/Local API calls per search.
- ZIP is a ranking preference, NOT a hard filter.
- Country/state/city remain the actual location filters.
- Use Google Maps result address as the primary source of location data.
- Use Google Maps for business discovery and targeted Google web search only for named decision-maker discovery.
- Do not use geopy/Nominatim.
- Use an optional, targeted browser fallback only when static HTML does not expose an email.
- Do not crawl dozens of pages.
- Only enrich the best candidates for email/extra phone/company information.
- Keep the public API compatible with the existing Flask route:

    search_buyers(
        buyer=..., product=..., country=..., state=...,
        city=..., zipcode=..., source=..., limit=...
    )
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

try:
    from serpapi import GoogleSearch
except ImportError:  # pragma: no cover
    GoogleSearch = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


# ============================================================
# ENVIRONMENT / LOGGING
# ============================================================

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY", "").strip()
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "").strip()
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "").strip()
ENABLE_HUNTER = os.getenv("ENABLE_HUNTER", "false").lower() == "true"
ENABLE_APOLLO = os.getenv("ENABLE_APOLLO", "false").lower() == "true"
ENRICHMENT_TIMEOUT = float(os.getenv("ENRICHMENT_TIMEOUT", "8"))

# Public-web decision-maker discovery. This is the primary contact lookup path.
ENABLE_CONTACT_SEARCH = os.getenv("ENABLE_CONTACT_SEARCH", "true").lower() == "true"
MAX_CONTACT_SEARCH_CALLS = int(os.getenv("MAX_CONTACT_SEARCH_CALLS", "4"))
CONTACT_SEARCH_RESULTS = int(os.getenv("CONTACT_SEARCH_RESULTS", "5"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# ============================================================
# PERFORMANCE SETTINGS
# ============================================================

# IMPORTANT: keep these low for a fast UI request.
MAX_LOCAL_CALLS = 3
MAX_LOCAL_RESULTS_PER_CALL = 20
MAX_CANDIDATES = 25
MAX_RESULTS = 50

# Enrich more candidates so real emails are not missed.
MAX_EMAIL_ENRICHMENT = 8
MAX_WORKERS = 8

# Real-world websites can be slow or redirect several times.
REQUEST_TIMEOUT = 4
MAX_CONTACT_PAGES = 2

# Only use browser rendering for candidates whose normal HTTP crawl found no email.
ENABLE_PLAYWRIGHT_FALLBACK = False
MAX_BROWSER_FALLBACKS = 0
BROWSER_TIMEOUT_MS = 6000

# Named-contact extraction. Generic inboxes are kept only as fallback.
GENERIC_EMAIL_PREFIXES = {
    "info", "contact", "sales", "support", "office", "admin", "hello",
    "help", "service", "customerservice", "customer.service", "orders",
    "order", "wholesale", "purchasing", "procurement", "buyer", "buyers",
    "business", "export", "exports", "marketing", "accounts", "billing",
    "enquiries", "inquiries", "reception", "team", "careers", "hr",
}

CONTACT_ROLE_PATTERNS = (
    ("Purchasing Manager", r"purchasing\s+manager"),
    ("Procurement Manager", r"procurement\s+manager"),
    ("Purchasing Director", r"purchasing\s+director"),
    ("Procurement Director", r"procurement\s+director"),
    ("Buying Manager", r"buying\s+manager"),
    ("Buyer", r"\bbuyer\b"),
    ("Merchandising Manager", r"merchandising\s+manager"),
    ("Category Manager", r"category\s+manager"),
    ("Wholesale Manager", r"wholesale\s+manager"),
    ("Owner", r"\bowner\b"),
    ("Founder", r"\bfounder\b"),
    ("Co-Founder", r"co[- ]founder"),
    ("CEO", r"\bceo\b|chief\s+executive\s+officer"),
    ("Director", r"\bdirector\b"),
    ("General Manager", r"general\s+manager"),
)

# Organic Google search is used only for targeted decision-maker discovery.
# It is NOT used to discover buyer businesses; Google Maps remains the business source.
ENABLE_ORGANIC_SEARCH = ENABLE_CONTACT_SEARCH

# ============================================================
# USER-AGENT / REGEX
# ============================================================

USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36",
)

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
)

PHONE_REGEX = re.compile(
    r"(?:\+\d{1,3}[\s().-]?)?"
    r"(?:\(?\d{2,4}\)?[\s.-]?){1,3}"
    r"\d{3,4}[\s.-]?\d{3,4}"
)

ZIP_US = re.compile(r"\b\d{5}(?:-\d{4})?\b")
ZIP_CA = re.compile(
    r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z]"
    r"\s?\d[ABCEGHJ-NPRSTV-Z]\d\b",
    re.I,
)
ZIP_UK = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.I)

US_STATE_ABBR = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

US_STATE_NAME_TO_ABBR = {value.lower(): key for key, value in US_STATE_ABBR.items()}

CA_PROVINCE_ABBR = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba",
    "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia", "ON": "Ontario", "PE": "Prince Edward Island",
    "QC": "Quebec", "SK": "Saskatchewan",
}

CA_PROVINCE_NAME_TO_ABBR = {
    value.lower(): key for key, value in CA_PROVINCE_ABBR.items()
}

COUNTRY_ALIASES = {
    "usa": "USA",
    "us": "USA",
    "u.s.": "USA",
    "u.s.a.": "USA",
    "united states": "USA",
    "united states of america": "USA",
    "canada": "Canada",
    "ca": "Canada",
    "uk": "UK",
    "united kingdom": "UK",
    "great britain": "UK",
    "england": "UK",
    "scotland": "UK",
    "wales": "UK",
}

COUNTRY_CONFIG = {
    "USA": {
        "gl": "us",
        "google_domain": "google.com",
        "location_name": "United States",
    },
    "Canada": {
        "gl": "ca",
        "google_domain": "google.ca",
        "location_name": "Canada",
    },
    "UK": {
        "gl": "uk",
        "google_domain": "google.co.uk",
        "location_name": "United Kingdom",
    },
}

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "icloud.com", "live.com", "msn.com",
    "protonmail.com", "mail.com", "yandex.com",
}

INVALID_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net",
    "localhost", "test.com", "invalid.com",
}

INVALID_EMAIL_DOMAIN_FRAGMENTS = (
    "wixpress", "sentry", "cloudflare", "shopifyemail", "sendgrid",
    "mailgun", "amazonaws", "googleusercontent", "hubspotemail",
    "klaviyo", "mailchimp", "freshdesk", "zendesk", "doubleclick",
    "googleadservices",
)

BLOCKED_DOMAINS = {
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
    "twitter.com", "x.com", "threads.net", "tiktok.com",
    "pinterest.com", "reddit.com", "amazon.com", "amazon.ca",
    "amazon.co.uk", "ebay.com", "etsy.com", "walmart.com",
    "wayfair.com", "alibaba.com", "aliexpress.com", "globalsources.com",
    "exporthub.com", "tradewheel.com", "go4worldbusiness.com",
    "tradeindia.com", "indiamart.com", "exportersindia.com",
    "made-in-china.com", "ec21.com", "ecplaza.net", "tradekey.com",
    "volza.com", "google.com", "google.ca", "google.co.uk",
    "google.co.in", "bing.com", "yahoo.com", "wikipedia.org",
    "wikimedia.org", "yelp.com", "yellowpages.com", "superpages.com",
    "manta.com", "merchantcircle.com", "foursquare.com",
    "tripadvisor.com", "chamberofcommerce.com", "mapquest.com",
    "zoominfo.com", "apollo.io", "crunchbase.com", "glassdoor.com",
    "indeed.com",
}

BLOCKED_TITLE_WORDS = {
    "directory", "directories", "database", "marketplace",
    "market report", "research and markets", "company database",
    "supplier directory", "yellow pages", "job board", "wikipedia",
}

PRODUCT_RELATED = {
    "candle": {
        "candle", "candles", "votive", "tealight", "tea light",
        "lantern", "candle holder", "wax", "home fragrance",
    },
    "singing bowl": {
        "singing bowl", "singing bowls", "tibetan bowl",
        "sound bowl", "sound healing", "chakra bowl",
        "sound bath", "meditation",
    },
    "bowl": {
        "bowl", "singing bowl", "tibetan bowl",
        "sound bath", "sound healing",
    },
}

BUYER_TYPES = {
    "Importer": {"importer", "importers", "imports"},
    "Wholesaler": {
        "wholesale", "wholesaler", "wholesalers",
        "bulk orders", "trade orders",
    },
    "Distributor": {"distributor", "distribution", "dealer", "dealers"},
    "Gift Retailer": {"gift shop", "gift store", "giftware", "souvenir"},
    "Wellness Retailer": {
        "wellness", "meditation", "yoga", "sound healing",
        "holistic", "spiritual", "metaphysical",
    },
    "Home Décor Retailer": {
        "home decor", "home décor", "interior decor",
        "home accessories",
    },
    "Specialty Retailer": {
        "boutique", "specialty store", "lifestyle store",
    },
    "Retailer": {
        "retail", "retailer", "retailers", "shop", "store",
    },
    "Manufacturer": {
        "manufacturer", "manufacturing", "factory",
    },
    "Online Store": {
        "online store", "online shop", "ecommerce", "e-commerce",
    },
}

COMMERCIAL_KEYWORDS = {
    "wholesale", "wholesaler", "bulk", "bulk order",
    "trade account", "importer", "importers", "distributor",
    "distribution", "minimum order", "moq", "private label",
    "custom branding", "retailer", "retailers",
    "trade pricing", "trade program",
}

session = requests.Session()


# ============================================================
# BASIC HELPERS
# ============================================================

def headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", unescape(str(value or ""))).strip()


def normalize_country(value: Any) -> str:
    raw = normalize_text(value).lower()
    if not raw:
        return "USA"
    return COUNTRY_ALIASES.get(raw, raw.title())


def normalize_city(value: Any) -> str:
    return re.sub(r"[^a-z0-9 ]", "", normalize_text(value).lower()).strip()


def normalize_region(value: Any) -> str:
    return re.sub(r"[^a-z0-9 ]", "", normalize_text(value).lower()).strip()


def normalize_zip(value: Any, country: str = "USA") -> str:
    value = normalize_text(value).upper()
    if not value:
        return ""

    country = normalize_country(country)

    if country == "USA":
        match = ZIP_US.search(value)
        return match.group(0) if match else ""

    if country == "Canada":
        match = ZIP_CA.search(value)
        return re.sub(r"\s+", " ", match.group(0)).strip() if match else ""

    if country == "UK":
        match = ZIP_UK.search(value)
        return re.sub(r"\s+", " ", match.group(0)).strip() if match else ""

    return value


def zip_matches(found: str, requested: str, country: str = "USA") -> bool:
    found_norm = normalize_zip(found, country)
    requested_norm = normalize_zip(requested, country)

    if not found_norm or not requested_norm:
        return False

    if normalize_country(country) == "USA":
        return found_norm[:5] == requested_norm[:5]

    return found_norm.replace(" ", "") == requested_norm.replace(" ", "")


def clean_url(url: Any) -> str:
    if not url:
        return ""

    try:
        parsed = urlparse(unquote(str(url).strip()))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""

        host = parsed.netloc.lower()
        host = host.replace(":80", "").replace(":443", "")
        return f"{parsed.scheme}://{host}"
    except Exception:
        return ""


def normalize_page_url(url: Any) -> str:
    if not url:
        return ""

    try:
        parsed = urlparse(unquote(str(url).strip()))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""

        return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path or '/'}"
    except Exception:
        return ""


def get_domain(url: Any) -> str:
    try:
        host = urlparse(str(url)).netloc.lower().split(":", 1)[0]
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def is_blocked_domain(url: str) -> bool:
    domain = get_domain(url)
    if not domain:
        return True

    return any(
        domain == blocked or domain.endswith("." + blocked)
        for blocked in BLOCKED_DOMAINS
    )


# ============================================================
# ADDRESS PARSING
# ============================================================

def _state_from_text_for_country(text: str, country: str) -> str:
    """Return canonical region if clearly present."""
    text = normalize_text(text)

    if country == "USA":
        # Prefer two-letter state code before full names.
        match = re.search(r"(?:^|,\s*)([A-Z]{2})(?:\s+\d{5}(?:-\d{4})?)?(?:,|$)", text)
        if match and match.group(1) in US_STATE_ABBR:
            return US_STATE_ABBR[match.group(1)]

        lower = text.lower()
        for name in sorted(US_STATE_NAME_TO_ABBR, key=len, reverse=True):
            if re.search(rf"\b{re.escape(name)}\b", lower, re.I):
                return US_STATE_NAME_TO_ABBR[name].title() if False else {
                    v.lower(): v for v in US_STATE_ABBR.values()
                }.get(name, name.title())

    if country == "Canada":
        match = re.search(r"(?:^|,\s*)([A-Z]{2})(?:\s+[A-Z]\d[A-Z]\s?\d[A-Z]\d)?(?:,|$)", text)
        if match and match.group(1) in CA_PROVINCE_ABBR:
            return CA_PROVINCE_ABBR[match.group(1)]

        lower = text.lower()
        for name in sorted(CA_PROVINCE_NAME_TO_ABBR, key=len, reverse=True):
            if re.search(rf"\b{re.escape(name)}\b", lower, re.I):
                return CA_PROVINCE_NAME_TO_ABBR[name].title() if False else {
                    v.lower(): v for v in CA_PROVINCE_ABBR.values()
                }.get(name, name.title())

    if country == "UK":
        # UK addresses do not have states in the US sense.
        return ""

    return ""


def _canonical_us_state_from_name(name: str) -> str:
    lower = normalize_text(name).lower()

    if lower in US_STATE_NAME_TO_ABBR:
        abbr = US_STATE_NAME_TO_ABBR[lower]
        return US_STATE_ABBR[abbr]

    if upper := normalize_text(name).upper():
        if upper in US_STATE_ABBR:
            return US_STATE_ABBR[upper]

    return normalize_text(name)


def _canonical_ca_province_from_name(name: str) -> str:
    lower = normalize_text(name).lower()

    if lower in CA_PROVINCE_NAME_TO_ABBR:
        abbr = CA_PROVINCE_NAME_TO_ABBR[lower]
        return CA_PROVINCE_ABBR[abbr]

    upper = normalize_text(name).upper()
    if upper in CA_PROVINCE_ABBR:
        return CA_PROVINCE_ABBR[upper]

    return normalize_text(name)


def parse_address(
    address: str,
    country_hint: str = "",
    target_city: str = "",
    target_state: str = "",
    target_zip: str = "",
) -> Dict[str, str]:
    """
    Parse normal Google Maps-style addresses.

    Examples:
      945 Sun Mun Wy, Los Angeles, CA 90012
      2237 Sunset Blvd, Los Angeles, CA 90026
      123 Main St, Austin, TX 78701, USA
    """
    result = {
        "street": "",
        "city": "",
        "state": "",
        "zipcode": "",
        "country": "",
    }

    address = normalize_text(address).strip(" ,")
    country = normalize_country(country_hint) if country_hint else ""

    if not address:
        if country:
            result["country"] = country
        return result

    # ZIP / postcode.
    if country == "USA":
        match = ZIP_US.search(address)
        if match:
            result["zipcode"] = match.group(0)
    elif country == "Canada":
        match = ZIP_CA.search(address)
        if match:
            result["zipcode"] = normalize_zip(match.group(0), "Canada")
    elif country == "UK":
        match = ZIP_UK.search(address)
        if match:
            result["zipcode"] = normalize_zip(match.group(0), "UK")
    else:
        # Try all, but do not treat a US ZIP as proof of another country.
        for pattern in (ZIP_US, ZIP_CA, ZIP_UK):
            match = pattern.search(address)
            if match:
                result["zipcode"] = normalize_text(match.group(0))
                break

    # USA: most Google addresses are:
    # street, city, ST ZIP
    if country == "USA" or (not country and ZIP_US.search(address)):
        us_match = re.search(
            r"^(?P<street>.+?),\s*"
            r"(?P<city>[^,]+?),\s*"
            r"(?P<state>[A-Z]{2})\s+"
            r"(?P<zip>\d{5}(?:-\d{4})?)"
            r"(?:,\s*(?P<country>.*))?$",
            address,
        )

        if us_match and us_match.group("state") in US_STATE_ABBR:
            result["street"] = normalize_text(us_match.group("street"))
            result["city"] = normalize_text(us_match.group("city"))
            result["state"] = US_STATE_ABBR[us_match.group("state")]
            result["zipcode"] = us_match.group("zip")
            result["country"] = "USA"
            return result

        # Less strict: ... city, ST ZIP
        us_match = re.search(
            r"^(?P<street>.+?),\s*"
            r"(?P<city>[^,]+?),\s*"
            r"(?P<state>[A-Z]{2})\s+"
            r"(?P<zip>\d{5}(?:-\d{4})?)",
            address,
        )
        if us_match and us_match.group("state") in US_STATE_ABBR:
            result["street"] = normalize_text(us_match.group("street"))
            result["city"] = normalize_text(us_match.group("city"))
            result["state"] = US_STATE_ABBR[us_match.group("state")]
            result["zipcode"] = us_match.group("zip")
            result["country"] = "USA"
            return result

    # Canada:
    if country == "Canada" or ZIP_CA.search(address):
        ca_match = re.search(
            r"^(?P<street>.+?),\s*"
            r"(?P<city>[^,]+?),\s*"
            r"(?P<province>[A-Z]{2})\s+"
            r"(?P<zip>[ABCEGHJ-NPRSTV-Z]\d[ABCEGHJ-NPRSTV-Z]"
            r"\s?\d[ABCEGHJ-NPRSTV-Z]\d)$",
            address,
            re.I,
        )
        if ca_match and ca_match.group("province").upper() in CA_PROVINCE_ABBR:
            result["street"] = normalize_text(ca_match.group("street"))
            result["city"] = normalize_text(ca_match.group("city"))
            result["state"] = CA_PROVINCE_ABBR[ca_match.group("province").upper()]
            result["zipcode"] = normalize_zip(ca_match.group("zip"), "Canada")
            result["country"] = "Canada"
            return result

    # Generic comma-based fallback.
    parts = [normalize_text(p) for p in address.split(",") if normalize_text(p)]

    # Remove trailing country words.
    if parts:
        last = parts[-1].lower()
        if last in {"usa", "us", "united states", "united states of america", "canada", "uk", "united kingdom"}:
            result["country"] = normalize_country(parts.pop())

    if not result["country"] and country:
        result["country"] = country

    # Try to locate explicit region.
    detected_state = _state_from_text_for_country(address, country or "USA")

    if detected_state:
        result["state"] = detected_state

    if result["state"]:
        # City is immediately before state in common comma-delimited addresses.
        state_index = -1
        state_lower = result["state"].lower()
        state_aliases = []

        if country == "USA":
            state_aliases = [result["state"], US_STATE_NAME_TO_ABBR.get(state_lower, "")]
        elif country == "Canada":
            state_aliases = [result["state"], CA_PROVINCE_NAME_TO_ABBR.get(state_lower, "")]

        for index, part in enumerate(parts):
            if any(alias and part.lower() == alias.lower() for alias in state_aliases):
                state_index = index
                break

        if state_index > 0:
            result["city"] = parts[state_index - 1]
            if state_index >= 2:
                result["street"] = ", ".join(parts[: state_index - 1])

    if not result["city"] and len(parts) >= 2:
        # If ZIP is in the final part, city is normally the previous segment.
        if result["zipcode"]:
            candidate = parts[-2]
        else:
            candidate = parts[-1]

        # Avoid selecting state-only segments.
        if candidate and len(candidate) <= 100:
            result["city"] = candidate

    if not result["street"]:
        street_match = re.search(
            r"\b\d{1,7}[A-Za-z0-9 .,'#/-]{2,120}",
            address,
        )
        if street_match:
            result["street"] = normalize_text(street_match.group(0)).strip(" ,")

    # Only normalize to the requested location when the requested text is visibly
    # present in the address itself.
    if target_city and re.search(
        rf"\b{re.escape(normalize_text(target_city))}\b",
        address,
        re.I,
    ):
        result["city"] = normalize_text(target_city)

    if target_state:
        requested_state = normalize_text(target_state)

        aliases = {requested_state.lower()}
        if country == "USA":
            abbr = US_STATE_NAME_TO_ABBR.get(requested_state.lower())
            if abbr:
                aliases.add(abbr.lower())
        elif country == "Canada":
            abbr = CA_PROVINCE_NAME_TO_ABBR.get(requested_state.lower())
            if abbr:
                aliases.add(abbr.lower())

        if any(
            re.search(rf"\b{re.escape(alias)}\b", address, re.I)
            for alias in aliases
            if alias
        ):
            if country == "USA":
                result["state"] = _canonical_us_state_from_name(requested_state)
            elif country == "Canada":
                result["state"] = _canonical_ca_province_from_name(requested_state)
            else:
                result["state"] = requested_state

    return result


def location_score(
    parsed: Dict[str, str],
    target_country: str,
    target_state: str,
    target_city: str,
    target_zip: str,
) -> int:
    score = 0

    if parsed.get("country") and normalize_country(parsed["country"]) == target_country:
        score += 20

    if (
        target_state
        and parsed.get("state")
        and normalize_region(parsed["state"]) == normalize_region(target_state)
    ):
        score += 30

    if (
        target_city
        and parsed.get("city")
        and normalize_city(parsed["city"]) == normalize_city(target_city)
    ):
        score += 35

    if (
        target_zip
        and parsed.get("zipcode")
        and zip_matches(parsed["zipcode"], target_zip, target_country)
    ):
        score += 35

    if parsed.get("zipcode"):
        score += 5

    if parsed.get("street"):
        score += 5

    return min(score, 100)


# ============================================================
# EMAIL / PHONE
# ============================================================

def valid_email(email: str) -> bool:
    email = unescape(normalize_text(email)).lower()

    if not EMAIL_REGEX.fullmatch(email):
        return False

    local, domain = email.rsplit("@", 1)

    if not local or not domain:
        return False

    if len(local) > 64 or len(domain) > 253:
        return False

    if domain in INVALID_EMAIL_DOMAINS:
        return False

    if any(fragment in domain for fragment in INVALID_EMAIL_DOMAIN_FRAGMENTS):
        return False

    if domain.endswith((".local", ".invalid")):
        return False

    if re.search(r"\.(?:png|jpg|jpeg|gif|svg|webp|ico|css|js|pdf)$", local, re.I):
        return False

    return True


def _decode_cloudflare_email(encoded: str) -> str:
    """Decode Cloudflare Email Protection's data-cfemail value."""
    try:
        raw = bytes.fromhex(normalize_text(encoded))
        if len(raw) < 2:
            return ""
        key = raw[0]
        return "".join(chr(byte ^ key) for byte in raw[1:])
    except Exception:
        return ""


def extract_emails(html: str) -> List[str]:
    """
    Extract public emails from HTML, including: 
    - normal text
    - mailto links
    - obfuscated [at]/[dot] forms
    - spaced @ / dot forms
    - HTML attributes/data attributes
    - Cloudflare data-cfemail protection
    """
    if not html:
        return []

    found = set()

    try:
        decoded = unescape(html)

        # Common text obfuscation.
        decoded = re.sub(
            r"\s*(?:\[at\]|\(at\)|\{at\}|\s+at\s+)\s*",
            "@",
            decoded,
            flags=re.I,
        )
        decoded = re.sub(
            r"\s*(?:\[dot\]|\(dot\)|\{dot\}|\s+dot\s+)\s*",
            ".",
            decoded,
            flags=re.I,
        )
        decoded = re.sub(r"\s+@\s+", "@", decoded)

        # Cloudflare-protected emails.
        cloudflare_hits = re.findall(r'data-cfemail=["\']([^"\']+)["\']', decoded, re.I)
        for encoded in cloudflare_hits:
            value = _decode_cloudflare_email(encoded)
            if valid_email(value):
                found.add(value.lower())

        soup = BeautifulSoup(decoded, "html.parser")

        # mailto links.
        for tag in soup.find_all("a", href=True):
            href = str(tag.get("href", ""))
            if href.lower().startswith("mailto:"):
                value = unquote(href[7:].split("?", 1)[0].strip())
                if valid_email(value):
                    found.add(value.lower())

        # Search complete tag attributes too. This catches data-email, content, title, etc.
        for tag in soup.find_all(True):
            for attr_value in tag.attrs.values():
                values = attr_value if isinstance(attr_value, list) else [attr_value]
                for raw in values:
                    value = unescape(str(raw or ""))
                    if not value:
                        continue
                    for email in EMAIL_REGEX.findall(value):
                        if valid_email(email):
                            found.add(email.lower())

        # Normal email strings anywhere in decoded HTML.
        for value in EMAIL_REGEX.findall(decoded):
            if valid_email(value):
                found.add(value.lower())

        # More tolerant obfuscated pattern like:
        # office @ objetsdartandspirit . com
        flexible = re.compile(
            r"[A-Za-z0-9._%+\-]+\s*@\s*"
            r"[A-Za-z0-9.-]+\s*\.\s*[A-Za-z]{2,}"
        )
        for value in flexible.findall(decoded):
            value = re.sub(r"\s+", "", value)
            if valid_email(value):
                found.add(value.lower())

    except Exception as error:
        logger.debug(f"Email extraction failed: {type(error).__name__}")

    return sorted(found)


def score_email(email: str, website: str = "") -> int:
    email = normalize_text(email).lower()

    if not email or not valid_email(email):
        return 0

    if is_generic_email(email):
        prefix_score = {
            "purchasing": 85,
            "procurement": 84,
            "buyer": 82,
            "buyers": 81,
            "wholesale": 78,
            "sales": 74,
            "business": 70,
            "orders": 68,
            "export": 66,
            "exports": 65,
            "contact": 50,
            "info": 45,
            "office": 40,
            "support": 35,
        }
        local = email_local_part(email)
        score = prefix_score.get(local, 35)
    else:
        score = 80

    domain = email.split("@", 1)[1]

    if domain in FREE_EMAIL_DOMAINS:
        score = min(score, 55)

    website_domain = get_domain(website)
    if website_domain and domain == website_domain:
        score = min(100, score + 10)

    return max(0, min(100, score))


def best_email(emails: Iterable[str], website: str = "") -> str:
    values = {
        normalize_text(email).lower()
        for email in emails
        if valid_email(email)
    }

    if not values:
        return ""

    return max(values, key=lambda x: score_email(x, website))


def extract_phones(text: str) -> List[str]:
    values: List[str] = []

    for match in PHONE_REGEX.findall(text or ""):
        value = normalize_text(match).strip(" ,.;")
        digits = re.sub(r"\D", "", value)

        if 7 <= len(digits) <= 15:
            values.append(value)

    return list(dict.fromkeys(values))


# ============================================================
# WEBSITE HELPERS
# ============================================================

def download(url: str) -> Optional[str]:
    """Download an HTML page with a short retry for transient website failures."""
    try:
        timeout = (3.5, REQUEST_TIMEOUT)
        last_error = None
        for attempt in range(2):
            try:
                response = session.get(
                    url,
                    headers=headers(),
                    timeout=timeout,
                    allow_redirects=True,
                )
                if response.status_code != 200:
                    if attempt == 0 and response.status_code in {429, 500, 502, 503, 504}:
                        continue
                    return None

                content_type = response.headers.get("Content-Type", "").lower()
                if content_type and not any(token in content_type for token in (
                    "text/html", "application/xhtml", "text/plain"
                )):
                    return None

                response.encoding = response.encoding or "utf-8"
                return response.text
            except requests.RequestException as error:
                last_error = error
                if attempt == 0:
                    continue

        if last_error:
            logger.debug(f"Website skipped: {url} | {type(last_error).__name__}")
    except Exception as error:
        logger.info(f"Website skipped: {url} | {type(error).__name__}")
    return None


def discover_contact_pages(website: str, html: str, max_pages: int = MAX_CONTACT_PAGES) -> List[str]:
    """Discover likely contact/team/purchasing pages without assuming URLs exist."""
    website = clean_url(website)
    if not website:
        return []

    domain = get_domain(website)
    candidates: List[str] = []
    seen = set()

    # First use real links from the homepage. These are more reliable than guessing paths.
    try:
        soup = BeautifulSoup(html or "", "html.parser")
        for tag in soup.find_all("a", href=True):
            href = str(tag.get("href", "")).strip()
            if not href or href.lower().startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            absolute = normalize_page_url(urljoin(website, href))
            if not absolute or get_domain(absolute) != domain:
                continue

            text_value = tag.get_text(" ", strip=True).lower()
            path = urlparse(absolute).path.lower()
            blob = f"{text_value} {path}"
            if any(key in blob for key in (
                "team", "staff", "people", "management", "leadership",
                "purchasing", "procurement", "buyer", "buyers",
                "wholesale", "sales", "contact", "about", "get in touch",
            )):
                if absolute not in seen:
                    seen.add(absolute)
                    candidates.append(absolute)
    except Exception:
        pass

    # Probe common paths only after real links. We actually download them later,
    # so nonexistent pages simply fail fast and do not become fake contact pages.
    preferred_paths = [
        "/team", "/our-team", "/staff", "/people", "/management",
        "/leadership", "/purchasing", "/procurement", "/buyers", "/buyer",
        "/wholesale", "/sales", "/contact", "/contact-us", "/contactus",
        "/contact-information", "/get-in-touch", "/about", "/about-us",
        "/pages/contact", "/pages/about", "/pages/wholesale",
    ]
    for path in preferred_paths:
        absolute = normalize_page_url(urljoin(website + "/", path.lstrip("/")))
        if absolute and get_domain(absolute) == domain and absolute not in seen:
            seen.add(absolute)
            candidates.append(absolute)
        if len(candidates) >= max_pages * 3:
            break

    # Give pages a deterministic priority: buyer/team first, then contact/about.
    def priority(url: str) -> Tuple[int, str]:
        path = urlparse(url).path.lower()
        if any(k in path for k in ("purchas", "procurement", "buyer", "wholesale")):
            p = 0
        elif any(k in path for k in ("team", "staff", "people", "management", "leadership")):
            p = 1
        elif any(k in path for k in ("contact", "get-in-touch", "sales")):
            p = 2
        elif "about" in path:
            p = 3
        else:
            p = 4
        return p, path

    candidates.sort(key=priority)
    return candidates[:max_pages]


def email_local_part(email: str) -> str:
    return normalize_text(email).lower().split("@", 1)[0]


def is_generic_email(email: str) -> bool:
    if not email or "@" not in email:
        return True
    local = email_local_part(email)
    compact = re.sub(r"[^a-z0-9]+", "", local)
    generic_compact = {
        re.sub(r"[^a-z0-9]+", "", item)
        for item in GENERIC_EMAIL_PREFIXES
    }
    return local in GENERIC_EMAIL_PREFIXES or compact in generic_compact


def _clean_person_name(value: str) -> str:
    value = normalize_text(value)
    value = re.sub(r"^(mr|mrs|ms|miss|dr|prof)\.?\s+", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" -|,:;")
    if not value or len(value) > 80:
        return ""
    words = value.split()
    if not (2 <= len(words) <= 5):
        return ""
    bad = {
        "contact", "email", "phone", "telephone", "address", "sales",
        "purchasing", "procurement", "buyer", "buyers", "manager",
        "director", "owner", "founder", "company", "team", "about",
        "welcome", "shop", "store", "wholesale", "support", "office",
    }
    if any(w.lower() in bad for w in words):
        return ""
    cleaned = [re.sub(r"[^A-Za-z'’-]", "", w) for w in words]
    if any(len(w) < 2 for w in cleaned):
        return ""
    return " ".join(w[:1].upper() + w[1:] for w in cleaned)


def _role_from_text(text: str) -> str:
    low = normalize_text(text).lower()
    for label, pattern in CONTACT_ROLE_PATTERNS:
        if re.search(pattern, low, re.I):
            return label
    return ""


def _name_from_email_local(email: str) -> str:
    """Infer a display name ONLY for an already-public name-like email."""
    if not email or is_generic_email(email):
        return ""
    local = email_local_part(email)
    if "+" in local or any(ch.isdigit() for ch in local):
        return ""
    parts = [p for p in re.split(r"[._-]+", local) if p]
    if 2 <= len(parts) <= 3 and all(re.fullmatch(r"[a-z]{2,30}", p, re.I) for p in parts):
        return " ".join(p.capitalize() for p in parts)
    return ""


def extract_named_contacts(html: str) -> List[Dict[str, str]]:
    """Extract public person/email pairs; never invent an email address."""
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    contacts: List[Dict[str, str]] = []

    # JSON-LD Person / employee data.
    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue

        def walk(value):
            if isinstance(value, dict):
                yield value
                for child in value.values():
                    yield from walk(child)
            elif isinstance(value, list):
                for child in value:
                    yield from walk(child)

        for item in walk(payload):
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("@type", "")).lower()
            if "person" not in item_type and "employee" not in item_type:
                continue
            email = str(item.get("email", "")).strip().lower()
            if not valid_email(email):
                continue
            name = _clean_person_name(str(item.get("name", "")))
            role = normalize_text(item.get("jobTitle") or item.get("role") or item.get("title") or "")
            if not role:
                role = _role_from_text(role)
            contacts.append({
                "contact_person": name,
                "contact_role": role,
                "email": email,
                "name_source": "structured" if name else "",
            })

    visible = extract_visible_text(html)
    lines = [normalize_text(line) for line in visible.splitlines() if normalize_text(line)]

    # Email + nearby text. Use generous context so cards split over several lines still match.
    role_labels = "|".join(re.escape(label) for label, _ in CONTACT_ROLE_PATTERNS)
    name_pattern = r"[A-Z][A-Za-z'’-]{1,30}(?:\s+[A-Z][A-Za-z'’-]{1,30}){1,4}"
    patterns = [
        re.compile(rf"({name_pattern})\s*(?:[-|,:]|–|—)\s*(?:the\s+)?(?:{role_labels})", re.I),
        re.compile(rf"(?:{role_labels})\s*(?:[-|,:]|–|—)\s*({name_pattern})", re.I),
    ]

    for idx, line in enumerate(lines):
        emails = extract_emails(line)
        if not emails:
            continue
        context_lines = lines[max(0, idx - 3): min(len(lines), idx + 4)]
        context = " | ".join(context_lines)
        role = _role_from_text(context)
        name = ""
        for pattern in patterns:
            match = pattern.search(context)
            if match:
                candidate_name = _clean_person_name(match.group(1))
                if candidate_name:
                    name = candidate_name
                    break
        for email in emails:
            if not name:
                inferred = _name_from_email_local(email)
                if inferred:
                    name = inferred
            contacts.append({
                "contact_person": name,
                "contact_role": role,
                "email": email,
                "name_source": "visible-context" if name else "",
            })

    # mailto links and their surrounding card.
    for tag in soup.find_all("a", href=True):
        href = str(tag.get("href", ""))
        if not href.lower().startswith("mailto:"):
            continue
        email = unquote(href[7:].split("?", 1)[0].strip().lower())
        if not valid_email(email):
            continue
        name = ""
        role = ""
        containers = [tag.parent]
        if tag.parent is not None:
            containers.append(tag.parent.parent)
        for container in containers:
            if not container:
                continue
            card = normalize_text(container.get_text(" ", strip=True))
            role = role or _role_from_text(card)
            for match in re.finditer(name_pattern, card):
                candidate_name = _clean_person_name(match.group(0))
                if candidate_name:
                    name = candidate_name
                    break
            if name:
                break
        if not name:
            name = _name_from_email_local(email)
        contacts.append({
            "contact_person": name,
            "contact_role": role,
            "email": email,
            "name_source": "mailto-context" if name else "",
        })

    # Deduplicate by email + name.
    dedup: Dict[Tuple[str, str], Dict[str, str]] = {}
    for contact in contacts:
        email = normalize_text(contact.get("email", "")).lower()
        if not valid_email(email):
            continue
        key = (email, normalize_text(contact.get("contact_person", "")).lower())
        existing = dedup.get(key)
        if not existing:
            dedup[key] = dict(contact)
        else:
            if not existing.get("contact_role") and contact.get("contact_role"):
                existing["contact_role"] = contact["contact_role"]
            if not existing.get("name_source") and contact.get("name_source"):
                existing["name_source"] = contact["name_source"]

    return list(dedup.values())


def score_contact(contact: Dict[str, str], website: str = "") -> int:
    email = normalize_text(contact.get("email", "")).lower()
    name = normalize_text(contact.get("contact_person", ""))
    role = normalize_text(contact.get("contact_role", "")).lower()
    if not valid_email(email):
        return 0

    score = 0
    if name:
        score += 45

    role_priority = {
        "purchasing manager": 35, "procurement manager": 35,
        "purchasing director": 34, "procurement director": 34,
        "buying manager": 32, "buyer": 30,
        "merchandising manager": 28, "category manager": 28,
        "wholesale manager": 27, "owner": 25, "founder": 24,
        "co-founder": 24, "ceo": 22, "director": 20,
        "general manager": 18,
    }
    for title, points in role_priority.items():
        if title in role:
            score += points
            break

    if not is_generic_email(email):
        score += 30
    else:
        score -= 35

    domain = email.split("@", 1)[1]
    if domain in FREE_EMAIL_DOMAINS:
        score -= 10
    website_domain = get_domain(website)
    if website_domain and domain == website_domain:
        score += 10

    return max(0, min(100, score))


def best_contact(contacts: Iterable[Dict[str, str]], website: str = "") -> Dict[str, str]:
    values = [c for c in contacts if valid_email(c.get("email", ""))]
    if not values:
        return {
            "contact_person": "", "contact_role": "", "email": "",
            "email_type": "Not Found", "contact_score": 0,
        }

    best = max(values, key=lambda c: score_contact(c, website))
    name = normalize_text(best.get("contact_person", ""))
    email = normalize_text(best.get("email", "")).lower()

    if name and not is_generic_email(email):
        email_type = "Named Business Email"
    elif name:
        email_type = "Named Contact / Generic Inbox"
    elif not is_generic_email(email):
        email_type = "Business Email"
    else:
        email_type = "Generic Business Email"

    return {
        "contact_person": name,
        "contact_role": normalize_text(best.get("contact_role", "")),
        "email": email,
        "email_type": email_type,
        "contact_score": score_contact(best, website),
    }



def _api_headers(api_key: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "X-API-Key": api_key,
    }


def hunter_domain_search(website: str) -> Dict[str, Any]:
    """Use Hunter Domain Search to find public professional emails for a company domain."""
    result = {
        "contacts": [],
        "domain": get_domain(website),
        "provider": "Hunter",
        "error": "",
    }
    if not ENABLE_HUNTER or not HUNTER_API_KEY:
        return result
    domain = get_domain(website)
    if not domain or is_blocked_domain(website):
        return result

    try:
        response = session.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": HUNTER_API_KEY},
            headers={"Accept": "application/json"},
            timeout=ENRICHMENT_TIMEOUT,
        )
        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result
        payload = response.json() or {}
        data = payload.get("data") or {}
        for item in data.get("emails") or []:
            email = normalize_text(item.get("value", "")).lower()
            if not valid_email(email):
                continue
            first = normalize_text(item.get("first_name", ""))
            last = normalize_text(item.get("last_name", ""))
            name = _clean_person_name(f"{first} {last}".strip())
            position = normalize_text(item.get("position", ""))
            department = normalize_text(item.get("department", ""))
            confidence = item.get("confidence") or 0
            result["contacts"].append({
                "contact_person": name,
                "contact_role": position or department,
                "email": email,
                "confidence": confidence,
                "name_source": "hunter",
                "provider": "Hunter",
                "email_status": normalize_text(item.get("type", "")),
                "sources": item.get("sources") or [],
            })
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def apollo_people_search(domain: str, roles: List[str], location: str = "") -> List[Dict[str, Any]]:
    """Find likely decision makers at a company. Search returns people; a follow-up enrichment gets contact data."""
    if not ENABLE_APOLLO or not APOLLO_API_KEY or not domain:
        return []
    try:
        payload = {
            "q_organization_domains_list": [domain],
            "person_titles": roles,
            "include_similar_titles": True,
            "per_page": 10,
            "page": 1,
        }
        if location:
            payload["organization_locations"] = [location]
        response = session.post(
            "https://api.apollo.io/api/v1/mixed_people/api_search",
            headers=_api_headers(APOLLO_API_KEY),
            json=payload,
            timeout=ENRICHMENT_TIMEOUT,
        )
        if response.status_code != 200:
            logger.info(f"Apollo search skipped for {domain} | HTTP {response.status_code}")
            return []
        data = response.json() or {}
        return data.get("people") or []
    except Exception as exc:
        logger.info(f"Apollo search failed for {domain} | {type(exc).__name__}")
        return []


def apollo_person_enrich(person: Dict[str, Any], domain: str) -> Optional[Dict[str, str]]:
    """Enrich a single Apollo person and request work email data."""
    if not APOLLO_API_KEY:
        return None
    person_id = normalize_text(person.get("id") or person.get("person_id", ""))
    name = normalize_text(person.get("name", ""))
    if not name:
        name = normalize_text(" ".join(x for x in [person.get("first_name", ""), person.get("last_name", "")] if x))
    if not person_id and not name:
        return None

    payload: Dict[str, Any] = {
        "domain": domain,
        "name": name,
        "run_waterfall_email": False,
        "reveal_personal_emails": False,
    }
    if person_id:
        payload["id"] = person_id
    try:
        response = session.post(
            "https://api.apollo.io/api/v1/people/match",
            headers=_api_headers(APOLLO_API_KEY),
            json=payload,
            timeout=ENRICHMENT_TIMEOUT,
        )
        if response.status_code != 200:
            return None
        data = response.json() or {}
        person_data = data.get("person") or data.get("data") or {}
        email = normalize_text(person_data.get("email", "")).lower()
        if not valid_email(email):
            return None
        status = normalize_text(person_data.get("email_status", ""))
        first = normalize_text(person_data.get("first_name", ""))
        last = normalize_text(person_data.get("last_name", ""))
        full_name = _clean_person_name(person_data.get("name", "") or f"{first} {last}".strip())
        role = normalize_text(person_data.get("title", ""))
        return {
            "contact_person": full_name,
            "contact_role": role,
            "email": email,
            "confidence": 100 if status.lower() == "verified" else 80,
            "name_source": "apollo",
            "provider": "Apollo",
            "email_status": status,
        }
    except Exception:
        return None


def choose_external_contact(website: str, fallback_contacts: List[Dict[str, str]], target_location: str = "", company: str = "", country: str = "USA") -> Dict[str, str]:
    """
    Contact waterfall:
      1. Public website pages
      2. Targeted public Google search for named decision-makers
      3. Optional Hunter/Apollo fallback only when explicitly enabled

    Never invent an email address.
    """
    domain = get_domain(website)
    all_contacts: List[Dict[str, str]] = list(fallback_contacts or [])

    # Best source: the company's own public website.
    best = best_contact(all_contacts, website)
    if best.get("contact_person") and best.get("contact_role") and best.get("email") and not is_generic_email(best["email"]):
        best["provider"] = "Company Website"
        return best

    # Public Google search: look for actual people and roles, not generic inboxes.
    public_contacts = search_public_decision_makers(
        website=website,
        company=company,
        location=target_location,
        country=country,
    )
    all_contacts.extend(public_contacts)

    best = best_contact(all_contacts, website)
    if best.get("contact_person") and best.get("email") and not is_generic_email(best["email"]):
        best["provider"] = "Company Website/Public Web"
        return best

    # If we found a person/role publicly but no public email, keep the decision-maker
    # rather than replacing it with info@ / sales@.
    named_people = [
        c for c in public_contacts + all_contacts
        if normalize_text(c.get("contact_person", ""))
        and normalize_text(c.get("contact_role", ""))
    ]
    if named_people:
        named_people.sort(
            key=lambda c: (
                _contact_role_priority(c.get("contact_role", "")),
                1 if valid_email(c.get("email", "")) and not is_generic_email(c.get("email", "")) else 0,
            ),
            reverse=True,
        )
        person = dict(named_people[0])
        if valid_email(person.get("email", "")) and not is_generic_email(person.get("email", "")):
            chosen = best_contact([person], website)
            chosen["provider"] = "Company Website/Public Web"
            return chosen
        return {
            "contact_person": normalize_text(person.get("contact_person", "")),
            "contact_role": normalize_text(person.get("contact_role", "")),
            "email": "",
            "email_type": "Decision Maker Found - Email Not Public",
            "contact_score": _contact_role_priority(person.get("contact_role", "")),
            "provider": "Public Web",
        }

    # Optional paid enrichment remains available, but it is not required.
    hunter = hunter_domain_search(website)
    all_contacts.extend(hunter.get("contacts") or [])
    best = best_contact(all_contacts, website)
    if best.get("contact_person") and best.get("email") and not is_generic_email(best["email"]):
        best["provider"] = "Company Website/Hunter"
        return best

    if ENABLE_APOLLO and APOLLO_API_KEY and domain:
        roles = [
            "Buyer", "Purchasing Manager", "Procurement Manager",
            "Buying Manager", "Wholesale Manager", "Merchandising Manager",
            "Category Manager", "Owner", "Founder", "CEO", "General Manager",
        ]
        people = apollo_people_search(domain, roles, target_location)
        people = sorted(
            people,
            key=lambda p: (
                _contact_role_priority(p.get("title", "")),
                normalize_text(p.get("title", "")),
            ),
            reverse=True,
        )
        for person in people[:5]:
            enriched = apollo_person_enrich(person, domain)
            if enriched:
                all_contacts.append(enriched)

        best = best_contact(all_contacts, website)
        if best.get("email"):
            best["provider"] = "Company Website/Public Web/Apollo"
            return best

    # Last resort: let existing website-email logic return a business inbox.
    best = best_contact(all_contacts, website)
    best["provider"] = best.get("provider") or "Public Web"
    return best


def enrich_website(website: str, target_location: str = "") -> Dict[str, Any]:
    result = {
        "email": "",
        "contact_person": "",
        "contact_role": "",
        "email_type": "Not Found",
        "contact_score": 0,
        "email_provider": "",
        "phone": "",
        "company": "",
        "pages_checked": 0,
        "emails_found": 0,
    }

    website = clean_url(website)
    if not website or is_blocked_domain(website):
        return result

    home = download(website)
    if not home:
        return result

    html_pages: List[Tuple[str, str]] = [(website, home)]
    result["pages_checked"] = 1
    page_urls = discover_contact_pages(website, home, max_pages=MAX_CONTACT_PAGES)

    # Always inspect discovered pages for email evidence; stop early only after a strong named buyer is found.
    contacts: List[Dict[str, str]] = []
    emails: List[str] = []
    phones: List[str] = []

    def absorb(html: str) -> int:
        nonlocal contacts, emails, phones, result
        emails.extend(extract_emails(html))
        phones.extend(extract_phones(extract_visible_text(html)))
        page_contacts = extract_named_contacts(html)
        contacts.extend(page_contacts)
        strong_now = max((score_contact(c, website) for c in contacts), default=0)
        try:
            soup = BeautifulSoup(html, "html.parser")
            for attrs in ({"property": "og:site_name"}, {"name": "application-name"}):
                tag = soup.find("meta", attrs=attrs)
                if tag:
                    value = normalize_text(tag.get("content", ""))
                    if value and value.lower() not in {"home", "contact", "shop", "store", "welcome"}:
                        result["company"] = value[:120]
                        break
            if not result["company"] and soup.title:
                value = re.split(r"\s+[|•–—:]\s+", normalize_text(soup.title.get_text(" ", strip=True)))[0]
                if value and value.lower() not in {"home", "contact", "shop", "store", "welcome"}:
                    result["company"] = value[:120]
        except Exception:
            pass
        return strong_now

    absorb(home)
    for page_url in page_urls:
        if normalize_page_url(page_url) == normalize_page_url(website):
            continue
        html = download(page_url)
        if not html:
            continue
        html_pages.append((page_url, html))
        result["pages_checked"] += 1
        strong_now = absorb(html)
        if strong_now >= 80:
            break

    # Website first. If it did not expose a named professional contact,
    # run Hunter, then Apollo as a fallback/decision-maker enrichment layer.
    chosen = choose_external_contact(
        website,
        contacts,
        target_location,
        company=result.get("company", "") or company_from_domain(website),
        country=(target_location.split(",")[-1].strip() if target_location else "USA"),
    )
    result["contact_person"] = chosen.get("contact_person", "")
    result["contact_role"] = chosen.get("contact_role", "")
    result["contact_score"] = chosen.get("contact_score", 0)
    result["email_provider"] = chosen.get("provider", "Website")

    if chosen.get("email"):
        result["email"] = chosen["email"]
        result["email_type"] = chosen.get("email_type") or (
            "Named Business Email" if chosen.get("contact_person") and not is_generic_email(chosen["email"])
            else "Generic Business Email" if is_generic_email(chosen["email"])
            else "Business Email"
        )
    else:
        # Do not replace a publicly identified decision-maker with info@/sales@.
        if not result.get("contact_person"):
            generic = best_email(emails, website)
            result["email"] = generic
            result["email_type"] = (
                "Generic Business Email" if generic and is_generic_email(generic)
                else ("Business Email" if generic else "Not Found")
            )
        else:
            result["email"] = ""
            result["email_type"] = result.get("email_type") or "Decision Maker Found - Email Not Public"

    result["phone"] = next(
        (phone for phone in phones if 7 <= len(re.sub(r"\D", "", phone)) <= 15),
        "",
    )
    result["emails_found"] = len(set(emails))
    return result

def company_from_domain(website: str) -> str:
    domain = get_domain(website)

    if not domain:
        return "Unknown Company"

    parts = domain.split(".")
    if len(parts) >= 2:
        label = parts[-2]
    else:
        label = parts[0]

    label = re.sub(r"[-_]+", " ", label).strip()

    return label.title() if label else "Unknown Company"


def clean_company_name(value: str, website: str = "") -> str:
    value = normalize_text(value)

    if not value:
        return company_from_domain(website)

    value = re.sub(
        r"^(home|official site|official website)\s*[-|:]+\s*",
        "",
        value,
        flags=re.I,
    )

    value = re.sub(
        r"\s*(?:\||•|–|—|:)\s*"
        r"(home|official site|official website|contact|about us|shop online).*$",
        "",
        value,
        flags=re.I,
    )

    if value.lower() in {
        "home", "welcome", "contact", "about", "about us",
        "shop", "store",
    }:
        return company_from_domain(website)

    return value[:120].strip() or company_from_domain(website)


def extract_visible_text(html: str) -> str:
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        return "\n".join(
            normalize_text(value)
            for value in soup.stripped_strings
            if normalize_text(value)
        )
    except Exception:
        return ""


# ============================================================
# BUYER SCORING
# ============================================================

def product_match(product: str, text: str) -> int:
    product = normalize_text(product).lower()
    text = normalize_text(text).lower()

    if not product:
        return 0

    if product in text:
        return 30

    words = [
        word
        for word in re.findall(r"[a-z0-9]+", product)
        if len(word) >= 3
    ]

    score = min(20, sum(1 for word in words if word in text) * 8)

    for key, synonyms in PRODUCT_RELATED.items():
        if key in product:
            score += min(
                10,
                sum(2 for synonym in synonyms if synonym in text),
            )

    return min(30, score)


def buyer_type(text: str) -> Tuple[str, int]:
    text = normalize_text(text).lower()

    scores = {
        kind: sum(1 for word in words if word in text)
        for kind, words in BUYER_TYPES.items()
    }

    kind = max(scores, key=scores.get)
    count = scores[kind]

    if count == 0:
        return "Retailer", 4

    return kind, min(20, 8 + count * 3)


def commercial_intent(text: str) -> Tuple[int, List[str]]:
    text = normalize_text(text).lower()

    found = [
        keyword
        for keyword in COMMERCIAL_KEYWORDS
        if keyword in text
    ]

    return min(15, len(found) * 3), found[:5]


def final_score(
    product_score: int,
    buyer_score: int,
    commercial_score: int,
    email_score: int,
    location_score_value: int,
    local_result: bool = True,
) -> int:
    score = (
        min(30, product_score)
        + min(15, buyer_score)
        + min(15, commercial_score)
        + min(10, round(email_score / 10))
        + min(20, round(location_score_value / 5))
    )

    if local_result:
        score += 10

    return max(0, min(100, score))


def why_buyer(
    product_score: int,
    buyer_kind: str,
    commercial_keywords: List[str],
    email: str,
) -> str:
    reasons = []

    if product_score >= 24:
        reasons.append("Strong product match")
    elif product_score >= 15:
        reasons.append("Related product category")

    if buyer_kind in {"Importer", "Wholesaler", "Distributor"}:
        reasons.append(f"{buyer_kind} business")
    elif buyer_kind not in {"Retailer", "Manufacturer", "Online Store"}:
        reasons.append(buyer_kind)

    if commercial_keywords:
        reasons.append("Commercial/wholesale intent")

    if email:
        reasons.append("Business email found")

    return " • ".join(reasons) or "Potential product buyer"


# ============================================================
# SERPAPI GOOGLE MAPS / LOCAL
# ============================================================

def build_local_queries(
    term: str,
    country: str = "",
    state: str = "",
    city: str = "",
    zipcode: str = "",
) -> List[str]:
    """Build diverse Google Maps queries. ZIP stays out of discovery."""
    base = normalize_text(term)
    location = ", ".join(
        x for x in (normalize_text(city), normalize_text(state), normalize_text(country))
        if x
    )

    product_lower = base.lower()
    if "singing bowl" in product_lower or product_lower.strip() == "bowl":
        variants = [
            base,
            "Tibetan singing bowls",
            "sound healing store",
            "meditation store",
            "metaphysical store",
            "spiritual store",
            "wellness store",
            "singing bowl wholesaler",
            "singing bowl importer",
            "singing bowl distributor",
        ]
    elif "candle" in product_lower or "candle holder" in product_lower:
        variants = [
            base,
            "candle holders",
            "home decor store",
            "gift store",
            "candle shop",
            "home fragrance store",
            "candle holder wholesaler",
            "candle holder importer",
            "candle holder distributor",
            "decorative accessories wholesaler",
        ]
    else:
        variants = [
            base,
            f"{base} retailer",
            f"{base} wholesaler",
            f"{base} importer",
            f"{base} distributor",
            f"{base} specialty store",
        ]

    queries = [f"{variant} in {location}" for variant in variants if variant and location]

    # Pick deliberately different search intents so Google Maps does not keep returning
    # the exact same local businesses.
    if "singing bowl" in product_lower or product_lower.strip() == "bowl":
        preferred = [
            base,
            "singing bowl wholesaler",
            "metaphysical store",
        ]
    elif "candle" in product_lower or "candle holder" in product_lower:
        preferred = [
            base,
            "candle holder wholesaler",
            "home decor store",
        ]
    else:
        preferred = [
            base,
            f"{base} wholesaler",
            f"{base} retailer",
        ]

    selected: List[str] = []
    for variant in preferred:
        query = f"{variant} in {location}"
        if query not in selected:
            selected.append(query)
        if len(selected) >= MAX_LOCAL_CALLS:
            break

    if len(selected) < MAX_LOCAL_CALLS:
        for query in queries:
            if query not in selected:
                selected.append(query)
            if len(selected) >= MAX_LOCAL_CALLS:
                break

    return selected[:MAX_LOCAL_CALLS]

def search_serpapi_organic(
    query: str,
    country: str,
    start: int = 0,
) -> List[Dict[str, Any]]:
    """Targeted Google web search used only to locate public decision-maker pages."""
    if not SERP_API_KEY or GoogleSearch is None:
        return []

    config = COUNTRY_CONFIG.get(country, COUNTRY_CONFIG["USA"])
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "start": start,
        "hl": "en",
        "gl": config["gl"],
        "google_domain": config["google_domain"],
        "num": CONTACT_SEARCH_RESULTS,
    }

    try:
        data = GoogleSearch(params).get_dict()
        if data.get("error"):
            logger.info(f"SerpAPI contact search error: {data.get('error')}")
            return []
        return data.get("organic_results", []) or []
    except Exception as error:
        logger.info(f"SerpAPI contact search failed: {type(error).__name__}")
        return []


def _contact_role_priority(role: str) -> int:
    role = normalize_text(role).lower()
    priorities = {
        "purchasing manager": 100,
        "procurement manager": 98,
        "buyer": 96,
        "founder": 92,
        "owner": 90,
        "ceo": 88,
        "co-founder": 87,
        "purchasing director": 86,
        "procurement director": 84,
        "buying manager": 82,
        "wholesale manager": 78,
        "merchandising manager": 74,
        "category manager": 72,
        "director": 65,
        "general manager": 60,
    }
    for key, value in priorities.items():
        if key in role:
            return value
    return 10 if role else 0


def search_public_decision_makers(
    website: str,
    company: str = "",
    location: str = "",
    country: str = "USA",
) -> List[Dict[str, str]]:
    """
    Search public web results for named Owner/Founder/CEO/Buyer/Purchasing/Procurement
    contacts and their publicly exposed business email addresses.

    This function never invents an email address. It only returns an email when
    the address is present in a public page/snippet that we can inspect.
    """
    if not ENABLE_CONTACT_SEARCH or not website or not SERP_API_KEY:
        return []

    domain = get_domain(website)
    if not domain or is_blocked_domain(website):
        return []

    roles_text = '"Owner" OR "Founder" OR "CEO" OR "Buyer" OR "Purchasing Manager" OR "Procurement Manager"'
    query = f'site:{domain} ({roles_text})'
    if company:
        query += f' "{company}"'

    results = search_serpapi_organic(query, country)
    contacts: List[Dict[str, str]] = []
    seen = set()

    for item in results:
        link = normalize_page_url(
            item.get("link") or item.get("url") or item.get("redirect_link") or ""
        )
        title = normalize_text(item.get("title", ""))
        snippet = normalize_text(item.get("snippet", ""))
        combined = " | ".join(x for x in (title, snippet) if x)

        # 1) Search-result title/snippet can expose a named person/role and sometimes an email.
        context = combined
        role = _role_from_text(context)
        name = ""
        name_pattern = r"[A-Z][A-Za-z'’-]{1,30}(?:\s+[A-Z][A-Za-z'’-]{1,30}){1,4}"
        for pattern in (
            re.compile(rf"({name_pattern})\s*(?:[-|,:]|–|—)\s*(?:the\s+)?(?:Owner|Founder|CEO|Buyer|Purchasing Manager|Procurement Manager)", re.I),
            re.compile(rf"(?:Owner|Founder|CEO|Buyer|Purchasing Manager|Procurement Manager)\s*(?:[-|,:]|–|—)\s*({name_pattern})", re.I),
        ):
            match = pattern.search(context)
            if match:
                candidate_name = _clean_person_name(match.group(1))
                if candidate_name:
                    name = candidate_name
                    break

        emails_here = extract_emails(context)
        if emails_here and not name:
            name = _name_from_email_local(emails_here[0])

        if name or role:
            # Pair an email with a person only when the source itself exposes both.
            # Never manufacture an email from a name.
            primary_email = emails_here[0].lower() if emails_here else ""
            key = (name.lower(), primary_email, role.lower())
            if key not in seen:
                seen.add(key)
                contacts.append({
                    "contact_person": name,
                    "contact_role": role,
                    "email": primary_email,
                    "name_source": "google-snippet" if name else "",
                    "provider": "Public Web Search",
                    "source_url": link,
                    "contact_priority": str(_contact_role_priority(role)),
                })

        # 2) Inspect same-domain result pages, which often contain the actual team card.
        if link and get_domain(link) == domain and not is_blocked_domain(link):
            html = download(link)
            if html:
                for found in extract_named_contacts(html):
                    found = dict(found)
                    found["provider"] = "Public Web Search"
                    found["source_url"] = link
                    found["contact_priority"] = str(_contact_role_priority(found.get("contact_role", "")))
                    key = (
                        normalize_text(found.get("contact_person", "")).lower(),
                        normalize_text(found.get("email", "")).lower(),
                        normalize_text(found.get("contact_role", "")).lower(),
                    )
                    if key not in seen:
                        seen.add(key)
                        contacts.append(found)

            # Do not crawl arbitrary pages from search results. One page per result is enough.

    contacts.sort(
        key=lambda c: (
            int(c.get("contact_priority", "0") or 0),
            1 if c.get("contact_person") else 0,
            1 if valid_email(c.get("email", "")) and not is_generic_email(c.get("email", "")) else 0,
        ),
        reverse=True,
    )

    return contacts


def search_serpapi_local(
    query: str,
    country: str,
    start: int = 0,
) -> List[Dict[str, Any]]:
    if not SERP_API_KEY:
        logger.error("SERP_API_KEY is missing.")
        return []

    if GoogleSearch is None:
        logger.error(
            "serpapi package is not installed. "
            "Run: pip install google-search-results"
        )
        return []

    config = COUNTRY_CONFIG.get(
        country,
        COUNTRY_CONFIG["USA"],
    )

    params = {
        "engine": "google_maps",
        "type": "search",
        "q": query,
        "api_key": SERP_API_KEY,
        "start": start,
        "hl": "en",
        "gl": config["gl"],
        "google_domain": config["google_domain"],
        "num": MAX_LOCAL_RESULTS_PER_CALL,
    }

    try:
        data = GoogleSearch(params).get_dict()

        if data.get("error"):
            logger.error(
                f"SerpAPI Local error: {data.get('error')}"
            )
            return []

        return data.get("local_results", []) or []

    except Exception as error:
        logger.error(
            f"SerpAPI Local request failed: "
            f"{type(error).__name__}: {error}"
        )
        return []


def extract_local_website(result: Dict[str, Any]) -> str:
    direct = (
        result.get("website")
        or result.get("link")
        or result.get("official_website")
        or ""
    )

    if isinstance(direct, dict):
        direct = (
            direct.get("link")
            or direct.get("url")
            or direct.get("website")
            or ""
        )

    cleaned = clean_url(direct)
    if cleaned:
        return cleaned

    links = result.get("links")

    if isinstance(links, dict):
        for key in (
            "website",
            "link",
            "official_website",
        ):
            value = links.get(key)

            if isinstance(value, dict):
                value = (
                    value.get("link")
                    or value.get("url")
                    or value.get("website")
                    or ""
                )

            cleaned = clean_url(value)
            if cleaned:
                return cleaned

    if isinstance(links, list):
        for item in links:
            if not isinstance(item, dict):
                continue

            value = (
                item.get("link")
                or item.get("url")
                or item.get("website")
                or ""
            )

            cleaned = clean_url(value)
            if cleaned:
                return cleaned

    return ""


def extract_local_candidate(
    result: Dict[str, Any],
    country: str,
    state: str,
    city: str,
    zipcode: str,
    product: str,
    query_rank: int,
) -> Optional[Dict[str, Any]]:
    title = normalize_text(result.get("title", ""))

    if not title:
        return None

    combined = " ".join(
        [
            title,
            normalize_text(result.get("type", "")),
            normalize_text(result.get("description", "")),
        ]
    ).lower()

    if any(word in combined for word in BLOCKED_TITLE_WORDS):
        return None

    website = extract_local_website(result)

    address = normalize_text(
        result.get("address")
        or result.get("location")
        or ""
    )

    phone = normalize_text(result.get("phone", ""))

    parsed = parse_address(
        address,
        country_hint=country,
        target_city=city,
        target_state=state,
        target_zip=zipcode,
    )

    location_score_value = location_score(
        parsed,
        country,
        state,
        city,
        zipcode,
    )

    text_for_scoring = " ".join(
        [
            title,
            normalize_text(result.get("type", "")),
            normalize_text(result.get("description", "")),
            normalize_text(result.get("snippet", "")),
        ]
    )

    product_score_value = product_match(product, text_for_scoring)
    buyer_kind, buyer_kind_score = buyer_type(text_for_scoring)
    commercial_score, commercial_keywords = commercial_intent(
        text_for_scoring
    )

    # Google Maps rank itself is a useful signal.
    google_position = query_rank

    discovery_score = (
        product_score_value
        + buyer_kind_score
        + commercial_score
        + min(20, max(0, 21 - google_position))
        + min(20, round(location_score_value / 5))
    )

    return {
        "company_guess": clean_company_name(title, website),
        "website": website,
        "title": title,
        "snippet": normalize_text(
            result.get("description")
            or result.get("snippet")
            or ""
        ),
        "source_address": address,
        "source_phone": phone,
        "source_type": normalize_text(
            result.get("type", "")
        ),
        "source": "Google Maps",
        "local_result": True,

        "parsed": parsed,
        "location_score": location_score_value,
        "product_match": product_score_value,
        "buyer_type": buyer_kind,
        "buyer_type_score": buyer_kind_score,
        "commercial_intent": commercial_score,
        "commercial_keywords": commercial_keywords,
        "discovery_score": min(100, discovery_score),
        "google_position": google_position,
    }


def candidate_key(candidate: Dict[str, Any]) -> str:
    website = candidate.get("website", "")
    domain = get_domain(website)

    if domain:
        return f"domain:{domain}"

    company = re.sub(
        r"[^a-z0-9]",
        "",
        normalize_text(candidate.get("company_guess", "")).lower(),
    )

    address = normalize_text(
        candidate.get("source_address", "")
    ).lower()

    return f"name:{company}|address:{address}"


def merge_candidate(
    existing: Dict[str, Any],
    incoming: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Keep the strongest version of duplicate Google results.
    """
    if not existing:
        return incoming

    # Prefer real website.
    if not existing.get("website") and incoming.get("website"):
        existing["website"] = incoming["website"]

    # Prefer a real address.
    if not existing.get("source_address") and incoming.get("source_address"):
        existing["source_address"] = incoming["source_address"]

    # Prefer phone.
    if not existing.get("source_phone") and incoming.get("source_phone"):
        existing["source_phone"] = incoming["source_phone"]

    # Keep the stronger rank / score.
    existing["google_position"] = min(
        existing.get("google_position", 999),
        incoming.get("google_position", 999),
    )

    for field in (
        "location_score",
        "product_match",
        "buyer_type_score",
        "commercial_intent",
        "discovery_score",
    ):
        existing[field] = max(
            existing.get(field, 0),
            incoming.get(field, 0),
        )

    if not existing.get("commercial_keywords") and incoming.get(
        "commercial_keywords"
    ):
        existing["commercial_keywords"] = incoming["commercial_keywords"]

    return existing


def dedupe_candidates(
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}

    for candidate in candidates:
        key = candidate_key(candidate)

        if not key:
            continue

        if key in merged:
            merged[key] = merge_candidate(
                merged[key],
                candidate,
            )
        else:
            merged[key] = candidate

    return list(merged.values())


# ============================================================
# FINAL CANDIDATE PROCESSING
# ============================================================

def build_final_record(
    candidate: Dict[str, Any],
    enrichment: Optional[Dict[str, Any]],
    target_country: str,
    target_state: str,
    target_city: str,
    target_zip: str,
    product: str,
) -> Optional[Dict[str, Any]]:
    parsed = dict(candidate.get("parsed") or {})

    if enrichment:
        email = enrichment.get("email", "")
        contact_person = enrichment.get("contact_person", "")
        contact_role = enrichment.get("contact_role", "")
        email_type = enrichment.get("email_type", "Not Found")
        contact_score = enrichment.get("contact_score", 0)
        phone = enrichment.get("phone", "")
        website_company = enrichment.get("company", "")
    else:
        email = ""
        contact_person = ""
        contact_role = ""
        email_type = "Not Found"
        contact_score = 0
        phone = candidate.get("source_phone", "")
        website_company = ""

    website = candidate.get("website", "")

    # Google Maps title is the strongest company name source.
    company = clean_company_name(
        candidate.get("company_guess", ""),
        website,
    )

    # Only use website name if it is clearly useful and not generic.
    if website_company:
        cleaned = clean_company_name(website_company, website)

        generic = {
            "home", "shop", "store", "welcome", "contact",
            "about", "about us",
        }

        if cleaned and cleaned.lower() not in generic:
            # Keep Google business title when available; use website name
            # only when the Google title is clearly generic.
            if company.lower() in generic or company == "Unknown Company":
                company = cleaned

    if not phone:
        phone = candidate.get("source_phone", "")

    result_city = normalize_text(parsed.get("city", ""))
    result_state = normalize_text(parsed.get("state", ""))
    result_zip = normalize_zip(
        parsed.get("zipcode", ""),
        target_country,
    )
    result_country = (
        normalize_country(parsed.get("country", ""))
        if parsed.get("country")
        else ""
    )

    # Google Maps was queried for the requested geographic area.
    # When country is missing from the address, country can safely be represented
    # as the searched Google market; we do NOT invent city/state/ZIP.
    if not result_country and target_country:
        result_country = target_country

    # Hard filters: country/state/city.
    # ZIP is a ranking preference, NOT a hard filter.
    if target_country and result_country and normalize_country(result_country) != target_country:
        return None

    # When the user explicitly requested state/city, we require those fields to
    # be verified from Google/website data rather than displaying "-".
    if target_state:
        if not result_state:
            return None
        if normalize_region(result_state) != normalize_region(target_state):
            return None

    if target_city:
        if not result_city:
            return None
        if normalize_city(result_city) != normalize_city(target_city):
            return None

    location_score_value = location_score(
        parsed,
        target_country,
        target_state,
        target_city,
        target_zip,
    )

    product_score_value = candidate.get("product_match", 0)
    buyer_kind = candidate.get("buyer_type", "Retailer")
    commercial_score = candidate.get("commercial_intent", 0)
    commercial_keywords = candidate.get(
        "commercial_keywords",
        [],
    )

    email_score_value = score_email(email, website)

    final = final_score(
        product_score_value,
        candidate.get("buyer_type_score", 0),
        commercial_score,
        email_score_value,
        location_score_value,
        local_result=True,
    )

    # ZIP preference bonus / penalty.
    zip_match = bool(
        target_zip
        and result_zip
        and zip_matches(result_zip, target_zip, target_country)
    )

    if zip_match:
        final = min(100, final + 12)

    # Do not reject merely because a valid Los Angeles business uses 90026,
    # 90027, 90041, etc. when the requested ZIP is 90012.
    if target_zip and not result_zip:
        # Missing ZIP is neutral rather than fatal.
        pass

    if final < 10:
        return None

    return {
        "company": company,
        "company_name": company,

        "country": result_country,
        "state": result_state,
        "city": result_city,
        "zipcode": result_zip,
        "zip_code": result_zip,

        "address": candidate.get("source_address", ""),
        "street": normalize_text(parsed.get("street", "")),

        "website": website,
        "contact_person": contact_person,
        "contact_role": contact_role,
        "email": email,
        "email_type": email_type,
        "contact_score": contact_score,
        "email_provider": (enrichment.get("email_provider", "") if enrichment else ""),
        "phone": phone,

        "buyer_type": buyer_kind,
        "buyer_score": final,

        "product_match": product_score_value,
        "email_score": email_score_value,
        "email_quality": (
            "Excellent"
            if email_score_value >= 90
            else "Good"
            if email_score_value >= 70
            else "Business"
            if email_score_value >= 40
            else "Not Found"
        ),

        "commercial_intent": commercial_score,
        "commercial_keywords": commercial_keywords,

        "location_score": location_score_value,
        "zip_match": zip_match,

        "why_buyer": why_buyer(
            product_score_value,
            buyer_kind,
            commercial_keywords,
            email,
        ),

        "rating": candidate.get("rating", ""),
        "reviews": candidate.get("reviews", ""),
        "google_position": candidate.get("google_position", ""),

        "contact_pages_checked": (
            enrichment.get("pages_checked", 0)
            if enrichment
            else 0
        ),
        "emails_found": (
            enrichment.get("emails_found", 0)
            if enrichment
            else 0
        ),

        "country_confidence": (
            100 if result_country == target_country else 0
        ),

        "source": "Google Maps",
    }


def candidate_fast_sort_key(candidate: Dict[str, Any]) -> Tuple:
    return (
        candidate.get("location_score", 0),
        candidate.get("product_match", 0),
        candidate.get("commercial_intent", 0),
        candidate.get("buyer_type_score", 0),
        -candidate.get("google_position", 999),
    )


def final_sort_key(buyer: Dict[str, Any]) -> Tuple:
    return (
        1 if buyer.get("zip_match") else 0,
        1 if buyer.get("contact_person") else 0,
        1 if buyer.get("contact_role") else 0,
        1 if buyer.get("email") else 0,
        1 if buyer.get("city") else 0,
        1 if buyer.get("state") else 0,
        1 if buyer.get("zipcode") else 0,
        1 if buyer.get("website") else 0,
        buyer.get("contact_score", 0),
        buyer.get("buyer_score", 0),
        buyer.get("product_match", 0),
        buyer.get("location_score", 0),
        -int(buyer.get("google_position") or 999),
    )


def _normalized_company_key(name: str) -> str:
    value = normalize_text(name).lower()
    value = re.sub(r"\b(inc|llc|ltd|limited|co|company|corp|corporation)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)


def remove_duplicate_final_records(
    buyers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Remove same-domain and obvious same-company duplicates."""
    seen_domains = set()
    seen_names_locations = set()
    unique: List[Dict[str, Any]] = []

    for buyer in buyers:
        domain = get_domain(buyer.get("website", ""))
        name_key = _normalized_company_key(buyer.get("company_name", ""))
        location_key = (
            normalize_city(buyer.get("city", "")),
            normalize_region(buyer.get("state", "")),
        )

        if domain and domain in seen_domains:
            continue
        if (name_key, location_key) in seen_names_locations:
            continue

        # Obvious duplicate names with small punctuation/wording differences.
        duplicate = False
        if name_key:
            for existing in unique:
                existing_key = _normalized_company_key(existing.get("company_name", ""))
                existing_location = (
                    normalize_city(existing.get("city", "")),
                    normalize_region(existing.get("state", "")),
                )
                if name_key == existing_key and location_key == existing_location:
                    duplicate = True
                    break
        if duplicate:
            continue

        unique.append(buyer)
        if domain:
            seen_domains.add(domain)
        seen_names_locations.add((name_key, location_key))

    return unique


# ============================================================
# PUBLIC SEARCH API
# ============================================================

def search_buyers(
    buyer: str = "",
    product: str = "",
    country: str = "",
    state: str = "",
    city: str = "",
    zipcode: str = "",
    source: str = "google",
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Main function used by Flask.

    Fast pipeline:
      1. Up to 3 Google Maps searches.
      2. Deduplicate.
      3. Rank candidates using Google result data.
      4. Enrich up to 25 website-backed candidates.
      5. Return final results.

    ZIP is ranking preference, not a hard filter.
    """

    term = normalize_text(product or buyer)

    if not term:
        logger.info("Product or buyer is required.")
        return []

    target_country = normalize_country(country)

    if target_country not in COUNTRY_CONFIG:
        target_country = "USA"

    target_state = normalize_text(state)
    target_city = normalize_text(city)
    target_zip = normalize_zip(zipcode, target_country)

    if zipcode and not target_zip:
        logger.error(
            f"Invalid {target_country} ZIP/postcode '{zipcode}'."
        )
        return []

    requested_limit = MAX_RESULTS

    if limit is not None:
        try:
            requested_limit = max(
                1,
                min(int(limit), MAX_RESULTS),
            )
        except (TypeError, ValueError):
            requested_limit = MAX_RESULTS

    logger.info("=" * 80)
    logger.info(
        f"BUYER SEARCH | term='{term}' "
        f"country='{target_country}' "
        f"state='{target_state}' "
        f"city='{target_city}' "
        f"zipcode='{target_zip}' "
        f"source='{source}'"
    )
    logger.info("=" * 80)

    # --------------------------------------------------------
    # 1. Google Maps discovery — MAX 3 CALLS
    # --------------------------------------------------------

    queries = build_local_queries(
        term,
        target_country,
        target_state,
        target_city,
        target_zip,
    )

    raw_candidates: List[Dict[str, Any]] = []
    api_calls = 0

    for query in queries[:MAX_LOCAL_CALLS]:
        if api_calls >= MAX_LOCAL_CALLS:
            break

        api_calls += 1

        results = search_serpapi_local(
            query,
            target_country,
            start=0,
        )

        logger.info(
            f"Google Maps query {api_calls}/{MAX_LOCAL_CALLS}: "
            f"{len(results)} results | {query}"
        )

        for position, item in enumerate(results, start=1):
            candidate = extract_local_candidate(
                item,
                country=target_country,
                state=target_state,
                city=target_city,
                zipcode=target_zip,
                product=term,
                query_rank=position,
            )

            if candidate:
                # Preserve useful Google metadata when supplied.
                candidate["rating"] = item.get("rating", "")
                candidate["reviews"] = (
                    item.get("reviews")
                    or item.get("reviews_count")
                    or ""
                )
                raw_candidates.append(candidate)

    candidates = dedupe_candidates(raw_candidates)

    logger.info(
        f"Unique Google Maps candidates: {len(candidates)}"
    )

    if not candidates:
        logger.info("No Google Maps candidates found.")
        return []

    # --------------------------------------------------------
    # 2. Rank BEFORE website crawling.
    #    This is the major speed improvement.
    # --------------------------------------------------------

    candidates.sort(
        key=candidate_fast_sort_key,
        reverse=True,
    )

    candidates = candidates[:MAX_CANDIDATES]

    # Enrich enough candidates to avoid false "Email Not Found" results.
    # We rank first, then enrich the top website-backed candidates.
    enrichment_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("website")
    ][:MAX_EMAIL_ENRICHMENT]

    logger.info(
        f"Website/email enrichment: "
        f"{len(enrichment_candidates)} candidates"
    )

    # Map domain -> enrichment.
    enrichments: Dict[str, Dict[str, Any]] = {}

    if enrichment_candidates:
        with ThreadPoolExecutor(
            max_workers=min(
                MAX_WORKERS,
                len(enrichment_candidates),
            )
        ) as executor:
            futures = {
                executor.submit(
                    enrich_website,
                    candidate["website"],
                    ", ".join(x for x in (target_city, target_state, target_country) if x),
                ): candidate
                for candidate in enrichment_candidates
            }

            for future in as_completed(futures):
                candidate = futures[future]
                website = candidate.get("website", "")

                try:
                    enrichment = future.result()

                    enrichments[get_domain(website)] = enrichment
                    logger.info(
                        f"ENRICHED: {candidate.get('company_guess', '')} | "
                        f"emails={enrichment.get('emails_found', 0)} | "
                        f"email={enrichment.get('email') or 'NONE'} | "
                        f"type={enrichment.get('email_type', 'Not Found')} | "
                        f"pages={enrichment.get('pages_checked', 0)} | "
                        f"browser={enrichment.get('browser_used', False)}"
                    )

                except Exception as error:
                    logger.info(
                        f"Enrichment failed: "
                        f"{candidate.get('company_guess', '')} | "
                        f"{type(error).__name__}"
                    )

    # --------------------------------------------------------
    # 3. Build final records.
    # --------------------------------------------------------

    buyers: List[Dict[str, Any]] = []

    for candidate in candidates:
        website = candidate.get("website", "")
        enrichment = (
            enrichments.get(get_domain(website), {})
            if website
            else {}
        )

        record = build_final_record(
            candidate=candidate,
            enrichment=enrichment,
            target_country=target_country,
            target_state=target_state,
            target_city=target_city,
            target_zip=target_zip,
            product=term,
        )

        if record:
            buyers.append(record)

    buyers = remove_duplicate_final_records(buyers)
    buyers.sort(key=final_sort_key, reverse=True)

    final = buyers[:requested_limit]

    logger.info(
        f"FINAL BUYERS RETURNED: {len(final)} | "
        f"named contacts={sum(1 for x in final if x.get('contact_person'))} | "
        f"emails={sum(1 for x in final if x.get('email'))}"
    )

    for item in final:
        logger.info(
            f"ACCEPTED: {item.get('company_name', '')} | "
            f"{item.get('state', '')} | "
            f"{item.get('city', '')} | "
            f"{item.get('zip_code', '')} | "
            f"{item.get('contact_person') or 'No Named Contact'} | "
            f"{item.get('contact_role') or 'No Role'} | "
            f"{item.get('email') or 'No Email'} | "
            f"{item.get('email_type') or ''} | "
            f"provider={item.get('email_provider') or ''}"
        )

    return final


# ============================================================
# COMPATIBILITY WRAPPERS
# ============================================================

def search_google_buyers(
    product: str,
    country: str = "",
    state: str = "",
    city: str = "",
    zipcode: str = "",
    source: str = "google",
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    return search_buyers(
        product=product,
        country=country,
        state=state,
        city=city,
        zipcode=zipcode,
        source=source,
        limit=limit,
    )


def search_exporters_india(
    product: str,
    country: str = "",
) -> List[Dict[str, Any]]:
    return search_google_buyers(
        product,
        country,
        source="ExportersIndia",
    )


def search_indiamart(
    product: str,
    country: str = "",
) -> List[Dict[str, Any]]:
    return search_google_buyers(
        product,
        country,
        source="IndiaMART",
    )


def search_tradeindia(
    product: str,
    country: str = "",
) -> List[Dict[str, Any]]:
    return search_google_buyers(
        product,
        country,
        source="TradeIndia",
    )


def search_alibaba(
    product: str,
    country: str = "",
) -> List[Dict[str, Any]]:
    return search_google_buyers(
        product,
        country,
        source="Alibaba",
    )
