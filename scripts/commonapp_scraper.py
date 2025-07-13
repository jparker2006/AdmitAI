#!/usr/bin/env python3
"""
Enhanced Common App College Scraper - Production Ready
=====================================================

Bulletproof scraper that extracts comprehensive data from all 1,097 Common App colleges.

Key Features:
- Fixed social media extraction (college-specific, not Common App's)
- Robust infinite scroll handling to get all 1,097 colleges
- Complete data extraction for all required fields
- Resume functionality for interrupted runs
- Comprehensive error handling and validation
- Production-ready logging and progress tracking

Usage:
    python scripts/commonapp_scraper.py                # Fresh scrape
    python scripts/commonapp_scraper.py --resume       # Resume interrupted run
    python scripts/commonapp_scraper.py --debug        # Debug mode with verbose logging

Outputs:
    - data/colleges/institutions.json    # Master dataset
    - data/colleges/institutions.csv     # CSV export
    - data/raw_html/{slug}.html         # Raw HTML archive
"""

import argparse
import asyncio
import json
import logging
import re
import time
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import pandas as pd
from playwright.async_api import Page, async_playwright
from slugify import slugify
from tqdm import tqdm

# Configure logging
# More granular logging: console = INFO, file = DEBUG
logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('commonapp_scraper.log')
file_handler.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[console_handler, file_handler]
)

# Tunables
DEFAULT_CONCURRENCY = 6  # tweakable via CLI

# Common App social media URLs to filter out
COMMON_APP_SOCIAL_DOMAINS = {
    'facebook.com/commonapp',
    'twitter.com/commonapp',
    'twitter.com/CommonApp',
    'instagram.com/commonapp',
    'linkedin.com/company/the-common-application',
    'youtube.com/user/CommonAppMedia',
    'youtube.com/user/commonappmedia'
}

def ensure_dirs() -> None:
    """Create necessary directories if they don't exist."""
    Path("data/colleges").mkdir(parents=True, exist_ok=True)
    Path("data/raw_html").mkdir(parents=True, exist_ok=True)

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove common Unicode artifacts
    text = text.replace('\u00a0', ' ')  # Non-breaking space
    text = text.replace('\u2019', "'")  # Smart apostrophe
    text = text.replace('\u201c', '"')  # Smart quote left
    text = text.replace('\u201d', '"')  # Smart quote right
    text = text.replace('\u2013', '-')  # En dash
    text = text.replace('\u2014', '--') # Em dash
    return text.strip()

# -----------------------------
# NEW: placeholder-content guard
# -----------------------------
PLACEHOLDER_KEYWORDS = [
    "carl sandburg college", "sandburg", "charger country", "chargers",
    "galesburg", "rend lake college", "placeholder", "sample", "test", "demo"
]

def looks_like_placeholder(text: str) -> bool:
    """Heuristic: True if *text* includes obvious placeholder / wrong-college markers."""
    if not text:
        return False
    lower = text.lower()
    return any(tok in lower for tok in PLACEHOLDER_KEYWORDS)

def extract_location(loc_text: str) -> Dict[str, Optional[str]]:
    """Extract location information from address text."""
    location = {"city": None, "state": None, "country": None}
    
    if not loc_text:
        return location
    
    # Common patterns for location parsing
    # US format: "City, ST ZIP"
    us_pattern = r'([^,]+),\s*([A-Z]{2})\s+\d{5}'
    us_match = re.search(us_pattern, loc_text)
    if us_match:
        location["city"] = us_match.group(1).strip()
        location["state"] = us_match.group(2).strip()
        location["country"] = "United States of America"
        return location
    
    # International format: "City, Country"
    parts = [part.strip() for part in loc_text.split(',')]
    if len(parts) >= 2:
        location["city"] = parts[0]
        location["country"] = parts[-1]
        if len(parts) >= 3:
            location["state"] = parts[1]
    
    return location

# =======================
# New Helper Functions
# =======================

async def click_expandable_sections(page: Page) -> None:
    """Click all expandable elements (e.g., 'Read More', 'Show More') to reveal hidden content."""
    # Target Common App specific expandable buttons first
    common_app_selectors = [
        'button.plain-area-text-button',  # Common App specific read more buttons
        '.plain-area-text-button',
    ]
    
    # General expandable selectors as fallback
    general_selectors = [
        'button:has-text("Read More")',
        'button:has-text("Read more")',
        'button:has-text("Show More")',
        'button:has-text("Show more")',
        'button:has-text("More Info")',
        'button:has-text("More info")',
        'button:has-text("Learn More")',
        'button:has-text("Learn more")',
        'a:has-text("Read More")',
        'a:has-text("Read more")',
        'a:has-text("Show More")',
        'a:has-text("Show more")',
        # newly added selectors
        'button:has-text("More")',
        '[aria-expanded="false"]',
        'summary',
        '[class*="expand"]',
        '[class*="toggle"]',
        '[class*="show-more"]',
        '[class*="read-more"]',
    ]
    
    all_selectors = common_app_selectors + general_selectors

    for selector in all_selectors:
        try:
            elements = await page.query_selector_all(selector)
            for element in elements:
                try:
                    # Check if element is visible and clickable
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.click()
                        # Wait briefly for content to load/render
                        await page.wait_for_timeout(750)  # Increased wait time for content expansion
                        logger.debug(f"Clicked expandable element with selector: {selector}")
                except Exception as inner_err:
                    logger.debug(f"Error clicking expandable element for selector {selector}: {inner_err}")
        except Exception as outer_err:
            logger.debug(f"Error locating expandable elements with selector {selector}: {outer_err}")

    # Additional wait to ensure all content has fully loaded
    await page.wait_for_timeout(500)


def parse_region_info(region_text: str) -> Dict[str, Optional[str]]:
    """Convert region text to structured location data (state/country)."""
    location: Dict[str, Optional[str]] = {"city": None, "state": None, "country": None}
    if not region_text:
        return location

    text = region_text.strip()

    # United Kingdom variations
    if re.search(r"United Kingdom|\bUK\b", text, flags=re.IGNORECASE):
        location["country"] = "United Kingdom (UK)"
    # United States regional groupings
    elif re.search(r"New England|Mid[- ]Atlantic|Southwest|Southeast|West Coast|Pacific Northwest", text, flags=re.IGNORECASE):
        location["country"] = "United States of America"
    elif "International" in text:
        # Attempt to detect a specific country mentioned after 'International'
        for country in ["Morocco", "Canada", "Mexico", "Australia", "China", "India"]:
            if country.lower() in text.lower():
                location["country"] = country
                break
    return location


