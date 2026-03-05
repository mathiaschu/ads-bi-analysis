#!/usr/bin/env python3
# Copyright (c) 2026 Mathias Chu — https://mathiaschu.com
"""
Google Ads Analysis Script
Processes Google Ads CSV exports or MCP JSON data and generates structured JSON results.
Supports campaign, keyword, search term, and ad reports.

Usage:
    python3 google_ads_analysis.py --input "path/to/csv_or_json" --mode lite --output "/tmp/results.json"
    python3 google_ads_analysis.py --input "dir_with_csvs/" --mode full --currency ARS --output "/tmp/results.json"
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# DECORATORS & HELPERS
# ═══════════════════════════════════════════════════════════════

def safe_analysis(func):
    """Decorator: catches exceptions, returns skipped status."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if result is None:
                return {'status': 'skipped', 'reason': 'Datos insuficientes o columnas faltantes'}
            result['status'] = 'ok'
            return result
        except Exception as e:
            return {'status': 'skipped', 'reason': f'Error: {str(e)}'}
    return wrapper


def has_columns(data, required):
    """Check if all required columns exist in data rows."""
    if not data:
        return False
    sample = data[0] if isinstance(data, list) else data
    return all(col in sample for col in required)


def parse_number(value):
    """Parse a number from string, handling various formats."""
    if value is None:
        return 0.0
    s = str(value).strip()
    if s in ('', '-', '--', 'N/A', 'nan', 'None'):
        return 0.0
    # Remove currency symbols
    s = re.sub(r'[A-Z]{3}|\$|€|£', '', s).strip()
    # Remove % sign
    s = s.replace('%', '')
    # Remove < > signs (impression share approximations)
    s = re.sub(r'[<>]', '', s).strip()
    if not s:
        return 0.0
    # Detect AR/EU format: ends with ,XX (2 digits after last comma)
    if re.search(r',\d{2}$', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '')
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_percentage(value):
    """Parse a percentage value, returns (float_value, is_approximate)."""
    if value is None:
        return None, False
    s = str(value).strip()
    if s in ('', '-', '--', 'N/A', 'nan', 'None'):
        return None, False
    approx = s.startswith('<') or s.startswith('>')
    clean = re.sub(r'[<>%\s]', '', s)
    try:
        return float(clean.replace(',', '')), approx
    except ValueError:
        return None, False


