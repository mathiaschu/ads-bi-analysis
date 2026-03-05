#!/usr/bin/env python3
# Copyright (c) 2026 Mathias Chu — https://mathiaschu.com
"""
Meta Ads Analysis Script
Generates JSON with all analysis results from Meta Ads CSV or MCP JSON.
Usage: python3 meta_ads_analysis.py --input PATH --mode lite|full --nomenclatura standard|alternative|auto --output PATH
"""

import argparse
import csv
import json
import sys
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import math

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("WARNING: pandas/numpy not found. Install with: pip3 install pandas numpy", file=sys.stderr)
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
# CSV COLUMN MAPPING
# ═══════════════════════════════════════════════════════════════

META_CSV_COLUMNS = {
    'Campaign name': 'campaign_name',
    'Ad set name': 'adset_name',
    'Ad name': 'ad_name',
    'Day': 'date_start',
    'Date': 'date_start',
    'Reporting starts': 'date_start',
    'Reporting ends': 'date_stop',
    'Impressions': 'impressions',
    'Reach': 'reach',
    'Frequency': 'frequency',
    'Clicks (all)': 'clicks',
    'Link clicks': 'link_clicks',
    'CPC (cost per link click)': 'cpc_link',
    'CPC (all)': 'cpc',
    'CPM (cost per 1,000 impressions)': 'cpm',
    'CTR (link click-through rate)': 'ctr_link',
    'CTR (all)': 'ctr',
    'Results': 'results',
    'Cost per result': 'cost_per_result',
    'Result type': 'result_type',
    'Purchases': 'purchases',
    'Purchase ROAS (return on ad spend)': 'purchase_roas',
    'Purchase conversion value': 'purchase_value',
    'Cost per purchase': 'cost_per_purchase',
    'Leads': 'leads',
    'Cost per lead': 'cost_per_lead',
    'ThruPlays': 'thruplay',
    'Video plays at 25%': 'video_p25',
    'Video plays at 50%': 'video_p50',
    'Video plays at 75%': 'video_p75',
    'Video plays at 100%': 'video_p100',
    '3-second video plays': 'video_3s',
    'Quality ranking': 'quality_ranking',
    'Engagement rate ranking': 'engagement_ranking',
    'Conversion rate ranking': 'conversion_ranking',
    'Impression device': 'device',
    'Platform': 'platform',
    'Placement': 'placement',
    'Country': 'country',
    'Region': 'region',
    'Landing page views': 'landing_page_views',
    'Adds to cart': 'add_to_cart',
    'Checkouts initiated': 'checkout_initiated',
    'Website purchases': 'purchases',
    'Outbound clicks': 'outbound_clicks',
    'Outbound CTR': 'outbound_ctr',
    'Cost per ThruPlay': 'cost_per_thruplay',
}

# Also handle "Amount spent" with currency suffix
AMOUNT_SPENT_PATTERNS = [
    'Amount spent',
    'Amount spent (ARS)',
    'Amount spent (USD)',
    'Amount spent (CLP)',
    'Amount spent (MXN)',
    'Amount spent (BRL)',
    'Amount spent (COP)',
    'Amount spent (PEN)',
    'Amount spent (EUR)',
]


# ═══════════════════════════════════════════════════════════════
# NOMENCLATURA PARSING
# ═══════════════════════════════════════════════════════════════

FORMATO_NORMALIZE = {
    'ugc': 'UGC', 'estatico': 'Estático', 'static': 'Estático',
    'estático': 'Estático', 'video': 'Video', 'carrusel': 'Carrusel',
    'carousel': 'Carrusel', 'catálogo': 'Catálogo', 'catalogo': 'Catálogo',
    'catalog': 'Catálogo', 'colección': 'Colección', 'coleccion': 'Colección',
    'collection': 'Colección', 'imagen': 'Estático', 'image': 'Estático',
    'reel': 'Video', 'reels': 'Video', 'dpa': 'Catálogo',
}

ETAPA_NORMALIZE = {
    'tof': 'TOF', 'tofu': 'TOF', 'top': 'TOF', 'prospecting': 'TOF',
    'mof': 'MOF', 'mofu': 'MOF', 'mid': 'MOF', 'consideration': 'MOF',
    'bof': 'BOF', 'bofu': 'BOF', 'bot': 'BOF', 'retargeting': 'BOF',
    'ret': 'BOF', 'rmk': 'BOF', 'remarketing': 'BOF',
}


def detect_nomenclatura(names, format_hint='auto'):
    """Detect nomenclatura format from a list of campaign/ad names."""
    if format_hint != 'auto':
        return format_hint

    pipe_count = sum(1 for n in names if ' | ' in str(n))
    if pipe_count > len(names) * 0.3:
        return 'standard'

    underscore_segments = sum(1 for n in names if len(str(n).split('_')) >= 3)
    etapa_in_underscore = sum(1 for n in names
                              if any(e in str(n).upper().split('_')[0:2]
                                     for e in ['TOF', 'MOF', 'BOF', 'TOFU', 'MOFU', 'BOFU']))
    if underscore_segments > len(names) * 0.3 and etapa_in_underscore > len(names) * 0.2:
        return 'alternative'

    return 'unknown'


def parse_nomenclatura_standard(name):
    """Parse standard format: Producto | Formato | Etapa | Creador | Variacion"""
    parts = [p.strip() for p in str(name).split('|')]
    result = {'producto': None, 'formato': None, 'etapa': None, 'creador': None, 'variacion': None, 'raw': str(name)}
    if len(parts) >= 1:
        result['producto'] = parts[0].strip().title() if parts[0].strip() else None
    if len(parts) >= 2:
        fmt = parts[1].strip().lower()
        result['formato'] = FORMATO_NORMALIZE.get(fmt, parts[1].strip())
    if len(parts) >= 3:
        etapa = parts[2].strip().lower()
        result['etapa'] = ETAPA_NORMALIZE.get(etapa, parts[2].strip().upper())
    if len(parts) >= 4:
        result['creador'] = parts[3].strip().title() if parts[3].strip() else None
    if len(parts) >= 5:
        result['variacion'] = parts[4].strip() if parts[4].strip() else None
    return result


def parse_nomenclatura_alternative(name):
    """Parse alternative format: Etapa_Producto_Formato_Variacion"""
    parts = str(name).split('_')
    result = {'producto': None, 'formato': None, 'etapa': None, 'creador': None, 'variacion': None, 'raw': str(name)}
    if len(parts) >= 1:
        etapa = parts[0].strip().lower()
        result['etapa'] = ETAPA_NORMALIZE.get(etapa, parts[0].strip().upper())
    if len(parts) >= 2:
        result['producto'] = parts[1].strip().replace('-', ' ').title()
    if len(parts) >= 3:
        fmt = parts[2].strip().lower()
        result['formato'] = FORMATO_NORMALIZE.get(fmt, parts[2].strip())
    if len(parts) >= 4:
        result['variacion'] = parts[3].strip()
    return result


def parse_nomenclatura(name, format_type):
    """Parse a name according to detected format."""
    if format_type == 'standard':
        return parse_nomenclatura_standard(name)
    elif format_type == 'alternative':
        return parse_nomenclatura_alternative(name)
    else:
        return {'producto': None, 'formato': None, 'etapa': None, 'creador': None, 'variacion': None, 'raw': str(name)}


# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════

def detect_meta_csv(headers):
    """Check if headers match Meta Ads Manager CSV format."""
    meta_fingerprint = ['Campaign name', 'Impressions', 'Reach']
    matches = sum(1 for h in meta_fingerprint if h in headers)
    return matches >= 2


def load_csv(path):
    """Load Meta Ads Manager CSV export."""
    # Try utf-8 first, then latin-1
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            df = pd.read_csv(path, encoding=encoding, low_memory=False)
            break
        except (UnicodeDecodeError, Exception):
            continue
    else:
        raise ValueError(f"Could not read CSV with any encoding: {path}")

    # Map columns
    rename_map = {}
    for col in df.columns:
        col_stripped = col.strip()
        if col_stripped in META_CSV_COLUMNS:
            rename_map[col] = META_CSV_COLUMNS[col_stripped]
        else:
            # Check amount spent patterns
            for pattern in AMOUNT_SPENT_PATTERNS:
                if col_stripped.startswith('Amount spent'):
                    rename_map[col] = 'spend'
                    break

    df = df.rename(columns=rename_map)

    # Clean numeric columns
    numeric_cols = ['impressions', 'reach', 'frequency', 'spend', 'clicks', 'link_clicks',
                    'cpc', 'cpc_link', 'cpm', 'ctr', 'ctr_link', 'results', 'cost_per_result',
                    'purchases', 'purchase_roas', 'purchase_value', 'cost_per_purchase',
                    'leads', 'cost_per_lead', 'thruplay', 'video_p25', 'video_p50',
                    'video_p75', 'video_p100', 'video_3s', 'landing_page_views',
                    'add_to_cart', 'checkout_initiated', 'outbound_clicks', 'outbound_ctr',
                    'cost_per_thruplay']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '.').str.replace(r'[^\d.\-]', '', regex=True),
                errors='coerce'
            ).fillna(0)

    # Parse dates
    if 'date_start' in df.columns:
        df['date_start'] = pd.to_datetime(df['date_start'], errors='coerce')

    return df