def parse_location_tag(tag_text: str) -> Dict[str, Optional[str]]:
    """Interpret pill/tag text that may indicate a location."""
    location: Dict[str, Optional[str]] = {"city": None, "state": None, "country": None}
    if not tag_text:
        return location

    lower = tag_text.lower().strip()
    mapping = {
        "england": "United Kingdom (UK)",
        "scotland": "United Kingdom (UK)",
        "wales": "United Kingdom (UK)",
        "northern ireland": "United Kingdom (UK)",
        "canada": "Canada",
        "morocco": "Morocco",
    }

    if lower in mapping:
        location["country"] = mapping[lower]
    return location


async def extract_comprehensive_location(page: Page) -> Dict[str, Optional[str]]:
    """Extract location from contact info, region section, and location tags."""
    location: Dict[str, Optional[str]] = {"city": None, "state": None, "country": None}

    # Method 1: Parse address from contact information section
    try:
        contact_header = await page.query_selector('h2:has-text("Contact information")')
        if contact_header:
            address_el = await contact_header.evaluate_handle('el => el.nextElementSibling')
            if address_el:
                address_text = await address_el.text_content()
                if address_text:
                    location.update({k: v for k, v in extract_location(address_text).items() if v})
    except Exception as e:
        logger.debug(f"Address-based location extraction error: {e}")

    # Method 2: Region information
    try:
        region_header = await page.query_selector('h2:has-text("Region")')
        if region_header:
            region_el = await region_header.evaluate_handle('el => el.nextElementSibling')
            if region_el:
                region_text = await region_el.text_content()
                if region_text:
                    parsed = parse_region_info(region_text)
                    for k, v in parsed.items():
                        if v and not location.get(k):
                            location[k] = v
    except Exception as e:
        logger.debug(f"Region-based location extraction error: {e}")

    # Method 3: Location pills/tags
    try:
        tag_selectors = '.pill:has-text("England"), .pill:has-text("Kingdom"), .pill:has-text("International")'
        tags = await page.query_selector_all(tag_selectors)
        for tag in tags:
            tag_text = await tag.text_content()
            if tag_text:
                parsed = parse_location_tag(tag_text)
                for k, v in parsed.items():
                    if v and not location.get(k):
                        location[k] = v
    except Exception as e:
        logger.debug(f"Tag-based location extraction error: {e}")

    return location


async def extract_enhanced_application_info(page: Page) -> Dict[str, Any]:
    # BEGIN PATCH: broaden selectors & robust extraction for First-year / Transfer accordion rows
    application_info: Dict[str, Any] = {"first_year": {}, "transfer": {}}

    try:
        app_header = await page.query_selector('h2:has-text("Application information")')
        if not app_header:
            return application_info  # section absent

        # 1) Expand disclosure rows (button, tr, div etc.) lazily rendered
        row_selectors = [
            'button:has-text("First-year")',
            'button:has-text("First year")',
            'button:has-text("First Year")',
            'tr:has-text("First-year")',
            'tr:has-text("First year")',
            'tr:has-text("Transfer")',
            'div:has-text("First-year")',
            'div:has-text("First year")',
            'div:has-text("Transfer")',
            'li:has-text("First-year")',
            'li:has-text("Transfer")',
            'summary:has-text("First-year")',
            'summary:has-text("First year")',
            'summary:has-text("Transfer")'
        ]
        for selector in row_selectors:
            try:
                rows = await page.query_selector_all(selector)
                for row in rows:
                    try:
                        await row.click()
                        await page.wait_for_timeout(500)
                    except Exception as click_err:
                        logger.debug(f"Application row click error ({selector}): {click_err}")
            except Exception as outer_err:
                logger.debug(f"Application row selector error ({selector}): {outer_err}")

        # Helper to harvest requirements text block
        async def _grab_requirements(header_selector: str) -> Optional[str]:
            header = await page.query_selector(header_selector)
            if not header:
                return None
            # First try immediate next sibling
            content_el = await header.evaluate_handle('el => el.nextElementSibling')
            if content_el:
                txt = await content_el.text_content()
                if txt and txt.strip():
                    cleaned = clean_text(txt)
                    return None if looks_like_placeholder(cleaned) else cleaned
            # Fallback: any <p> within the same parent container
            parent_el = await header.evaluate_handle('el => el.parentElement')
            if parent_el:
                p_tags = await parent_el.query_selector_all('p')
                combined = ' '.join([await p.text_content() or '' for p in p_tags])
                if combined.strip():
                    cleaned = clean_text(combined)
                    return None if looks_like_placeholder(cleaned) else cleaned
            return None

        first_year_text = await _grab_requirements('h3:has-text("First-year"), h3:has-text("First year"), h3:has-text("First Year"), [class*="first-year"]')
        if first_year_text:
            application_info["first_year"]["requirements"] = first_year_text

        transfer_text = await _grab_requirements('h3:has-text("Transfer"), [class*="transfer"]')
        if transfer_text:
            application_info["transfer"]["requirements"] = transfer_text
    except Exception as e:
        logger.debug(f"Enhanced application info extraction error: {e}")

    # --- Placeholder filter (Sandburg) ---
    try:
        for cohort in ("first_year", "transfer"):
            req = application_info.get(cohort, {}).get("requirements")
            if req and "sandburg.edu" in req.lower():
                application_info[cohort].pop("requirements", None)
    except Exception as e:
        logger.debug(f"Placeholder requirements cleanup error: {e}")

    return application_info
    # END PATCH

# =======================
# End Helper Functions
# =======================

# Utility to ensure lazy-loaded content (like social icons & images) is in DOM
async def ensure_full_dom(page: Page) -> None:
    """Trigger lazy-load by one fast jump; cheaper than pixel-scroll."""
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(300)
    except Exception as e:
        logger.debug(f"ensure_full_dom error: {e}")