def parse_date(value):
    """Parse date from various formats."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s in ('-', '--', 'N/A'):
        return None
    # Try common formats
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%b %d, %Y', '%B %d, %Y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def safe_div(a, b, default=0.0):
    """Safe division."""
    if b is None or b == 0:
        return default
    return a / b


def fmt_pct(value, decimals=1):
    """Format as percentage."""
    if value is None:
        return None
    return round(value, decimals)


def semaphore_roas(value):
    """ROAS semaphore: green >4, yellow 2-4, red <2."""
    if value is None:
        return 'gray'
    if value >= 4:
        return 'green'
    elif value >= 2:
        return 'yellow'
    return 'red'


def semaphore_ctr(value):
    """CTR semaphore: green >3%, yellow 1.5-3%, red <1.5%."""
    if value is None:
        return 'gray'
    if value >= 3:
        return 'green'
    elif value >= 1.5:
        return 'yellow'
    return 'red'


def semaphore_conv_rate(value):
    """Conv Rate semaphore: green >3%, yellow 1-3%, red <1%."""
    if value is None:
        return 'gray'
    if value >= 3:
        return 'green'
    elif value >= 1:
        return 'yellow'
    return 'red'


def semaphore_qs(value):
    """Quality Score semaphore: green 7+, yellow 5-6, red 1-4."""
    if value is None:
        return 'gray'
    if value >= 7:
        return 'green'
    elif value >= 5:
        return 'yellow'
    return 'red'


def semaphore_is(value):
    """Impression Share semaphore: green >80, yellow 50-80, red <50."""
    if value is None:
        return 'gray'
    if value >= 80:
        return 'green'
    elif value >= 50:
        return 'yellow'
    return 'red'


# ═══════════════════════════════════════════════════════════════
# CSV / JSON LOADING
# ═══════════════════════════════════════════════════════════════

# Column name mapping: CSV header → canonical name
COLUMN_MAP = {
    # Campaign / Ad Group
    'Campaign': 'campaign_name', 'Campaign name': 'campaign_name',
    'Campaign ID': 'campaign_id',
    'Campaign type': 'campaign_type', 'Campaign Type': 'campaign_type',
    'Campaign status': 'campaign_status',
    'Campaign subtype': 'campaign_subtype',
    'Ad group': 'ad_group_name', 'Ad group name': 'ad_group_name',
    'Ad group ID': 'ad_group_id',
    'Ad group status': 'ad_group_status',
    'Ad group type': 'ad_group_type',
    'Network': 'network', 'Network (with search partners)': 'network_with_partners',
    # Date
    'Day': 'date', 'Date': 'date',
    'Week': 'week', 'Month': 'month', 'Quarter': 'quarter', 'Year': 'year',
    'Day of week': 'day_of_week', 'Hour of day': 'hour_of_day',
    # Metrics
    'Impressions': 'impressions', 'Clicks': 'clicks',
    'Interactions': 'interactions', 'Interaction rate': 'interaction_rate',
    # Conversions
    'Conversions': 'conversions', 'All conv.': 'all_conversions',
    'Conv. rate': 'conversion_rate', 'All conv. rate': 'all_conversion_rate',
    'Conv. value': 'conversion_value', 'All conv. value': 'all_conversion_value',
    'Conv. value / cost': 'conv_value_per_cost',
    'All conv. value / cost': 'all_conv_value_per_cost',
    'Value / conv.': 'value_per_conversion',
    'View-through conv.': 'view_through_conversions',
    # Impression Share
    'Search impr. share': 'search_impression_share', 'Impr. share': 'impression_share',
    'Search lost IS (rank)': 'search_lost_is_rank',
    'Search lost IS (budget)': 'search_lost_is_budget',
    'Display impr. share': 'display_impression_share',
    'Display lost IS (rank)': 'display_lost_is_rank',
    'Display lost IS (budget)': 'display_lost_is_budget',
    'Search top IS': 'search_top_is', 'Search abs. top IS': 'search_abs_top_is',
    'Search exact match IS': 'search_exact_match_is',
    'Click share': 'click_share',
    # Quality Score
    'Quality score': 'quality_score', 'Quality Score': 'quality_score',
    'Exp. CTR': 'expected_ctr', 'Ad relevance': 'ad_relevance',
    'Landing page exp.': 'landing_page_experience',
    'Historical Quality Score': 'hist_quality_score',
    # Keywords / Search Terms
    'Keyword': 'keyword', 'Search keyword': 'keyword',
    'Match type': 'match_type', 'Keyword state': 'keyword_status',
    'Search term': 'search_term',
    'Added / Excluded': 'search_term_status',
    'Keyword / Placement': 'keyword_or_placement',
    # Ads
    'Headline 1': 'headline_1', 'Headline 2': 'headline_2', 'Headline 3': 'headline_3',
    'Description 1': 'description_1', 'Description 2': 'description_2',
    'Responsive search ad headlines': 'rsa_headlines',
    'Responsive search ad descriptions': 'rsa_descriptions',
    'Ad strength': 'ad_strength', 'Ad type': 'ad_type',
    'Final URL': 'final_url', 'Ad status': 'ad_status',
    # Bidding
    'Bid strategy type': 'bid_strategy_type', 'Bid strategy name': 'bid_strategy_name',
    'Target CPA': 'target_cpa', 'Target ROAS': 'target_roas',
    'Max CPC limit': 'max_cpc',
    # PMax
    'Asset group': 'asset_group_name', 'Asset group name': 'asset_group_name',
    'Asset group status': 'asset_group_status',
    'Listing group': 'listing_group',
    # Geo
    'Country/Territory': 'country', 'Region': 'region', 'City': 'city',
    'Most specific location': 'location', 'Location type': 'location_type',
    # Device
    'Device': 'device',
    # Auction insights
    'Display URL domain': 'competitor_domain',
    'Overlap rate': 'auction_overlap', 'Outranking share': 'auction_outranking',
    'Position above rate': 'auction_pos_above',
    'Top of page rate': 'auction_top_rate', 'Abs. top of page rate': 'auction_abs_top_rate',
}

# Cost columns with possible currency suffix
COST_COLUMN_PATTERNS = {
    'Cost': 'cost', 'Avg. CPC': 'avg_cpc', 'Avg. CPM': 'avg_cpm', 'Avg. cost': 'avg_cost',
    'Cost / conv.': 'cost_per_conversion', 'Cost / all conv.': 'cost_per_all_conversion',
}

# Percentage columns (stored as percentage, not decimal)
PERCENTAGE_COLUMNS = {
    'CTR', 'Conv. rate', 'All conv. rate', 'Interaction rate',
    'Search impr. share', 'Impr. share', 'Search lost IS (rank)',
    'Search lost IS (budget)', 'Search top IS', 'Search abs. top IS',
    'Search exact match IS', 'Click share', 'Display impr. share',
    'Display lost IS (rank)', 'Display lost IS (budget)',
    'Overlap rate', 'Outranking share', 'Position above rate',
    'Top of page rate', 'Abs. top of page rate',
}

# Integer columns
INTEGER_COLUMNS = {'impressions', 'clicks', 'interactions', 'hour_of_day'}

# Campaign type normalization
CAMPAIGN_TYPE_MAP = {
    'SEARCH': 'Search', 'Search': 'Search', 'search': 'Search',
    'SHOPPING': 'Shopping', 'Shopping': 'Shopping', 'shopping': 'Shopping',
    'PERFORMANCE_MAX': 'PMax', 'Performance Max': 'PMax', 'performance max': 'PMax',
    'DISPLAY': 'Display', 'Display': 'Display', 'display': 'Display',
    'VIDEO': 'Video', 'Video': 'Video', 'video': 'Video',
    'DEMAND_GEN': 'Demand Gen', 'Demand Gen': 'Demand Gen',
}


def detect_currency(headers):
    """Detect currency from CSV headers like 'Cost (ARS)'."""
    for h in headers:
        match = re.search(r'\(([A-Z]{3})\)', h)
        if match:
            return match.group(1)
    return 'auto'


def detect_report_type(headers):
    """Detect which type of Google Ads report this is."""
    header_set = {h.strip() for h in headers}

    if 'Search term' in header_set:
        return 'search_term'

    kw_markers = {'Keyword', 'Search keyword', 'Quality score', 'Quality Score'}
    if len(header_set & kw_markers) >= 2:
        return 'keyword'

    ad_markers = {'Headline 1', 'Responsive search ad headlines', 'Ad strength', 'Description 1'}
    if len(header_set & ad_markers) >= 1 and 'Ad group' in header_set:
        return 'ad'

    return 'campaign'


def detect_encoding(filepath):
    """Detect file encoding."""
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                f.read(4096)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'utf-8'


def detect_delimiter(filepath, encoding):
    """Detect CSV delimiter."""
    with open(filepath, 'r', encoding=encoding) as f:
        sample = f.read(4096)
    # Count potential delimiters in first line
    first_line = sample.split('\n')[0]
    counts = {',': first_line.count(','), '\t': first_line.count('\t'), ';': first_line.count(';')}
    return max(counts, key=counts.get) if max(counts.values()) > 0 else ','


def map_column_name(raw_header, currency):
    """Map a raw CSV header to canonical name."""
    h = raw_header.strip()

    # Direct mapping
    if h in COLUMN_MAP:
        return COLUMN_MAP[h]

    # Cost columns with currency suffix: "Cost (ARS)" → "cost"
    for pattern, canonical in COST_COLUMN_PATTERNS.items():
        if h.startswith(pattern):
            return canonical

    # CTR with parenthetical
    if h.startswith('CTR'):
        return 'ctr'

    # Impression share with auction context
    if 'Impression share' in h and 'competitor' not in h.lower():
        return 'auction_is' if 'Display URL' in str(raw_header) else 'impression_share'

    return None  # Unknown column


def load_csv(filepath, currency='auto'):
    """Load a Google Ads CSV export and normalize columns."""
    encoding = detect_encoding(filepath)
    delimiter = detect_delimiter(filepath, encoding)

    rows = []
    with open(filepath, 'r', encoding=encoding, newline='') as f:
        # Skip Google Ads header rows (non-CSV metadata)
        lines = f.readlines()

    # Find the actual header row (first row with known column names)
    header_idx = 0
    for i, line in enumerate(lines):
        if any(marker in line for marker in ('Campaign', 'Impressions', 'Keyword', 'Search term', 'Ad group')):
            header_idx = i
            break

    # Parse CSV from header row
    reader = csv.DictReader(lines[header_idx:], delimiter=delimiter)
    raw_headers = reader.fieldnames or []

    # Detect currency if auto
    if currency == 'auto':
        currency = detect_currency(raw_headers)

    # Detect report type
    report_type = detect_report_type(raw_headers)

    # Build column mapping
    col_map = {}
    for h in raw_headers:
        canonical = map_column_name(h, currency)
        if canonical:
            col_map[h] = canonical

    # Read and normalize rows
    for raw_row in reader:
        row = {}
        for raw_col, canonical in col_map.items():
            raw_val = raw_row.get(raw_col, '')

            # Parse based on column type
            if canonical in INTEGER_COLUMNS:
                row[canonical] = int(parse_number(raw_val))
            elif canonical in ('cost', 'avg_cpc', 'avg_cpm', 'avg_cost', 'cost_per_conversion',
                             'cost_per_all_conversion', 'conversion_value', 'all_conversion_value',
                             'conversions', 'all_conversions', 'conversion_rate', 'all_conversion_rate',
                             'conv_value_per_cost', 'all_conv_value_per_cost', 'value_per_conversion',
                             'view_through_conversions', 'target_cpa', 'target_roas', 'max_cpc'):
                row[canonical] = parse_number(raw_val)
            elif canonical in ('search_impression_share', 'search_lost_is_rank', 'search_lost_is_budget',
                             'search_top_is', 'search_abs_top_is', 'search_exact_match_is',
                             'impression_share', 'click_share', 'display_impression_share',
                             'display_lost_is_rank', 'display_lost_is_budget',
                             'auction_is', 'auction_overlap', 'auction_outranking',
                             'auction_pos_above', 'auction_top_rate', 'auction_abs_top_rate', 'ctr'):
                val, approx = parse_percentage(raw_val)
                row[canonical] = val
            elif canonical == 'quality_score':
                if raw_val and raw_val.strip() not in ('', '--', '-', 'N/A'):
                    try:
                        row[canonical] = int(float(raw_val))
                    except (ValueError, TypeError):
                        row[canonical] = None
                else:
                    row[canonical] = None
            elif canonical == 'date':
                row[canonical] = parse_date(raw_val)
            elif canonical == 'hour_of_day':
                try:
                    row[canonical] = int(parse_number(raw_val))
                except (ValueError, TypeError):
                    row[canonical] = None
            elif canonical == 'campaign_type':
                raw = str(raw_val).strip()
                row[canonical] = CAMPAIGN_TYPE_MAP.get(raw, raw)
            else:
                row[canonical] = str(raw_val).strip() if raw_val else None

        # Only keep rows with some data
        if any(v is not None and v != '' and v != 0 and v != 0.0 for v in row.values()):
            rows.append(row)

    return rows, report_type, currency, encoding, delimiter


def load_json(filepath):
    """Load MCP JSON output (from GAQL queries)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle various JSON structures
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        if 'results' in data:
            rows = data['results']
        elif 'data' in data:
            rows = data['data']
        else:
            rows = [data]
    else:
        rows = []

    # Normalize GAQL field names and micros
    normalized = []
    for raw in rows:
        row = {}

        # Flatten nested structures (campaign.name, metrics.impressions, etc.)
        flat = {}
        for k, v in raw.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    flat[f'{k}.{k2}'] = v2
            else:
                flat[k] = v

        # Map GAQL fields
        gaql_map = {
            'campaign.name': 'campaign_name', 'campaign.id': 'campaign_id',
            'campaign.status': 'campaign_status',
            'campaign.advertising_channel_type': 'campaign_type',
            'campaign.bidding_strategy_type': 'bid_strategy_type',
            'ad_group.name': 'ad_group_name', 'ad_group.id': 'ad_group_id',
            'ad_group_criterion.keyword.text': 'keyword',
            'ad_group_criterion.keyword.match_type': 'match_type',
            'ad_group_criterion.quality_info.quality_score': 'quality_score',
            'ad_group_criterion.quality_info.creative_quality_score': 'ad_relevance',
            'ad_group_criterion.quality_info.search_predicted_ctr': 'expected_ctr',
            'ad_group_criterion.quality_info.post_click_quality_score': 'landing_page_experience',
            'search_term_view.search_term': 'search_term',
            'search_term_view.status': 'search_term_status',
            'asset_group.name': 'asset_group_name',
            'asset_group.status': 'asset_group_status',
            'asset_group.ad_strength': 'ad_strength',
            'segments.date': 'date', 'segments.day_of_week': 'day_of_week',
            'segments.device': 'device', 'segments.hour': 'hour_of_day',
            'segments.ad_network_type': 'network',
            'geographic_view.country_criterion_id': 'country_id',
            'geographic_view.location_type': 'location_type',
            'metrics.impressions': 'impressions', 'metrics.clicks': 'clicks',
            'metrics.conversions': 'conversions', 'metrics.all_conversions': 'all_conversions',
            'metrics.conversions_value': 'conversion_value',
            'metrics.all_conversions_value': 'all_conversion_value',
            'metrics.ctr': 'ctr', 'metrics.average_cpc': 'avg_cpc',
            'metrics.average_cpm': 'avg_cpm',
            'metrics.conversions_from_interactions_rate': 'conversion_rate',
            'metrics.value_per_conversion': 'value_per_conversion',
            'metrics.search_impression_share': 'search_impression_share',
            'metrics.search_budget_lost_impression_share': 'search_lost_is_budget',
            'metrics.search_rank_lost_impression_share': 'search_lost_is_rank',
            'metrics.search_top_impression_share': 'search_top_is',
            'metrics.search_absolute_top_impression_share': 'search_abs_top_is',
        }

        # Micros fields (divide by 1,000,000)
        micros_fields = {
            'metrics.cost_micros': 'cost',
            'metrics.cost_per_conversion': 'cost_per_conversion',
            'metrics.cost_per_all_conversions': 'cost_per_all_conversion',
            'campaign.target_cpa.target_cpa_micros': 'target_cpa',
        }

        # Percentage fields from API (multiply by 100)
        pct_fields = {
            'metrics.ctr', 'metrics.conversions_from_interactions_rate',
            'metrics.search_impression_share', 'metrics.search_budget_lost_impression_share',
            'metrics.search_rank_lost_impression_share', 'metrics.search_top_impression_share',
            'metrics.search_absolute_top_impression_share',
        }

        for gaql_key, canonical in gaql_map.items():
            if gaql_key in flat:
                val = flat[gaql_key]
                if gaql_key in pct_fields and val is not None:
                    try:
                        row[canonical] = float(val) * 100
                    except (ValueError, TypeError):
                        row[canonical] = None
                elif canonical in INTEGER_COLUMNS:
                    try:
                        row[canonical] = int(float(val)) if val is not None else 0
                    except (ValueError, TypeError):
                        row[canonical] = 0
                elif canonical == 'date':
                    row[canonical] = parse_date(val)
                elif canonical == 'campaign_type':
                    row[canonical] = CAMPAIGN_TYPE_MAP.get(str(val), str(val))
                else:
                    row[canonical] = val

        for gaql_key, canonical in micros_fields.items():
            if gaql_key in flat and flat[gaql_key] is not None:
                try:
                    row[canonical] = float(flat[gaql_key]) / 1_000_000
                except (ValueError, TypeError):
                    row[canonical] = 0.0

        # Average CPC from API is also in micros
        if 'metrics.average_cpc' in flat and flat['metrics.average_cpc'] is not None:
            try:
                row['avg_cpc'] = float(flat['metrics.average_cpc']) / 1_000_000
            except (ValueError, TypeError):
                pass

        if row:
            normalized.append(row)

    return normalized


