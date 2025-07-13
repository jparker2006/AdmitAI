#!/usr/bin/env python3
"""
CDS_parser.py
-------------
CLI utility to automatically locate, download, parse, and save Common Data Set (CDS)
information for a list of colleges.

Usage examples
--------------
# Single college (quotes recommended for multi-word names)
python scripts/CDS_parser.py --college "Harvard University"

# Multiple colleges (repeat --college)
python scripts/CDS_parser.py --college "UCLA" --college "University of Michigan"

# Batch mode from newline-delimited text file
python scripts/CDS_parser.py --batch ./scripts/college_list.txt

Creates JSON files under data/colleges/CDS/{slugified_college_name}.json
and logs progress to scripts/logs/CDS_parser.log

Dependencies
------------
- googlesearch-python (pip install googlesearch-python)
- requests
- pdfplumber
- python-slugify
- unidecode

Note: For some PDFs that are scanned images only, text extraction will fail. Such
cases are logged (is_scanned=True) so that an OCR fallback can be implemented
later.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from slugify import slugify  # type: ignore
from unidecode import unidecode  # type: ignore

try:
    from googlesearch import search  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "googlesearch-python is required. Install with `pip install googlesearch-python`."
    ) from exc

try:
    import pdfplumber  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pdfplumber is required. Install with `pip install pdfplumber`. ") from exc


# ---------------------------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "colleges" / "CDS"
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "CDS_parser.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def google_search_cds_pdf(college_name: str, max_results: int = 10) -> Optional[Tuple[str, str]]:
    """Search Google for the most recent CDS PDF link for a college.

    Returns
    -------
    tuple(pdf_url, year_string) if found, otherwise None.
    """
    query = f'"{college_name}" "Common Data Set" site:.edu filetype:pdf'
    logger.info("Google search query: %s", query)

    results = list(search(query, num_results=max_results))
    pdf_links = [url for url in results if url.lower().endswith(".pdf") and ".edu" in url]

    if not pdf_links:
        logger.warning("No CDS PDF link found for %s", college_name)
        return None

    # Attempt to infer year from the URL (e.g., 2023-2024 or 2023)
    year_pattern = re.compile(r"(20\d{2})[\-_]?(20\d{2})?")
    for url in pdf_links:
        if (m := year_pattern.search(url)):
            if m.group(2):
                year_str = f"{m.group(1)}-{m.group(2)}"
            else:
                # Assume single year refers to academic year starting that year (e.g., 2023 => 2023-2024)
                year_str = f"{m.group(1)}-{int(m.group(1)) + 1}"
            return url, year_str

    # Fallback: return first pdf link, year unknown
    return pdf_links[0], "unknown"


def download_pdf(url: str) -> Path:
    """Download a PDF to a temporary file and return its Path."""
    logger.info("Downloading PDF: %s", url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(tmp_fd, "wb") as tmp_file:
        tmp_file.write(response.content)
    return Path(tmp_path)


def extract_text(pdf_path: Path) -> Tuple[str, bool]:
    """Extract text from a PDF using pdfplumber.

    Returns (text, is_scanned)
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texts: List[str] = []
            pages_no_text = 0
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texts.append(page_text)
                else:
                    pages_no_text += 1

            total_pages = len(pdf.pages)
            is_scanned = total_pages > 0 and pages_no_text / total_pages > 0.8
            full_text = "\n".join(texts)
            return full_text, is_scanned
    except Exception as exc:
        logger.exception("Failed to extract text from %s: %s", pdf_path, exc)
        return "", True


def split_sections(cds_text: str) -> Dict[str, str]:
    """Split the CDS text into sections keyed by their capital letter (A, B, C...)."""
    pattern = re.compile(r"Section\s+([A-Z])", re.IGNORECASE)
    matches = list(pattern.finditer(cds_text))

    sections: Dict[str, str] = {}
    for idx, match in enumerate(matches):
        section_letter = match.group(1).upper()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(cds_text)
        sections[section_letter] = cds_text[start:end].strip()
    return sections

# ---------------------------------------------------------------------------
# Basic Field Parsers (can be improved over time)
# ---------------------------------------------------------------------------