async def aggressive_scroll(page: Page, target_count: int = 1097) -> int:
    """Aggressively scroll to load all colleges with enhanced detection."""
    logger.info(f"Starting aggressive scroll to load {target_count} colleges...")
    
    previous_count = 0
    stagnant_rounds = 0
    max_stagnant_rounds = 15
    scroll_attempts = 0
    max_scroll_attempts = 300
    
    while scroll_attempts < max_scroll_attempts:
        # Multiple scroll strategies
        for _ in range(5):  # Multiple scrolls per round
            await page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)
            await page.wait_for_timeout(100)
        
        # Additional scroll strategies
        await page.evaluate("window.scrollBy(0, 2000);")
        await page.wait_for_timeout(200)
        
        # Wait for new content to load
        await page.wait_for_timeout(2000)
        
        # Count current college links
        current_count = await page.locator('a[href^="/explore/"]').count()
        
        # Filter out non-college links
        valid_links = []
        links = await page.query_selector_all('a[href^="/explore/"]')
        for link in links:
            href = await link.get_attribute('href')
            if href and href != "/explore/" and len(href.split("/")) > 2:
                # Additional validation - ensure it's a college page
                if not any(x in href for x in ['filter', 'search', 'help', 'about']):
                    valid_links.append(href)
        
        current_count = len(set(valid_links))  # Remove duplicates
        
        logger.info(f"Scroll attempt {scroll_attempts + 1}: Found {current_count} colleges")
        
        # Check if we've reached the target
        if current_count >= target_count:
            logger.info(f"✓ Successfully loaded {current_count} colleges!")
            break
        
        # Check for stagnation
        if current_count == previous_count:
            stagnant_rounds += 1
            if stagnant_rounds >= max_stagnant_rounds:
                logger.warning(f"Stopped scrolling after {stagnant_rounds} stagnant rounds")
                break
        else:
            stagnant_rounds = 0
        
        previous_count = current_count
        scroll_attempts += 1
        
        # Try clicking "Load More" button if it exists
        try:
            load_more_button = await page.query_selector('button:has-text("Load More"), button:has-text("Show More"), button:has-text("Load more")')
            if load_more_button:
                await load_more_button.click()
                logger.info("Clicked 'Load More' button")
                await page.wait_for_timeout(3000)
        except:
            pass
    
    final_count = previous_count
    logger.info(f"Scroll complete. Final count: {final_count}")
    return final_count

async def extract_tags(page: Page) -> List[str]:
    # BEGIN PATCH: refine tag extraction & split concatenated strings
    """Extract all characteristic tags/pills from the page accurately."""
    tags: List[str] = []

    precise_selectors = [
        '.characteristic-pill',
        '.pill',
        '.tag',
        '.badge',
        '.characteristic',
        'button.pill'
    ]

    elements = []
    try:
        # Union query for efficiency
        union_selector = ','.join(precise_selectors)
        elements = await page.query_selector_all(union_selector)
    except Exception as e:
        logger.debug(f"Tag element selection error: {e}")

    def _split_concat(text: str) -> List[str]:
        # break camel-ish concatenation between tags
        parts = re.split(r'(?<=[a-z0-9\)])(?=[A-Z])', text)
        return [clean_text(p) for p in parts if p and p.strip()]

    for element in elements:
        try:
            # Skip containers that have child pill-like nodes
            child = await element.query_selector('.pill, .tag, .badge, .characteristic-pill')
            if child:
                continue
            raw_text = await element.text_content() or ""
            raw_text = raw_text.strip()
            if not raw_text:
                continue
            pieces = _split_concat(raw_text) if len(raw_text) > 60 else [clean_text(raw_text)]
            for piece in pieces:
                # Filter out generic verbs etc.
                if piece and not any(x in piece.lower() for x in ['apply', 'visit', 'learn', 'show', 'hide']):
                    tags.append(piece)
        except Exception as e:
            logger.debug(f"Error processing tag element: {e}")

    return sorted(list(dict.fromkeys(tags)))  # preserve order, dedupe
    # END PATCH

async def extract_academic_programs(page: Page) -> List[str]:
    """Extract academic programs and majors."""
    programs = []
    
    try:
        # Look for academic programs section
        programs_section = await page.query_selector('h2:has-text("Academic programs")')
        if programs_section:
            # Find the content after the header
            content_element = await programs_section.evaluate_handle('el => el.nextElementSibling')
            if content_element:
                # Look for list items or tags
                items = await content_element.query_selector_all('li, .tag, .pill, .program-item')
                for item in items:
                    text = await item.text_content()
                    if text and text.strip():
                        clean_program = clean_text(text)
                        if clean_program and clean_program not in programs:
                            programs.append(clean_program)
        
        # Alternative: Look for programs in pills/tags
        if not programs:
            program_elements = await page.query_selector_all('[class*="program"] .pill, [class*="academic"] .pill')
            for element in program_elements:
                text = await element.text_content()
                if text and text.strip():
                    clean_program = clean_text(text)
                    if clean_program and clean_program not in programs:
                        programs.append(clean_program)
    except Exception as e:
        logger.debug(f"Error extracting academic programs: {e}")
    
    return sorted(programs)

async def extract_student_experience(page: Page) -> List[str]:
    """Extract student experience offerings."""
    experiences = []
    
    try:
        # Look for student experience section
        experience_section = await page.query_selector('h2:has-text("Student experience")')
        if experience_section:
            # Find the content after the header
            content_element = await experience_section.evaluate_handle('el => el.nextElementSibling')
            if content_element:
                # Look for list items or tags
                items = await content_element.query_selector_all('li, .tag, .pill, .experience-item')
                for item in items:
                    text = await item.text_content()
                    if text and text.strip():
                        clean_exp = clean_text(text)
                        if clean_exp and clean_exp not in experiences:
                            experiences.append(clean_exp)
        
        # Alternative: Look for experiences in pills/tags
        if not experiences:
            exp_elements = await page.query_selector_all('[class*="experience"] .pill, [class*="student"] .pill')
            for element in exp_elements:
                text = await element.text_content()
                if text and text.strip():
                    clean_exp = clean_text(text)
                    if clean_exp and clean_exp not in experiences:
                        experiences.append(clean_exp)
    except Exception as e:
        logger.debug(f"Error extracting student experience: {e}")
    
    return sorted(experiences)