def load_json(path):
    """Load MCP API JSON output."""
    with open(path, 'r') as f:
        data = json.load(f)

    # Handle both list of records and nested format
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and 'data' in data:
        records = data['data']
    else:
        records = [data]

    df = pd.json_normalize(records)

    # Map MCP field names to canonical
    mcp_mapping = {
        'campaign_name': 'campaign_name',
        'adset_name': 'adset_name',
        'ad_name': 'ad_name',
        'date_start': 'date_start',
        'date_stop': 'date_stop',
        'impressions': 'impressions',
        'reach': 'reach',
        'frequency': 'frequency',
        'spend': 'spend',
        'clicks': 'clicks',
        'cpc': 'cpc',
        'cpm': 'cpm',
        'ctr': 'ctr',
        'cpp': 'cpp',
        'actions': 'actions',
        'action_values': 'action_values',
        'cost_per_action_type': 'cost_per_action_type',
        'quality_ranking': 'quality_ranking',
        'engagement_rate_ranking': 'engagement_ranking',
        'conversion_rate_ranking': 'conversion_ranking',
    }

    rename_map = {k: v for k, v in mcp_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Extract purchases from actions array if present
    if 'actions' in df.columns:
        def extract_action(actions, action_type):
            if isinstance(actions, list):
                for a in actions:
                    if a.get('action_type') == action_type:
                        return float(a.get('value', 0))
            return 0.0
        df['purchases'] = df['actions'].apply(lambda x: extract_action(x, 'purchase'))
        df['leads'] = df['actions'].apply(lambda x: extract_action(x, 'lead'))
        df['link_clicks'] = df['actions'].apply(lambda x: extract_action(x, 'link_click'))
        df['landing_page_views'] = df['actions'].apply(lambda x: extract_action(x, 'landing_page_view'))
        df['add_to_cart'] = df['actions'].apply(lambda x: extract_action(x, 'add_to_cart'))
        df['checkout_initiated'] = df['actions'].apply(lambda x: extract_action(x, 'initiate_checkout'))

    if 'action_values' in df.columns:
        def extract_value(vals, action_type):
            if isinstance(vals, list):
                for v in vals:
                    if v.get('action_type') == action_type:
                        return float(v.get('value', 0))
            return 0.0
        df['purchase_value'] = df['action_values'].apply(lambda x: extract_value(x, 'purchase'))

    # Clean numeric
    numeric_cols = ['impressions', 'reach', 'frequency', 'spend', 'clicks', 'link_clicks',
                    'cpc', 'cpm', 'ctr', 'purchases', 'purchase_value', 'leads',
                    'landing_page_views', 'add_to_cart', 'checkout_initiated',
                    'thruplay', 'video_p25', 'video_p50', 'video_p75', 'video_p100', 'video_3s']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'date_start' in df.columns:
        df['date_start'] = pd.to_datetime(df['date_start'], errors='coerce')

    return df


def load_data(path):
    """Auto-detect format and load data."""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.json':
        return load_json(path)
    elif ext in ('.csv', '.tsv', '.txt'):
        return load_csv(path)
    else:
        # Try CSV first, then JSON
        try:
            return load_csv(path)
        except Exception:
            return load_json(path)


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def safe_div(a, b, default=0.0):
    """Safe division avoiding ZeroDivisionError."""
    if b == 0 or pd.isna(b):
        return default
    return a / b


def weighted_avg(values, weights):
    """Weighted average."""
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / total_weight


def semaphore(value, thresholds, reverse=False):
    """Return semaphore color based on thresholds.
    thresholds = (green_threshold, yellow_threshold)
    reverse=True means lower is better (e.g., frequency, CPA)
    """
    green_t, yellow_t = thresholds
    if reverse:
        if value <= green_t:
            return 'green'
        elif value <= yellow_t:
            return 'yellow'
        else:
            return 'red'
    else:
        if value >= green_t:
            return 'green'
        elif value >= yellow_t:
            return 'yellow'
        else:
            return 'red'


def fmt_currency(val, decimals=0):
    """Format as currency string."""
    if pd.isna(val):
        return '$0'
    if decimals == 0:
        return f"${val:,.0f}".replace(',', '.')
    return f"${val:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def fmt_pct(val, decimals=1):
    """Format as percentage."""
    if pd.isna(val):
        return '0.0%'
    return f"{val:.{decimals}f}%"


def fmt_number(val, decimals=0):
    """Format number with thousands separator."""
    if pd.isna(val):
        return '0'
    if decimals == 0:
        return f"{val:,.0f}".replace(',', '.')
    return f"{val:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def compute_roas(df_slice):
    """Compute ROAS from a dataframe slice."""
    total_value = df_slice['purchase_value'].sum() if 'purchase_value' in df_slice.columns else 0
    total_spend = df_slice['spend'].sum() if 'spend' in df_slice.columns else 0
    return safe_div(total_value, total_spend)


def compute_cpa(df_slice):
    """Compute CPA (cost per purchase)."""
    total_spend = df_slice['spend'].sum() if 'spend' in df_slice.columns else 0
    total_purchases = df_slice['purchases'].sum() if 'purchases' in df_slice.columns else 0
    return safe_div(total_spend, total_purchases)


def compute_ctr_weighted(df_slice):
    """Compute CTR weighted by impressions."""
    if 'clicks' not in df_slice.columns or 'impressions' not in df_slice.columns:
        return 0.0
    total_clicks = df_slice['clicks'].sum()
    total_imps = df_slice['impressions'].sum()
    return safe_div(total_clicks * 100, total_imps)


def compute_cpm_weighted(df_slice):
    """Compute CPM weighted by impressions."""
    if 'spend' not in df_slice.columns or 'impressions' not in df_slice.columns:
        return 0.0
    total_spend = df_slice['spend'].sum()
    total_imps = df_slice['impressions'].sum()
    return safe_div(total_spend * 1000, total_imps)


def has_columns(df, cols):
    """Check if dataframe has all required columns."""
    return all(c in df.columns for c in cols)


def skip_result(analysis_id, title, category, reason):
    """Return a skipped analysis result."""
    return {
        'id': analysis_id,
        'title': title,
        'category': category,
        'status': 'skipped',
        'skip_reason': reason,
        'data': {},
        'insight': '',
        'recommendation': ''
    }


# ═══════════════════════════════════════════════════════════════
# ANALYSES — LITE (1-18)
# ═══════════════════════════════════════════════════════════════

def analysis_01_dashboard(df):
    """#1 Dashboard ejecutivo"""
    title = "Dashboard Ejecutivo"
    cat = "Overview"
    try:
        total_spend = df['spend'].sum() if 'spend' in df.columns else 0
        total_purchases = df['purchases'].sum() if 'purchases' in df.columns else 0
        total_revenue = df['purchase_value'].sum() if 'purchase_value' in df.columns else 0
        total_imps = df['impressions'].sum() if 'impressions' in df.columns else 0
        total_reach = df['reach'].sum() if 'reach' in df.columns else 0
        total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0
        total_link_clicks = df['link_clicks'].sum() if 'link_clicks' in df.columns else 0

        roas = safe_div(total_revenue, total_spend)
        cpa = safe_div(total_spend, total_purchases)
        ctr = safe_div(total_clicks * 100, total_imps)
        cpm = safe_div(total_spend * 1000, total_imps)
        avg_freq = safe_div(total_imps, total_reach)

        # Date range
        date_min = df['date_start'].min() if 'date_start' in df.columns else None
        date_max = df['date_start'].max() if 'date_start' in df.columns else None

        return {
            'id': 1, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'spend': round(total_spend, 2),
                'purchases': int(total_purchases),
                'revenue': round(total_revenue, 2),
                'roas': round(roas, 2),
                'cpa': round(cpa, 2),
                'impressions': int(total_imps),
                'reach': int(total_reach),
                'clicks': int(total_clicks),
                'link_clicks': int(total_link_clicks),
                'ctr': round(ctr, 2),
                'cpm': round(cpm, 2),
                'frequency': round(avg_freq, 2),
                'date_min': str(date_min.date()) if date_min and not pd.isna(date_min) else '',
                'date_max': str(date_max.date()) if date_max and not pd.isna(date_max) else '',
                'num_campaigns': df['campaign_name'].nunique() if 'campaign_name' in df.columns else 0,
                'num_adsets': df['adset_name'].nunique() if 'adset_name' in df.columns else 0,
                'num_ads': df['ad_name'].nunique() if 'ad_name' in df.columns else 0,
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(1, title, cat, str(e))


def analysis_02_benchmarks(df):
    """#2 Semáforo de benchmarks"""
    title = "Semáforo de Benchmarks AR/LATAM"
    cat = "Overview"
    try:
        total_imps = df['impressions'].sum()
        total_clicks = df['clicks'].sum()
        total_spend = df['spend'].sum()
        total_reach = df['reach'].sum() if 'reach' in df.columns else 0
        total_purchases = df['purchases'].sum() if 'purchases' in df.columns else 0
        total_revenue = df['purchase_value'].sum() if 'purchase_value' in df.columns else 0
        total_link_clicks = df['link_clicks'].sum() if 'link_clicks' in df.columns else 0

        ctr = safe_div(total_clicks * 100, total_imps)
        cpm = safe_div(total_spend * 1000, total_imps)
        freq = safe_div(total_imps, total_reach) if total_reach > 0 else 0
        roas = safe_div(total_revenue, total_spend)
        cpc = safe_div(total_spend, total_link_clicks)
        cpa = safe_div(total_spend, total_purchases)

        metrics = [
            {'metric': 'CTR (all)', 'value': round(ctr, 2), 'unit': '%',
             'semaphore': semaphore(ctr, (2.0, 1.0)),
             'benchmark': '> 2% verde | 1-2% amarillo | < 1% rojo'},
            {'metric': 'CPM', 'value': round(cpm, 2), 'unit': '$',
             'semaphore': 'contextual',
             'benchmark': 'Contextual por vertical'},
            {'metric': 'Frecuencia', 'value': round(freq, 2), 'unit': 'x',
             'semaphore': semaphore(freq, (3.0, 5.0), reverse=True),
             'benchmark': '< 3 verde | 3-5 amarillo | > 5 rojo'},
            {'metric': 'ROAS', 'value': round(roas, 2), 'unit': 'x',
             'semaphore': semaphore(roas, (3.0, 1.5)),
             'benchmark': '> 3x verde | 1.5-3x amarillo | < 1.5x rojo'},
            {'metric': 'CPC (Link Click)', 'value': round(cpc, 2), 'unit': '$',
             'semaphore': 'contextual',
             'benchmark': 'Contextual por vertical'},
            {'metric': 'CPA (Purchase)', 'value': round(cpa, 2), 'unit': '$',
             'semaphore': 'contextual',
             'benchmark': 'Contextual por vertical y ticket promedio'},
        ]

        return {
            'id': 2, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'metrics': metrics},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(2, title, cat, str(e))


def analysis_03_daily_evolution(df):
    """#3 Evolución diaria"""
    title = "Evolución Diaria de Métricas Clave"
    cat = "Overview"
    if 'date_start' not in df.columns:
        return skip_result(3, title, cat, "No date column found")
    try:
        daily = df.groupby('date_start').agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
            clicks=('clicks', 'sum') if 'clicks' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        daily['roas'] = daily.apply(lambda r: safe_div(r['purchase_value'], r['spend']), axis=1)
        daily['cpa'] = daily.apply(lambda r: safe_div(r['spend'], r['purchases']), axis=1)
        daily['ctr'] = daily.apply(lambda r: safe_div(r['clicks'] * 100, r['impressions']), axis=1)
        daily['cpm'] = daily.apply(lambda r: safe_div(r['spend'] * 1000, r['impressions']), axis=1)

        daily = daily.sort_values('date_start')
        rows = []
        for _, r in daily.iterrows():
            rows.append({
                'date': str(r['date_start'].date()) if not pd.isna(r['date_start']) else '',
                'spend': round(r['spend'], 2),
                'roas': round(r['roas'], 2),
                'cpa': round(r['cpa'], 2),
                'purchases': int(r['purchases']),
                'ctr': round(r['ctr'], 2),
                'cpm': round(r['cpm'], 2),
            })

        return {
            'id': 3, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'daily': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(3, title, cat, str(e))


def analysis_04_campaigns(df):
    """#4 Performance por campaña"""
    title = "Performance por Campaña"
    cat = "Campañas"
    if 'campaign_name' not in df.columns:
        return skip_result(4, title, cat, "No campaign_name column")
    try:
        camps = df.groupby('campaign_name').agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            clicks=('clicks', 'sum') if 'clicks' in df.columns else ('spend', lambda x: 0),
            link_clicks=('link_clicks', 'sum') if 'link_clicks' in df.columns else ('spend', lambda x: 0),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
            reach=('reach', 'sum') if 'reach' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        camps['roas'] = camps.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        camps['cpa'] = camps.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        camps['ctr'] = camps.apply(lambda r: round(safe_div(r['clicks'] * 100, r['impressions']), 2), axis=1)
        camps['cpm'] = camps.apply(lambda r: round(safe_div(r['spend'] * 1000, r['impressions']), 2), axis=1)
        camps['freq'] = camps.apply(lambda r: round(safe_div(r['impressions'], r['reach']), 2), axis=1)

        camps = camps.sort_values('spend', ascending=False)
        rows = []
        for _, r in camps.iterrows():
            rows.append({
                'campaign': r['campaign_name'],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'revenue': round(r['purchase_value'], 2),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
                'cpm': r['cpm'],
                'frequency': r['freq'],
                'roas_semaphore': semaphore(r['roas'], (3.0, 1.5)),
                'ctr_semaphore': semaphore(r['ctr'], (2.0, 1.0)),
                'freq_semaphore': semaphore(r['freq'], (3.0, 5.0), reverse=True),
            })

        return {
            'id': 4, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'campaigns': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(4, title, cat, str(e))


def analysis_05_budget_distribution(df):
    """#5 Budget vs resultados"""
    title = "Distribución de Budget vs Resultados"
    cat = "Campañas"
    if not has_columns(df, ['campaign_name', 'spend']):
        return skip_result(5, title, cat, "Missing campaign_name or spend")
    try:
        camps = df.groupby('campaign_name').agg(
            spend=('spend', 'sum'),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        total_spend = camps['spend'].sum()
        total_purchases = camps['purchases'].sum()

        camps['roas'] = camps.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        camps['spend_pct'] = camps.apply(lambda r: round(safe_div(r['spend'] * 100, total_spend), 1), axis=1)
        camps['purchases_pct'] = camps.apply(lambda r: round(safe_div(r['purchases'] * 100, total_purchases), 1) if total_purchases > 0 else 0, axis=1)

        rows = []
        for _, r in camps.iterrows():
            rows.append({
                'campaign': r['campaign_name'],
                'spend': round(r['spend'], 2),
                'spend_pct': r['spend_pct'],
                'purchases': int(r['purchases']),
                'purchases_pct': r['purchases_pct'],
                'roas': r['roas'],
                'efficiency': 'over' if r['spend_pct'] > r['purchases_pct'] + 5 else ('under' if r['purchases_pct'] > r['spend_pct'] + 5 else 'balanced'),
            })

        return {
            'id': 5, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'distribution': rows, 'total_spend': round(total_spend, 2), 'total_purchases': int(total_purchases)},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(5, title, cat, str(e))


def analysis_06_learning_phase(df):
    """#6 Learning Phase status"""
    title = "Learning Phase Status"
    cat = "Campañas"
    if 'adset_name' not in df.columns:
        return skip_result(6, title, cat, "No adset_name column")
    try:
        adsets = df.groupby('adset_name').agg(
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            leads=('leads', 'sum') if 'leads' in df.columns else ('spend', lambda x: 0),
            spend=('spend', 'sum'),
            days=('date_start', 'nunique') if 'date_start' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        adsets['optimization_events'] = adsets['purchases'] + adsets['leads']
        adsets['status'] = adsets['optimization_events'].apply(
            lambda x: 'active' if x >= 50 else ('learning' if x >= 10 else 'learning_limited')
        )

        rows = []
        for _, r in adsets.iterrows():
            rows.append({
                'adset': r['adset_name'],
                'optimization_events': int(r['optimization_events']),
                'spend': round(r['spend'], 2),
                'days': int(r['days']),
                'status': r['status'],
                'events_needed': max(0, 50 - int(r['optimization_events'])),
            })

        summary = {
            'total': len(rows),
            'active': sum(1 for r in rows if r['status'] == 'active'),
            'learning': sum(1 for r in rows if r['status'] == 'learning'),
            'learning_limited': sum(1 for r in rows if r['status'] == 'learning_limited'),
        }

        return {
            'id': 6, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'adsets': rows, 'summary': summary},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(6, title, cat, str(e))


def analysis_07_adsets(df):
    """#7 Performance por ad set"""
    title = "Performance por Ad Set"
    cat = "Ad Sets"
    if 'adset_name' not in df.columns:
        return skip_result(7, title, cat, "No adset_name column")
    try:
        adsets = df.groupby('adset_name').agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            clicks=('clicks', 'sum') if 'clicks' in df.columns else ('spend', lambda x: 0),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
            reach=('reach', 'sum') if 'reach' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        adsets['roas'] = adsets.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        adsets['cpa'] = adsets.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        adsets['ctr'] = adsets.apply(lambda r: round(safe_div(r['clicks'] * 100, r['impressions']), 2), axis=1)
        adsets['cpm'] = adsets.apply(lambda r: round(safe_div(r['spend'] * 1000, r['impressions']), 2), axis=1)

        adsets = adsets.sort_values('spend', ascending=False)
        avg_cpa = safe_div(adsets['spend'].sum(), adsets['purchases'].sum())

        rows = []
        for _, r in adsets.iterrows():
            rows.append({
                'adset': r['adset_name'],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'revenue': round(r['purchase_value'], 2),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
                'cpm': r['cpm'],
                'breakdown_warning': r['cpa'] > avg_cpa * 1.3 if avg_cpa > 0 else False,
            })

        return {
            'id': 7, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'adsets': rows,
                'avg_cpa': round(avg_cpa, 2),
                'breakdown_note': 'Ad sets con CPA superior al promedio NO necesariamente son ineficientes. El Breakdown Effect puede hacer que su CPA marginal sea inferior. Ver meta-ads-analyzer/references/breakdown_effect.md'
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(7, title, cat, str(e))


def analysis_08_audiences(df):
    """#8 Análisis de audiencias"""
    title = "Análisis de Audiencias"
    cat = "Ad Sets"
    if 'adset_name' not in df.columns:
        return skip_result(8, title, cat, "No adset_name column")
    try:
        # Group by adset and compute metrics
        adsets = df.groupby('adset_name').agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
            reach=('reach', 'sum') if 'reach' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        adsets['roas'] = adsets.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        adsets['cpa'] = adsets.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        adsets['conv_rate'] = adsets.apply(lambda r: round(safe_div(r['purchases'] * 100, r['reach']), 4), axis=1)

        adsets = adsets.sort_values('roas', ascending=False)
        rows = []
        for _, r in adsets.iterrows():
            rows.append({
                'audience': r['adset_name'],
                'spend': round(r['spend'], 2),
                'reach': int(r['reach']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'conv_rate': r['conv_rate'],
            })

        return {
            'id': 8, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'audiences': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(8, title, cat, str(e))


def analysis_09_ads_ranking(df):
    """#9 Ranking de ads"""
    title = "Ranking de Ads por Eficiencia"
    cat = "Ads"
    if 'ad_name' not in df.columns:
        return skip_result(9, title, cat, "No ad_name column")
    try:
        ads = df.groupby('ad_name').agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            clicks=('clicks', 'sum') if 'clicks' in df.columns else ('spend', lambda x: 0),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        ads['roas'] = ads.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        ads['cpa'] = ads.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        ads['ctr'] = ads.apply(lambda r: round(safe_div(r['clicks'] * 100, r['impressions']), 2), axis=1)

        # Score: normalize ROAS (higher=better), CPA (lower=better), CTR (higher=better)
        max_roas = ads['roas'].max() if ads['roas'].max() > 0 else 1
        min_cpa = ads[ads['cpa'] > 0]['cpa'].min() if (ads['cpa'] > 0).any() else 1
        max_ctr = ads['ctr'].max() if ads['ctr'].max() > 0 else 1

        ads['score'] = (
            (ads['roas'] / max_roas) * 0.4 +
            (1 - ads['cpa'].clip(0, min_cpa * 10) / (min_cpa * 10)) * 0.35 +
            (ads['ctr'] / max_ctr) * 0.25
        )
        ads = ads.sort_values('score', ascending=False)

        rows = []
        for rank, (_, r) in enumerate(ads.head(20).iterrows(), 1):
            rows.append({
                'rank': rank,
                'ad': r['ad_name'],
                'spend': round(r['spend'], 2),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
                'score': round(r['score'], 3),
            })

        return {
            'id': 9, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'ads': rows, 'total_ads': len(ads)},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(9, title, cat, str(e))


def analysis_10_creative_fatigue(df):
    """#10 Creative fatigue detection"""
    title = "Creative Fatigue Detection"
    cat = "Ads"
    if not has_columns(df, ['ad_name', 'date_start']):
        return skip_result(10, title, cat, "Missing ad_name or date_start")
    try:
        # For each ad, compute frequency and CTR over time
        ad_daily = df.groupby(['ad_name', 'date_start']).agg(
            impressions=('impressions', 'sum'),
            clicks=('clicks', 'sum') if 'clicks' in df.columns else ('impressions', lambda x: 0),
            reach=('reach', 'sum') if 'reach' in df.columns else ('impressions', lambda x: 0),
        ).reset_index()

        ad_daily['ctr'] = ad_daily.apply(lambda r: safe_div(r['clicks'] * 100, r['impressions']), axis=1)
        ad_daily['freq'] = ad_daily.apply(lambda r: safe_div(r['impressions'], r['reach']) if r['reach'] > 0 else 0, axis=1)

        fatigued = []
        for ad_name in ad_daily['ad_name'].unique():
            ad_data = ad_daily[ad_daily['ad_name'] == ad_name].sort_values('date_start')
            if len(ad_data) < 5:
                continue

            # Split into first half and second half
            mid = len(ad_data) // 2
            first_half = ad_data.iloc[:mid]
            second_half = ad_data.iloc[mid:]

            ctr_first = safe_div(first_half['clicks'].sum() * 100, first_half['impressions'].sum())
            ctr_second = safe_div(second_half['clicks'].sum() * 100, second_half['impressions'].sum())
            freq_avg = safe_div(ad_data['impressions'].sum(), ad_data['reach'].sum()) if 'reach' in ad_data.columns else 0

            ctr_change = safe_div((ctr_second - ctr_first) * 100, ctr_first) if ctr_first > 0 else 0

            if ctr_change < -20 or freq_avg > 4:
                fatigued.append({
                    'ad': ad_name,
                    'ctr_first_half': round(ctr_first, 2),
                    'ctr_second_half': round(ctr_second, 2),
                    'ctr_change_pct': round(ctr_change, 1),
                    'avg_frequency': round(freq_avg, 2),
                    'days_active': len(ad_data),
                    'fatigue_signals': [],
                })
                if ctr_change < -20:
                    fatigued[-1]['fatigue_signals'].append(f'CTR cayó {abs(round(ctr_change,1))}%')
                if freq_avg > 4:
                    fatigued[-1]['fatigue_signals'].append(f'Frecuencia alta: {round(freq_avg,1)}x')

        fatigued.sort(key=lambda x: x['ctr_change_pct'])

        return {
            'id': 10, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'fatigued_ads': fatigued[:15], 'total_analyzed': ad_daily['ad_name'].nunique()},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(10, title, cat, str(e))


def analysis_11_funnel(df):
    """#11 Funnel completo"""
    title = "Funnel Completo"
    cat = "Funnel"
    try:
        total_imps = df['impressions'].sum() if 'impressions' in df.columns else 0
        total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0
        total_link_clicks = df['link_clicks'].sum() if 'link_clicks' in df.columns else 0
        total_lpv = df['landing_page_views'].sum() if 'landing_page_views' in df.columns else 0
        total_atc = df['add_to_cart'].sum() if 'add_to_cart' in df.columns else 0
        total_ic = df['checkout_initiated'].sum() if 'checkout_initiated' in df.columns else 0
        total_purchases = df['purchases'].sum() if 'purchases' in df.columns else 0

        stages = [
            {'stage': 'Impressions', 'value': int(total_imps), 'pct': 100.0},
            {'stage': 'Clicks (all)', 'value': int(total_clicks), 'pct': round(safe_div(total_clicks * 100, total_imps), 2)},
            {'stage': 'Link Clicks', 'value': int(total_link_clicks), 'pct': round(safe_div(total_link_clicks * 100, total_imps), 2)},
        ]
        if total_lpv > 0:
            stages.append({'stage': 'Landing Page Views', 'value': int(total_lpv), 'pct': round(safe_div(total_lpv * 100, total_imps), 2)})
        if total_atc > 0:
            stages.append({'stage': 'Add to Cart', 'value': int(total_atc), 'pct': round(safe_div(total_atc * 100, total_imps), 2)})
        if total_ic > 0:
            stages.append({'stage': 'Checkout Initiated', 'value': int(total_ic), 'pct': round(safe_div(total_ic * 100, total_imps), 2)})
        stages.append({'stage': 'Purchases', 'value': int(total_purchases), 'pct': round(safe_div(total_purchases * 100, total_imps), 4)})

        return {
            'id': 11, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'funnel': stages},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(11, title, cat, str(e))


def analysis_12_dropoff(df):
    """#12 Drop-off analysis"""
    title = "Drop-off Analysis por Etapa"
    cat = "Funnel"
    try:
        total_imps = df['impressions'].sum() if 'impressions' in df.columns else 0
        total_clicks = df['link_clicks'].sum() if 'link_clicks' in df.columns else df['clicks'].sum() if 'clicks' in df.columns else 0
        total_lpv = df['landing_page_views'].sum() if 'landing_page_views' in df.columns else 0
        total_atc = df['add_to_cart'].sum() if 'add_to_cart' in df.columns else 0
        total_ic = df['checkout_initiated'].sum() if 'checkout_initiated' in df.columns else 0
        total_purchases = df['purchases'].sum() if 'purchases' in df.columns else 0

        transitions = []
        pairs = [
            ('Impressions → Clicks', total_imps, total_clicks),
            ('Clicks → Landing Page Views', total_clicks, total_lpv),
            ('Landing Page Views → Add to Cart', total_lpv, total_atc),
            ('Add to Cart → Checkout', total_atc, total_ic),
            ('Checkout → Purchase', total_ic, total_purchases),
        ]
        for label, prev, curr in pairs:
            if prev > 0 and curr > 0:
                conv = round(safe_div(curr * 100, prev), 2)
                drop = round(100 - conv, 2)
                transitions.append({
                    'transition': label,
                    'from_value': int(prev),
                    'to_value': int(curr),
                    'conversion_rate': conv,
                    'dropoff_rate': drop,
                })

        return {
            'id': 12, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'transitions': transitions},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(12, title, cat, str(e))


def analysis_13_seasonality(df):
    """#13 Estacionalidad"""
    title = "Estacionalidad (Día de Semana)"
    cat = "Temporal"
    if 'date_start' not in df.columns:
        return skip_result(13, title, cat, "No date column")
    try:
        df_copy = df.copy()
        df_copy['dow'] = df_copy['date_start'].dt.dayofweek
        df_copy['dow_name'] = df_copy['date_start'].dt.day_name()

        dow = df_copy.groupby(['dow', 'dow_name']).agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            purchases=('purchases', 'sum') if 'purchases' in df_copy.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df_copy.columns else ('spend', lambda x: 0),
        ).reset_index().sort_values('dow')

        dow['roas'] = dow.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        dow['cpa'] = dow.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        dow['cpm'] = dow.apply(lambda r: round(safe_div(r['spend'] * 1000, r['impressions']), 2), axis=1)

        rows = []
        for _, r in dow.iterrows():
            rows.append({
                'day': r['dow_name'],
                'day_num': int(r['dow']),
                'spend': round(r['spend'], 2),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'cpm': r['cpm'],
            })

        best_day = max(rows, key=lambda x: x['roas']) if rows else None
        worst_day = min(rows, key=lambda x: x['roas']) if rows else None

        return {
            'id': 13, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'by_day': rows,
                'best_day': best_day['day'] if best_day else '',
                'worst_day': worst_day['day'] if worst_day else '',
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(13, title, cat, str(e))


def analysis_14_trend(df):
    """#14 Tendencia CPA/ROAS"""
    title = "Tendencia de CPA/ROAS"
    cat = "Temporal"
    if 'date_start' not in df.columns:
        return skip_result(14, title, cat, "No date column")
    try:
        daily = df.groupby('date_start').agg(
            spend=('spend', 'sum'),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
        ).reset_index().sort_values('date_start')

        if len(daily) < 7:
            return skip_result(14, title, cat, "Not enough data points for trend analysis")

        # Compute rolling 7-day ROAS and CPA
        daily['roas_7d'] = daily.apply(lambda r: safe_div(r['purchase_value'], r['spend']), axis=1)
        daily['cpa_7d'] = daily.apply(lambda r: safe_div(r['spend'], r['purchases']), axis=1)

        # Compute periods
        max_date = daily['date_start'].max()
        periods = {}
        for days, label in [(30, 'last_30d'), (60, 'last_60d'), (90, 'last_90d')]:
            cutoff = max_date - timedelta(days=days)
            period_data = daily[daily['date_start'] >= cutoff]
            if len(period_data) > 0:
                periods[label] = {
                    'roas': round(safe_div(period_data['purchase_value'].sum(), period_data['spend'].sum()), 2),
                    'cpa': round(safe_div(period_data['spend'].sum(), period_data['purchases'].sum()), 2),
                    'spend': round(period_data['spend'].sum(), 2),
                    'purchases': int(period_data['purchases'].sum()),
                    'days': len(period_data),
                }

        # Trend direction (last 7 days vs previous 7 days)
        if len(daily) >= 14:
            last_7 = daily.tail(7)
            prev_7 = daily.iloc[-14:-7]
            roas_last = safe_div(last_7['purchase_value'].sum(), last_7['spend'].sum())
            roas_prev = safe_div(prev_7['purchase_value'].sum(), prev_7['spend'].sum())
            roas_trend = 'improving' if roas_last > roas_prev else ('declining' if roas_last < roas_prev else 'stable')
        else:
            roas_trend = 'insufficient_data'

        return {
            'id': 14, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'periods': periods, 'trend': roas_trend},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(14, title, cat, str(e))


def analysis_15_geo(df):
    """#15 Performance por región/país"""
    title = "Performance por Región"
    cat = "Geo"
    geo_col = None
    if 'region' in df.columns and df['region'].notna().sum() > 0:
        geo_col = 'region'
    elif 'country' in df.columns and df['country'].notna().sum() > 0:
        geo_col = 'country'

    if geo_col is None:
        return skip_result(15, title, cat, "No geographic data available")
    try:
        geo = df.groupby(geo_col).agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        geo['roas'] = geo.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        geo['cpa'] = geo.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        geo['cpm'] = geo.apply(lambda r: round(safe_div(r['spend'] * 1000, r['impressions']), 2), axis=1)

        geo = geo.sort_values('spend', ascending=False)
        rows = []
        for _, r in geo.iterrows():
            rows.append({
                'region': r[geo_col],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'cpm': r['cpm'],
            })

        return {
            'id': 15, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'regions': rows[:20], 'geo_type': geo_col, 'total_regions': len(rows)},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(15, title, cat, str(e))


def analysis_16_placement(df):
    """#16 Performance por placement"""
    title = "Performance por Placement"
    cat = "Placement"
    if 'placement' not in df.columns or df['placement'].notna().sum() == 0:
        return skip_result(16, title, cat, "No placement data")
    try:
        plc = df.groupby('placement').agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            clicks=('clicks', 'sum') if 'clicks' in df.columns else ('spend', lambda x: 0),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        plc['roas'] = plc.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        plc['cpa'] = plc.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        plc['ctr'] = plc.apply(lambda r: round(safe_div(r['clicks'] * 100, r['impressions']), 2), axis=1)
        plc['cpm'] = plc.apply(lambda r: round(safe_div(r['spend'] * 1000, r['impressions']), 2), axis=1)

        avg_cpa = safe_div(plc['spend'].sum(), plc['purchases'].sum())
        plc = plc.sort_values('spend', ascending=False)

        rows = []
        for _, r in plc.iterrows():
            rows.append({
                'placement': r['placement'],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
                'cpm': r['cpm'],
                'breakdown_warning': r['cpa'] > avg_cpa * 1.3 if avg_cpa > 0 and r['purchases'] > 0 else False,
            })

        return {
            'id': 16, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'placements': rows,
                'avg_cpa': round(avg_cpa, 2),
                'breakdown_note': 'Placements con CPA superior al promedio pueden estar capturando conversiones marginales baratas en otros placements. No pausar sin análisis de marginal CPA.'
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(16, title, cat, str(e))


def analysis_17_device(df):
    """#17 Performance por dispositivo"""
    title = "Performance por Dispositivo"
    cat = "Device"
    if 'device' not in df.columns or df['device'].notna().sum() == 0:
        return skip_result(17, title, cat, "No device data")
    try:
        dev = df.groupby('device').agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
            clicks=('clicks', 'sum') if 'clicks' in df.columns else ('spend', lambda x: 0),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
        ).reset_index()

        dev['roas'] = dev.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
        dev['cpa'] = dev.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
        dev['ctr'] = dev.apply(lambda r: round(safe_div(r['clicks'] * 100, r['impressions']), 2), axis=1)
        dev['cpm'] = dev.apply(lambda r: round(safe_div(r['spend'] * 1000, r['impressions']), 2), axis=1)
        dev['spend_pct'] = dev.apply(lambda r: round(safe_div(r['spend'] * 100, dev['spend'].sum()), 1), axis=1)

        dev = dev.sort_values('spend', ascending=False)
        rows = []
        for _, r in dev.iterrows():
            rows.append({
                'device': r['device'],
                'spend': round(r['spend'], 2),
                'spend_pct': r['spend_pct'],
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
                'cpm': r['cpm'],
            })

        return {
            'id': 17, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'devices': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(17, title, cat, str(e))


def analysis_18_recommendations(df, all_results):
    """#18 Top 5 recomendaciones"""
    title = "Top 5 Recomendaciones Priorizadas"
    cat = "Estratégico"
    try:
        # Gather signals from previous analyses
        signals = []

        # Check benchmarks
        for r in all_results:
            if r['id'] == 2 and r['status'] == 'ok':
                for m in r['data'].get('metrics', []):
                    if m.get('semaphore') == 'red':
                        signals.append({
                            'priority': 'high',
                            'area': m['metric'],
                            'signal': f"{m['metric']} en rojo: {m['value']}{m['unit']}",
                            'type': 'benchmark_red'
                        })

        # Check learning phase
        for r in all_results:
            if r['id'] == 6 and r['status'] == 'ok':
                summary = r['data'].get('summary', {})
                if summary.get('learning_limited', 0) > 0:
                    signals.append({
                        'priority': 'high',
                        'area': 'Learning Phase',
                        'signal': f"{summary['learning_limited']} ad sets en learning limited",
                        'type': 'learning_limited'
                    })

        # Check creative fatigue
        for r in all_results:
            if r['id'] == 10 and r['status'] == 'ok':
                fatigued = r['data'].get('fatigued_ads', [])
                if len(fatigued) > 0:
                    signals.append({
                        'priority': 'medium',
                        'area': 'Creative Fatigue',
                        'signal': f"{len(fatigued)} ads con señales de fatigue",
                        'type': 'fatigue'
                    })

        # Check funnel dropoffs
        for r in all_results:
            if r['id'] == 12 and r['status'] == 'ok':
                for t in r['data'].get('transitions', []):
                    if t['dropoff_rate'] > 95:
                        signals.append({
                            'priority': 'medium',
                            'area': 'Funnel',
                            'signal': f"Drop-off de {t['dropoff_rate']}% en {t['transition']}",
                            'type': 'funnel_leak'
                        })

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        signals.sort(key=lambda x: priority_order.get(x['priority'], 2))

        return {
            'id': 18, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'signals': signals[:10]},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(18, title, cat, str(e))


# ═══════════════════════════════════════════════════════════════
# ANALYSES — FULL (19-32)
# ═══════════════════════════════════════════════════════════════

def analysis_19_nomenclatura_parse(df, nomenclatura_format):
    """#19 Parseo de naming"""
    title = "Parseo de Nomenclatura"
    cat = "Nomenclatura"
    name_col = 'ad_name' if 'ad_name' in df.columns else ('adset_name' if 'adset_name' in df.columns else None)
    if name_col is None:
        return skip_result(19, title, cat, "No name column available")
    if nomenclatura_format == 'unknown':
        return skip_result(19, title, cat, "Nomenclatura format not detected. Use --nomenclatura to specify.")
    try:
        names = df[name_col].dropna().unique()
        parsed = []
        for name in names:
            p = parse_nomenclatura(name, nomenclatura_format)
            parsed.append(p)

        # Summary stats
        formatos = Counter(p['formato'] for p in parsed if p['formato'])
        etapas = Counter(p['etapa'] for p in parsed if p['etapa'])
        creadores = Counter(p['creador'] for p in parsed if p['creador'])
        productos = Counter(p['producto'] for p in parsed if p['producto'])
        unparsed = sum(1 for p in parsed if not p['formato'] and not p['etapa'])

        return {
            'id': 19, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'format': nomenclatura_format,
                'total_names': len(names),
                'parsed_count': len(parsed) - unparsed,
                'unparsed_count': unparsed,
                'formatos': dict(formatos),
                'etapas': dict(etapas),
                'creadores': dict(creadores),
                'productos': dict(productos.most_common(15)),
                'sample': parsed[:10],
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(19, title, cat, str(e))


def _group_by_parsed_field(df, field, nomenclatura_format):
    """Helper to group performance by a parsed nomenclatura field."""
    name_col = 'ad_name' if 'ad_name' in df.columns else 'adset_name'
    df_copy = df.copy()
    df_copy['_parsed_field'] = df_copy[name_col].apply(
        lambda x: parse_nomenclatura(x, nomenclatura_format).get(field)
    )
    df_copy = df_copy[df_copy['_parsed_field'].notna()]
    if len(df_copy) == 0:
        return None

    grouped = df_copy.groupby('_parsed_field').agg(
        spend=('spend', 'sum'),
        impressions=('impressions', 'sum'),
        clicks=('clicks', 'sum') if 'clicks' in df_copy.columns else ('spend', lambda x: 0),
        purchases=('purchases', 'sum') if 'purchases' in df_copy.columns else ('spend', lambda x: 0),
        purchase_value=('purchase_value', 'sum') if 'purchase_value' in df_copy.columns else ('spend', lambda x: 0),
        reach=('reach', 'sum') if 'reach' in df_copy.columns else ('spend', lambda x: 0),
    ).reset_index()

    grouped['roas'] = grouped.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)
    grouped['cpa'] = grouped.apply(lambda r: round(safe_div(r['spend'], r['purchases']), 2), axis=1)
    grouped['ctr'] = grouped.apply(lambda r: round(safe_div(r['clicks'] * 100, r['impressions']), 2), axis=1)
    grouped['cpm'] = grouped.apply(lambda r: round(safe_div(r['spend'] * 1000, r['impressions']), 2), axis=1)

    return grouped.sort_values('spend', ascending=False)


def analysis_20_content_type(df, nomenclatura_format):
    """#20 Performance por tipo de contenido"""
    title = "Performance por Tipo de Contenido"
    cat = "Nomenclatura"
    if nomenclatura_format == 'unknown':
        return skip_result(20, title, cat, "Nomenclatura not detected")
    try:
        grouped = _group_by_parsed_field(df, 'formato', nomenclatura_format)
        if grouped is None or len(grouped) == 0:
            return skip_result(20, title, cat, "No formato data parsed")

        rows = []
        for _, r in grouped.iterrows():
            rows.append({
                'content_type': r['_parsed_field'],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
                'cpm': r['cpm'],
            })

        return {
            'id': 20, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'content_types': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(20, title, cat, str(e))


def analysis_21_funnel_stage(df, nomenclatura_format):
    """#21 Performance por etapa de funnel"""
    title = "Performance por Etapa de Funnel"
    cat = "Nomenclatura"
    if nomenclatura_format == 'unknown':
        return skip_result(21, title, cat, "Nomenclatura not detected")
    try:
        grouped = _group_by_parsed_field(df, 'etapa', nomenclatura_format)
        if grouped is None or len(grouped) == 0:
            return skip_result(21, title, cat, "No etapa data parsed")

        rows = []
        for _, r in grouped.iterrows():
            rows.append({
                'stage': r['_parsed_field'],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
                'cpm': r['cpm'],
            })

        return {
            'id': 21, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'stages': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(21, title, cat, str(e))


def analysis_22_creator(df, nomenclatura_format):
    """#22 Performance por creador"""
    title = "Performance por Creador/Productor"
    cat = "Nomenclatura"
    if nomenclatura_format == 'unknown':
        return skip_result(22, title, cat, "Nomenclatura not detected")
    try:
        grouped = _group_by_parsed_field(df, 'creador', nomenclatura_format)
        if grouped is None or len(grouped) == 0:
            return skip_result(22, title, cat, "No creator data parsed")

        rows = []
        for _, r in grouped.iterrows():
            rows.append({
                'creator': r['_parsed_field'],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
            })

        return {
            'id': 22, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'creators': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(22, title, cat, str(e))


def analysis_23_product(df, nomenclatura_format):
    """#23 Performance por producto"""
    title = "Performance por Producto/Colección"
    cat = "Nomenclatura"
    if nomenclatura_format == 'unknown':
        return skip_result(23, title, cat, "Nomenclatura not detected")
    try:
        grouped = _group_by_parsed_field(df, 'producto', nomenclatura_format)
        if grouped is None or len(grouped) == 0:
            return skip_result(23, title, cat, "No product data parsed")

        rows = []
        for _, r in grouped.iterrows():
            rows.append({
                'product': r['_parsed_field'],
                'spend': round(r['spend'], 2),
                'impressions': int(r['impressions']),
                'purchases': int(r['purchases']),
                'roas': r['roas'],
                'cpa': r['cpa'],
                'ctr': r['ctr'],
            })

        return {
            'id': 23, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'products': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(23, title, cat, str(e))


def analysis_24_format_stage_matrix(df, nomenclatura_format):
    """#24 Matrix formato × etapa"""
    title = "Matrix Formato × Etapa (ROAS)"
    cat = "Nomenclatura"
    if nomenclatura_format == 'unknown':
        return skip_result(24, title, cat, "Nomenclatura not detected")
    try:
        name_col = 'ad_name' if 'ad_name' in df.columns else 'adset_name'
        df_copy = df.copy()
        df_copy['_formato'] = df_copy[name_col].apply(
            lambda x: parse_nomenclatura(x, nomenclatura_format).get('formato')
        )
        df_copy['_etapa'] = df_copy[name_col].apply(
            lambda x: parse_nomenclatura(x, nomenclatura_format).get('etapa')
        )
        df_copy = df_copy[df_copy['_formato'].notna() & df_copy['_etapa'].notna()]

        if len(df_copy) == 0:
            return skip_result(24, title, cat, "No formato+etapa data parsed")

        matrix = df_copy.groupby(['_formato', '_etapa']).agg(
            spend=('spend', 'sum'),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df_copy.columns else ('spend', lambda x: 0),
            purchases=('purchases', 'sum') if 'purchases' in df_copy.columns else ('spend', lambda x: 0),
        ).reset_index()

        matrix['roas'] = matrix.apply(lambda r: round(safe_div(r['purchase_value'], r['spend']), 2), axis=1)

        # Build heatmap data
        formatos = sorted(matrix['_formato'].unique())
        etapas = sorted(matrix['_etapa'].unique())
        heatmap = {}
        for _, r in matrix.iterrows():
            key = f"{r['_formato']}|{r['_etapa']}"
            heatmap[key] = {
                'roas': r['roas'],
                'spend': round(r['spend'], 2),
                'purchases': int(r['purchases']),
            }

        return {
            'id': 24, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'formatos': formatos, 'etapas': etapas, 'matrix': heatmap},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(24, title, cat, str(e))


def analysis_25_relevance(df):
    """#25 Ad Relevance Diagnostics"""
    title = "Ad Relevance Diagnostics"
    cat = "Creativo"
    ranking_cols = ['quality_ranking', 'engagement_ranking', 'conversion_ranking']
    if not any(c in df.columns for c in ranking_cols):
        return skip_result(25, title, cat, "No ranking data available")
    try:
        ad_col = 'ad_name' if 'ad_name' in df.columns else 'adset_name'
        rankings = df.groupby(ad_col).agg({
            c: 'first' for c in ranking_cols if c in df.columns
        }).reset_index()

        # Count distribution
        distribution = {}
        for col in ranking_cols:
            if col in rankings.columns:
                distribution[col] = rankings[col].value_counts().to_dict()

        rows = []
        for _, r in rankings.iterrows():
            row = {'name': r[ad_col]}
            for col in ranking_cols:
                if col in r.index:
                    row[col] = r[col]
            rows.append(row)

        return {
            'id': 25, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'rankings': rows[:20], 'distribution': distribution},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(25, title, cat, str(e))


def analysis_26_hook_rate(df):
    """#26 Hook rate analysis"""
    title = "Hook Rate Analysis"
    cat = "Creativo"
    if 'video_3s' not in df.columns and 'video_p25' not in df.columns:
        return skip_result(26, title, cat, "No video view data")
    try:
        ad_col = 'ad_name' if 'ad_name' in df.columns else 'adset_name'
        ads = df.groupby(ad_col).agg(
            impressions=('impressions', 'sum'),
            video_3s=('video_3s', 'sum') if 'video_3s' in df.columns else ('impressions', lambda x: 0),
            video_p25=('video_p25', 'sum') if 'video_p25' in df.columns else ('impressions', lambda x: 0),
            spend=('spend', 'sum'),
        ).reset_index()

        ads['hook_rate'] = ads.apply(lambda r: round(safe_div(r['video_3s'] * 100, r['impressions']), 2), axis=1)
        ads = ads[ads['impressions'] > 100]  # Min impressions filter
        ads = ads.sort_values('hook_rate', ascending=False)

        rows = []
        for _, r in ads.head(20).iterrows():
            rows.append({
                'ad': r[ad_col],
                'impressions': int(r['impressions']),
                'video_3s': int(r['video_3s']),
                'hook_rate': r['hook_rate'],
                'spend': round(r['spend'], 2),
            })

        avg_hook = safe_div(ads['video_3s'].sum() * 100, ads['impressions'].sum())

        return {
            'id': 26, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'ads': rows, 'avg_hook_rate': round(avg_hook, 2)},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(26, title, cat, str(e))


def analysis_27_video_completion(df):
    """#27 Video completion rates"""
    title = "Video Completion Rates"
    cat = "Creativo"
    video_cols = ['video_p25', 'video_p50', 'video_p75', 'video_p100']
    if not any(c in df.columns for c in video_cols):
        return skip_result(27, title, cat, "No video completion data")
    try:
        totals = {}
        total_imps = df['impressions'].sum()
        for col in video_cols:
            if col in df.columns:
                val = df[col].sum()
                totals[col] = {
                    'value': int(val),
                    'rate': round(safe_div(val * 100, total_imps), 2),
                }

        # Per ad breakdown
        ad_col = 'ad_name' if 'ad_name' in df.columns else 'adset_name'
        ads = df.groupby(ad_col).agg(
            impressions=('impressions', 'sum'),
            **{col: (col, 'sum') for col in video_cols if col in df.columns},
        ).reset_index()

        ads = ads[ads['impressions'] > 100]
        rows = []
        for _, r in ads.head(15).iterrows():
            row = {'ad': r[ad_col], 'impressions': int(r['impressions'])}
            for col in video_cols:
                if col in r.index:
                    row[col.replace('video_', '') + '_rate'] = round(safe_div(r[col] * 100, r['impressions']), 2)
            rows.append(row)

        return {
            'id': 27, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'totals': totals, 'ads': rows},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(27, title, cat, str(e))


def analysis_28_attribution(df):
    """#28 Attribution window comparison"""
    title = "Attribution Window Comparison"
    cat = "Revenue"
    # This requires multiple attribution columns which Meta CSV may not have
    # Check for common patterns
    return skip_result(28, title, cat, "Attribution window comparison requires separate API calls with different attribution settings. Use MCP API with time_increment and action_attribution_windows parameters.")


def analysis_29_forecast(df):
    """#29 Forecast de spend/ROAS"""
    title = "Forecast de Spend/ROAS (30 días)"
    cat = "Revenue"
    if 'date_start' not in df.columns:
        return skip_result(29, title, cat, "No date column")
    try:
        daily = df.groupby('date_start').agg(
            spend=('spend', 'sum'),
            purchase_value=('purchase_value', 'sum') if 'purchase_value' in df.columns else ('spend', lambda x: 0),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
        ).reset_index().sort_values('date_start')

        if len(daily) < 14:
            return skip_result(29, title, cat, "Need at least 14 days of data for forecast")

        # Simple linear trend on last 30 days
        recent = daily.tail(30).copy()
        recent['day_num'] = range(len(recent))

        # Linear regression for spend
        x = recent['day_num'].values
        y_spend = recent['spend'].values
        y_roas = recent.apply(lambda r: safe_div(r['purchase_value'], r['spend']), axis=1).values

        # Numpy polyfit
        if len(x) > 1:
            spend_slope, spend_intercept = np.polyfit(x, y_spend, 1)
            roas_slope, roas_intercept = np.polyfit(x, y_roas, 1)
        else:
            spend_slope, spend_intercept = 0, y_spend[0]
            roas_slope, roas_intercept = 0, y_roas[0]

        # Forecast 30 days
        forecast_days = 30
        last_day = len(recent) - 1
        forecast = []
        for i in range(1, forecast_days + 1):
            day = last_day + i
            f_spend = max(0, spend_slope * day + spend_intercept)
            f_roas = max(0, roas_slope * day + roas_intercept)
            forecast.append({
                'day': i,
                'forecast_spend': round(f_spend, 2),
                'forecast_roas': round(f_roas, 2),
            })

        total_forecast_spend = sum(f['forecast_spend'] for f in forecast)
        avg_forecast_roas = safe_div(sum(f['forecast_roas'] for f in forecast), len(forecast))

        return {
            'id': 29, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'forecast': forecast,
                'total_forecast_spend': round(total_forecast_spend, 2),
                'avg_forecast_roas': round(avg_forecast_roas, 2),
                'spend_trend': 'increasing' if spend_slope > 0 else 'decreasing',
                'roas_trend': 'improving' if roas_slope > 0 else 'declining',
                'model': 'linear_trend',
                'caveat': 'Forecast basado en tendencia lineal simple. No es una predicción — es una proyección de la tendencia actual.',
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(29, title, cat, str(e))


def analysis_30_overlap(df):
    """#30 Auction overlap detection"""
    title = "Auction Overlap Detection"
    cat = "Avanzado"
    if not has_columns(df, ['adset_name', 'date_start']):
        return skip_result(30, title, cat, "Missing adset_name or date_start")
    try:
        # Detect potential overlap: ad sets in same campaign with similar targeting
        # and high CPM variance day-to-day
        daily_adset = df.groupby(['adset_name', 'date_start']).agg(
            spend=('spend', 'sum'),
            impressions=('impressions', 'sum'),
        ).reset_index()

        daily_adset['cpm'] = daily_adset.apply(lambda r: safe_div(r['spend'] * 1000, r['impressions']), axis=1)

        # Check CPM coefficient of variation per ad set
        cpm_cv = daily_adset.groupby('adset_name')['cpm'].agg(['mean', 'std']).reset_index()
        cpm_cv['cv'] = cpm_cv.apply(lambda r: safe_div(r['std'], r['mean']), axis=1)
        cpm_cv = cpm_cv.sort_values('cv', ascending=False)

        # High CV might indicate auction competition
        suspicious = []
        for _, r in cpm_cv.iterrows():
            if r['cv'] > 0.4 and r['mean'] > 0:
                suspicious.append({
                    'adset': r['adset_name'],
                    'avg_cpm': round(r['mean'], 2),
                    'cpm_std': round(r['std'], 2),
                    'cv': round(r['cv'], 3),
                    'risk': 'high' if r['cv'] > 0.6 else 'medium',
                })

        return {
            'id': 30, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'suspicious_overlap': suspicious[:10],
                'note': 'CPM alta variabilidad puede indicar overlap de auctions entre ad sets. Verificar con Delivery Insights en Ads Manager.',
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(30, title, cat, str(e))


def analysis_31_pacing(df):
    """#31 Budget pacing analysis"""
    title = "Budget Pacing Analysis"
    cat = "Avanzado"
    if not has_columns(df, ['campaign_name', 'date_start', 'spend']):
        return skip_result(31, title, cat, "Missing required columns")
    try:
        # Analyze daily spend consistency per campaign
        camp_daily = df.groupby(['campaign_name', 'date_start']).agg(
            spend=('spend', 'sum'),
        ).reset_index()

        results = []
        for camp in camp_daily['campaign_name'].unique():
            camp_data = camp_daily[camp_daily['campaign_name'] == camp].sort_values('date_start')
            if len(camp_data) < 3:
                continue

            avg_spend = camp_data['spend'].mean()
            std_spend = camp_data['spend'].std()
            cv = safe_div(std_spend, avg_spend)

            # Detect underspend/overspend days
            underspend_days = (camp_data['spend'] < avg_spend * 0.5).sum()
            overspend_days = (camp_data['spend'] > avg_spend * 1.5).sum()

            results.append({
                'campaign': camp,
                'avg_daily_spend': round(avg_spend, 2),
                'spend_std': round(std_spend, 2),
                'cv': round(cv, 3),
                'underspend_days': int(underspend_days),
                'overspend_days': int(overspend_days),
                'total_days': len(camp_data),
                'pacing': 'stable' if cv < 0.3 else ('variable' if cv < 0.5 else 'erratic'),
            })

        results.sort(key=lambda x: x['cv'], reverse=True)

        return {
            'id': 31, 'title': title, 'category': cat, 'status': 'ok',
            'data': {'campaigns': results},
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(31, title, cat, str(e))


def analysis_32_marginal_cpa(df):
    """#32 Marginal CPA trend"""
    title = "Marginal CPA Trend"
    cat = "Avanzado"
    if not has_columns(df, ['date_start', 'spend']):
        return skip_result(32, title, cat, "Missing required columns")
    try:
        daily = df.groupby('date_start').agg(
            spend=('spend', 'sum'),
            purchases=('purchases', 'sum') if 'purchases' in df.columns else ('spend', lambda x: 0),
        ).reset_index().sort_values('date_start')

        if len(daily) < 7:
            return skip_result(32, title, cat, "Not enough data for marginal CPA analysis")

        daily['cpa'] = daily.apply(lambda r: safe_div(r['spend'], r['purchases']), axis=1)
        daily['cumulative_spend'] = daily['spend'].cumsum()
        daily['cumulative_purchases'] = daily['purchases'].cumsum()
        daily['avg_cpa'] = daily.apply(lambda r: safe_div(r['cumulative_spend'], r['cumulative_purchases']), axis=1)

        # Marginal CPA: CPA of the incremental spend
        # Approximate with rolling 3-day window
        daily['spend_3d'] = daily['spend'].rolling(3, min_periods=1).sum()
        daily['purchases_3d'] = daily['purchases'].rolling(3, min_periods=1).sum()
        daily['marginal_cpa'] = daily.apply(lambda r: safe_div(r['spend_3d'], r['purchases_3d']), axis=1)

        rows = []
        for _, r in daily.iterrows():
            rows.append({
                'date': str(r['date_start'].date()) if not pd.isna(r['date_start']) else '',
                'spend': round(r['spend'], 2),
                'purchases': int(r['purchases']),
                'daily_cpa': round(r['cpa'], 2),
                'avg_cpa': round(r['avg_cpa'], 2),
                'marginal_cpa_3d': round(r['marginal_cpa'], 2),
            })

        # Trend: is marginal CPA rising or falling?
        if len(daily) >= 14:
            recent_marginal = daily.tail(7)['marginal_cpa'].mean()
            prev_marginal = daily.iloc[-14:-7]['marginal_cpa'].mean()
            trend = 'rising' if recent_marginal > prev_marginal * 1.1 else ('falling' if recent_marginal < prev_marginal * 0.9 else 'stable')
        else:
            trend = 'insufficient_data'

        return {
            'id': 32, 'title': title, 'category': cat, 'status': 'ok',
            'data': {
                'daily': rows,
                'trend': trend,
                'note': 'Marginal CPA es el costo de la próxima conversión, aproximado con ventana rolling de 3 días. Si el marginal CPA sube mientras el average CPA es bajo, la cuenta está cerca de saturación.',
            },
            'insight': '', 'recommendation': ''
        }
    except Exception as e:
        return skip_result(32, title, cat, str(e))


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def run_analyses(df, mode, nomenclatura_format):
    """Run all analyses for the given mode."""
    results = []

    # LITE analyses (1-17, then 18 depends on previous results)
    results.append(analysis_01_dashboard(df))
    results.append(analysis_02_benchmarks(df))
    results.append(analysis_03_daily_evolution(df))
    results.append(analysis_04_campaigns(df))
    results.append(analysis_05_budget_distribution(df))
    results.append(analysis_06_learning_phase(df))
    results.append(analysis_07_adsets(df))
    results.append(analysis_08_audiences(df))
    results.append(analysis_09_ads_ranking(df))
    results.append(analysis_10_creative_fatigue(df))
    results.append(analysis_11_funnel(df))
    results.append(analysis_12_dropoff(df))
    results.append(analysis_13_seasonality(df))
    results.append(analysis_14_trend(df))
    results.append(analysis_15_geo(df))
    results.append(analysis_16_placement(df))
    results.append(analysis_17_device(df))
    # #18 depends on all previous results
    results.append(analysis_18_recommendations(df, results))

    if mode == 'full':
        # FULL analyses (19-32)
        results.append(analysis_19_nomenclatura_parse(df, nomenclatura_format))
        results.append(analysis_20_content_type(df, nomenclatura_format))
        results.append(analysis_21_funnel_stage(df, nomenclatura_format))
        results.append(analysis_22_creator(df, nomenclatura_format))
        results.append(analysis_23_product(df, nomenclatura_format))
        results.append(analysis_24_format_stage_matrix(df, nomenclatura_format))
        results.append(analysis_25_relevance(df))
        results.append(analysis_26_hook_rate(df))
        results.append(analysis_27_video_completion(df))
        results.append(analysis_28_attribution(df))
        results.append(analysis_29_forecast(df))
        results.append(analysis_30_overlap(df))
        results.append(analysis_31_pacing(df))
        results.append(analysis_32_marginal_cpa(df))

    return results


def main():
    parser = argparse.ArgumentParser(description='Meta Ads Analysis Script')
    parser.add_argument('--input', required=True, help='Path to CSV or JSON input file')
    parser.add_argument('--mode', choices=['lite', 'full'], default='lite', help='Analysis mode')
    parser.add_argument('--nomenclatura', choices=['standard', 'alternative', 'auto'], default='auto',
                        help='Nomenclatura format for parsing ad names')
    parser.add_argument('--output', required=True, help='Path for output JSON')
    args = parser.parse_args()

    # Load data
    print(f"Loading data from: {args.input}", file=sys.stderr)
    try:
        df = load_data(args.input)
    except Exception as e:
        print(f"ERROR loading data: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns", file=sys.stderr)
    print(f"Columns: {list(df.columns)}", file=sys.stderr)

    # Detect nomenclatura
    name_col = 'ad_name' if 'ad_name' in df.columns else ('adset_name' if 'adset_name' in df.columns else None)
    if name_col:
        names = df[name_col].dropna().unique()[:20].tolist()
        nomenclatura_format = detect_nomenclatura(names, args.nomenclatura)
    else:
        nomenclatura_format = 'unknown'
    print(f"Nomenclatura format: {nomenclatura_format}", file=sys.stderr)

    # Run analyses
    print(f"Running {args.mode} mode analyses...", file=sys.stderr)
    results = run_analyses(df, args.mode, nomenclatura_format)

    # Build output
    ok_count = sum(1 for r in results if r['status'] == 'ok')
    skip_count = sum(1 for r in results if r['status'] == 'skipped')

    output = {
        'meta': {
            'mode': args.mode,
            'input_file': args.input,
            'total_rows': len(df),
            'columns': list(df.columns),
            'nomenclatura_format': nomenclatura_format,
            'analyses_ok': ok_count,
            'analyses_skipped': skip_count,
            'analyses_total': len(results),
            'generated_at': datetime.now().isoformat(),
        },
        'analyses': results,
    }

    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    print(f"Done: {ok_count} OK, {skip_count} skipped. Output: {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