def load_input(input_path, currency='auto'):
    """Load input from CSV, JSON, or directory of CSVs."""
    path = Path(input_path)

    if path.is_dir():
        # Load all CSVs in directory
        all_data = {}
        for f in sorted(path.glob('*.csv')):
            rows, rtype, curr, enc, delim = load_csv(str(f), currency)
            if rows:
                all_data[rtype] = rows
                if currency == 'auto' and curr != 'auto':
                    currency = curr
        return all_data, currency

    if ',' in input_path and not path.exists():
        # Multiple files separated by comma
        all_data = {}
        for fp in input_path.split(','):
            fp = fp.strip()
            if fp.endswith('.json'):
                rows = load_json(fp)
                all_data['json'] = rows
            else:
                rows, rtype, curr, enc, delim = load_csv(fp, currency)
                if rows:
                    all_data[rtype] = rows
                    if currency == 'auto' and curr != 'auto':
                        currency = curr
        return all_data, currency

    # Single file
    if path.suffix.lower() == '.json':
        rows = load_json(str(path))
        return {'campaign': rows}, currency
    else:
        rows, rtype, curr, enc, delim = load_csv(str(path), currency)
        return {rtype: rows}, curr


# ═══════════════════════════════════════════════════════════════
# HELPER: aggregate rows
# ═══════════════════════════════════════════════════════════════

def get_val(row, key, default=0.0):
    """Safely get a numeric value from a row."""
    val = row.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def aggregate_by(rows, group_key):
    """Aggregate rows by a group key, summing numeric metrics."""
    groups = defaultdict(lambda: {
        'impressions': 0, 'clicks': 0, 'cost': 0.0,
        'conversions': 0.0, 'conversion_value': 0.0,
        'all_conversions': 0.0, 'all_conversion_value': 0.0,
        '_count': 0,
    })
    for row in rows:
        key = row.get(group_key)
        if key is None:
            continue
        g = groups[key]
        g['impressions'] += int(get_val(row, 'impressions'))
        g['clicks'] += int(get_val(row, 'clicks'))
        g['cost'] += get_val(row, 'cost')
        g['conversions'] += get_val(row, 'conversions')
        g['conversion_value'] += get_val(row, 'conversion_value')
        g['all_conversions'] += get_val(row, 'all_conversions')
        g['all_conversion_value'] += get_val(row, 'all_conversion_value')
        g['_count'] += 1
        # Carry forward non-numeric fields from first row
        for extra_key in ('campaign_type', 'bid_strategy_type', 'target_cpa', 'target_roas',
                         'ad_strength', 'asset_group_status', 'match_type', 'quality_score',
                         'expected_ctr', 'ad_relevance', 'landing_page_experience',
                         'headline_1', 'description_1', 'rsa_headlines', 'ad_type',
                         'search_impression_share', 'search_lost_is_rank', 'search_lost_is_budget',
                         'search_top_is', 'search_abs_top_is', 'device', 'country', 'region', 'city',
                         'search_term_status', 'keyword_status', 'ad_group_name'):
            if extra_key in row and row[extra_key] is not None and extra_key not in g:
                g[extra_key] = row[extra_key]

    # Compute derived metrics
    result = {}
    for key, g in groups.items():
        g['ctr'] = safe_div(g['clicks'], g['impressions']) * 100
        g['cpc'] = safe_div(g['cost'], g['clicks'])
        g['cpa'] = safe_div(g['cost'], g['conversions'])
        g['roas'] = safe_div(g['conversion_value'], g['cost'])
        g['conv_rate'] = safe_div(g['conversions'], g['clicks']) * 100
        result[key] = g

    return result


def aggregate_by_date(rows):
    """Aggregate rows by date."""
    groups = defaultdict(lambda: {
        'impressions': 0, 'clicks': 0, 'cost': 0.0,
        'conversions': 0.0, 'conversion_value': 0.0,
    })
    for row in rows:
        d = row.get('date')
        if d is None:
            continue
        if isinstance(d, datetime):
            d_key = d.strftime('%Y-%m-%d')
        else:
            d_key = str(d)
        g = groups[d_key]
        g['impressions'] += int(get_val(row, 'impressions'))
        g['clicks'] += int(get_val(row, 'clicks'))
        g['cost'] += get_val(row, 'cost')
        g['conversions'] += get_val(row, 'conversions')
        g['conversion_value'] += get_val(row, 'conversion_value')

    result = {}
    for d_key, g in groups.items():
        g['ctr'] = safe_div(g['clicks'], g['impressions']) * 100
        g['cpa'] = safe_div(g['cost'], g['conversions'])
        g['roas'] = safe_div(g['conversion_value'], g['cost'])
        result[d_key] = g

    return dict(sorted(result.items()))


def total_metrics(rows):
    """Compute total metrics across all rows."""
    totals = {'impressions': 0, 'clicks': 0, 'cost': 0.0,
              'conversions': 0.0, 'conversion_value': 0.0,
              'all_conversions': 0.0, 'all_conversion_value': 0.0}
    for row in rows:
        totals['impressions'] += int(get_val(row, 'impressions'))
        totals['clicks'] += int(get_val(row, 'clicks'))
        totals['cost'] += get_val(row, 'cost')
        totals['conversions'] += get_val(row, 'conversions')
        totals['conversion_value'] += get_val(row, 'conversion_value')
        totals['all_conversions'] += get_val(row, 'all_conversions')
        totals['all_conversion_value'] += get_val(row, 'all_conversion_value')
    totals['ctr'] = safe_div(totals['clicks'], totals['impressions']) * 100
    totals['cpc'] = safe_div(totals['cost'], totals['clicks'])
    totals['cpa'] = safe_div(totals['cost'], totals['conversions'])
    totals['roas'] = safe_div(totals['conversion_value'], totals['cost'])
    totals['conv_rate'] = safe_div(totals['conversions'], totals['clicks']) * 100
    return totals


def get_date_range(rows):
    """Get min/max date from rows."""
    dates = []
    for row in rows:
        d = row.get('date')
        if d is not None:
            if isinstance(d, datetime):
                dates.append(d)
            else:
                parsed = parse_date(str(d))
                if parsed:
                    dates.append(parsed)
    if not dates:
        return None, None
    return min(dates), max(dates)


def has_conversion_lag(rows):
    """Check if data includes last 7 days."""
    _, max_date = get_date_range(rows)
    if max_date is None:
        return False
    today = datetime.now()
    return (today - max_date).days <= 7


# ═══════════════════════════════════════════════════════════════
# ANALYSES — LITE (1-18)
# ═══════════════════════════════════════════════════════════════