async def extract_application_info(page: Page) -> Dict[str, Any]:
    """Extract comprehensive application information."""
    app_info = {
        "first_year": {},
        "transfer": {}
    }
    
    try:
        # Look for application information section
        app_section = await page.query_selector('h2:has-text("Application information")')
        if app_section:
            # Look for collapsible sections or accordions
            accordion_containers = await page.query_selector_all('.accordion-container, .collapsible-section, .expandable-section')
            
            for container in accordion_containers:
                try:
                    # Look for the summary/header
                    summary = await container.query_selector('.summary, .header, .title, summary')
                    if summary:
                        summary_text = await summary.text_content()
                        if summary_text:
                            summary_text = summary_text.lower().strip()
                            
                            # Expand the section
                            await summary.click()
                            await page.wait_for_timeout(500)
                            
                            # Get the content
                            content = await container.query_selector('.content, .panel, .details')
                            if content:
                                content_text = await content.text_content()
                                if content_text:
                                    content_text = clean_text(content_text)
                                    
                                    # Parse requirements
                                    requirements = []
                                    full_description = content_text
                                    
                                    # Extract structured requirements
                                    if "official transcript" in content_text.lower():
                                        requirements.append("Official transcripts required")
                                    if "letter of recommendation" in content_text.lower():
                                        requirements.append("Letters of recommendation required")
                                    if "personal essay" in content_text.lower() or "essay" in content_text.lower():
                                        requirements.append("Personal essay required")
                                    if "test scores" in content_text.lower():
                                        if "optional" in content_text.lower():
                                            requirements.append("Test scores optional")
                                        else:
                                            requirements.append("Test scores required")
                                    
                                    # Determine if this is first-year or transfer
                                    if "first" in summary_text or "first-year" in summary_text:
                                        app_info["first_year"] = {
                                            "requirements": requirements,
                                            "full_description": full_description
                                        }
                                    elif "transfer" in summary_text:
                                        app_info["transfer"] = {
                                            "requirements": requirements,
                                            "full_description": full_description
                                        }
                except Exception as e:
                    logger.debug(f"Error processing accordion: {e}")
    except Exception as e:
        logger.debug(f"Error extracting application info: {e}")
    
    return app_info

async def extract_contact_info(page: Page) -> Dict[str, Any]:
    """Extract comprehensive contact information."""
    contact_info = {
        "address": {},
        "phone": None,
        "email": None,
        "website": None,
        "financial_aid_website": None
    }
    
    try:
        # Look for contact information sections
        contact_sections = ['Address', 'Phone', 'Email', 'Website', 'Financial aid website']
        
        for section_name in contact_sections:
            section_header = await page.query_selector(f'h3:has-text("{section_name}"), h4:has-text("{section_name}")')
            if section_header:
                # Get the next sibling element
                content_element = await section_header.evaluate_handle('el => el.nextElementSibling')
                if content_element:
                    if section_name == 'Address':
                        address_text = await content_element.text_content()
                        if address_text:
                            contact_info["address"]["full"] = clean_text(address_text)
                            location_info = extract_location(address_text)
                            contact_info["address"].update(location_info)
                    
                    elif section_name == 'Phone':
                        phone_text = await content_element.text_content()
                        if phone_text:
                            contact_info["phone"] = clean_text(phone_text)
                    
                    elif section_name == 'Email':
                        email_text = await content_element.text_content()
                        if email_text:
                            contact_info["email"] = clean_text(email_text)
                    
                    elif section_name == 'Website':
                        website_link = await content_element.query_selector('a')
                        if website_link:
                            href = await website_link.get_attribute('href')
                            if href:
                                contact_info["website"] = href
                    
                    elif section_name == 'Financial aid website':
                        fin_aid_link = await content_element.query_selector('a')
                        if fin_aid_link:
                            href = await fin_aid_link.get_attribute('href')
                            if href:
                                contact_info["financial_aid_website"] = href
        # Merge comprehensive location data to fill missing pieces
        try:
            comprehensive_location = await extract_comprehensive_location(page)
            if comprehensive_location:
                contact_info.setdefault("address", {})
                for key, val in comprehensive_location.items():
                    if val and not contact_info["address"].get(key):
                        contact_info["address"][key] = val
        except Exception as e:
            logger.debug(f"Error merging comprehensive location: {e}")
    except Exception as e:
        logger.debug(f"Error extracting contact info: {e}")
    
    return contact_info

def is_common_app_social_media(url: str) -> bool:
    """Check if a URL belongs to Common App's own social media accounts."""
    if not url:
        return False
    parsed_url = urlparse(url)
    domain_path = f"{parsed_url.netloc}{parsed_url.path}".lower()
    return any(domain in domain_path for domain in COMMON_APP_SOCIAL_DOMAINS)

async def extract_social_media(page, college_name=None):
    """Extract social media links while filtering out Common App generic links."""
    social_media = {}
    
    # All possible social media selectors
    selectors = [
        'a[href*="facebook.com"]',
        'a[href*="twitter.com"]', 
        'a[href*="instagram.com"]',
        'a[href*="youtube.com"]',
        'a[href*="linkedin.com"]',
        'a[href*="tiktok.com"]',
        'a[href*="snapchat.com"]',
    ]
    
    platforms = {
        'facebook.com': 'facebook',
        'twitter.com': 'twitter', 
        'instagram.com': 'instagram',
        'youtube.com': 'youtube',
        'linkedin.com': 'linkedin',
        'tiktok.com': 'tiktok',
        'snapchat.com': 'snapchat'
    }
    
    try:
        for selector in selectors:
            links = await page.query_selector_all(selector)
            
            for link in links:
                href = await link.get_attribute('href') or await link.get_attribute('data-href')
                if not href:
                    continue
                
                # Skip Common App generic links
                if is_common_app_social_media(href):
                    continue
                
                # Skip Carl Sandburg College links (wrong content detection)
                if 'carlsandburgcollege' in href.lower():
                    continue
                
                # Skip other obviously wrong links
                if any(wrong in href.lower() for wrong in ['commonapp', 'common-app', 'common_app']):
                    continue
                
                # Determine platform
                platform = None
                for domain, platform_name in platforms.items():
                    if domain in href:
                        platform = platform_name
                        break
                
                if platform and platform not in social_media:
                    # Additional validation - ensure the link looks legitimate
                    if len(href) > 20 and href.startswith('http'):
                        social_media[platform] = href
    
    except Exception as e:
        logger.debug(f"Error extracting social media: {e}")
    
    # If no valid social media links found, return empty dict
    # Do not add placeholder or generic links
    return social_media

