#!/usr/bin/env python3
"""
Utility functions for NHL Playoff Framework data pipeline.
Includes retry logic, data validation, and common helpers.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

import requests

from config import (
    REQUEST_TIMEOUT, REQUEST_RETRIES, REQUEST_RETRY_DELAY,
    USER_AGENT, DATA_DIR, FRESHNESS_THRESHOLDS, VALID_RANGES,
    ALL_TEAMS, get_current_timestamp
)

# =============================================================================
# LOGGING SETUP
# =============================================================================
def setup_logging(name="nhl_pipeline", level=logging.INFO):
    """Set up logging with consistent format."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logging()

# =============================================================================
# HTTP REQUEST HELPERS WITH RETRY
# =============================================================================
class FetchError(Exception):
    """Custom exception for fetch failures."""
    pass

def retry_request(max_retries=REQUEST_RETRIES, delay=REQUEST_RETRY_DELAY):
    """Decorator to retry failed requests."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, FetchError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
            raise FetchError(f"Failed after {max_retries} attempts: {last_error}")
        return wrapper
    return decorator

@retry_request()
def fetch_url(url, params=None, headers=None, timeout=REQUEST_TIMEOUT):
    """Fetch URL with retry logic and proper headers."""
    default_headers = {"User-Agent": USER_AGENT}
    if headers:
        default_headers.update(headers)

    logger.debug(f"Fetching: {url}")
    response = requests.get(url, params=params, headers=default_headers, timeout=timeout)
    response.raise_for_status()
    return response

def fetch_json(url, params=None, headers=None):
    """Fetch JSON data from URL."""
    response = fetch_url(url, params=params, headers=headers)
    return response.json()

def fetch_html(url, params=None, headers=None):
    """Fetch HTML content from URL."""
    response = fetch_url(url, params=params, headers=headers)
    return response.text

# =============================================================================
# DATA FILE HELPERS
# =============================================================================
def load_json_file(filepath):
    """Load a JSON file, return empty dict if not found or invalid."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return {}

def save_json_file(filepath, data, indent=2):
    """Save data to a JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=indent)

    logger.info(f"Saved data to {filepath}")

def get_file_age_hours(filepath):
    """Get the age of a file in hours, or None if file doesn't exist."""
    filepath = Path(filepath)
    if not filepath.exists():
        return None

    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    age = datetime.now() - mtime
    return age.total_seconds() / 3600

# =============================================================================
# DATA FRESHNESS CHECKING
# =============================================================================
def check_data_freshness(data_type, filepath=None):
    """
    Check if data file is fresh enough.
    Returns: (is_fresh, age_hours, threshold_hours)
    """
    if filepath is None:
        filepath = DATA_DIR / f"{data_type}.json"

    threshold = FRESHNESS_THRESHOLDS.get(data_type, 24)
    age = get_file_age_hours(filepath)

    if age is None:
        return False, None, threshold

    is_fresh = age < threshold
    return is_fresh, age, threshold

def get_data_freshness_report():
    """Generate a report on all data file freshness."""
    report = []

    files = [
        ("nhl_standings", "nhl_standings.json"),
        ("moneypuck_stats", "moneypuck_stats.json"),
        ("nst_stats", "nst_stats.json"),
        ("odds", "odds.json"),
        ("teams", "teams.json"),
    ]

    for data_type, filename in files:
        filepath = DATA_DIR / filename
        is_fresh, age, threshold = check_data_freshness(data_type, filepath)

        if age is not None:
            status = "✓ FRESH" if is_fresh else "⚠ STALE"
            age_str = f"{age:.1f}h"
        else:
            status = "✗ MISSING"
            age_str = "N/A"

        report.append({
            "file": filename,
            "status": status,
            "age_hours": age,
            "threshold_hours": threshold,
            "age_str": age_str,
            "is_fresh": is_fresh,
        })

    return report