@safe_analysis
def analysis_01_dashboard(rows, **kwargs):
    """Dashboard ejecutivo."""
    if not rows:
        return None
    totals = total_metrics(rows)
    if totals['impressions'] == 0:
        return None

    date_min, date_max = get_date_range(rows)
    period = ''
    if date_min and date_max:
        period = f"{date_min.strftime('%Y-%m-%d')} → {date_max.strftime('%Y-%m-%d')}"

    # MoM comparison
    mom = None
    if date_min and date_max:
        period_days = (date_max - date_min).days
        if period_days > 7:
            midpoint = date_min + timedelta(days=period_days // 2)
            first_half = [r for r in rows if r.get('date') and isinstance(r['date'], datetime) and r['date'] < midpoint]
            second_half = [r for r in rows if r.get('date') and isinstance(r['date'], datetime) and r['date'] >= midpoint]
            if first_half and second_half:
                t1 = total_metrics(first_half)
                t2 = total_metrics(second_half)
                mom = {}
                for m in ('cost', 'conversions', 'roas', 'cpa'):
                    if t1.get(m, 0) > 0:
                        mom[m] = round((t2.get(m, 0) - t1.get(m, 0)) / t1[m] * 100, 1)

    return {
        'period': period,
        'cost': round(totals['cost'], 2),
        'conversions': round(totals['conversions'], 1),
        'conversion_value': round(totals['conversion_value'], 2),
        'roas': round(totals['roas'], 2),
        'cpa': round(totals['cpa'], 2),
        'impressions': totals['impressions'],
        'clicks': totals['clicks'],
        'ctr': round(totals['ctr'], 2),
        'avg_cpc': round(totals['cpc'], 2),
        'conv_rate': round(totals['conv_rate'], 2),
        'conversion_lag_warning': has_conversion_lag(rows),
        'mom_change': mom,
    }


@safe_analysis
def analysis_02_benchmarks(rows, **kwargs):
    """Semáforo de benchmarks."""
    if not rows:
        return None
    totals = total_metrics(rows)
    if totals['impressions'] == 0:
        return None

    # QS average if keyword data available
    kw_data = kwargs.get('keyword_rows', [])
    avg_qs = None
    if kw_data:
        qs_values = [r['quality_score'] for r in kw_data if r.get('quality_score') is not None and r['quality_score'] > 0]
        if qs_values:
            # Weight by impressions if available
            qs_impr = [(r['quality_score'], get_val(r, 'impressions', 1))
                       for r in kw_data if r.get('quality_score') is not None and r['quality_score'] > 0]
            total_impr = sum(i for _, i in qs_impr)
            if total_impr > 0:
                avg_qs = sum(q * i for q, i in qs_impr) / total_impr
            else:
                avg_qs = sum(qs_values) / len(qs_values)

    # IS average
    is_values = [get_val(r, 'search_impression_share') for r in rows
                 if r.get('search_impression_share') is not None]
    avg_is = sum(is_values) / len(is_values) if is_values else None

    metrics = [
        {'name': 'CTR', 'value': round(totals['ctr'], 2), 'unit': '%', 'status': semaphore_ctr(totals['ctr'])},
        {'name': 'CPC', 'value': round(totals['cpc'], 2), 'unit': kwargs.get('currency', ''), 'status': 'yellow'},
        {'name': 'Conv Rate', 'value': round(totals['conv_rate'], 2), 'unit': '%', 'status': semaphore_conv_rate(totals['conv_rate'])},
        {'name': 'ROAS', 'value': round(totals['roas'], 2), 'unit': 'x', 'status': semaphore_roas(totals['roas'])},
    ]

    if avg_is is not None:
        metrics.append({'name': 'Impression Share', 'value': round(avg_is, 1), 'unit': '%', 'status': semaphore_is(avg_is)})

    if avg_qs is not None:
        metrics.append({'name': 'Quality Score', 'value': round(avg_qs, 1), 'unit': '/10', 'status': semaphore_qs(avg_qs)})

    return {'metrics': metrics}


@safe_analysis
def analysis_03_daily_evolution(rows, **kwargs):
    """Evolución diaria de métricas clave."""
    dates = [r for r in rows if r.get('date') is not None]
    if len(dates) < 3:
        return None

    by_date = aggregate_by_date(rows)
    if len(by_date) < 3:
        return None

    daily = []
    sorted_dates = sorted(by_date.keys())
    max_date = sorted_dates[-1] if sorted_dates else None
    lag_cutoff = None
    if max_date:
        try:
            lag_cutoff = (datetime.strptime(max_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        except ValueError:
            pass

    for d in sorted_dates:
        g = by_date[d]
        entry = {
            'date': d,
            'cost': round(g['cost'], 2),
            'conversions': round(g['conversions'], 1),
            'roas': round(g['roas'], 2),
            'cpa': round(g['cpa'], 2),
            'ctr': round(g['ctr'], 2),
            'conversion_lag_warning': lag_cutoff is not None and d > lag_cutoff,
        }
        daily.append(entry)

    # 7-day moving averages
    ma7 = []
    for i in range(6, len(daily)):
        window = daily[i-6:i+1]
        ma7.append({
            'date': daily[i]['date'],
            'roas_ma7': round(sum(d['roas'] for d in window) / 7, 2),
            'cpa_ma7': round(sum(d['cpa'] for d in window) / 7, 2),
        })

    # Trend
    if len(daily) >= 6:
        first_half = daily[:len(daily)//2]
        second_half = daily[len(daily)//2:]
        avg_roas_first = sum(d['roas'] for d in first_half) / len(first_half)
        avg_roas_second = sum(d['roas'] for d in second_half) / len(second_half)
        if avg_roas_second > avg_roas_first * 1.05:
            trend = 'up'
        elif avg_roas_second < avg_roas_first * 0.95:
            trend = 'down'
        else:
            trend = 'flat'
    else:
        trend = 'flat'

    return {'daily': daily, 'moving_avg_7d': ma7, 'trend': trend}


@safe_analysis
def analysis_04_campaign_performance(rows, **kwargs):
    """Performance por campaña."""
    if not any(r.get('campaign_name') for r in rows):
        return None

    by_campaign = aggregate_by(rows, 'campaign_name')
    if not by_campaign:
        return None

    total_cost = sum(g['cost'] for g in by_campaign.values())

    campaigns = []
    for name, g in sorted(by_campaign.items(), key=lambda x: x[1]['cost'], reverse=True):
        campaigns.append({
            'name': name,
            'type': g.get('campaign_type', 'Unknown'),
            'cost': round(g['cost'], 2),
            'impressions': g['impressions'],
            'clicks': g['clicks'],
            'conversions': round(g['conversions'], 1),
            'conversion_value': round(g['conversion_value'], 2),
            'roas': round(g['roas'], 2),
            'cpa': round(g['cpa'], 2),
            'ctr': round(g['ctr'], 2),
            'cpc': round(g['cpc'], 2),
            'conv_rate': round(g['conv_rate'], 2),
            'roas_status': semaphore_roas(g['roas']),
            'cost_share_pct': round(safe_div(g['cost'], total_cost) * 100, 1),
        })

    return {'campaigns': campaigns}


@safe_analysis
def analysis_05_budget_vs_results(rows, **kwargs):
    """Distribución de budget vs resultados."""
    if not any(r.get('campaign_name') for r in rows):
        return None

    by_campaign = aggregate_by(rows, 'campaign_name')
    if len(by_campaign) < 2:
        return None

    total_cost = sum(g['cost'] for g in by_campaign.values())
    total_revenue = sum(g['conversion_value'] for g in by_campaign.values())

    scatter = []
    gaps = []
    for name, g in by_campaign.items():
        cost_share = safe_div(g['cost'], total_cost) * 100
        rev_share = safe_div(g['conversion_value'], total_revenue) * 100 if total_revenue > 0 else 0
        entry = {
            'campaign': name,
            'cost': round(g['cost'], 2),
            'roas': round(g['roas'], 2),
            'conversions': round(g['conversions'], 1),
            'cost_share_pct': round(cost_share, 1),
            'revenue_share_pct': round(rev_share, 1),
        }
        scatter.append(entry)

        if cost_share > rev_share + 10:
            gaps.append({**entry, 'verdict': 'ineficiente'})
        elif rev_share > cost_share + 10:
            gaps.append({**entry, 'verdict': 'eficiente'})

    scatter.sort(key=lambda x: x['cost'], reverse=True)

    return {'scatter_points': scatter, 'efficiency_gaps': gaps}


@safe_analysis
def analysis_06_smart_bidding(rows, **kwargs):
    """Smart Bidding status y evaluación."""
    if not any(r.get('bid_strategy_type') for r in rows):
        return None

    by_campaign = aggregate_by(rows, 'campaign_name')
    strategies = []
    for name, g in by_campaign.items():
        strategy = g.get('bid_strategy_type')
        if not strategy:
            continue

        # Normalize strategy name
        strategy_display = strategy.replace('TARGET_', 'Target ').replace('MAXIMIZE_', 'Max ').replace('_', ' ').title()

        target = None
        actual = None
        drift = None
        status = 'unknown'

        if 'CPA' in strategy.upper() or 'cpa' in strategy.lower():
            target = g.get('target_cpa')
            actual = g['cpa']
            if target and target > 0:
                drift = round((actual - target) / target * 100, 1)
                if drift < -10:
                    status = 'outperforming'
                elif drift > 20:
                    status = 'underperforming'
                else:
                    status = 'on_target'
        elif 'ROAS' in strategy.upper() or 'roas' in strategy.lower():
            target = g.get('target_roas')
            actual = g['roas']
            if target and target > 0:
                drift = round((actual - target) / target * 100, 1)
                if drift > 10:
                    status = 'outperforming'
                elif drift < -20:
                    status = 'underperforming'
                else:
                    status = 'on_target'

        strategies.append({
            'campaign': name,
            'strategy': strategy_display,
            'target': round(target, 2) if target else None,
            'actual': round(actual, 2) if actual else None,
            'drift_pct': drift,
            'status': status,
        })

    if not strategies:
        return None

    summary = {
        'total': len(strategies),
        'outperforming': sum(1 for s in strategies if s['status'] == 'outperforming'),
        'on_target': sum(1 for s in strategies if s['status'] == 'on_target'),
        'underperforming': sum(1 for s in strategies if s['status'] == 'underperforming'),
    }

    return {'strategies': strategies, 'summary': summary}


@safe_analysis
def analysis_07_quality_score(kw_rows, **kwargs):
    """Quality Score distribution."""
    if not kw_rows:
        return None

    qs_rows = [r for r in kw_rows if r.get('quality_score') is not None and r['quality_score'] > 0]
    if len(qs_rows) < 5:
        return None

    # Histogram
    histogram = []
    for qs in range(1, 11):
        count = sum(1 for r in qs_rows if r['quality_score'] == qs)
        histogram.append({'qs': qs, 'count': count})

    # Weighted average by impressions
    qs_impr = [(r['quality_score'], max(get_val(r, 'impressions'), 1)) for r in qs_rows]
    total_impr = sum(i for _, i in qs_impr)
    avg_qs = sum(q * i for q, i in qs_impr) / total_impr if total_impr > 0 else 0

    # Components breakdown
    components = {}
    for comp in ('expected_ctr', 'ad_relevance', 'landing_page_experience'):
        vals = [r.get(comp) for r in qs_rows if r.get(comp)]
        if vals:
            counts = Counter(str(v).lower().replace('_', ' ') for v in vals)
            components[comp] = {
                'above': counts.get('above average', 0),
                'average': counts.get('average', 0),
                'below': counts.get('below average', 0),
            }

    # Low QS high spend
    low_qs_high_spend = []
    for r in sorted(qs_rows, key=lambda x: get_val(x, 'cost'), reverse=True):
        if r['quality_score'] <= 4 and get_val(r, 'cost') > 0:
            weak = 'unknown'
            for comp in ('expected_ctr', 'ad_relevance', 'landing_page_experience'):
                if r.get(comp) and 'below' in str(r[comp]).lower():
                    weak = comp
                    break
            low_qs_high_spend.append({
                'keyword': r.get('keyword', 'N/A'),
                'qs': r['quality_score'],
                'cost': round(get_val(r, 'cost'), 2),
                'weak_component': weak,
            })
            if len(low_qs_high_spend) >= 10:
                break

    return {
        'histogram': histogram,
        'avg_qs_weighted': round(avg_qs, 1),
        'components': components,
        'low_qs_high_spend': low_qs_high_spend,
    }


@safe_analysis
def analysis_08_top_keywords(kw_rows, **kwargs):
    """Top keywords por conversión."""
    if not kw_rows:
        return None

    converting = [r for r in kw_rows if get_val(r, 'conversions') >= 1]
    if len(converting) < 3:
        return None

    keywords = []
    for r in sorted(converting, key=lambda x: get_val(x, 'conversions'), reverse=True)[:20]:
        conv = get_val(r, 'conversions')
        cost = get_val(r, 'cost')
        clicks = get_val(r, 'clicks')
        impr = get_val(r, 'impressions')
        cpa = safe_div(cost, conv)
        keywords.append({
            'keyword': r.get('keyword', 'N/A'),
            'conversions': round(conv, 1),
            'cost': round(cost, 2),
            'cpa': round(cpa, 2),
            'conv_rate': round(safe_div(conv, clicks) * 100, 2),
            'ctr': round(safe_div(clicks, impr) * 100, 2),
            'cpc': round(safe_div(cost, clicks), 2),
            'quality_score': r.get('quality_score'),
            'cpa_status': semaphore_roas(safe_div(get_val(r, 'conversion_value'), cost)) if cost > 0 else 'gray',
        })

    return {'keywords': keywords}


@safe_analysis
def analysis_09_impression_share(rows, **kwargs):
    """Impression Share analysis."""
    is_rows = [r for r in rows if r.get('search_impression_share') is not None]
    if not is_rows:
        return None

    by_campaign = aggregate_by(rows, 'campaign_name')
    campaigns = []
    for name, g in sorted(by_campaign.items(), key=lambda x: x[1]['cost'], reverse=True):
        is_val = g.get('search_impression_share')
        lost_budget = g.get('search_lost_is_budget')
        lost_rank = g.get('search_lost_is_rank')
        top_is = g.get('search_top_is')
        abs_top_is = g.get('search_abs_top_is')

        if is_val is None:
            continue

        # Diagnosis
        if lost_rank and lost_budget:
            if lost_rank > lost_budget:
                diagnosis = 'Rank loss dominante — mejorar QS o subir bid'
            elif lost_budget > lost_rank:
                diagnosis = 'Budget loss dominante — aumentar presupuesto'
            else:
                diagnosis = 'Pérdida mixta rank + budget'
        else:
            diagnosis = ''

        campaigns.append({
            'campaign': name,
            'is': round(is_val, 1) if is_val else None,
            'lost_budget': round(lost_budget, 1) if lost_budget else None,
            'lost_rank': round(lost_rank, 1) if lost_rank else None,
            'top_is': round(top_is, 1) if top_is else None,
            'abs_top_is': round(abs_top_is, 1) if abs_top_is else None,
            'is_status': semaphore_is(is_val) if is_val else 'gray',
            'diagnosis': diagnosis,
        })

    if not campaigns:
        return None

    avg_is_vals = [c['is'] for c in campaigns if c['is'] is not None]
    account_avg = sum(avg_is_vals) / len(avg_is_vals) if avg_is_vals else None

    return {'campaigns': campaigns, 'account_avg_is': round(account_avg, 1) if account_avg else None}


@safe_analysis
def analysis_10_wasted_spend(st_rows, **kwargs):
    """Wasted spend analysis — search terms sin conversiones."""
    if not st_rows:
        return None

    zero_conv = [r for r in st_rows if get_val(r, 'conversions') == 0 and get_val(r, 'cost') > 0]
    if not zero_conv:
        return None

    total_wasted = sum(get_val(r, 'cost') for r in zero_conv)
    total_spend = sum(get_val(r, 'cost') for r in st_rows)

    top_wasted = sorted(zero_conv, key=lambda x: get_val(x, 'cost'), reverse=True)[:20]
    top_list = [{
        'search_term': r.get('search_term', 'N/A'),
        'cost': round(get_val(r, 'cost'), 2),
        'clicks': int(get_val(r, 'clicks')),
        'conversions': 0,
    } for r in top_wasted]

    return {
        'total_wasted': round(total_wasted, 2),
        'wasted_pct': round(safe_div(total_wasted, total_spend) * 100, 1),
        'top_wasted_terms': top_list,
        'total_zero_conv_terms': len(zero_conv),
    }


@safe_analysis
def analysis_11_keyword_opportunities(st_rows, **kwargs):
    """Oportunidades de keywords — search terms con conversiones no agregados."""
    if not st_rows:
        return None

    opportunities = [r for r in st_rows
                     if get_val(r, 'conversions') >= 1
                     and r.get('search_term_status') not in ('Added', 'ADDED', 'Excluded', 'EXCLUDED')]

    if not opportunities:
        return None

    opps = sorted(opportunities, key=lambda x: get_val(x, 'conversions'), reverse=True)[:20]
    opp_list = []
    for r in opps:
        conv = get_val(r, 'conversions')
        cost = get_val(r, 'cost')
        clicks = get_val(r, 'clicks')
        opp_list.append({
            'search_term': r.get('search_term', 'N/A'),
            'conversions': round(conv, 1),
            'cost': round(cost, 2),
            'cpa': round(safe_div(cost, conv), 2),
            'conv_rate': round(safe_div(conv, clicks) * 100, 2),
            'status': r.get('search_term_status', 'None'),
            'recommendation': 'Agregar como Exact match',
        })

    return {
        'opportunities': opp_list,
        'total_opportunities': len(opportunities),
        'potential_conversions': round(sum(get_val(r, 'conversions') for r in opportunities), 1),
    }


@safe_analysis
def analysis_12_ad_ranking(ad_rows, campaign_rows, **kwargs):
    """Ranking de ads/RSA por eficiencia."""
    source = ad_rows if ad_rows else campaign_rows
    if not source:
        return None

    # Group by ad group + headline
    group_key = 'ad_group_name' if any(r.get('ad_group_name') for r in source) else 'campaign_name'
    converting = [r for r in source if get_val(r, 'conversions') >= 1]
    if not converting:
        # Fall back to all with clicks
        converting = [r for r in source if get_val(r, 'clicks') >= 1]
    if not converting:
        return None

    ads = []
    for r in sorted(converting, key=lambda x: get_val(x, 'conversions'), reverse=True)[:15]:
        conv = get_val(r, 'conversions')
        cost = get_val(r, 'cost')
        clicks = get_val(r, 'clicks')
        impr = get_val(r, 'impressions')
        headline = r.get('headline_1') or r.get('rsa_headlines', '').split('|')[0] if r.get('rsa_headlines') else None
        ads.append({
            'ad_group': r.get(group_key, 'N/A'),
            'headline': headline or 'N/A',
            'impressions': int(impr),
            'clicks': int(clicks),
            'conversions': round(conv, 1),
            'ctr': round(safe_div(clicks, impr) * 100, 2),
            'conv_rate': round(safe_div(conv, clicks) * 100, 2),
            'cpa': round(safe_div(cost, conv), 2),
            'ad_strength': r.get('ad_strength'),
        })

    return {'ads': ads}


@safe_analysis
def analysis_13_ad_strength(ad_rows, campaign_rows, **kwargs):
    """Ad strength distribution."""
    source = ad_rows if ad_rows else campaign_rows
    if not source:
        return None

    with_strength = [r for r in source if r.get('ad_strength')]
    if not with_strength:
        return None

    # Distribution
    strength_groups = defaultdict(list)
    for r in with_strength:
        s = str(r['ad_strength']).strip()
        # Normalize
        s_lower = s.lower()
        if 'excellent' in s_lower:
            s = 'Excellent'
        elif 'good' in s_lower:
            s = 'Good'
        elif 'average' in s_lower:
            s = 'Average'
        elif 'poor' in s_lower:
            s = 'Poor'
        strength_groups[s].append(r)

    total = len(with_strength)
    distribution = []
    for strength in ('Excellent', 'Good', 'Average', 'Poor'):
        group = strength_groups.get(strength, [])
        if not group:
            distribution.append({'strength': strength, 'count': 0, 'pct': 0, 'avg_ctr': None, 'avg_cpa': None})
            continue
        avg_ctr = safe_div(
            sum(get_val(r, 'clicks') for r in group),
            sum(get_val(r, 'impressions') for r in group)
        ) * 100
        total_conv = sum(get_val(r, 'conversions') for r in group)
        total_cost = sum(get_val(r, 'cost') for r in group)
        avg_cpa = safe_div(total_cost, total_conv)
        distribution.append({
            'strength': strength,
            'count': len(group),
            'pct': round(len(group) / total * 100, 0),
            'avg_ctr': round(avg_ctr, 2),
            'avg_cpa': round(avg_cpa, 2) if total_conv > 0 else None,
        })

    # Poor with high spend
    poor = strength_groups.get('Poor', [])
    poor_high_spend = [{
        'ad_group': r.get('ad_group_name', 'N/A'),
        'ad_strength': 'Poor',
        'cost': round(get_val(r, 'cost'), 2),
    } for r in sorted(poor, key=lambda x: get_val(x, 'cost'), reverse=True)[:5]]

    return {'distribution': distribution, 'poor_high_spend': poor_high_spend}


@safe_analysis
def analysis_14_funnel(rows, **kwargs):
    """Funnel completo."""
    totals = total_metrics(rows)
    if totals['impressions'] == 0:
        return None

    steps = [
        {'name': 'Impressions', 'value': totals['impressions'], 'rate_from_prev': None, 'pct_of_top': 100},
        {'name': 'Clicks', 'value': totals['clicks'],
         'rate_from_prev': round(totals['ctr'], 2),
         'pct_of_top': round(safe_div(totals['clicks'], totals['impressions']) * 100, 3)},
        {'name': 'Conversions', 'value': round(totals['conversions'], 1),
         'rate_from_prev': round(totals['conv_rate'], 2),
         'pct_of_top': round(safe_div(totals['conversions'], totals['impressions']) * 100, 4)},
    ]

    return {
        'steps': steps,
        'overall_conversion_rate': round(safe_div(totals['conversions'], totals['impressions']) * 100, 4),
        'cost_per_step': {
            'cpm': round(safe_div(totals['cost'], totals['impressions']) * 1000, 2),
            'cpc': round(totals['cpc'], 2),
            'cpa': round(totals['cpa'], 2),
        },
    }


@safe_analysis
def analysis_15_seasonality(rows, **kwargs):
    """Estacionalidad — día de semana + hora."""
    if not rows:
        return None

    # By day of week
    day_data = defaultdict(lambda: {'cost': 0, 'conversions': 0, 'clicks': 0, 'impressions': 0})
    for r in rows:
        dow = r.get('day_of_week')
        if dow is None and r.get('date') and isinstance(r['date'], datetime):
            dow = r['date'].strftime('%A')
        if dow:
            # Normalize
            dow = str(dow).strip().upper()
            day_map = {'MONDAY': 'Monday', 'TUESDAY': 'Tuesday', 'WEDNESDAY': 'Wednesday',
                       'THURSDAY': 'Thursday', 'FRIDAY': 'Friday', 'SATURDAY': 'Saturday', 'SUNDAY': 'Sunday'}
            dow = day_map.get(dow, dow.title())
            d = day_data[dow]
            d['cost'] += get_val(r, 'cost')
            d['conversions'] += get_val(r, 'conversions')
            d['clicks'] += int(get_val(r, 'clicks'))
            d['impressions'] += int(get_val(r, 'impressions'))

    by_day = []
    for day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'):
        if day in day_data:
            d = day_data[day]
            by_day.append({
                'day': day,
                'cost': round(d['cost'], 2),
                'conversions': round(d['conversions'], 1),
                'cpa': round(safe_div(d['cost'], d['conversions']), 2),
                'ctr': round(safe_div(d['clicks'], d['impressions']) * 100, 2),
            })

    if not by_day:
        return None

    # By hour
    by_hour = []
    hour_data = defaultdict(lambda: {'cost': 0, 'conversions': 0, 'clicks': 0, 'impressions': 0})
    for r in rows:
        h = r.get('hour_of_day')
        if h is not None:
            hd = hour_data[int(h)]
            hd['cost'] += get_val(r, 'cost')
            hd['conversions'] += get_val(r, 'conversions')
            hd['clicks'] += int(get_val(r, 'clicks'))
            hd['impressions'] += int(get_val(r, 'impressions'))

    for h in sorted(hour_data.keys()):
        d = hour_data[h]
        by_hour.append({
            'hour': h,
            'cost': round(d['cost'], 2),
            'conversions': round(d['conversions'], 1),
            'cpa': round(safe_div(d['cost'], d['conversions']), 2),
        })

    # Best/worst
    best_day = min(by_day, key=lambda x: x['cpa'] if x['cpa'] > 0 else 99999)['day'] if by_day else None
    worst_day = max(by_day, key=lambda x: x['cpa'])['day'] if by_day else None

    best_hours = [h['hour'] for h in sorted(by_hour, key=lambda x: x['cpa'] if x['cpa'] > 0 else 99999)[:3]] if by_hour else []
    worst_hours = [h['hour'] for h in sorted(by_hour, key=lambda x: x['cpa'], reverse=True)[:3]] if by_hour else []

    return {
        'by_day': by_day,
        'by_hour': by_hour,
        'best_day': best_day,
        'worst_day': worst_day,
        'best_hours': best_hours,
        'worst_hours': worst_hours,
    }


@safe_analysis
def analysis_16_geo(rows, **kwargs):
    """Performance por ubicación geográfica."""
    # Try most specific first
    geo_col = None
    for col in ('city', 'region', 'country', 'location'):
        if any(r.get(col) for r in rows):
            geo_col = col
            break

    if not geo_col:
        return None

    by_geo = aggregate_by(rows, geo_col)
    if not by_geo:
        return None

    total_cost = sum(g['cost'] for g in by_geo.values())

    locations = []
    for loc, g in sorted(by_geo.items(), key=lambda x: x[1]['conversions'], reverse=True)[:15]:
        locations.append({
            'location': loc,
            'cost': round(g['cost'], 2),
            'conversions': round(g['conversions'], 1),
            'cpa': round(g['cpa'], 2),
            'roas': round(g['roas'], 2),
            'ctr': round(g['ctr'], 2),
            'cost_share_pct': round(safe_div(g['cost'], total_cost) * 100, 1),
            'cpa_status': semaphore_roas(g['roas']),
        })

    return {'locations': locations, 'geo_level': geo_col}


@safe_analysis
def analysis_17_device(rows, **kwargs):
    """Performance por dispositivo."""
    if not any(r.get('device') for r in rows):
        return None

    by_device = aggregate_by(rows, 'device')
    if not by_device:
        return None

    total_cost = sum(g['cost'] for g in by_device.values())
    total_conv = sum(g['conversions'] for g in by_device.values())

    devices = []
    for dev, g in sorted(by_device.items(), key=lambda x: x[1]['cost'], reverse=True):
        # Normalize device name
        dev_name = str(dev).replace('MOBILE', 'Mobile').replace('DESKTOP', 'Desktop').replace('TABLET', 'Tablet')
        dev_name = dev_name.replace('Mobile phones', 'Mobile').replace('Computers', 'Desktop').replace('Tablets', 'Tablet')
        devices.append({
            'device': dev_name,
            'cost': round(g['cost'], 2),
            'impressions': g['impressions'],
            'clicks': g['clicks'],
            'conversions': round(g['conversions'], 1),
            'ctr': round(g['ctr'], 2),
            'cpc': round(g['cpc'], 2),
            'conv_rate': round(g['conv_rate'], 2),
            'cpa': round(g['cpa'], 2),
            'roas': round(g['roas'], 2),
            'cost_share_pct': round(safe_div(g['cost'], total_cost) * 100, 1),
            'conv_share_pct': round(safe_div(g['conversions'], total_conv) * 100, 1) if total_conv > 0 else 0,
        })

    return {'devices': devices}


@safe_analysis
def analysis_18_recommendations(all_results, **kwargs):
    """Top 5 recomendaciones priorizadas — built from all prior analyses."""
    # This analysis is special: Claude generates the recommendations based on all results
    # The script outputs a placeholder that Claude fills in
    return {
        'recommendations': [],
        '_note': 'Claude generates recommendations based on all analysis results',
    }


# ═══════════════════════════════════════════════════════════════
# ANALYSES — FULL ONLY (19-30)
# ═══════════════════════════════════════════════════════════════

@safe_analysis
def analysis_19_pmax_asset_groups(rows, **kwargs):
    """Asset group performance (PMax)."""
    pmax_rows = [r for r in rows if r.get('asset_group_name')]
    if not pmax_rows:
        return None

    by_ag = aggregate_by(pmax_rows, 'asset_group_name')
    if not by_ag:
        return None

    asset_groups = []
    for name, g in sorted(by_ag.items(), key=lambda x: x[1]['conversions'], reverse=True):
        asset_groups.append({
            'name': name,
            'impressions': g['impressions'],
            'clicks': g['clicks'],
            'conversions': round(g['conversions'], 1),
            'cost': round(g['cost'], 2),
            'ctr': round(g['ctr'], 2),
            'cpa': round(g['cpa'], 2),
            'roas': round(g['roas'], 2),
            'ad_strength': g.get('ad_strength'),
        })

    return {'asset_groups': asset_groups}


@safe_analysis
def analysis_20_pmax_ad_strength(rows, **kwargs):
    """Ad strength por asset group (PMax)."""
    pmax_rows = [r for r in rows if r.get('asset_group_name') and r.get('ad_strength')]
    if not pmax_rows:
        return None

    asset_groups = []
    seen = set()
    for r in pmax_rows:
        name = r['asset_group_name']
        if name in seen:
            continue
        seen.add(name)
        strength = str(r['ad_strength']).strip()
        rec = ''
        if 'poor' in strength.lower():
            rec = 'Faltan assets mínimos. Agregar: 5+ headlines, 5+ descriptions, 3+ images, 1+ video'
        elif 'average' in strength.lower():
            rec = 'Agregar más variaciones de headlines y al menos 1 video para mejorar a Good'
        elif 'good' in strength.lower():
            rec = 'Agregar 2+ headlines y 1+ video para alcanzar Excellent'
        else:
            rec = 'Excelente cobertura de assets'

        asset_groups.append({
            'name': name,
            'ad_strength': strength,
            'recommendation': rec,
        })

    return {'asset_groups': asset_groups}


@safe_analysis
def analysis_21_pmax_cannibalization(rows, st_rows, **kwargs):
    """Canibalización PMax vs Search branded."""
    if not st_rows:
        return None
    # This analysis requires brand terms detection — best done by Claude
    return {
        'overlap_terms': [],
        '_note': 'Claude analyzes brand term overlap between PMax and Search campaigns',
    }


@safe_analysis
def analysis_22_learning_period(rows, **kwargs):
    """Learning period status (Smart Bidding)."""
    if not any(r.get('bid_strategy_type') for r in rows):
        return None

    # Need date data to check last 14 days
    date_rows = [r for r in rows if r.get('date') and isinstance(r['date'], datetime)]
    if not date_rows:
        return None

    max_date = max(r['date'] for r in date_rows)
    cutoff_14d = max_date - timedelta(days=14)

    recent = [r for r in date_rows if r['date'] >= cutoff_14d]
    by_campaign = aggregate_by(recent, 'campaign_name')

    campaigns = []
    for name, g in by_campaign.items():
        strategy = g.get('bid_strategy_type')
        if not strategy:
            continue
        conv_14d = g['conversions']
        status = 'learning' if conv_14d < 30 else 'stable'
        est_days = round(safe_div(30 - conv_14d, safe_div(conv_14d, 14)) , 0) if conv_14d < 30 and conv_14d > 0 else (999 if conv_14d == 0 else 0)

        campaigns.append({
            'campaign': name,
            'strategy': str(strategy).replace('TARGET_', 'Target ').replace('_', ' ').title(),
            'conv_last_14d': round(conv_14d, 1),
            'status': status,
            'est_days_remaining': est_days if status == 'learning' else 0,
            'recommendation': f'No editar hasta salir de learning (~{int(est_days)} días)' if status == 'learning' else 'Stable — evaluar performance',
        })

    summary = {
        'total_smart_bidding': len(campaigns),
        'in_learning': sum(1 for c in campaigns if c['status'] == 'learning'),
        'stable': sum(1 for c in campaigns if c['status'] == 'stable'),
    }

    return {'campaigns': campaigns, 'summary': summary}


@safe_analysis
def analysis_23_smart_bidding_drift(rows, **kwargs):
    """Target vs actual performance (drift over time)."""
    if not any(r.get('bid_strategy_type') for r in rows):
        return None

    date_rows = [r for r in rows if r.get('date') and isinstance(r['date'], datetime)]
    if not date_rows:
        return None

    # Group by campaign and week
    campaign_weeks = defaultdict(lambda: defaultdict(lambda: {
        'cost': 0, 'conversions': 0, 'conversion_value': 0
    }))
    campaign_targets = {}

    for r in date_rows:
        name = r.get('campaign_name')
        if not name or not r.get('bid_strategy_type'):
            continue
        week = r['date'].strftime('%Y-W%U')
        cw = campaign_weeks[name][week]
        cw['cost'] += get_val(r, 'cost')
        cw['conversions'] += get_val(r, 'conversions')
        cw['conversion_value'] += get_val(r, 'conversion_value')
        if name not in campaign_targets:
            campaign_targets[name] = {
                'strategy': r.get('bid_strategy_type'),
                'target_cpa': r.get('target_cpa'),
                'target_roas': r.get('target_roas'),
            }

    campaigns = []
    for name, weeks in campaign_weeks.items():
        info = campaign_targets.get(name, {})
        strategy = info.get('strategy', '')
        weekly = []

        for week in sorted(weeks.keys()):
            w = weeks[week]
            if 'CPA' in str(strategy).upper():
                actual = safe_div(w['cost'], w['conversions'])
                target = info.get('target_cpa')
                drift = round(safe_div(actual - target, target) * 100, 1) if target else None
                weekly.append({'week': week, 'actual_cpa': round(actual, 2), 'drift_pct': drift})
            elif 'ROAS' in str(strategy).upper():
                actual = safe_div(w['conversion_value'], w['cost'])
                target = info.get('target_roas')
                drift = round(safe_div(actual - target, target) * 100, 1) if target else None
                weekly.append({'week': week, 'actual_roas': round(actual, 2), 'drift_pct': drift})

        if weekly:
            # Trend
            drifts = [w.get('drift_pct') for w in weekly if w.get('drift_pct') is not None]
            trend = 'stable'
            if len(drifts) >= 2:
                if drifts[-1] < drifts[0]:
                    trend = 'improving' if 'CPA' in str(strategy).upper() else 'worsening'
                elif drifts[-1] > drifts[0]:
                    trend = 'worsening' if 'CPA' in str(strategy).upper() else 'improving'

            campaigns.append({
                'campaign': name,
                'strategy': str(strategy).replace('TARGET_', 'Target ').replace('_', ' ').title(),
                'target': info.get('target_cpa') or info.get('target_roas'),
                'weekly_actuals': weekly,
                'trend': trend,
                'current_drift_pct': drifts[-1] if drifts else None,
            })

    if not campaigns:
        return None

    return {'campaigns': campaigns}


@safe_analysis
def analysis_24_match_type(kw_rows, **kwargs):
    """Match type analysis."""
    if not kw_rows or not any(r.get('match_type') for r in kw_rows):
        return None

    by_match = aggregate_by(kw_rows, 'match_type')
    if len(by_match) < 2:
        return None

    total_cost = sum(g['cost'] for g in by_match.values())
    total_conv = sum(g['conversions'] for g in by_match.values())

    match_types = []
    for mt, g in by_match.items():
        mt_name = str(mt).replace('EXACT', 'Exact').replace('PHRASE', 'Phrase').replace('BROAD', 'Broad').title()
        match_types.append({
            'type': mt_name,
            'keywords': g['_count'],
            'cost': round(g['cost'], 2),
            'conversions': round(g['conversions'], 1),
            'cpa': round(g['cpa'], 2),
            'ctr': round(g['ctr'], 2),
            'conv_rate': round(g['conv_rate'], 2),
            'cost_share_pct': round(safe_div(g['cost'], total_cost) * 100, 1),
            'conv_share_pct': round(safe_div(g['conversions'], total_conv) * 100, 1) if total_conv > 0 else 0,
        })

    return {'match_types': match_types}


@safe_analysis
def analysis_25_negative_gaps(st_rows, **kwargs):
    """Negative keyword coverage gaps."""
    if not st_rows:
        return None

    # Find patterns in zero-conversion terms
    zero_conv = [r for r in st_rows if get_val(r, 'conversions') == 0 and get_val(r, 'cost') > 0]
    if not zero_conv:
        return None

    # Group by common words
    word_costs = defaultdict(lambda: {'cost': 0, 'count': 0})
    for r in zero_conv:
        term = r.get('search_term', '')
        words = str(term).lower().split()
        for word in words:
            if len(word) > 3:  # Skip short words
                wc = word_costs[word]
                wc['cost'] += get_val(r, 'cost')
                wc['count'] += 1

    # Top wasteful patterns
    suggested = sorted(word_costs.items(), key=lambda x: x[1]['cost'], reverse=True)[:15]
    suggestions = [{
        'term': word,
        'occurrences': data['count'],
        'total_cost': round(data['cost'], 2),
        'pattern': 'repeated wasteful term',
    } for word, data in suggested if data['count'] >= 2]

    already_excluded = sum(1 for r in st_rows if r.get('search_term_status') in ('Excluded', 'EXCLUDED'))

    return {
        'suggested_negatives': suggestions,
        'total_potential_savings': round(sum(s['total_cost'] for s in suggestions), 2),
        'already_excluded': already_excluded,
        'new_suggestions': len(suggestions),
    }


@safe_analysis
def analysis_26_ad_copy(ad_rows, **kwargs):
    """Ad copy analysis."""
    if not ad_rows:
        return None

    with_headline = [r for r in ad_rows if r.get('headline_1') or r.get('rsa_headlines')]
    if not with_headline:
        return None

    # Extract unique headlines with performance
    headline_perf = defaultdict(lambda: {'impressions': 0, 'clicks': 0, 'conversions': 0})
    for r in with_headline:
        headlines = []
        if r.get('rsa_headlines'):
            headlines = [h.strip() for h in str(r['rsa_headlines']).split('|') if h.strip()]
        elif r.get('headline_1'):
            headlines = [r['headline_1']]

        for h in headlines:
            hp = headline_perf[h]
            hp['impressions'] += int(get_val(r, 'impressions'))
            hp['clicks'] += int(get_val(r, 'clicks'))
            hp['conversions'] += get_val(r, 'conversions')

    # Top by CTR
    headlines_with_ctr = [
        {'headline': h, 'ctr': round(safe_div(p['clicks'], p['impressions']) * 100, 2), 'impressions': p['impressions']}
        for h, p in headline_perf.items() if p['impressions'] >= 100
    ]
    top_ctr = sorted(headlines_with_ctr, key=lambda x: x['ctr'], reverse=True)[:10]

    # Top by conversions
    headlines_with_conv = [
        {'headline': h, 'conv_rate': round(safe_div(p['conversions'], p['clicks']) * 100, 2), 'conversions': round(p['conversions'], 1)}
        for h, p in headline_perf.items() if p['clicks'] >= 10
    ]
    top_conv = sorted(headlines_with_conv, key=lambda x: x['conversions'], reverse=True)[:10]

    return {
        'top_headlines_ctr': top_ctr,
        'top_headlines_conv': top_conv,
        'patterns': [],  # Claude fills in pattern analysis
    }


@safe_analysis
def analysis_27_conversion_health(rows, **kwargs):
    """Conversion tracking health."""
    totals = total_metrics(rows)
    if totals['conversions'] == 0 and totals['all_conversions'] == 0:
        return None

    primary_pct = safe_div(totals['conversions'], totals['all_conversions']) * 100 if totals['all_conversions'] > 0 else 100
    secondary_only = totals['all_conversions'] - totals['conversions']

    # Conversion lag
    by_date = aggregate_by_date(rows)
    sorted_dates = sorted(by_date.keys())
    lag_info = None
    if len(sorted_dates) >= 14:
        last_7 = [by_date[d] for d in sorted_dates[-7:]]
        earlier = [by_date[d] for d in sorted_dates[:-7]]
        last_7_avg = sum(d['conversions'] for d in last_7) / 7
        earlier_avg = sum(d['conversions'] for d in earlier) / len(earlier)
        lag_ratio = safe_div(last_7_avg, earlier_avg)
        lag_info = {
            'last_7d_daily_avg': round(last_7_avg, 1),
            'period_daily_avg': round(earlier_avg, 1),
            'lag_ratio': round(lag_ratio, 2),
            'status': 'significant_lag' if lag_ratio < 0.65 else ('mild_lag' if lag_ratio < 0.85 else 'normal'),
        }

    vt = sum(get_val(r, 'view_through_conversions') for r in rows)

    return {
        'primary_conversions': round(totals['conversions'], 1),
        'all_conversions': round(totals['all_conversions'], 1),
        'primary_pct': round(primary_pct, 1),
        'secondary_only': round(secondary_only, 1),
        'view_through': round(vt, 1),
        'view_through_pct': round(safe_div(vt, totals['all_conversions']) * 100, 1) if totals['all_conversions'] > 0 else 0,
        'conversion_lag': lag_info,
        'health': 'good' if primary_pct > 50 else 'review_needed',
    }


@safe_analysis
def analysis_28_attribution(rows, **kwargs):
    """Attribution model comparison."""
    # Placeholder — Claude fills in based on campaign types
    by_campaign = aggregate_by(rows, 'campaign_name')
    if not by_campaign:
        return None

    biases = []
    for name, g in by_campaign.items():
        ctype = g.get('campaign_type', 'Unknown')
        if ctype in ('Search',) and 'brand' in name.lower():
            bias = 'Overcounted in Last Click'
            funnel = 'Lower funnel'
        elif ctype in ('Display', 'Video', 'Demand Gen') or 'pmax' in name.lower() or ctype == 'PMax':
            bias = 'Undercounted in Last Click'
            funnel = 'Upper funnel'
        else:
            bias = 'Neutral'
            funnel = 'Mid funnel'

        biases.append({
            'campaign': name,
            'type': funnel,
            'likely_bias': bias,
        })

    return {
        'model_used': 'Estimated (no multi-model data)',
        'campaign_attribution_bias': biases,
    }


@safe_analysis
def analysis_29_auction_insights(rows, **kwargs):
    """Auction insights."""
    auction_rows = [r for r in rows if r.get('competitor_domain')]
    if not auction_rows:
        return None

    by_competitor = defaultdict(lambda: {
        'auction_is': [], 'auction_overlap': [], 'auction_outranking': [],
        'auction_pos_above': [], 'auction_top_rate': [], 'auction_abs_top_rate': [],
    })

    for r in auction_rows:
        comp = r['competitor_domain']
        for field in ('auction_is', 'auction_overlap', 'auction_outranking',
                      'auction_pos_above', 'auction_top_rate', 'auction_abs_top_rate'):
            val = r.get(field)
            if val is not None:
                by_competitor[comp][field].append(val)

    competitors = []
    for comp, data in by_competitor.items():
        avg = lambda vals: round(sum(vals) / len(vals), 1) if vals else None
        overlap = avg(data['auction_overlap'])
        outranking = avg(data['auction_outranking'])
        threat = 'high' if overlap and overlap > 70 and outranking and outranking < 50 else ('medium' if overlap and overlap > 50 else 'low')

        competitors.append({
            'domain': comp,
            'impression_share': avg(data['auction_is']),
            'overlap_rate': overlap,
            'outranking_share': outranking,
            'top_rate': avg(data['auction_top_rate']),
            'abs_top_rate': avg(data['auction_abs_top_rate']),
            'threat_level': threat,
        })

    competitors.sort(key=lambda x: x.get('overlap_rate') or 0, reverse=True)

    # Our IS (from campaign data)
    campaign_rows = kwargs.get('campaign_rows', rows)
    is_vals = [get_val(r, 'search_impression_share') for r in campaign_rows if r.get('search_impression_share')]
    our_is = round(sum(is_vals) / len(is_vals), 1) if is_vals else None

    return {
        'competitors': competitors[:10],
        'our_is': our_is,
        'top_threat': competitors[0]['domain'] if competitors else None,
    }


@safe_analysis
def analysis_30_budget_forecast(rows, **kwargs):
    """Budget forecast y oportunidad de scaling."""
    totals = total_metrics(rows)
    if totals['cost'] == 0:
        return None

    # IS data
    is_vals = [get_val(r, 'search_impression_share') for r in rows if r.get('search_impression_share')]
    lost_budget_vals = [get_val(r, 'search_lost_is_budget') for r in rows if r.get('search_lost_is_budget')]
    lost_rank_vals = [get_val(r, 'search_lost_is_rank') for r in rows if r.get('search_lost_is_rank')]

    if not lost_budget_vals:
        return None

    avg_lost_budget = sum(lost_budget_vals) / len(lost_budget_vals)
    avg_lost_rank = sum(lost_rank_vals) / len(lost_rank_vals) if lost_rank_vals else 0

    # Scaling viability
    viable = avg_lost_rank < 20  # Don't scale if rank loss is high (QS problem)

    # Estimate additional conversions
    date_range = get_date_range(rows)
    days = (date_range[1] - date_range[0]).days + 1 if date_range[0] and date_range[1] else 30
    daily_budget = totals['cost'] / days if days > 0 else 0
    est_additional_conv = totals['conversions'] * (avg_lost_budget / 100) if avg_lost_budget > 0 else 0
    est_additional_cost = totals['cost'] * (avg_lost_budget / 100) if avg_lost_budget > 0 else 0
    est_marginal_cpa = safe_div(est_additional_cost, est_additional_conv)

    # Scenarios
    scenarios = []
    for pct_increase in (10, 25, 50):
        conv_increase = pct_increase * 0.7  # Diminishing returns
        new_cpa = totals['cpa'] * (1 + pct_increase / 100 * 0.15)  # CPA inflation estimate
        scenarios.append({
            'budget_increase_pct': pct_increase,
            'est_conv_increase_pct': round(conv_increase, 0),
            'est_new_cpa': round(new_cpa, 2),
        })

    return {
        'current_daily_budget': round(daily_budget, 2),
        'is_lost_budget': round(avg_lost_budget, 1),
        'is_lost_rank': round(avg_lost_rank, 1),
        'scaling_opportunity': {
            'headroom_pct': round(avg_lost_budget, 1),
            'estimated_additional_conversions': round(est_additional_conv, 0),
            'estimated_additional_cost': round(est_additional_cost, 2),
            'estimated_marginal_cpa': round(est_marginal_cpa, 2),
            'viable': viable,
        },
        'forecast_scenarios': scenarios,
    }


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

LITE_ANALYSES = [
    (1, 'Dashboard ejecutivo', 'Overview', 'campaign'),
    (2, 'Semáforo de benchmarks', 'Overview', 'campaign'),
    (3, 'Evolución diaria de métricas clave', 'Overview', 'campaign'),
    (4, 'Performance por campaña', 'Campañas', 'campaign'),
    (5, 'Distribución de budget vs resultados', 'Campañas', 'campaign'),
    (6, 'Smart Bidding status y evaluación', 'Campañas', 'campaign'),
    (7, 'Quality Score distribution', 'Keywords', 'keyword'),
    (8, 'Top keywords por conversión', 'Keywords', 'keyword'),
    (9, 'Impression Share analysis', 'Keywords', 'campaign'),
    (10, 'Wasted spend analysis', 'Search Terms', 'search_term'),
    (11, 'Oportunidades de keywords', 'Search Terms', 'search_term'),
    (12, 'Ranking de ads/RSA por eficiencia', 'Ads', 'ad'),
    (13, 'Ad strength distribution', 'Ads', 'ad'),
    (14, 'Funnel completo', 'Funnel', 'campaign'),
    (15, 'Estacionalidad', 'Temporal', 'campaign'),
    (16, 'Performance por ubicación geográfica', 'Geo', 'campaign'),
    (17, 'Performance por dispositivo', 'Device', 'campaign'),
    (18, 'Top 5 recomendaciones priorizadas', 'Estratégico', 'special'),
]

FULL_EXTRA = [
    (19, 'Asset group performance (PMax)', 'PMax', 'campaign'),
    (20, 'Ad strength por asset group', 'PMax', 'campaign'),
    (21, 'Canibalización PMax vs Search branded', 'PMax', 'special'),
    (22, 'Learning period status', 'Smart Bidding', 'campaign'),
    (23, 'Target vs actual performance', 'Smart Bidding', 'campaign'),
    (24, 'Match type analysis', 'Keywords', 'keyword'),
    (25, 'Negative keyword coverage gaps', 'Keywords', 'search_term'),
    (26, 'Ad copy analysis', 'Ads', 'ad'),
    (27, 'Conversion tracking health', 'Conversion', 'campaign'),
    (28, 'Attribution model comparison', 'Conversion', 'campaign'),
    (29, 'Auction insights', 'Auction', 'campaign'),
    (30, 'Budget forecast y oportunidad de scaling', 'Estratégico', 'campaign'),
]

ANALYSIS_FUNCTIONS = {
    1: analysis_01_dashboard,
    2: analysis_02_benchmarks,
    3: analysis_03_daily_evolution,
    4: analysis_04_campaign_performance,
    5: analysis_05_budget_vs_results,
    6: analysis_06_smart_bidding,
    7: analysis_07_quality_score,
    8: analysis_08_top_keywords,
    9: analysis_09_impression_share,
    10: analysis_10_wasted_spend,
    11: analysis_11_keyword_opportunities,
    12: analysis_12_ad_ranking,
    13: analysis_13_ad_strength,
    14: analysis_14_funnel,
    15: analysis_15_seasonality,
    16: analysis_16_geo,
    17: analysis_17_device,
    18: analysis_18_recommendations,
    19: analysis_19_pmax_asset_groups,
    20: analysis_20_pmax_ad_strength,
    21: analysis_21_pmax_cannibalization,
    22: analysis_22_learning_period,
    23: analysis_23_smart_bidding_drift,
    24: analysis_24_match_type,
    25: analysis_25_negative_gaps,
    26: analysis_26_ad_copy,
    27: analysis_27_conversion_health,
    28: analysis_28_attribution,
    29: analysis_29_auction_insights,
    30: analysis_30_budget_forecast,
}


def run_analyses(data, mode='lite', currency='auto'):
    """Run all analyses for the given mode."""
    analyses_list = LITE_ANALYSES if mode == 'lite' else LITE_ANALYSES + FULL_EXTRA

    # Separate data by report type
    campaign_rows = data.get('campaign', []) or data.get('json', [])
    keyword_rows = data.get('keyword', [])
    search_term_rows = data.get('search_term', [])
    ad_rows = data.get('ad', [])

    # All rows combined for general metrics
    all_rows = campaign_rows + keyword_rows + search_term_rows + ad_rows

    results = {}
    for num, name, category, source_type in analyses_list:
        print(f"  Running #{num}: {name}...", file=sys.stderr)

        func = ANALYSIS_FUNCTIONS.get(num)
        if not func:
            results[str(num)] = {
                'number': num, 'name': name, 'category': category,
                'data': {'status': 'skipped', 'reason': 'Not implemented'},
            }
            continue

        # Route to correct data source
        if source_type == 'keyword':
            source = keyword_rows if keyword_rows else campaign_rows
            if num == 7:
                result = func(source, currency=currency)
            elif num == 8:
                result = func(source, currency=currency)
            elif num == 24:
                result = func(source)
            else:
                result = func(source)
        elif source_type == 'search_term':
            source = search_term_rows if search_term_rows else []
            result = func(source)
        elif source_type == 'ad':
            if num in (12, 13):
                result = func(ad_rows, campaign_rows)
            elif num == 26:
                result = func(ad_rows)
            else:
                result = func(ad_rows if ad_rows else campaign_rows)
        elif source_type == 'special':
            if num == 18:
                result = func(results)
            elif num == 21:
                result = func(campaign_rows, search_term_rows)
            else:
                result = func(campaign_rows)
        else:
            result = func(campaign_rows, keyword_rows=keyword_rows, currency=currency,
                         campaign_rows=campaign_rows)

        results[str(num)] = {
            'number': num,
            'name': name,
            'category': category,
            'data': result,
        }

    return results


def compute_summary(data, currency):
    """Compute hero metrics for the report."""
    all_rows = []
    for rows in data.values():
        all_rows.extend(rows)

    totals = total_metrics(all_rows)
    date_min, date_max = get_date_range(all_rows)

    # Detect campaign types
    types = set()
    for r in all_rows:
        ct = r.get('campaign_type')
        if ct:
            types.add(ct)

    return {
        'total_cost': round(totals['cost'], 2),
        'total_conversions': round(totals['conversions'], 1),
        'total_conversion_value': round(totals['conversion_value'], 2),
        'roas': round(totals['roas'], 2),
        'cpa': round(totals['cpa'], 2),
        'total_impressions': totals['impressions'],
        'total_clicks': totals['clicks'],
        'ctr': round(totals['ctr'], 2),
        'avg_cpc': round(totals['cpc'], 2),
        'date_min': date_min.strftime('%Y-%m-%d') if date_min else None,
        'date_max': date_max.strftime('%Y-%m-%d') if date_max else None,
        'currency': currency,
        'campaign_types': sorted(list(types)),
        'conversion_lag_warning': has_conversion_lag(all_rows),
        'total_rows': len(all_rows),
    }


def main():
    parser = argparse.ArgumentParser(description='Google Ads Analysis')
    parser.add_argument('--input', required=True, help='Path to CSV, JSON, or directory')
    parser.add_argument('--mode', choices=['lite', 'full'], default='lite', help='Analysis mode')
    parser.add_argument('--currency', default='auto', help='Currency code (ARS, USD, auto)')
    parser.add_argument('--output', required=True, help='Output JSON path')
    args = parser.parse_args()

    # Validate input
    input_path = args.input
    if ',' not in input_path and not os.path.exists(input_path):
        print(f"ERROR: File/directory not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading input: {input_path}", file=sys.stderr)
    data, currency = load_input(input_path, args.currency)

    total_rows = sum(len(rows) for rows in data.values())
    report_types = list(data.keys())
    print(f"Report types: {report_types} | Currency: {currency} | Total rows: {total_rows}", file=sys.stderr)

    if total_rows == 0:
        print("ERROR: No data loaded", file=sys.stderr)
        sys.exit(1)

    print(f"Computing summary...", file=sys.stderr)
    summary = compute_summary(data, currency)

    print(f"Running {args.mode} analyses...", file=sys.stderr)
    analyses = run_analyses(data, args.mode, currency)

    output = {
        'mode': args.mode,
        'currency': currency,
        'report_types': report_types,
        'summary': summary,
        'analyses': analyses,
    }

    # Serialize
    def make_serializable(obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, set):
            return list(obj)
        return obj

    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items()}
        if isinstance(d, list):
            return [clean_dict(v) for v in d]
        return make_serializable(d)

    output = clean_dict(output)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    print(f"Results written to: {args.output}", file=sys.stderr)
    ok_count = sum(1 for a in analyses.values() if a['data'].get('status') == 'ok')
    skip_count = sum(1 for a in analyses.values() if a['data'].get('status') == 'skipped')
    print(f"Done: {ok_count} ok, {skip_count} skipped", file=sys.stderr)


if __name__ == '__main__':
    main()