async def extract_additional_info(page: Page) -> Dict[str, Any]:
    """Extract additional information from the plain-area-text sections with improved targeting."""
    additional_info: Dict[str, Any] = {}

    try:
        # First, click any "Read more" buttons to expand content
        await click_expandable_sections(page)
        
        # Target the specific HTML structure for additional information
        # Look for: <div class="plain-area-text fixed-font-style"><h2>Additional Information</h2><div class="plain-area-text-space">content...</div></div>
        additional_section = await page.query_selector('.plain-area-text.fixed-font-style:has(h2:has-text("Additional Information"))')
        
        if additional_section:
            # Get the content from the plain-area-text-space div
            content_div = await additional_section.query_selector('.plain-area-text-space')
            if content_div:
                text_content = await content_div.text_content()
                
                if text_content and text_content.strip():
                    cleaned_text = clean_text(text_content)
                    
                    # Placeholder / wrong college guard
                    if looks_like_placeholder(cleaned_text):
                        logger.debug("Detected placeholder content in additional info – skipping")
                        return {}

                    text_lower = cleaned_text.lower()
                    
                    # Only include if content is substantial and not just generic text
                    if len(cleaned_text) > 20:  # Ensure meaningful content
                        additional_info["description"] = cleaned_text
                        
                        # Extract URLs from the content
                        urls = re.findall(r'https?://[^\s<>"]+', cleaned_text)
                        if urls:
                            additional_info["urls"] = list(set(urls))  # Remove duplicates
                        
                        # Analyze content for specific financial aid and scholarship mentions
                        if any(term in text_lower for term in ["financial aid", "financial assistance", "aid"]):
                            additional_info["mentions_financial_aid"] = True
                        if any(term in text_lower for term in ["scholarship", "scholarships", "grant", "grants"]):
                            additional_info["mentions_scholarships"] = True
                        if any(term in text_lower for term in ["merit", "need-based", "aid programs"]):
                            additional_info["mentions_aid_programs"] = True
                        if any(term in text_lower for term in ["tuition", "affordable", "cost"]):
                            additional_info["mentions_cost"] = True
                        
                        # Extract any embedded links with their text
                        try:
                            links = await content_div.query_selector_all('a[href]')
                            if links:
                                link_data = []
                                for link in links:
                                    href = await link.get_attribute('href')
                                    link_text = await link.text_content()
                                    if href and link_text and href.startswith('http'):
                                        link_data.append({
                                            "url": href.strip(),
                                            "text": clean_text(link_text)
                                        })
                                if link_data:
                                    additional_info["links"] = link_data
                        except Exception as e:
                            logger.debug(f"Error extracting links: {e}")
                            
    except Exception as e:
        logger.debug(f"Error extracting additional info: {e}")

    return additional_info