# =============================================================================
# DATA VALIDATION
# =============================================================================
def validate_metric_range(value, metric_name, team=None):
    """
    Validate that a metric value is within expected range.
    Returns: (is_valid, message)
    """
    if metric_name not in VALID_RANGES:
        return True, None

    min_val, max_val = VALID_RANGES[metric_name]

    if value is None:
        return False, f"{metric_name} is None"

    # Handle PDO which may be stored as ratio (1.00) or percentage (100.0)
    check_value = value
    if metric_name == "pdo" and value < 2:  # It's in ratio format
        check_value = value * 100

    if not (min_val <= check_value <= max_val):
        team_str = f" for {team}" if team else ""
        return False, f"{metric_name}{team_str} = {value} is outside expected range [{min_val}, {max_val}]"

    return True, None

def validate_team_data(team_data, required_fields=None):
    """
    Validate a single team's data.
    Returns: (is_valid, errors)
    """
    errors = []

    if not team_data:
        return False, ["No data provided"]

    team = team_data.get("team", "UNKNOWN")

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in team_data or team_data[field] is None:
                errors.append(f"Missing required field: {field}")

    # Validate metric ranges
    metric_checks = ["hdcfPct", "cfPct", "pdo", "ppPct", "pkPct", "gsax"]
    for metric in metric_checks:
        if metric in team_data:
            is_valid, msg = validate_metric_range(team_data[metric], metric, team)
            if not is_valid:
                errors.append(msg)

    return len(errors) == 0, errors

def validate_teams_data(teams_dict, min_teams=32):
    """
    Validate all teams data.
    Returns: (is_valid, summary)
    """
    issues = []

    # Check team count
    if len(teams_dict) < min_teams:
        issues.append(f"Only {len(teams_dict)} teams (expected {min_teams})")

    # Check for missing teams
    for team in ALL_TEAMS:
        if team not in teams_dict:
            issues.append(f"Missing team: {team}")

    # Validate each team
    team_errors = {}
    for team, data in teams_dict.items():
        is_valid, errors = validate_team_data(data)
        if not is_valid:
            team_errors[team] = errors

    if team_errors:
        issues.append(f"{len(team_errors)} teams have validation errors")

    return len(issues) == 0, {
        "issues": issues,
        "team_errors": team_errors,
        "team_count": len(teams_dict),
    }

# =============================================================================
# NUMERIC HELPERS
# =============================================================================
def safe_float(value, default=0.0):
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        # Handle percentage strings
        str_val = str(value).replace('%', '').replace(',', '').strip()
        return float(str_val)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int."""
    if value is None:
        return default
    try:
        return int(float(str(value).replace(',', '').strip()))
    except (ValueError, TypeError):
        return default

def round_to(value, decimals=1):
    """Round value to specified decimal places."""
    if value is None:
        return None
    return round(value, decimals)

# =============================================================================
# METADATA HELPERS
# =============================================================================
def create_metadata(source, url=None, notes=None, extra=None):
    """Create standard metadata dict for data files."""
    from config import CURRENT_SEASON

    metadata = {
        "source": source,
        "season": CURRENT_SEASON,
        "fetchedAt": get_current_timestamp(),
    }

    if url:
        metadata["url"] = url
    if notes:
        metadata["notes"] = notes
    if extra:
        metadata.update(extra)

    return metadata

# =============================================================================
# CONSOLE OUTPUT HELPERS
# =============================================================================
def print_header(title, char="="):
    """Print a formatted header."""
    line = char * 60
    print(f"\n{line}")
    print(f" {title}")
    print(f"{line}\n")

def print_status(label, status, color=None):
    """Print a status line."""
    # ANSI color codes
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "reset": "\033[0m",
    }

    if color and color in colors:
        status = f"{colors[color]}{status}{colors['reset']}"

    print(f"  {label}: {status}")


if __name__ == "__main__":
    # Test utilities
    print_header("NHL Pipeline Utilities Test")

    print("Testing data freshness check...")
    report = get_data_freshness_report()
    for item in report:
        color = "green" if item["is_fresh"] else "yellow" if item["age_hours"] else "red"
        print_status(item["file"], f"{item['status']} ({item['age_str']} / {item['threshold_hours']}h)", color)