def parse_acceptance_rate(section_b_text: str) -> Dict[str, Optional[float]]:
    """Attempt to parse acceptance rate and related numbers from Section B text."""
    numbers = {
        "total_applicants": _find_int(section_b_text, r"Total\s+first-time\s+.*?applicants[\s:]+(\d+[\d,]*)"),
        "total_admits": _find_int(section_b_text, r"Total\s+admits[\s:]+(\d+[\d,]*)"),
        "total_enrolled": _find_int(section_b_text, r"Total\s+enrolled[\s:]+(\d+[\d,]*)"),
    }
    if numbers["total_applicants"] and numbers["total_admits"]:
        numbers["acceptance_rate"] = round(numbers["total_admits"] / numbers["total_applicants"], 4)
    else:
        numbers["acceptance_rate"] = None
    return numbers


def parse_scores(section_c_text: str) -> Dict[str, Optional[int]]:
    """Parse SAT/ACT score ranges from Section C text."""
    scores = {
        "SAT_25": _find_int(section_c_text, r"25th\s+percentile.*?SAT.*?(\d{3,4})"),
        "SAT_75": _find_int(section_c_text, r"75th\s+percentile.*?SAT.*?(\d{3,4})"),
        "ACT_25": _find_int(section_c_text, r"25th\s+percentile.*?ACT.*?(\d{1,2})"),
        "ACT_75": _find_int(section_c_text, r"75th\s+percentile.*?ACT.*?(\d{1,2})"),
    }
    return scores


def parse_fin_aid(section_g_text: str) -> Dict[str, Optional[float]]:
    """Parse basic financial aid stats from Section G text."""
    aid = {
        "average_need_based_aid": _find_int(section_g_text, r"Average.*?need.*?based.*?\$([\d,]+)"),
        "percent_receiving_aid": _find_float(section_g_text, r"Receiving.*?aid.*?([\d\.]+)%"),
    }
    return aid

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

def _find_int(text: str, pattern: str) -> Optional[int]:
    if (m := re.search(pattern, text, re.IGNORECASE | re.DOTALL)):
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def _find_float(text: str, pattern: str) -> Optional[float]:
    if (m := re.search(pattern, text, re.IGNORECASE | re.DOTALL)):
        try:
            return float(m.group(1).replace("%", ""))
        except ValueError:
            return None
    return None

# ---------------------------------------------------------------------------
# Core Processing
# ---------------------------------------------------------------------------

def process_college(college_name: str) -> None:
    logger.info("Processing college: %s", college_name)
    search_result = google_search_cds_pdf(college_name)
    if not search_result:
        logger.error("Skipping %s – no PDF found", college_name)
        return

    pdf_url, year = search_result
    pdf_path = download_pdf(pdf_url)

    cds_text, is_scanned = extract_text(pdf_path)
    pdf_path.unlink(missing_ok=True)  # remove temp file

    if is_scanned:
        logger.warning("%s appears to be a scanned PDF. OCR not yet implemented.", college_name)
    if not cds_text.strip():
        logger.error("No text extracted for %s", college_name)
        return

    sections_text = split_sections(cds_text)
    section_b = sections_text.get("B", "")
    section_c = sections_text.get("C", "")
    section_g = sections_text.get("G", "")

    data = {
        "college": college_name,
        "year": year,
        "source_url": pdf_url,
        "is_scanned": is_scanned,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sections": {
            "B": parse_acceptance_rate(section_b),
            "C": parse_scores(section_c),
            "G": parse_fin_aid(section_g),
        },
    }

    output_path = DATA_DIR / f"{slugify(college_name)}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved parsed data for %s to %s", college_name, output_path)


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse Common Data Set PDFs for colleges.")
    parser.add_argument(
        "--college",
        action="append",
        dest="colleges",
        help="College name to process. Can be repeated.",
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="Path to text file with one college name per line.",
    )
    return parser.parse_args(argv)


def gather_college_list(args: argparse.Namespace) -> List[str]:
    colleges: List[str] = []
    if args.colleges:
        colleges.extend(args.colleges)
    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.exists():
            logger.error("Batch file not found: %s", batch_path)
        else:
            with open(batch_path, encoding="utf-8") as f:
                batch_names = [line.strip() for line in f.readlines() if line.strip()]
            colleges.extend(batch_names)
    return list(dict.fromkeys(colleges))  # unique, preserve order


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    colleges = gather_college_list(args)

    if not colleges:
        print("No colleges provided. Use --college or --batch.")
        return

    for college in colleges:
        try:
            process_college(college)
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled exception processing %s: %s", college, exc)


if __name__ == "__main__":
    main() 