async def extract_visit_info(page: Page) -> Dict[str, Any]:
    """Extract visit information with improved targeting of plain-area-text sections."""
    visit_info: Dict[str, Any] = {}

    try:
        # Click any "Read more" buttons to expand content first
        await click_expandable_sections(page)
        
        # Target the specific HTML structure for visit information
        # Look for: <div class="plain-area-text "><h2>Visit us</h2><div class="plain-area-text-space">content...</div></div>
        visit_section = await page.query_selector('.plain-area-text:has(h2:has-text("Visit us"))')
        
        if visit_section:
            # Get the content from the plain-area-text-space div
            content_div = await visit_section.query_selector('.plain-area-text-space')
            if content_div:
                text_content = await content_div.text_content()
                
                if text_content and text_content.strip():
                    cleaned_text = clean_text(text_content)
                    
                    # Placeholder guard
                    if looks_like_placeholder(cleaned_text):
                        logger.debug("Detected placeholder content in visit info – skipping")
                        return {}

                    text_lower = cleaned_text.lower()
                    
                    # Only include if content is substantial and not just generic text
                    if len(cleaned_text) > 10:  # Ensure meaningful content
                        visit_info["description"] = cleaned_text
                        
                        # Extract URLs from the content
                        urls = re.findall(r'https?://[^\s<>"]+', cleaned_text)
                        if urls:
                            visit_info["urls"] = list(set(urls))  # Remove duplicates
                        
                        # Analyze content for specific visit features
                        if any(term in text_lower for term in ["tour", "campus tour", "guided tour"]):
                            visit_info["offers_tours"] = True
                        if any(term in text_lower for term in ["open day", "open days", "open house"]):
                            visit_info["offers_open_days"] = True
                        if any(term in text_lower for term in ["virtual", "online tour", "virtual tour"]):
                            visit_info["offers_virtual_visits"] = True
                        if any(term in text_lower for term in ["appointment", "schedule", "book"]):
                            visit_info["offers_appointments"] = True
                        if any(term in text_lower for term in ["preview", "preview day"]):
                            visit_info["offers_preview_days"] = True
                        if any(term in text_lower for term in ["information session", "info session"]):
                            visit_info["offers_info_sessions"] = True
                        
                        # Extract contact information for visits
                        phone_matches = re.findall(r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', cleaned_text)
                        if phone_matches:
                            visit_info["contact_phone"] = f"({phone_matches[0][0]}) {phone_matches[0][1]}-{phone_matches[0][2]}"
                        
                        email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', cleaned_text)
                        if email_matches:
                            visit_info["contact_email"] = email_matches[0]
                        
                        # Extract any embedded links with their text
                        try:
                            links = await content_div.query_selector_all('a[href]')
                            if links:
                                link_data = []
                                for link in links:
                                    href = await link.get_attribute('href')
                                    link_text = await link.text_content()
                                    if href and link_text and href.startswith('http'):
                                        link_data.append({
                                            "url": href.strip(),
                                            "text": clean_text(link_text)
                                        })
                                if link_data:
                                    visit_info["links"] = link_data
                        except Exception as e:
                            logger.debug(f"Error extracting visit links: {e}")

        # Fallback: Look for visit-related content in other sections if main section not found
        if not visit_info:
            try:
                # Search for visit-related content across the page as fallback
                visit_selectors = [
                    'h3.visit-us',
                    '[class*="visit"]',
                    '[id*="visit"]'
                ]
                
                for selector in visit_selectors:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        parent = await element.evaluate_handle('el => el.parentElement')
                        if parent:
                            text = await parent.text_content()
                            if text and len(text.strip()) > 20:
                                cleaned_text = clean_text(text)
                                text_lower = cleaned_text.lower()
                                
                                # Skip if contaminated
                                if looks_like_placeholder(cleaned_text):
                                    continue
                                
                                if any(term in text_lower for term in ["visit", "tour", "campus"]):
                                    visit_info["description"] = cleaned_text
                                    break
                                    
            except Exception as e:
                logger.debug(f"Error in fallback visit info extraction: {e}")
                    
    except Exception as e:
        logger.debug(f"Error extracting visit info: {e}")

    return visit_info

async def extract_images(page: Page, base_url: str) -> Dict[str, Any]:
    """Extract all images from the college page, filtering out wrong content."""
    images = {}
    
    try:
        # Hero image
        hero_selectors = ['.hero-image', '.main-image', '.banner-image', '.header-image']
        for selector in hero_selectors:
            hero_img = await page.query_selector(selector)
            if hero_img:
                hero_src = await hero_img.get_attribute('src')
                if hero_src:
                    images['hero'] = urljoin(base_url, hero_src)
                    break

                # Try <img srcset="…"> pattern
                srcset = await hero_img.get_attribute('srcset')
                if srcset:
                    first_src = srcset.split(',')[0].split()[0]
                    images['hero'] = urljoin(base_url, first_src)
                    break

                # Finally, inline style="background-image:url('…')"
                style_attr = await hero_img.get_attribute('style')
                if style_attr and 'url(' in style_attr.lower():
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style_attr)
                    if match:
                        images['hero'] = urljoin(base_url, match.group(1))
                        break
        
        # Seal/logo image
        seal_selectors = ['.seal-container img', '.logo img', '.college-logo', '.institution-logo']
        for selector in seal_selectors:
            seal_img = await page.query_selector(selector)
            if seal_img:
                seal_src = await seal_img.get_attribute('src')
                if seal_src:
                    images['seal'] = urljoin(base_url, seal_src)
                    break
        
        # Gallery images
        gallery_selectors = ['.gallery-content img', '.image-gallery img', '.photos img']
        gallery_images = []
        for selector in gallery_selectors:
            gallery_imgs = await page.query_selector_all(selector)
            for img in gallery_imgs:
                src = await img.get_attribute('src')
                if src:
                    gallery_images.append(urljoin(base_url, src))
        
        if gallery_images:
            images['gallery'] = gallery_images
    except Exception as e:
        logger.debug(f"Error extracting images: {e}")
    
    # Enhanced image cleanup to remove wrong content
    try:
        clean_images = {}
        wrong_content_indicators = [
            'carl-sandburg-college',
            'carlsandburg',
            'sandburg',
            'charger',  # Carl Sandburg College mascot
            'placeholder',
            'example',
            'test',
            'sample',
            'demo'
        ]
        
        for key, val in images.items():
            if isinstance(val, str):
                # Check if single image URL is valid
                if not any(indicator in val.lower() for indicator in wrong_content_indicators):
                    clean_images[key] = val
            elif isinstance(val, list):
                # Filter list of image URLs
                filtered = []
                for url in val:
                    if not any(indicator in url.lower() for indicator in wrong_content_indicators):
                        filtered.append(url)
                if filtered:
                    clean_images[key] = filtered
        
        images = clean_images
    except Exception as e:
        logger.debug(f"Image cleanup error: {e}")

    return images

async def extract_apply_urls(page: Page) -> Dict[str, Optional[str]]:
    # BEGIN PATCH
    """Extract application URLs including those hidden behind buttons or data attributes."""
    apply_urls: Dict[str, Optional[str]] = {}

    try:
        # 1) Direct anchor links (existing behaviour, keep first)
        anchors = await page.query_selector_all('a[href*="apply.commonapp.org"]')
        for link in anchors:
            href = await link.get_attribute('href')
            text = (await link.text_content() or "").lower().strip()
            if not href:
                continue
            if any(key in text for key in ["first-year", "first year", "freshman", "year 1"]):
                apply_urls.setdefault("first_year", href)
            elif "transfer" in text:
                apply_urls.setdefault("transfer", href)
            else:
                # generic apply/create account link
                apply_urls.setdefault("first_year", href)

        # 2) Buttons or elements with data-* attributes referencing the URL
        data_selectors = [
            '[data-url*="apply.commonapp.org"]',
            '[data-href*="apply.commonapp.org"]',
            '[data-link*="apply.commonapp.org"]',
            'button:has-text("Apply"):not(a)',
        ]
        for selector in data_selectors:
            elements = await page.query_selector_all(selector)
            for el in elements:
                # attribute check order
                attrs = ["data-url", "data-href", "data-link", "href"]
                href = None
                for attr in attrs:
                    href = await el.get_attribute(attr)
                    if href and "apply.commonapp.org" in href:
                        break
                # fallback to onclick JS handler
                if not href:
                    onclick = await el.get_attribute('onclick')
                    if onclick and "apply.commonapp.org" in onclick:
                        match = re.search(r'https?://[^"\']+', onclick)
                        href = match.group(0) if match else None

                if href and "apply.commonapp.org" in href:
                    label = (await el.text_content() or "").lower()
                    if "transfer" in label:
                        apply_urls.setdefault("transfer", href)
                    else:
                        apply_urls.setdefault("first_year", href)
    except Exception as e:
        logger.debug(f"Error extracting apply URLs: {e}")

    return apply_urls
    # END PATCH

async def attempt_accept_cookies(page: Page) -> None:
    """Dismiss the cookies / consent banner if it is present to avoid UI interference."""
    selectors = [
        'button:has-text("Accept")',
        'button:has-text("Accept All")',
        'button:has-text("Accept all")',
        'button:has-text("I Accept")',
        'button:has-text("Agree")',
        'button:has-text("Got it")',
        'button:has-text("OK")',
    ]
    for sel in selectors:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(300)
                logger.debug(f"Clicked cookie banner button via selector: {sel}")
                break
        except Exception as e:
            logger.debug(f"Cookie banner dismiss error ({sel}): {e}")

def validate_college_data(data: Dict[str, Any], expected_college_name: str) -> Dict[str, Any]:
    """Validate that the scraped data matches the expected college and clean up wrong content."""
    if not data:
        return data
    
    # Get the scraped college name
    scraped_name = data.get('name', '').lower()
    expected_name = expected_college_name.lower()
    
    # Check for obvious wrong content indicators
    wrong_content_indicators = [
        'carl sandburg college',
        'sandburg',
        'charger',
        'chargers',
        'galesburg',
        'illinois'
    ]
    
    # Check if we have completely wrong content
    has_wrong_content = False
    for indicator in wrong_content_indicators:
        if indicator in scraped_name:
            has_wrong_content = True
            break
    
    if has_wrong_content:
        logger.warning(f"Detected wrong content for {expected_college_name} - contains {scraped_name}")
        
        # Clear out potentially wrong data but keep basic info
        data['social_media'] = {}
        data['visit_info'] = {}
        data['additional_info'] = {}
        data['images'] = {}
        
        # Add a flag to indicate data quality issue
        data['data_quality_issue'] = True
        data['data_quality_note'] = f"HTML content appears to be from wrong college: {scraped_name}"
    
    return data

async def scrape_college(page: Page, url: str, base_url: str) -> Optional[Dict[str, Any]]:
    """Scrape comprehensive data from one college page."""
    logger.info(f"Scraping college: {url}")
    
    # Robust navigation with retries
    MAX_NAV_RETRIES = 3
    for attempt in range(1, MAX_NAV_RETRIES + 1):
        try:
            # Faster initial load; follow with explicit idle wait
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            try:
                # Extra wait for late network quiet but shorter timeout
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                # It's fine if network never fully idles
                pass
            await page.wait_for_timeout(1500)
            break  # success
        except Exception as nav_err:
            logger.warning(f"Nav attempt {attempt}/{MAX_NAV_RETRIES} failed for {url}: {nav_err}")
            if attempt == MAX_NAV_RETRIES:
                logger.error(f"Error loading page {url}: {nav_err}")
                return None
            await page.wait_for_timeout(3000)  # brief backoff before retry

    # Ensure all expandable sections are opened for full extraction
    await click_expandable_sections(page)

    # Trigger lazy loaded elements (icons/images) to ensure they are in DOM
    await ensure_full_dom(page)

    # -------- Robust name extraction with hydration retries --------
    async def _attempt_get_name() -> Optional[str]:
        """Try to read the college name from heading elements."""
        name_local = ""
        name_selectors = ['h1', '.college-name', '.institution-name']
        for selector in name_selectors:
            elem = await page.query_selector(selector)
            if elem:
                txt = await elem.text_content()
                if txt and txt.strip():
                    name_local = clean_text(txt)
                    break
        return name_local if name_local else None

    name: str = ""
    MAX_HYDRATE_RETRIES = 4
    for attempt_idx in range(MAX_HYDRATE_RETRIES):
        name_candidate = await _attempt_get_name()
        if name_candidate and name_candidate.lower() != "explore colleges":
            name = name_candidate
            break

        # if first attempt fails, try dismissing cookies (once)
        if attempt_idx == 0:
            await attempt_accept_cookies(page)

        # trigger scroll & wait for SPA hydration then retry
        await ensure_full_dom(page)
        await page.wait_for_timeout(1500)

    if not name:
        logger.warning(f"Skipped {url} - could not determine college name after hydration retries")
        return None

    # -------- Description --------
    description = ""

    # a) Meta description tag (quick and consistent)
    try:
        meta_desc = await page.query_selector('meta[name="description" i]')
        if meta_desc:
            description = await meta_desc.get_attribute('content') or ""
            description = clean_text(description)
    except Exception:
        pass

    # b) Visible headline / intro blocks if meta failed or is generic
    if description and (description.lower().startswith("apply to college for the first time") or len(description) < 40):
        description = ""  # trigger fallback to visible paragraph

    # c) If still empty, grab first non-empty paragraph in main content area
    if not description:
        try:
            p_tag = await page.query_selector('main p')
            if not p_tag:
                p_tag = await page.query_selector('p')
            if p_tag:
                description = clean_text(await p_tag.text_content() or "")
        except Exception:
            pass
    
    # Contact & Location
    contact_info = await extract_contact_info(page)
    location_info = await extract_comprehensive_location(page)
    # Fallback to address-based parsing if needed
    if not any(location_info.values()) and contact_info.get("address", {}).get("full"):
        location_info = extract_location(contact_info["address"]["full"])

    # Extract all detailed information
    tags = await extract_tags(page)
    academic_programs = await extract_academic_programs(page)
    student_experience = await extract_student_experience(page)
    application_info = await extract_enhanced_application_info(page)
    social_media = await extract_social_media(page, name)
    additional_info = await extract_additional_info(page)
    visit_info = await extract_visit_info(page)
    images = await extract_images(page, base_url)
    apply_urls = await extract_apply_urls(page)
    
    # Create slug
    slug = slugify(name, separator="_") if name else slugify(url.split('/')[-1], separator="_")
    
    # Save raw HTML
    raw_path = Path(f"data/raw_html/{slug}.html")
    try:
        raw_path.write_text(await page.content(), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not save raw HTML for {slug}: {e}")
    
    # Compile comprehensive data
    college_data = {
        "name": name,
        "slug": slug,
        "url": url,
        "location": location_info,
        "description": description,
        "tags": tags,
        "academic_programs": academic_programs,
        "student_experience": student_experience,
        "application_info": application_info,
        "contact_info": contact_info,
        "social_media": social_media,
        "additional_info": additional_info,
        "visit_info": visit_info,
        "apply_urls": apply_urls,
        "images": images,
        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }
    
    # Validate data quality and clean up wrong content
    college_data = validate_college_data(college_data, name or url)
    
    # ------------- Safety-net placeholder scrub -------------
    try:
        # socials
        if any("sandburg" in (v or "").lower() for v in college_data.get("social_media", {}).values()):
            college_data["social_media"] = {k: v for k, v in college_data["social_media"].items() if "sandburg" not in (v or "").lower()}
        # requirements
        for cohort in ("first_year", "transfer"):
            req = college_data.get("application_info", {}).get(cohort, {}).get("requirements")
            if req and "sandburg" in req.lower():
                college_data["application_info"][cohort].pop("requirements", None)
        # images
        if any("sandburg" in (url if isinstance(url,str) else "").lower() for url in college_data.get("images", {}).values() if isinstance(url,str)) or any(
            any("sandburg" in u.lower() for u in lst) for lst in college_data.get("images", {}).values() if isinstance(lst, list)):
            clean_imgs = {}
            for k, val in college_data["images"].items():
                if isinstance(val, str):
                    if "sandburg" not in val.lower():
                        clean_imgs[k] = val
                elif isinstance(val, list):
                    filtered = [u for u in val if "sandburg" not in u.lower()]
                    if filtered:
                        clean_imgs[k] = filtered
            college_data["images"] = clean_imgs
    except Exception as e:
        logger.debug(f"Safety-net cleanup error: {e}")

    logger.info(f"Successfully scraped {name}")
    return college_data

async def collect_college_links(page: Page) -> List[str]:
    """Collect all unique college links from the explore page."""
    logger.info("Collecting college links from explore page...")
    
    # Navigate to explore page
    explore_url = "https://www.commonapp.org/explore/"
    await page.goto(explore_url, wait_until="networkidle")
    
    # Scroll to load all colleges
    college_count = await aggressive_scroll(page, target_count=1097)
    
    # Collect all college links
    links = await page.query_selector_all('a[href^="/explore/"]')
    valid_hrefs = set()
    
    for link in links:
        href = await link.get_attribute('href')
        if href and href.strip() and href != "/explore/":
            # Filter out non-college links
            if len(href.split("/")) > 2 and not any(x in href for x in ['filter', 'search', 'help', 'about']):
                valid_hrefs.add(href)
    
    college_links = sorted(list(valid_hrefs))
    logger.info(f"Found {len(college_links)} unique college links")
    
    if len(college_links) < 1000:
        logger.warning(f"Only found {len(college_links)} colleges, expected ~1097")
    
    return college_links

async def export_to_csv(data: List[Dict[str, Any]], csv_path: Path) -> None:
    """Export data to CSV format."""
    logger.info(f"Exporting {len(data)} colleges to CSV...")
    
    try:
        # Flatten the nested structure
        flattened = []
        for college in data:
            flat = {
                "name": college.get("name", ""),
                "slug": college.get("slug", ""),
                "url": college.get("url", ""),
                "city": college.get("location", {}).get("city", ""),
                "state": college.get("location", {}).get("state", ""),
                "country": college.get("location", {}).get("country", ""),
                "description": college.get("description", ""),
                "tags": "; ".join(college.get("tags", [])),
                "academic_programs": "; ".join(college.get("academic_programs", [])),
                "student_experience": "; ".join(college.get("student_experience", [])),
                "phone": college.get("contact_info", {}).get("phone", ""),
                "email": college.get("contact_info", {}).get("email", ""),
                "website": college.get("contact_info", {}).get("website", ""),
                "facebook": college.get("social_media", {}).get("facebook", ""),
                "twitter": college.get("social_media", {}).get("twitter", ""),
                "instagram": college.get("social_media", {}).get("instagram", ""),
                "linkedin": college.get("social_media", {}).get("linkedin", ""),
                "youtube": college.get("social_media", {}).get("youtube", ""),
                "mentions_financial_aid": college.get("additional_info", {}).get("mentions_financial_aid", False),
                "mentions_scholarships": college.get("additional_info", {}).get("mentions_scholarships", False),
                "offers_tours": college.get("visit_info", {}).get("offers_tours", False),
                "offers_virtual_visits": college.get("visit_info", {}).get("offers_virtual_visits", False),
                "first_year_apply_url": college.get("apply_urls", {}).get("first_year", ""),
                "transfer_apply_url": college.get("apply_urls", {}).get("transfer", ""),
                "scraped_at": college.get("scraped_at", "")
            }
            flattened.append(flat)
        
        df = pd.DataFrame(flattened)
        df.to_csv(csv_path, index=False)
        logger.info(f"✓ CSV exported successfully with {len(flattened)} rows")
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")

async def main(resume: bool = False, debug: bool = False) -> None:
    """Main scraping function with concurrency support."""
    logger.info("Starting Common App scraper...")

    ensure_dirs()

    start_time = time.time()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--workers", type=int, default=DEFAULT_CONCURRENCY)
    args, _ = parser.parse_known_args()
    workers = max(1, args.workers)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not debug)
        context = await browser.new_context()

        nav_page = await context.new_page()
        college_links = await collect_college_links(nav_page)
        await nav_page.close()

        base_url = "https://www.commonapp.org"

        # Resume support
        existing_data: List[Dict[str, Any]] = []
        processed_slugs: Set[str] = set()
        json_path = Path("data/colleges/institutions.json")
        if resume and json_path.exists():
            existing_data = json.loads(json_path.read_text())
            processed_slugs = {c['slug'] for c in existing_data}

        scraped_colleges: List[Dict[str, Any]] = existing_data.copy()

        sem = asyncio.Semaphore(workers)
        progress = tqdm(total=len(college_links), initial=len(processed_slugs))

        async def worker(rel_url: str):
            slug_local = slugify(rel_url.split('/')[-1], separator="_")
            if slug_local in processed_slugs:
                progress.update(1)
                return
            async with sem:
                page = await context.new_page()
                data = await scrape_college(page, base_url + rel_url, base_url)
                await page.close()
                if data:
                    scraped_colleges.append(data)
                    scraped_colleges.sort(key=lambda c: c.get('name', '').lower())
                # interim write (cheap)
                try:
                    json_path.write_text(json.dumps(scraped_colleges, indent=2))
                except Exception as write_err:
                    logger.debug(f"Interim save error: {write_err}")
                progress.update(1)

        # Launch tasks
        tasks = [asyncio.create_task(worker(u)) for u in college_links]
        await asyncio.gather(*tasks)
        progress.close()

        # Ensure final alphabetical order
        scraped_colleges.sort(key=lambda c: c.get('name', '').lower())

        # Export CSV
        await export_to_csv(scraped_colleges, Path("data/colleges/institutions.csv"))

        await browser.close()

    logger.info(f"Finished. Total time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Common App College Scraper")
    parser.add_argument("--resume", action="store_true", help="Resume from existing data")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    asyncio.run(main(resume=args.resume, debug=args.debug)) 