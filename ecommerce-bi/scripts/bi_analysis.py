#!/usr/bin/env python3
# Copyright (c) 2026 Mathias Chu — https://mathiaschu.com
"""
eCommerce BI Analysis Script
Generates JSON with all analysis results from a sales CSV.
Usage: python3 bi_analysis.py --csv PATH --mode lite|full --output PATH
"""

import argparse
import csv
import json
import sys
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import combinations
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
# PLATFORM DETECTION & COLUMN MAPPING
# ═══════════════════════════════════════════════════════════════

PLATFORM_FINGERPRINTS = {
    'tiendanube': ['Número de orden', 'Estado de la orden', 'Nombre del producto', 'Medio de envío'],
    'shopify': ['Name', 'Financial Status', 'Lineitem name', 'Lineitem quantity'],
    'woocommerce': ['Order ID', 'Order Status', 'Product Name', 'Order Total'],
}

COLUMN_MAPS = {
    'tiendanube': {
        'Número de orden': 'order_id',
        'Email': 'email',
        'Fecha': 'date',
        'Estado de la orden': 'order_status',
        'Estado del pago': 'payment_status',
        'Estado del envío': 'shipping_status',
        'Moneda': 'currency',
        'Subtotal de productos': 'subtotal',
        'Descuento': 'discount',
        'Costo de envío': 'shipping_cost',
        'Total': 'total',
        'Nombre del comprador': 'customer_name',
        'Teléfono': 'phone',
        'Dirección': 'shipping_address',
        'Ciudad': 'city',
        'Localidad': 'locality',
        'Código postal': 'zip_code',
        'Provincia o estado': 'state',
        'País': 'country',
        'Medio de envío': 'shipping_method',
        'Medio de pago': 'payment_method',
        'Cupón de descuento': 'coupon',
        'Fecha de pago': 'payment_date',
        'Fecha de envío': 'shipping_date',
        'Nombre del producto': 'product_name',
        'Precio del producto': 'product_price',
        'Cantidad del producto': 'product_qty',
        'SKU': 'sku',
        'Canal': 'channel',
        'Fecha y hora de cancelación': 'cancellation_date',
        'Motivo de cancelación': 'cancellation_reason',
    },
    'shopify': {
        'Name': 'order_id',
        'Email': 'email',
        'Created at': 'date',
        'Financial Status': 'payment_status',
        'Fulfillment Status': 'shipping_status',
        'Currency': 'currency',
        'Subtotal': 'subtotal',
        'Discount Amount': 'discount',
        'Shipping': 'shipping_cost',
        'Total': 'total',
        'Billing Name': 'customer_name',
        'Billing Phone': 'phone',
        'Shipping Street': 'shipping_address',
        'Shipping City': 'city',
        'Shipping Zip': 'zip_code',
        'Shipping Province': 'state',
        'Shipping Country': 'country',
        'Lineitem name': 'product_name',
        'Lineitem price': 'product_price',
        'Lineitem quantity': 'product_qty',
        'Lineitem sku': 'sku',
        'Source': 'channel',
        'Payment Method': 'payment_method',
        'Discount Code': 'coupon',
        'Cancelled at': 'cancellation_date',
        'Cancel Reason': 'cancellation_reason',
    },
    'woocommerce': {
        'Order ID': 'order_id',
        'Customer Email': 'email',
        'Order Date': 'date',
        'Order Status': 'order_status',
        'Currency': 'currency',
        'Cart Discount': 'discount',
        'Order Shipping': 'shipping_cost',
        'Order Total': 'total',
        'Billing First Name': '_billing_first',
        'Billing Last Name': '_billing_last',
        'Billing Phone': 'phone',
        'Shipping Address 1': 'shipping_address',
        'Shipping City': 'city',
        'Shipping Postcode': 'zip_code',
        'Shipping State': 'state',
        'Shipping Country': 'country',
        'Product Name': 'product_name',
        'Product Price': 'product_price',
        'Quantity': 'product_qty',
        'SKU': 'sku',
        'Payment Method Title': 'payment_method',
        'Coupon Code': 'coupon',
    },
}

STATUS_MAPS = {
    'tiendanube': {
        'order_status': {
            'Abierta': 'open', 'Cerrada': 'closed', 'Cancelada': 'cancelled',
        },
        'payment_status': {
            'Pagado': 'paid', 'Pendiente': 'pending', 'Reembolsado': 'refunded',
            'Abandonado': 'abandoned',
        },
    },
    'shopify': {
        'payment_status': {
            'paid': 'paid', 'pending': 'pending', 'refunded': 'refunded',
            'partially_refunded': 'refunded', 'voided': 'cancelled',
        },
    },
    'woocommerce': {
        'order_status': {
            'wc-completed': 'closed', 'wc-processing': 'open', 'wc-on-hold': 'pending',
            'wc-cancelled': 'cancelled', 'wc-refunded': 'refunded', 'wc-failed': 'failed',
            'wc-pending': 'pending', 'completed': 'closed', 'processing': 'open',
            'on-hold': 'pending', 'cancelled': 'cancelled', 'refunded': 'refunded',
        },
    },
}


def detect_encoding(filepath):
    """Try latin-1 first (common for Tiendanube), then utf-8."""
    for enc in ['latin-1', 'utf-8', 'utf-8-sig', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                f.read(4096)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'latin-1'


def detect_delimiter(filepath, encoding):
    """Detect CSV delimiter by counting occurrences in first line."""
    with open(filepath, 'r', encoding=encoding) as f:
        first_line = f.readline()
    semicolons = first_line.count(';')
    commas = first_line.count(',')
    tabs = first_line.count('\t')
    if semicolons > commas and semicolons > tabs:
        return ';'
    if tabs > commas:
        return '\t'
    return ','


def detect_platform(headers):
    """Score each platform by matching fingerprint headers."""
    best_platform = 'generic'
    best_score = 0
    for platform, fingerprints in PLATFORM_FINGERPRINTS.items():
        score = sum(1 for fp in fingerprints if fp in headers)
        if score > best_score:
            best_score = score
            best_platform = platform
    if best_score < 2:
        return 'generic'
    return best_platform


def load_csv(filepath):
    """Load CSV, detect platform, normalize columns."""
    encoding = detect_encoding(filepath)
    delimiter = detect_delimiter(filepath, encoding)

    df = pd.read_csv(filepath, encoding=encoding, delimiter=delimiter, dtype=str, on_bad_lines='skip')
    df.columns = [c.strip().strip('"') for c in df.columns]

    platform = detect_platform(df.columns.tolist())
    col_map = COLUMN_MAPS.get(platform, {})

    # Rename columns
    rename = {}
    for orig, canon in col_map.items():
        if orig in df.columns:
            rename[orig] = canon
    df = df.rename(columns=rename)

    # WooCommerce: concat first + last name
    if platform == 'woocommerce' and '_billing_first' in df.columns:
        df['customer_name'] = (df.get('_billing_first', '').fillna('') + ' ' + df.get('_billing_last', '').fillna('')).str.strip()

    # Normalize statuses
    status_map = STATUS_MAPS.get(platform, {})
    for col, vmap in status_map.items():
        if col in df.columns:
            df[col] = df[col].map(lambda x: vmap.get(str(x).strip(), str(x).strip().lower()) if pd.notna(x) else '')

    # Infer order_status from cancellation_date for Shopify
    if platform == 'shopify' and 'order_status' not in df.columns:
        df['order_status'] = 'closed'
        if 'cancellation_date' in df.columns:
            df.loc[df['cancellation_date'].notna() & (df['cancellation_date'] != ''), 'order_status'] = 'cancelled'

    # Parse dates
    df = parse_dates(df, platform)

    # Parse numerics
    for col in ['total', 'subtotal', 'discount', 'shipping_cost', 'product_price', 'product_qty']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(r'[^\d.\-]', '', regex=True), errors='coerce')

    # Fill product_qty NaN with 1
    if 'product_qty' in df.columns:
        df['product_qty'] = df['product_qty'].fillna(1).astype(int)

    return df, platform, encoding, delimiter


def parse_dates(df, platform):
    """Parse date columns based on platform."""
    date_formats = {
        'tiendanube': ['%d/%m/%Y %H:%M', '%d/%m/%Y'],
        'shopify': ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S %z', '%Y-%m-%d'],
        'woocommerce': ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y'],
    }
    fmts = date_formats.get(platform, ['%Y-%m-%d', '%d/%m/%Y', '%d/%m/%Y %H:%M'])

    for col in ['date', 'payment_date', 'shipping_date', 'cancellation_date']:
        if col not in df.columns:
            continue
        parsed = pd.NaT
        for fmt in fmts:
            try:
                parsed = pd.to_datetime(df[col], format=fmt, errors='coerce')
                if parsed.notna().sum() > len(df) * 0.5:
                    break
            except Exception:
                continue
        if not isinstance(parsed, pd.Series):
            parsed = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
        else:
            # Fill remaining NaT with flexible parsing
            mask = parsed.isna() & df[col].notna()
            if mask.any():
                parsed.loc[mask] = pd.to_datetime(df.loc[mask, col], errors='coerce', dayfirst=True)
        # Remove timezone info for consistency
        if hasattr(parsed, 'dt') and parsed.dt.tz is not None:
            parsed = parsed.dt.tz_localize(None)
        df[col] = parsed

    return df


def safe_analysis(func):
    """Decorator to catch errors and return skipped status."""
    def wrapper(df, **kwargs):
        try:
            result = func(df, **kwargs)
            if result is None:
                return {'status': 'skipped', 'reason': 'No data available for this analysis'}
            result['status'] = 'ok'
            return result
        except Exception as e:
            return {'status': 'skipped', 'reason': str(e)}
    wrapper.__name__ = func.__name__
    return wrapper


def has_columns(df, required):
    """Check if DataFrame has all required columns with data."""
    for col in required:
        if col not in df.columns or df[col].isna().all():
            return False
    return True


# ═══════════════════════════════════════════════════════════════
# HELPER: Get orders DataFrame (deduplicated to order level)
# ═══════════════════════════════════════════════════════════════

def get_orders(df):
    """Get order-level data (one row per order) with aggregated total."""
    if 'order_id' not in df.columns:
        return df
    order_cols = ['order_id', 'email', 'date', 'order_status', 'payment_status',
                  'total', 'discount', 'shipping_cost', 'state', 'city', 'country',
                  'shipping_method', 'payment_method', 'coupon', 'channel',
                  'cancellation_date', 'cancellation_reason', 'customer_name',
                  'payment_date', 'shipping_date']
    available = [c for c in order_cols if c in df.columns and c != 'order_id']
    orders = df.groupby('order_id').first()[available].reset_index()
    return orders


def fmt_currency(val, currency='ARS'):
    """Format number as currency string."""
    if pd.isna(val):
        return '$0'
    if abs(val) >= 1_000_000:
        return f'${val/1_000_000:,.1f}M'
    if abs(val) >= 1_000:
        return f'${val:,.0f}'
    return f'${val:,.2f}'


# ═══════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS — LITE (1-20)
# ═══════════════════════════════════════════════════════════════

def normalize_product_name(name):
    """Extract base product name without size/color variants.
    Examples:
        'Biker Cadbury (2, Chocolate)' → 'Biker Cadbury'
        'Pack x 3 Bombachas Bella Algodón (3)' → 'Pack x 3 Bombachas Bella Algodón'
        'Remera Lisa - Negro - S' → 'Remera Lisa'
        'Bikini Agnes (1, Lavanda)' → 'Bikini Agnes'
    """
    import re
    if pd.isna(name):
        return name
    name = str(name).strip()
    # Remove parenthetical variants: (talle, color) or (color, talle) or (talle)
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name).strip()
    # Remove trailing size/color after dash: " - Negro - S"
    parts = name.split(' - ')
    if len(parts) >= 2:
        # Keep only the first meaningful part (product name)
        name = parts[0].strip()
    return name


@safe_analysis
def analysis_01_market_basket(df, **kwargs):
    """Market Basket Analysis — product pairs and trios with support/confidence/lift."""
    if not has_columns(df, ['order_id', 'product_name']):
        return None

    # Normalize product names to base products (without variant details)
    df_mb = df[df['product_name'].notna()].copy()
    df_mb['base_product'] = df_mb['product_name'].apply(normalize_product_name)

    # Filter to valid orders only
    orders_products = df_mb.groupby('order_id')['base_product'].apply(
        lambda x: list(set(x.str.strip()))
    ).reset_index()
    orders_products.columns = ['order_id', 'product_name']

    # Only orders with 2+ products
    multi = orders_products[orders_products['product_name'].apply(len) >= 2]
    if len(multi) < 10:
        return {'pairs': [], 'trios': [], 'note': 'Insufficient multi-product orders (<10)'}

    total_orders = len(orders_products)

    # Count individual product frequency
    product_freq = Counter()
    for products in orders_products['product_name']:
        for p in products:
            product_freq[p] += 1

    # Pairs
    pair_counts = Counter()
    for products in multi['product_name']:
        for pair in combinations(sorted(products), 2):
            pair_counts[pair] += 1

    # Adaptive threshold: 1% for small datasets, 0.3% for large
    min_support = 0.003 if total_orders > 1000 else 0.01

    pairs = []
    for (a, b), count in pair_counts.most_common(200):
        support = count / total_orders
        if support < min_support:
            continue
        confidence_ab = count / product_freq[a] if product_freq[a] > 0 else 0
        confidence_ba = count / product_freq[b] if product_freq[b] > 0 else 0
        lift = support / ((product_freq[a] / total_orders) * (product_freq[b] / total_orders)) if product_freq[a] > 0 and product_freq[b] > 0 else 0
        if lift > 1.0:
            pairs.append({
                'items': [a, b],
                'support': round(support * 100, 2),
                'confidence': round(max(confidence_ab, confidence_ba) * 100, 2),
                'lift': round(lift, 2),
                'count': count,
            })
    pairs.sort(key=lambda x: x['lift'], reverse=True)

    # Trios (top pairs only to limit computation)
    trio_counts = Counter()
    for products in multi['product_name']:
        if len(products) >= 3:
            for trio in combinations(sorted(products), 3):
                trio_counts[trio] += 1

    trios = []
    for items, count in trio_counts.most_common(50):
        support = count / total_orders
        if support < min_support * 0.5:
            continue
        expected = 1.0
        for item in items:
            expected *= product_freq[item] / total_orders
        lift = support / expected if expected > 0 else 0
        if lift > 1.0:
            trios.append({
                'items': list(items),
                'support': round(support * 100, 2),
                'lift': round(lift, 2),
                'count': count,
            })
    trios.sort(key=lambda x: x['lift'], reverse=True)

    return {
        'total_orders': total_orders,
        'multi_product_orders': len(multi),
        'multi_product_pct': round(len(multi) / total_orders * 100, 1),
        'pairs': pairs[:30],
        'trios': trios[:15],
    }


@safe_analysis
def analysis_02_category_affinity(df, **kwargs):
    """Afinidad entre categorías."""
    if not has_columns(df, ['order_id', 'product_name']):
        return None

    def extract_category(name):
        if pd.isna(name):
            return 'Sin categoría'
        name = str(name).strip()
        for sep in [' - ', ' | ', ' / ']:
            if sep in name:
                return name.split(sep)[0].strip()
        words = name.split()
        return words[0] if words else 'Sin categoría'

    df_cat = df.copy()
    df_cat['category'] = df_cat['product_name'].apply(extract_category)

    orders_cats = df_cat.groupby('order_id')['category'].apply(lambda x: list(set(x))).reset_index()
    multi = orders_cats[orders_cats['category'].apply(len) >= 2]

    if len(multi) < 5:
        return {'pairs': [], 'note': 'Insufficient multi-category orders'}

    total_orders = len(orders_cats)
    cat_freq = Counter()
    for cats in orders_cats['category']:
        for c in cats:
            cat_freq[c] += 1

    pair_counts = Counter()
    for cats in multi['category']:
        for pair in combinations(sorted(cats), 2):
            pair_counts[pair] += 1

    pairs = []
    for (a, b), count in pair_counts.most_common(30):
        support = count / total_orders
        lift = support / ((cat_freq[a] / total_orders) * (cat_freq[b] / total_orders)) if cat_freq[a] > 0 and cat_freq[b] > 0 else 0
        pairs.append({
            'categories': [a, b],
            'support': round(support * 100, 2),
            'lift': round(lift, 2),
            'count': count,
        })
    pairs.sort(key=lambda x: x['lift'], reverse=True)

    # Category distribution
    cat_revenue = df_cat.groupby('category').apply(
        lambda x: (x['product_price'].fillna(0) * x['product_qty'].fillna(1)).sum()
    ).sort_values(ascending=False)

    distribution = [{'category': cat, 'revenue': round(rev, 2)} for cat, rev in cat_revenue.head(15).items()]

    return {'pairs': pairs[:20], 'distribution': distribution}


@safe_analysis
def analysis_03_product_ranking(df, **kwargs):
    """Ranking de productos por revenue, unidades, tendencia."""
    if not has_columns(df, ['product_name', 'product_price', 'product_qty']):
        return None

    df_valid = df[df['product_name'].notna()].copy()
    df_valid['line_revenue'] = df_valid['product_price'].fillna(0) * df_valid['product_qty'].fillna(1)

    ranking = df_valid.groupby('product_name').agg(
        revenue=('line_revenue', 'sum'),
        units=('product_qty', 'sum'),
        orders=('order_id', 'nunique') if 'order_id' in df_valid.columns else ('product_name', 'count'),
        avg_price=('product_price', 'mean'),
    ).reset_index()

    # Trend: last 3 months vs prior 3 months
    if 'date' in df_valid.columns and df_valid['date'].notna().any():
        max_date = df_valid['date'].max()
        cutoff = max_date - pd.DateOffset(months=3)
        cutoff_prior = cutoff - pd.DateOffset(months=3)

        recent = df_valid[df_valid['date'] >= cutoff].groupby('product_name')['line_revenue'].sum()
        prior = df_valid[(df_valid['date'] >= cutoff_prior) & (df_valid['date'] < cutoff)].groupby('product_name')['line_revenue'].sum()

        trend = {}
        for product in ranking['product_name']:
            r = recent.get(product, 0)
            p = prior.get(product, 0)
            if p > 0:
                trend[product] = round((r - p) / p * 100, 1)
            elif r > 0:
                trend[product] = 100.0
            else:
                trend[product] = 0.0
        ranking['trend_pct'] = ranking['product_name'].map(trend)
    else:
        ranking['trend_pct'] = 0.0

    ranking = ranking.sort_values('revenue', ascending=False).head(30)

    return {
        'products': ranking.to_dict('records'),
        'total_products': df_valid['product_name'].nunique(),
    }


@safe_analysis
def analysis_04_anchor_products(df, **kwargs):
    """Productos ancla — los que más arrastran cross-sell."""
    if not has_columns(df, ['order_id', 'product_name']):
        return None

    orders_products = df[df['product_name'].notna()].groupby('order_id')['product_name'].apply(
        lambda x: list(set(x.str.strip()))
    ).reset_index()

    multi = orders_products[orders_products['product_name'].apply(len) >= 2]
    if len(multi) < 10:
        return None

    # Count how many multi-product orders each product appears in
    anchor_counts = Counter()
    companion_map = defaultdict(Counter)
    for _, row in multi.iterrows():
        products = row['product_name']
        for p in products:
            anchor_counts[p] += 1
            for other in products:
                if other != p:
                    companion_map[p][other] += 1

    anchors = []
    for product, count in anchor_counts.most_common(20):
        top_companions = companion_map[product].most_common(5)
        anchors.append({
            'product': product,
            'multi_order_count': count,
            'top_companions': [{'product': c, 'count': n} for c, n in top_companions],
        })

    return {'anchors': anchors}


@safe_analysis
def analysis_05_long_tail(df, **kwargs):
    """Long tail 80/20 — Pareto analysis."""
    if not has_columns(df, ['product_name', 'product_price', 'product_qty']):
        return None

    df_valid = df[df['product_name'].notna()].copy()
    df_valid['line_revenue'] = df_valid['product_price'].fillna(0) * df_valid['product_qty'].fillna(1)

    product_revenue = df_valid.groupby('product_name')['line_revenue'].sum().sort_values(ascending=False)
    total_revenue = product_revenue.sum()

    if total_revenue == 0:
        return None

    cumsum = product_revenue.cumsum()
    cum_pct = cumsum / total_revenue * 100

    products_80 = (cum_pct <= 80).sum() + 1  # +1 to include the one that crosses 80%
    total_products = len(product_revenue)

    pareto_data = []
    for i, (product, revenue) in enumerate(product_revenue.head(30).items()):
        pareto_data.append({
            'product': product,
            'revenue': round(revenue, 2),
            'pct_of_total': round(revenue / total_revenue * 100, 2),
            'cumulative_pct': round(cum_pct.iloc[i], 2),
        })

    return {
        'total_products': total_products,
        'products_80_pct': min(products_80, total_products),
        'pct_products_80': round(min(products_80, total_products) / total_products * 100, 1),
        'total_revenue': round(total_revenue, 2),
        'pareto_data': pareto_data,
    }


@safe_analysis
def analysis_06_cancellation_by_product(df, **kwargs):
    """Productos con alta tasa de cancelación."""
    if not has_columns(df, ['product_name']):
        return None

    has_cancel = False
    if 'order_status' in df.columns:
        has_cancel = True
        df_valid = df[df['product_name'].notna()].copy()
        df_valid['is_cancelled'] = df_valid['order_status'].isin(['cancelled', 'Cancelada', 'cancelada'])
    elif 'cancellation_date' in df.columns:
        has_cancel = True
        df_valid = df[df['product_name'].notna()].copy()
        df_valid['is_cancelled'] = df_valid['cancellation_date'].notna()
    if not has_cancel:
        return None

    overall_rate = df_valid['is_cancelled'].mean()

    product_stats = df_valid.groupby('product_name').agg(
        total_orders=('order_id', 'nunique') if 'order_id' in df_valid.columns else ('product_name', 'count'),
        cancelled=('is_cancelled', 'sum'),
    ).reset_index()
    product_stats['cancel_rate'] = product_stats['cancelled'] / product_stats['total_orders']

    # Flag products with rate > 2x average and at least 5 orders
    flagged = product_stats[
        (product_stats['cancel_rate'] > overall_rate * 2) &
        (product_stats['total_orders'] >= 5)
    ].sort_values('cancel_rate', ascending=False)

    return {
        'overall_cancel_rate': round(overall_rate * 100, 2),
        'flagged_products': flagged.head(15).to_dict('records'),
        'total_products_analyzed': len(product_stats),
    }


@safe_analysis
def analysis_07_rfm(df, **kwargs):
    """Segmentación RFM."""
    if not has_columns(df, ['email', 'date', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & (orders['email'] != '')]
    orders = orders[orders['date'].notna()]
    orders = orders[orders['total'].notna() & (orders['total'] > 0)]

    if len(orders) < 50:
        return None

    reference_date = orders['date'].max() + timedelta(days=1)

    rfm = orders.groupby('email').agg(
        recency=('date', lambda x: (reference_date - x.max()).days),
        frequency=('order_id', 'nunique') if 'order_id' in orders.columns else ('email', 'count'),
        monetary=('total', 'sum'),
    ).reset_index()

    # Score 1-5 using quintiles
    for col in ['recency', 'frequency', 'monetary']:
        try:
            if col == 'recency':
                rfm[f'{col}_score'] = pd.qcut(rfm[col], 5, labels=[5, 4, 3, 2, 1], duplicates='drop').astype(int)
            else:
                rfm[f'{col}_score'] = pd.qcut(rfm[col], 5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)
        except ValueError:
            # Not enough unique values for 5 bins
            rfm[f'{col}_score'] = pd.qcut(rfm[col].rank(method='first'), 5, labels=[1, 2, 3, 4, 5] if col != 'recency' else [5, 4, 3, 2, 1], duplicates='drop').astype(int)

    # Segment mapping
    def rfm_segment(row):
        r, f, m = row['recency_score'], row['frequency_score'], row['monetary_score']
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        if r >= 3 and f >= 3 and m >= 3:
            return 'Loyal'
        if r >= 3 and f <= 2:
            return 'Potential Loyal'
        if r >= 4 and f == 1:
            return 'New'
        if r == 3 and f == 1:
            return 'Promising'
        if r == 2 and f >= 2 and f <= 3:
            return 'Need Attention'
        if r == 2 and f >= 1 and f <= 2:
            return 'About to Sleep'
        if r <= 2 and f >= 3:
            return 'At Risk'
        if r == 1 and f >= 4:
            return "Can't Lose"
        if r <= 2 and f <= 2 and m <= 2:
            return 'Hibernating'
        if r == 1 and f == 1:
            return 'Lost'
        return 'Other'

    rfm['segment'] = rfm.apply(rfm_segment, axis=1)

    segment_summary = rfm.groupby('segment').agg(
        count=('email', 'count'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        avg_monetary=('monetary', 'mean'),
    ).reset_index()
    segment_summary['pct'] = round(segment_summary['count'] / len(rfm) * 100, 1)
    segment_summary = segment_summary.sort_values('count', ascending=False)

    return {
        'total_customers': len(rfm),
        'segments': segment_summary.to_dict('records'),
        'rfm_stats': {
            'avg_recency': round(rfm['recency'].mean(), 1),
            'avg_frequency': round(rfm['frequency'].mean(), 2),
            'avg_monetary': round(rfm['monetary'].mean(), 2),
        },
    }


@safe_analysis
def analysis_08_clv(df, **kwargs):
    """Customer Lifetime Value."""
    if not has_columns(df, ['email', 'date', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & orders['date'].notna() & (orders['total'] > 0)]

    customer = orders.groupby('email').agg(
        total_revenue=('total', 'sum'),
        order_count=('order_id', 'nunique') if 'order_id' in orders.columns else ('email', 'count'),
        first_order=('date', 'min'),
        last_order=('date', 'max'),
    ).reset_index()

    customer['aov'] = customer['total_revenue'] / customer['order_count']
    customer['lifespan_days'] = (customer['last_order'] - customer['first_order']).dt.days
    customer['avg_days_between'] = customer.apply(
        lambda r: r['lifespan_days'] / (r['order_count'] - 1) if r['order_count'] > 1 else None, axis=1
    )

    # CLV = AOV × frequency_per_year × expected_lifespan (3 years)
    customer['freq_per_year'] = customer.apply(
        lambda r: 365 / r['avg_days_between'] if r['avg_days_between'] and r['avg_days_between'] > 0 else r['order_count'], axis=1
    )
    customer['clv_3y'] = customer['aov'] * customer['freq_per_year'] * 3

    # Quartiles
    customer['clv_quartile'] = pd.qcut(customer['clv_3y'], 4, labels=['Low', 'Medium', 'High', 'Very High'], duplicates='drop')

    quartile_summary = customer.groupby('clv_quartile', observed=True).agg(
        count=('email', 'count'),
        avg_clv=('clv_3y', 'mean'),
        avg_aov=('aov', 'mean'),
        avg_orders=('order_count', 'mean'),
    ).reset_index()

    return {
        'total_customers': len(customer),
        'avg_clv': round(customer['clv_3y'].mean(), 2),
        'median_clv': round(customer['clv_3y'].median(), 2),
        'avg_aov': round(customer['aov'].mean(), 2),
        'avg_orders': round(customer['order_count'].mean(), 2),
        'avg_lifespan_days': round(customer['lifespan_days'].mean(), 1),
        'quartiles': quartile_summary.to_dict('records'),
        'top_10': customer.nlargest(10, 'clv_3y')[['email', 'total_revenue', 'order_count', 'aov', 'clv_3y']].to_dict('records'),
    }


@safe_analysis
def analysis_09_cohorts(df, **kwargs):
    """Análisis de cohortes — retención mensual."""
    if not has_columns(df, ['email', 'date']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & orders['date'].notna()]

    orders['order_month'] = orders['date'].dt.to_period('M')

    first_purchase = orders.groupby('email')['order_month'].min().reset_index()
    first_purchase.columns = ['email', 'cohort']

    orders = orders.merge(first_purchase, on='email')
    orders['months_since'] = (orders['order_month'] - orders['cohort']).apply(lambda x: x.n if hasattr(x, 'n') else 0)

    # Build cohort matrix
    cohort_data = orders.groupby(['cohort', 'months_since'])['email'].nunique().reset_index()
    cohort_data.columns = ['cohort', 'months_since', 'customers']

    cohort_sizes = cohort_data[cohort_data['months_since'] == 0].set_index('cohort')['customers']

    # Pivot to matrix
    matrix = cohort_data.pivot(index='cohort', columns='months_since', values='customers').fillna(0)

    # Convert to retention %
    retention = matrix.div(cohort_sizes, axis=0) * 100

    # Limit to last 12 cohorts and 12 months
    retention = retention.tail(12)
    if retention.columns.max() > 12:
        retention = retention[[c for c in retention.columns if c <= 12]]

    # Convert to serializable format
    cohort_matrix = []
    for cohort in retention.index:
        row = {'cohort': str(cohort)}
        for month in retention.columns:
            row[f'M+{int(month)}'] = round(retention.loc[cohort, month], 1)
        row['cohort_size'] = int(cohort_sizes.get(cohort, 0))
        cohort_matrix.append(row)

    # Average retention curve
    avg_retention = {}
    for month in retention.columns:
        vals = retention[month].dropna()
        if len(vals) > 0:
            avg_retention[f'M+{int(month)}'] = round(vals.mean(), 1)

    return {
        'cohort_matrix': cohort_matrix,
        'avg_retention': avg_retention,
        'total_cohorts': len(retention),
    }


@safe_analysis
def analysis_10_repurchase_rate(df, **kwargs):
    """Tasa de recompra y tiempo entre compras."""
    if not has_columns(df, ['email', 'date']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & orders['date'].notna()]
    orders = orders.sort_values(['email', 'date'])

    customer_orders = orders.groupby('email').agg(
        order_count=('order_id', 'nunique') if 'order_id' in orders.columns else ('email', 'count'),
    ).reset_index()

    total_customers = len(customer_orders)
    repeat_customers = (customer_orders['order_count'] >= 2).sum()
    repurchase_rate = repeat_customers / total_customers * 100 if total_customers > 0 else 0

    # Time between purchases
    repeat = orders[orders['email'].isin(customer_orders[customer_orders['order_count'] >= 2]['email'])]
    repeat = repeat.sort_values(['email', 'date'])
    repeat['prev_date'] = repeat.groupby('email')['date'].shift(1)
    repeat['days_between'] = (repeat['date'] - repeat['prev_date']).dt.days
    repeat = repeat[repeat['days_between'].notna() & (repeat['days_between'] > 0)]

    time_stats = {}
    if len(repeat) > 0:
        time_stats = {
            'median_days': round(repeat['days_between'].median(), 1),
            'mean_days': round(repeat['days_between'].mean(), 1),
            'p25_days': round(repeat['days_between'].quantile(0.25), 1),
            'p75_days': round(repeat['days_between'].quantile(0.75), 1),
        }

    # Distribution of order counts
    order_dist = customer_orders['order_count'].value_counts().sort_index().head(10)
    distribution = [{'orders': int(k), 'customers': int(v)} for k, v in order_dist.items()]

    return {
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'repurchase_rate': round(repurchase_rate, 1),
        'time_between_purchases': time_stats,
        'order_distribution': distribution,
    }


@safe_analysis
def analysis_11_revenue_evolution(df, **kwargs):
    """Evolución revenue mensual."""
    if not has_columns(df, ['date', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['date'].notna() & orders['total'].notna()]
    orders['month'] = orders['date'].dt.to_period('M')

    monthly = orders.groupby('month').agg(
        revenue=('total', 'sum'),
        orders=('order_id', 'nunique') if 'order_id' in orders.columns else ('month', 'count'),
        avg_ticket=('total', 'mean'),
    ).reset_index()
    monthly['month_str'] = monthly['month'].astype(str)

    # MoM change
    monthly['mom_pct'] = monthly['revenue'].pct_change() * 100

    # YoY change
    monthly['yoy_pct'] = None
    for i, row in monthly.iterrows():
        yoy_month = row['month'] - 12
        match = monthly[monthly['month'] == yoy_month]
        if len(match) > 0:
            prev_rev = match.iloc[0]['revenue']
            if prev_rev > 0:
                monthly.at[i, 'yoy_pct'] = round((row['revenue'] - prev_rev) / prev_rev * 100, 1)

    # Trend direction
    if len(monthly) >= 3:
        last_3 = monthly['revenue'].tail(3).values
        if last_3[-1] > last_3[0] * 1.05:
            trend = 'up'
        elif last_3[-1] < last_3[0] * 0.95:
            trend = 'down'
        else:
            trend = 'flat'
    else:
        trend = 'insufficient_data'

    result_data = monthly[['month_str', 'revenue', 'orders', 'avg_ticket', 'mom_pct', 'yoy_pct']].copy()
    result_data = result_data.round(2)

    return {
        'monthly': result_data.to_dict('records'),
        'trend': trend,
        'total_revenue': round(orders['total'].sum(), 2),
        'total_orders': len(orders),
    }


@safe_analysis
def analysis_12_avg_ticket(df, **kwargs):
    """Ticket promedio — evolución y segmentación."""
    if not has_columns(df, ['total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['total'].notna() & (orders['total'] > 0)]

    overall_aov = orders['total'].mean()
    median_aov = orders['total'].median()

    # Distribution buckets
    bins = [0, 5000, 10000, 20000, 50000, 100000, 200000, float('inf')]
    labels = ['$0-5K', '$5-10K', '$10-20K', '$20-50K', '$50-100K', '$100-200K', '$200K+']
    orders['bucket'] = pd.cut(orders['total'], bins=bins, labels=labels, right=False)
    distribution = orders['bucket'].value_counts().sort_index()
    dist_data = [{'range': str(k), 'count': int(v)} for k, v in distribution.items() if v > 0]

    # Monthly evolution
    monthly_aov = None
    if 'date' in orders.columns and orders['date'].notna().any():
        orders['month'] = orders['date'].dt.to_period('M')
        monthly = orders.groupby('month')['total'].mean().reset_index()
        monthly['month_str'] = monthly['month'].astype(str)
        monthly_aov = monthly[['month_str', 'total']].rename(columns={'total': 'aov'}).round(2).to_dict('records')

    # New vs returning
    new_vs_return = None
    if 'email' in orders.columns and 'date' in orders.columns:
        first_dates = orders.groupby('email')['date'].min().reset_index()
        first_dates.columns = ['email', 'first_date']
        orders = orders.merge(first_dates, on='email')
        orders['is_new'] = orders['date'] == orders['first_date']
        new_aov = orders[orders['is_new']]['total'].mean()
        returning_aov = orders[~orders['is_new']]['total'].mean()
        new_vs_return = {
            'new_aov': round(new_aov, 2) if not pd.isna(new_aov) else 0,
            'returning_aov': round(returning_aov, 2) if not pd.isna(returning_aov) else 0,
        }

    return {
        'overall_aov': round(overall_aov, 2),
        'median_aov': round(median_aov, 2),
        'distribution': dist_data,
        'monthly_evolution': monthly_aov,
        'new_vs_returning': new_vs_return,
    }


@safe_analysis
def analysis_13_revenue_by_category(df, **kwargs):
    """Revenue por categoría."""
    if not has_columns(df, ['product_name', 'product_price', 'product_qty']):
        return None

    def extract_category(name):
        if pd.isna(name):
            return 'Sin categoría'
        name = str(name).strip()
        for sep in [' - ', ' | ', ' / ']:
            if sep in name:
                return name.split(sep)[0].strip()
        return name.split()[0] if name.split() else 'Sin categoría'

    df_valid = df[df['product_name'].notna()].copy()
    df_valid['category'] = df_valid['product_name'].apply(extract_category)
    df_valid['line_revenue'] = df_valid['product_price'].fillna(0) * df_valid['product_qty'].fillna(1)

    cat_stats = df_valid.groupby('category').agg(
        revenue=('line_revenue', 'sum'),
        units=('product_qty', 'sum'),
        products=('product_name', 'nunique'),
    ).reset_index()

    total = cat_stats['revenue'].sum()
    cat_stats['pct'] = round(cat_stats['revenue'] / total * 100, 1) if total > 0 else 0
    cat_stats = cat_stats.sort_values('revenue', ascending=False)

    # Trend per category
    if 'date' in df_valid.columns and df_valid['date'].notna().any():
        max_date = df_valid['date'].max()
        cutoff = max_date - pd.DateOffset(months=3)
        recent = df_valid[df_valid['date'] >= cutoff].groupby('category')['line_revenue'].sum()
        prior = df_valid[(df_valid['date'] < cutoff) & (df_valid['date'] >= cutoff - pd.DateOffset(months=3))].groupby('category')['line_revenue'].sum()
        trend = {}
        for cat in cat_stats['category']:
            r = recent.get(cat, 0)
            p = prior.get(cat, 0)
            trend[cat] = round((r - p) / p * 100, 1) if p > 0 else (100.0 if r > 0 else 0.0)
        cat_stats['trend_pct'] = cat_stats['category'].map(trend)

    return {
        'categories': cat_stats.head(20).to_dict('records'),
        'total_revenue': round(total, 2),
    }


@safe_analysis
def analysis_14_discount_impact(df, **kwargs):
    """Impacto de descuentos."""
    if not has_columns(df, ['total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['total'].notna() & (orders['total'] > 0)]

    has_discount_col = 'discount' in orders.columns and orders['discount'].notna().any()
    has_coupon_col = 'coupon' in orders.columns

    if not has_discount_col and not has_coupon_col:
        return None

    if has_discount_col:
        orders['has_discount'] = orders['discount'].fillna(0) > 0
    else:
        orders['has_discount'] = orders['coupon'].notna() & (orders['coupon'] != '')

    with_disc = orders[orders['has_discount']]
    without_disc = orders[~orders['has_discount']]

    comparison = {
        'with_discount': {
            'orders': len(with_disc),
            'aov': round(with_disc['total'].mean(), 2) if len(with_disc) > 0 else 0,
            'revenue': round(with_disc['total'].sum(), 2),
            'pct_orders': round(len(with_disc) / len(orders) * 100, 1),
        },
        'without_discount': {
            'orders': len(without_disc),
            'aov': round(without_disc['total'].mean(), 2) if len(without_disc) > 0 else 0,
            'revenue': round(without_disc['total'].sum(), 2),
            'pct_orders': round(len(without_disc) / len(orders) * 100, 1),
        },
    }

    # Top coupons
    top_coupons = None
    if has_coupon_col:
        coupons = orders[orders['coupon'].notna() & (orders['coupon'] != '')]
        if len(coupons) > 0:
            top = coupons.groupby('coupon').agg(
                uses=('order_id', 'count') if 'order_id' in coupons.columns else ('coupon', 'count'),
                revenue=('total', 'sum'),
                aov=('total', 'mean'),
            ).sort_values('revenue', ascending=False).head(10).reset_index()
            top_coupons = top.round(2).to_dict('records')

    total_discount = 0
    if has_discount_col:
        total_discount = round(orders['discount'].fillna(0).sum(), 2)

    return {
        'comparison': comparison,
        'top_coupons': top_coupons,
        'total_discount_amount': total_discount,
    }


@safe_analysis
def analysis_15_geo_heatmap(df, **kwargs):
    """Heatmap por provincia."""
    if not has_columns(df, ['state', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['state'].notna() & (orders['state'] != '') & orders['total'].notna()]

    geo = orders.groupby('state').agg(
        orders=('order_id', 'nunique') if 'order_id' in orders.columns else ('state', 'count'),
        revenue=('total', 'sum'),
        aov=('total', 'mean'),
        customers=('email', 'nunique') if 'email' in orders.columns else ('state', 'count'),
    ).reset_index()
    geo = geo.sort_values('revenue', ascending=False)

    total_revenue = geo['revenue'].sum()
    geo['pct_revenue'] = round(geo['revenue'] / total_revenue * 100, 1) if total_revenue > 0 else 0

    return {
        'provinces': geo.round(2).to_dict('records'),
        'total_provinces': len(geo),
    }


@safe_analysis
def analysis_16_shipping_vs_conversion(df, **kwargs):
    """Costo de envío vs conversión por zona."""
    if not has_columns(df, ['shipping_cost', 'state']):
        return None

    orders = get_orders(df)
    orders = orders[orders['state'].notna() & (orders['state'] != '')]

    geo_shipping = orders.groupby('state').agg(
        avg_shipping=('shipping_cost', 'mean'),
        order_count=('order_id', 'nunique') if 'order_id' in orders.columns else ('state', 'count'),
        free_shipping_pct=('shipping_cost', lambda x: round((x.fillna(0) == 0).mean() * 100, 1)),
        avg_total=('total', 'mean') if 'total' in orders.columns else ('shipping_cost', 'mean'),
    ).reset_index()
    geo_shipping = geo_shipping.round(2)

    # Flag high-cost low-volume states
    median_shipping = geo_shipping['avg_shipping'].median()
    median_orders = geo_shipping['order_count'].median()
    geo_shipping['flagged'] = (geo_shipping['avg_shipping'] > median_shipping * 1.5) & (geo_shipping['order_count'] < median_orders * 0.5)

    return {
        'states': geo_shipping.sort_values('order_count', ascending=False).to_dict('records'),
        'overall_avg_shipping': round(orders['shipping_cost'].mean(), 2),
        'overall_free_pct': round((orders['shipping_cost'].fillna(0) == 0).mean() * 100, 1),
    }


@safe_analysis
def analysis_17_cancellation_rate(df, **kwargs):
    """Tasa de cancelación general."""
    orders = get_orders(df)

    if 'order_status' in orders.columns:
        orders['is_cancelled'] = orders['order_status'].isin(['cancelled', 'Cancelada', 'cancelada'])
    elif 'cancellation_date' in orders.columns:
        orders['is_cancelled'] = orders['cancellation_date'].notna()
    else:
        return None

    total = len(orders)
    cancelled = orders['is_cancelled'].sum()
    rate = cancelled / total * 100 if total > 0 else 0

    # Trend
    monthly_rate = None
    if 'date' in orders.columns and orders['date'].notna().any():
        orders['month'] = orders['date'].dt.to_period('M')
        monthly = orders.groupby('month').agg(
            total=('is_cancelled', 'count'),
            cancelled=('is_cancelled', 'sum'),
        ).reset_index()
        monthly['rate'] = round(monthly['cancelled'] / monthly['total'] * 100, 2)
        monthly['month_str'] = monthly['month'].astype(str)
        monthly_rate = monthly[['month_str', 'rate', 'cancelled', 'total']].to_dict('records')

    # Reasons
    reasons = None
    if 'cancellation_reason' in orders.columns:
        cancelled_orders = orders[orders['is_cancelled']]
        if len(cancelled_orders) > 0:
            reason_counts = cancelled_orders['cancellation_reason'].fillna('Sin motivo').value_counts().head(10)
            reasons = [{'reason': str(k), 'count': int(v)} for k, v in reason_counts.items()]

    # By payment method
    by_payment = None
    if 'payment_method' in orders.columns:
        pm_stats = orders.groupby('payment_method').agg(
            total=('is_cancelled', 'count'),
            cancelled=('is_cancelled', 'sum'),
        ).reset_index()
        pm_stats['rate'] = round(pm_stats['cancelled'] / pm_stats['total'] * 100, 2)
        pm_stats = pm_stats[pm_stats['total'] >= 5].sort_values('rate', ascending=False)
        by_payment = pm_stats.to_dict('records')

    return {
        'total_orders': total,
        'cancelled_orders': int(cancelled),
        'cancel_rate': round(rate, 2),
        'monthly_trend': monthly_rate,
        'reasons': reasons,
        'by_payment_method': by_payment,
    }


@safe_analysis
def analysis_18_payment_mix(df, **kwargs):
    """Mix de medios de pago."""
    if not has_columns(df, ['payment_method', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['payment_method'].notna() & (orders['payment_method'] != '')]

    mix = orders.groupby('payment_method').agg(
        order_count=('order_id', 'nunique') if 'order_id' in orders.columns else ('payment_method', 'count'),
        revenue=('total', 'sum'),
        aov=('total', 'mean'),
    ).reset_index()

    total_orders = mix['order_count'].sum()
    total_revenue = mix['revenue'].sum()
    mix['pct_orders'] = round(mix['order_count'] / total_orders * 100, 1)
    mix['pct_revenue'] = round(mix['revenue'] / total_revenue * 100, 1)
    mix = mix.sort_values('revenue', ascending=False).round(2)

    # Monthly trend (top 5 methods)
    monthly_trend = None
    top_methods = mix.head(5)['payment_method'].tolist()
    if 'date' in orders.columns and orders['date'].notna().any():
        orders['month'] = orders['date'].dt.to_period('M')
        monthly = orders[orders['payment_method'].isin(top_methods)].groupby(['month', 'payment_method']).size().reset_index(name='count')
        monthly['month_str'] = monthly['month'].astype(str)
        monthly_trend = monthly[['month_str', 'payment_method', 'count']].to_dict('records')

    return {
        'payment_methods': mix.to_dict('records'),
        'monthly_trend': monthly_trend,
    }


@safe_analysis
def analysis_19_bundling(df, **kwargs):
    """Oportunidades de bundling basado en Market Basket."""
    basket = kwargs.get('basket_results')
    if not basket or basket.get('status') != 'ok' or not basket.get('pairs'):
        return None

    if not has_columns(df, ['product_name', 'product_price']):
        return None

    # Get average price per base product (basket uses normalized names)
    df_priced = df[df['product_name'].notna() & df['product_price'].notna()].copy()
    df_priced['base_product'] = df_priced['product_name'].apply(normalize_product_name)
    avg_prices = df_priced.groupby('base_product')['product_price'].mean().to_dict()

    bundles = []
    for pair in basket['pairs'][:15]:
        items = pair['items']
        prices = [avg_prices.get(item, 0) for item in items]
        sum_price = sum(prices)
        if sum_price <= 0:
            continue
        bundle_price_85 = round(sum_price * 0.85, 2)
        bundle_price_90 = round(sum_price * 0.90, 2)

        bundles.append({
            'items': items,
            'individual_total': round(sum_price, 2),
            'bundle_price_10pct': bundle_price_90,
            'bundle_price_15pct': bundle_price_85,
            'lift': pair['lift'],
            'historical_copurchases': pair['count'],
            'support': pair['support'],
        })

    return {'bundles': bundles}


@safe_analysis
def analysis_20_seasonality(df, **kwargs):
    """Estacionalidad — mes, día semana, hora."""
    if not has_columns(df, ['date', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['date'].notna() & orders['total'].notna()]

    # By month
    orders['month_num'] = orders['date'].dt.month
    month_names = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                   7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
    by_month = orders.groupby('month_num').agg(
        revenue=('total', 'sum'), orders=('total', 'count'),
    ).reset_index()
    by_month['month'] = by_month['month_num'].map(month_names)

    # By day of week
    orders['dow'] = orders['date'].dt.dayofweek
    dow_names = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    by_dow = orders.groupby('dow').agg(
        revenue=('total', 'sum'), orders=('total', 'count'),
    ).reset_index()
    by_dow['day'] = by_dow['dow'].map(dow_names)

    # By hour (if timestamps available)
    by_hour = None
    if orders['date'].dt.hour.sum() > 0:
        orders['hour'] = orders['date'].dt.hour
        by_hour = orders.groupby('hour').agg(
            revenue=('total', 'sum'), orders=('total', 'count'),
        ).reset_index().round(2).to_dict('records')

    # Peak and low
    peak_month = by_month.loc[by_month['revenue'].idxmax(), 'month'] if len(by_month) > 0 else None
    low_month = by_month.loc[by_month['revenue'].idxmin(), 'month'] if len(by_month) > 0 else None
    peak_day = by_dow.loc[by_dow['orders'].idxmax(), 'day'] if len(by_dow) > 0 else None

    return {
        'by_month': by_month[['month', 'revenue', 'orders']].round(2).to_dict('records'),
        'by_day_of_week': by_dow[['day', 'revenue', 'orders']].round(2).to_dict('records'),
        'by_hour': by_hour,
        'peak_month': peak_month,
        'low_month': low_month,
        'peak_day': peak_day,
    }


# ═══════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS — FULL ONLY (21-38)
# ═══════════════════════════════════════════════════════════════

COLORS_ES = ['negro', 'blanco', 'rojo', 'azul', 'verde', 'rosa', 'gris', 'beige',
             'marrón', 'marron', 'celeste', 'naranja', 'violeta', 'bordo', 'crudo',
             'natural', 'nude', 'camel', 'coral', 'fucsia', 'lila', 'mostaza',
             'terracota', 'turquesa', 'dorado', 'plateado', 'chocolate', 'arena',
             'hueso', 'salmón', 'salmon', 'oliva', 'tostado', 'aqua', 'ivory',
             'black', 'white', 'red', 'blue', 'green', 'pink', 'grey', 'gray',
             'brown', 'orange', 'purple', 'yellow', 'gold', 'silver']

SIZES = ['xxs', 'xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl', '2xl', '3xl',
         'unico', 'único', 'u', 'os', 'one size', 'free size',
         '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46',
         '28', '29', '30', '31', '32', '33']


def extract_color(name):
    if pd.isna(name):
        return None
    name_lower = str(name).lower()
    for color in COLORS_ES:
        if color in name_lower.split():
            return color.capitalize()
        if f' {color} ' in f' {name_lower} ':
            return color.capitalize()
    return None


def extract_size(name, sku=''):
    combined = f'{name} {sku}'.lower() if not pd.isna(name) else str(sku).lower()
    tokens = combined.replace('-', ' ').replace('/', ' ').split()
    for token in tokens:
        if token.strip() in SIZES:
            return token.strip().upper()
    return None


@safe_analysis
def analysis_21_color_affinity(df, **kwargs):
    """Afinidad entre colores."""
    if not has_columns(df, ['order_id', 'product_name']):
        return None

    df_color = df[df['product_name'].notna()].copy()
    df_color['color'] = df_color['product_name'].apply(extract_color)
    df_color = df_color[df_color['color'].notna()]

    if len(df_color) < 50:
        return None

    # Color distribution
    color_dist = df_color['color'].value_counts().head(20)
    distribution = [{'color': k, 'count': int(v)} for k, v in color_dist.items()]

    # Cross-tab by order
    orders_colors = df_color.groupby('order_id')['color'].apply(lambda x: list(set(x))).reset_index()
    multi = orders_colors[orders_colors['color'].apply(len) >= 2]

    pairs = []
    if len(multi) >= 5:
        pair_counts = Counter()
        for colors in multi['color']:
            for pair in combinations(sorted(colors), 2):
                pair_counts[pair] += 1
        for (a, b), count in pair_counts.most_common(15):
            pairs.append({'colors': [a, b], 'count': count})

    return {'distribution': distribution, 'pairs': pairs}


@safe_analysis
def analysis_22_size_affinity(df, **kwargs):
    """Afinidad entre talles."""
    if not has_columns(df, ['product_name']):
        return None

    df_size = df[df['product_name'].notna()].copy()
    sku_col = 'sku' if 'sku' in df_size.columns else ''
    df_size['size'] = df_size.apply(
        lambda r: extract_size(r['product_name'], r.get('sku', '')), axis=1
    )
    df_size = df_size[df_size['size'].notna()]

    if len(df_size) < 50:
        return None

    size_dist = df_size['size'].value_counts()
    distribution = [{'size': k, 'count': int(v)} for k, v in size_dist.items()]

    # Size patterns per customer
    customer_sizes = None
    if 'email' in df_size.columns:
        cs = df_size.groupby('email')['size'].apply(lambda x: list(set(x))).reset_index()
        multi_size = cs[cs['size'].apply(len) >= 2]
        if len(multi_size) > 0:
            customer_sizes = {
                'customers_multi_size': len(multi_size),
                'pct_multi_size': round(len(multi_size) / len(cs) * 100, 1),
            }

    return {'distribution': distribution, 'customer_size_patterns': customer_sizes}


@safe_analysis
def analysis_23_sku_variants(df, **kwargs):
    """Análisis de SKU/variantes."""
    if not has_columns(df, ['sku', 'product_name', 'product_price', 'product_qty']):
        return None

    df_valid = df[df['sku'].notna() & (df['sku'] != '') & df['product_name'].notna()].copy()
    if len(df_valid) < 20:
        return None

    df_valid['line_revenue'] = df_valid['product_price'].fillna(0) * df_valid['product_qty'].fillna(1)

    # Extract base product (product_name without variant info)
    def base_product(name):
        for sep in [' - ', ' | ', ' / ']:
            if sep in str(name):
                return str(name).split(sep)[0].strip()
        return str(name).strip()

    df_valid['base'] = df_valid['product_name'].apply(base_product)

    variant_stats = df_valid.groupby(['base', 'sku']).agg(
        revenue=('line_revenue', 'sum'),
        units=('product_qty', 'sum'),
        avg_price=('product_price', 'mean'),
    ).reset_index()

    # Products with multiple variants
    multi_variant = variant_stats.groupby('base').filter(lambda x: len(x) >= 2)
    if len(multi_variant) == 0:
        return {'variants': [], 'note': 'No multi-variant products found'}

    # Best/worst per base
    results = []
    for base in multi_variant['base'].unique()[:15]:
        variants = multi_variant[multi_variant['base'] == base].sort_values('revenue', ascending=False)
        results.append({
            'product': base,
            'variants': variants[['sku', 'revenue', 'units', 'avg_price']].round(2).to_dict('records'),
        })

    return {'products': results}


@safe_analysis
def analysis_24_product_lifecycle(df, **kwargs):
    """Ciclo de vida del producto."""
    if not has_columns(df, ['product_name', 'product_price', 'product_qty', 'date']):
        return None

    df_valid = df[df['product_name'].notna() & df['date'].notna()].copy()
    df_valid['line_revenue'] = df_valid['product_price'].fillna(0) * df_valid['product_qty'].fillna(1)
    df_valid['month'] = df_valid['date'].dt.to_period('M')

    # Products with 6+ months of data
    product_months = df_valid.groupby('product_name')['month'].nunique()
    eligible = product_months[product_months >= 6].index

    if len(eligible) == 0:
        return None

    lifecycles = []
    for product in list(eligible)[:20]:
        prod_data = df_valid[df_valid['product_name'] == product]
        monthly = prod_data.groupby('month')['line_revenue'].sum().sort_index()

        # Classify stage based on last 3 months trend
        if len(monthly) >= 3:
            last_3 = monthly.tail(3).values
            first_3 = monthly.head(3).values
            recent_avg = last_3.mean()
            early_avg = first_3.mean()
            mid_avg = monthly.values[len(monthly)//3:2*len(monthly)//3].mean() if len(monthly) >= 6 else early_avg

            if recent_avg > mid_avg * 1.1 and recent_avg > early_avg:
                stage = 'Growth'
            elif recent_avg < mid_avg * 0.8:
                stage = 'Decline'
            elif recent_avg > early_avg * 1.5:
                stage = 'Growth'
            elif abs(recent_avg - mid_avg) / mid_avg < 0.15 if mid_avg > 0 else True:
                stage = 'Maturity'
            else:
                stage = 'Introduction'
        else:
            stage = 'Introduction'

        lifecycles.append({
            'product': product,
            'stage': stage,
            'months_active': len(monthly),
            'total_revenue': round(monthly.sum(), 2),
            'monthly_revenue': [{'month': str(m), 'revenue': round(v, 2)} for m, v in monthly.items()],
        })

    # Summary by stage
    stage_counts = Counter(lc['stage'] for lc in lifecycles)

    return {'products': lifecycles, 'stage_summary': dict(stage_counts)}


@safe_analysis
def analysis_25_upgrade_pattern(df, **kwargs):
    """Patrón de upgrade — clientes que aumentan AOV."""
    if not has_columns(df, ['email', 'date', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & orders['date'].notna() & (orders['total'] > 0)]

    customer_orders = orders.groupby('email').filter(lambda x: len(x) >= 3)
    if len(customer_orders) == 0:
        return None

    customer_orders = customer_orders.sort_values(['email', 'date'])

    upgrades = []
    for email, group in customer_orders.groupby('email'):
        totals = group['total'].values
        if len(totals) >= 3:
            first_half_avg = totals[:len(totals)//2].mean()
            second_half_avg = totals[len(totals)//2:].mean()
            if first_half_avg > 0:
                change_pct = (second_half_avg - first_half_avg) / first_half_avg * 100
                upgrades.append({
                    'email': email,
                    'first_half_aov': round(first_half_avg, 2),
                    'second_half_aov': round(second_half_avg, 2),
                    'change_pct': round(change_pct, 1),
                })

    upgraders = [u for u in upgrades if u['change_pct'] > 20]
    downgraders = [u for u in upgrades if u['change_pct'] < -20]

    return {
        'total_analyzed': len(upgrades),
        'upgraders': len(upgraders),
        'upgrader_pct': round(len(upgraders) / len(upgrades) * 100, 1) if upgrades else 0,
        'downgraders': len(downgraders),
        'avg_upgrade_pct': round(np.mean([u['change_pct'] for u in upgraders]), 1) if upgraders else 0,
        'top_upgraders': sorted(upgraders, key=lambda x: x['change_pct'], reverse=True)[:10],
    }


@safe_analysis
def analysis_26_vip_customers(df, **kwargs):
    """Clientes VIP — top 10%."""
    if not has_columns(df, ['email', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & (orders['total'] > 0)]

    customer = orders.groupby('email').agg(
        revenue=('total', 'sum'),
        orders=('order_id', 'nunique') if 'order_id' in orders.columns else ('email', 'count'),
        aov=('total', 'mean'),
    ).reset_index()

    cutoff = customer['revenue'].quantile(0.90)
    vips = customer[customer['revenue'] >= cutoff].sort_values('revenue', ascending=False)

    # VIP favorite products
    vip_emails = set(vips['email'])
    vip_orders = df[df['email'].isin(vip_emails)]
    fav_products = None
    if 'product_name' in vip_orders.columns:
        fav_products = vip_orders['product_name'].value_counts().head(10)
        fav_products = [{'product': k, 'count': int(v)} for k, v in fav_products.items()]

    # VIP by state
    vip_states = None
    if 'state' in orders.columns:
        vip_state_orders = orders[orders['email'].isin(vip_emails)]
        if 'state' in vip_state_orders.columns:
            vip_states = vip_state_orders['state'].value_counts().head(10)
            vip_states = [{'state': k, 'count': int(v)} for k, v in vip_states.items()]

    return {
        'vip_count': len(vips),
        'vip_pct': round(len(vips) / len(customer) * 100, 1),
        'vip_revenue': round(vips['revenue'].sum(), 2),
        'vip_revenue_pct': round(vips['revenue'].sum() / customer['revenue'].sum() * 100, 1),
        'avg_orders': round(vips['orders'].mean(), 1),
        'avg_aov': round(vips['aov'].mean(), 2),
        'top_vips': vips.head(15).round(2).to_dict('records'),
        'favorite_products': fav_products,
        'top_states': vip_states,
    }


@safe_analysis
def analysis_27_churn(df, **kwargs):
    """Análisis de churn."""
    if not has_columns(df, ['email', 'date']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & orders['date'].notna()]
    orders = orders.sort_values(['email', 'date'])

    max_date = orders['date'].max()

    customer = orders.groupby('email').agg(
        order_count=('order_id', 'nunique') if 'order_id' in orders.columns else ('email', 'count'),
        last_order=('date', 'max'),
        first_order=('date', 'min'),
    ).reset_index()

    # Avg purchase interval per customer
    repeat = customer[customer['order_count'] >= 2].copy()
    if len(repeat) > 0:
        repeat['lifespan'] = (repeat['last_order'] - repeat['first_order']).dt.days
        repeat['avg_interval'] = repeat['lifespan'] / (repeat['order_count'] - 1)
        global_avg_interval = repeat['avg_interval'].median()
    else:
        global_avg_interval = 90  # default 90 days

    churn_threshold = max(global_avg_interval * 2, 60)

    customer['days_since_last'] = (max_date - customer['last_order']).dt.days
    customer['is_churned'] = customer['days_since_last'] > churn_threshold

    churned = customer[customer['is_churned']]
    active = customer[~customer['is_churned']]

    # Last products of churned customers
    churned_products = None
    if 'product_name' in df.columns:
        churned_emails = set(churned['email'])
        churned_orders = df[df['email'].isin(churned_emails) & df['product_name'].notna()]
        if len(churned_orders) > 0:
            prods = churned_orders['product_name'].value_counts().head(10)
            churned_products = [{'product': k, 'count': int(v)} for k, v in prods.items()]

    return {
        'total_customers': len(customer),
        'churned': len(churned),
        'churn_rate': round(len(churned) / len(customer) * 100, 1),
        'active': len(active),
        'churn_threshold_days': round(churn_threshold, 0),
        'avg_purchase_interval': round(global_avg_interval, 1),
        'last_products_churned': churned_products,
    }


@safe_analysis
def analysis_28_revenue_by_channel(df, **kwargs):
    """Revenue por canal."""
    if not has_columns(df, ['channel', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['channel'].notna() & (orders['channel'] != '')]

    if orders['channel'].nunique() < 2:
        return None

    channel_stats = orders.groupby('channel').agg(
        revenue=('total', 'sum'),
        orders=('order_id', 'nunique') if 'order_id' in orders.columns else ('channel', 'count'),
        aov=('total', 'mean'),
    ).reset_index()

    total_rev = channel_stats['revenue'].sum()
    channel_stats['pct'] = round(channel_stats['revenue'] / total_rev * 100, 1)
    channel_stats = channel_stats.sort_values('revenue', ascending=False).round(2)

    return {'channels': channel_stats.to_dict('records')}


@safe_analysis
def analysis_29_price_analysis(df, **kwargs):
    """Análisis de precio — distribución y sweet spots."""
    if not has_columns(df, ['product_price', 'product_qty']):
        return None

    prices = df[df['product_price'].notna() & (df['product_price'] > 0)].copy()

    if len(prices) < 20:
        return None

    # Distribution
    p_min = prices['product_price'].min()
    p_max = prices['product_price'].max()
    p_mean = prices['product_price'].mean()
    p_median = prices['product_price'].median()

    # Sweet spots: price points with highest volume
    prices['price_bucket'] = pd.cut(prices['product_price'], bins=20)
    volume_by_price = prices.groupby('price_bucket', observed=True)['product_qty'].sum().sort_values(ascending=False)
    sweet_spots = []
    for bucket, vol in volume_by_price.head(5).items():
        sweet_spots.append({
            'range': f'${bucket.left:,.0f}-${bucket.right:,.0f}',
            'volume': int(vol),
        })

    return {
        'min_price': round(p_min, 2),
        'max_price': round(p_max, 2),
        'mean_price': round(p_mean, 2),
        'median_price': round(p_median, 2),
        'sweet_spots': sweet_spots,
        'total_items': len(prices),
    }


@safe_analysis
def analysis_30_city_penetration(df, **kwargs):
    """Penetración por ciudad."""
    if not has_columns(df, ['city', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['city'].notna() & (orders['city'] != '')]

    city_stats = orders.groupby('city').agg(
        orders=('order_id', 'nunique') if 'order_id' in orders.columns else ('city', 'count'),
        revenue=('total', 'sum'),
    ).reset_index().sort_values('revenue', ascending=False)

    return {
        'top_cities': city_stats.head(20).round(2).to_dict('records'),
        'total_cities': len(city_stats),
    }


@safe_analysis
def analysis_31_shipping_by_zone(df, **kwargs):
    """Medio de envío por zona."""
    if not has_columns(df, ['shipping_method', 'state']):
        return None

    orders = get_orders(df)
    orders = orders[orders['shipping_method'].notna() & orders['state'].notna()]

    crosstab = pd.crosstab(orders['state'], orders['shipping_method'])
    # Top 10 states × top 5 methods
    top_states = orders['state'].value_counts().head(10).index
    top_methods = orders['shipping_method'].value_counts().head(5).index
    crosstab = crosstab.loc[crosstab.index.isin(top_states), crosstab.columns.isin(top_methods)]

    result = []
    for state in crosstab.index:
        row = {'state': state}
        for method in crosstab.columns:
            row[method] = int(crosstab.loc[state, method])
        result.append(row)

    return {'crosstab': result, 'methods': list(crosstab.columns)}


@safe_analysis
def analysis_32_fulfillment_time(df, **kwargs):
    """Tiempo de fulfillment."""
    if not has_columns(df, ['date', 'shipping_date']):
        return None

    orders = get_orders(df)
    orders = orders[orders['date'].notna() & orders['shipping_date'].notna()]
    orders['fulfillment_days'] = (orders['shipping_date'] - orders['date']).dt.days
    orders = orders[orders['fulfillment_days'] >= 0]

    if len(orders) < 10:
        return None

    stats = {
        'median_days': round(orders['fulfillment_days'].median(), 1),
        'mean_days': round(orders['fulfillment_days'].mean(), 1),
        'p90_days': round(orders['fulfillment_days'].quantile(0.90), 1),
        'total_orders': len(orders),
    }

    # By shipping method
    by_method = None
    if 'shipping_method' in orders.columns:
        method_stats = orders.groupby('shipping_method')['fulfillment_days'].agg(['median', 'mean', 'count']).reset_index()
        method_stats.columns = ['method', 'median_days', 'mean_days', 'orders']
        method_stats = method_stats[method_stats['orders'] >= 5].round(1)
        by_method = method_stats.to_dict('records')

    # Trend
    monthly_trend = None
    if orders['date'].notna().any():
        orders['month'] = orders['date'].dt.to_period('M')
        monthly = orders.groupby('month')['fulfillment_days'].median().reset_index()
        monthly['month_str'] = monthly['month'].astype(str)
        monthly_trend = monthly[['month_str', 'fulfillment_days']].round(1).to_dict('records')

    stats['by_method'] = by_method
    stats['monthly_trend'] = monthly_trend
    return stats


@safe_analysis
def analysis_33_channel_analysis(df, **kwargs):
    """Análisis completo de canal."""
    if not has_columns(df, ['channel', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['channel'].notna() & (orders['channel'] != '')]

    channel = orders.groupby('channel').agg(
        orders=('order_id', 'nunique') if 'order_id' in orders.columns else ('channel', 'count'),
        revenue=('total', 'sum'),
        aov=('total', 'mean'),
        customers=('email', 'nunique') if 'email' in orders.columns else ('channel', 'count'),
    ).reset_index()

    # Cancel rate by channel
    if 'order_status' in orders.columns:
        cancel = orders.groupby('channel').apply(
            lambda x: (x['order_status'].isin(['cancelled', 'Cancelada'])).mean() * 100
        ).reset_index(name='cancel_rate')
        channel = channel.merge(cancel, on='channel', how='left')

    channel = channel.sort_values('revenue', ascending=False).round(2)

    return {'channels': channel.to_dict('records')}


@safe_analysis
def analysis_34_free_shipping(df, **kwargs):
    """Eficiencia de envío gratis."""
    if not has_columns(df, ['shipping_cost', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['total'].notna() & (orders['total'] > 0)]

    orders['free_shipping'] = orders['shipping_cost'].fillna(0) == 0

    free = orders[orders['free_shipping']]
    paid = orders[~orders['free_shipping']]

    if len(free) < 5 or len(paid) < 5:
        return None

    comparison = {
        'free_shipping': {
            'orders': len(free),
            'aov': round(free['total'].mean(), 2),
            'revenue': round(free['total'].sum(), 2),
        },
        'paid_shipping': {
            'orders': len(paid),
            'aov': round(paid['total'].mean(), 2),
            'revenue': round(paid['total'].sum(), 2),
        },
    }

    # Retention comparison
    retention = None
    if 'email' in orders.columns and 'date' in orders.columns:
        free_emails = set(free['email'].dropna())
        paid_emails = set(paid['email'].dropna())

        free_repeat = orders[orders['email'].isin(free_emails)].groupby('email').size()
        paid_repeat = orders[orders['email'].isin(paid_emails)].groupby('email').size()

        retention = {
            'free_avg_orders': round(free_repeat.mean(), 2),
            'paid_avg_orders': round(paid_repeat.mean(), 2),
        }

    return {'comparison': comparison, 'retention': retention}


@safe_analysis
def analysis_35_forecast(df, **kwargs):
    """Forecast de ventas — SMA + tendencia lineal."""
    if not has_columns(df, ['date', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['date'].notna() & orders['total'].notna()]
    orders['month'] = orders['date'].dt.to_period('M')

    monthly = orders.groupby('month')['total'].sum().sort_index()

    if len(monthly) < 6:
        return None

    # Linear regression on monthly data
    x = np.arange(len(monthly))
    y = monthly.values.astype(float)

    # y = mx + b
    n = len(x)
    sum_x = x.sum()
    sum_y = y.sum()
    sum_xy = (x * y).sum()
    sum_x2 = (x * x).sum()

    m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    b = (sum_y - m * sum_x) / n

    # Residual std for confidence band
    y_pred = m * x + b
    residual_std = np.std(y - y_pred)

    # Forecast 6 months
    last_period = monthly.index[-1]
    forecast = []
    for i in range(1, 7):
        future_x = len(monthly) - 1 + i
        predicted = m * future_x + b
        predicted = max(predicted, 0)
        period = last_period + i

        # 3-month SMA
        sma_values = list(monthly.values[-3:]) + [f['predicted'] for f in forecast]
        sma = np.mean(sma_values[-3:])

        # Average of linear and SMA
        blended = (predicted + sma) / 2

        forecast.append({
            'month': str(period),
            'predicted': round(blended, 2),
            'lower': round(max(blended - residual_std, 0), 2),
            'upper': round(blended + residual_std, 2),
        })

    # Historical for context
    historical = [{'month': str(m), 'revenue': round(v, 2)} for m, v in monthly.tail(12).items()]

    return {
        'historical': historical,
        'forecast': forecast,
        'trend_slope': round(m, 2),
        'trend_direction': 'up' if m > 0 else 'down' if m < 0 else 'flat',
    }


@safe_analysis
def analysis_36_cross_sell_recommendations(df, **kwargs):
    """Recomendación de cross-sell para top productos."""
    basket = kwargs.get('basket_results')
    if not basket or basket.get('status') != 'ok' or not basket.get('pairs'):
        return None

    # Build recommendation map from basket pairs
    recs = defaultdict(list)
    for pair in basket['pairs']:
        a, b = pair['items']
        recs[a].append({'product': b, 'lift': pair['lift'], 'support': pair['support']})
        recs[b].append({'product': a, 'lift': pair['lift'], 'support': pair['support']})

    # Top 20 products by revenue
    if has_columns(df, ['product_name', 'product_price', 'product_qty']):
        df_valid = df[df['product_name'].notna()].copy()
        df_valid['line_revenue'] = df_valid['product_price'].fillna(0) * df_valid['product_qty'].fillna(1)
        top_products = df_valid.groupby('product_name')['line_revenue'].sum().nlargest(20).index
    else:
        top_products = list(recs.keys())[:20]

    recommendations = []
    for product in top_products:
        if product in recs:
            sorted_recs = sorted(recs[product], key=lambda x: x['lift'], reverse=True)[:3]
            recommendations.append({
                'product': product,
                'cross_sell': sorted_recs,
            })

    return {'recommendations': recommendations}


@safe_analysis
def analysis_37_pricing_analysis(df, **kwargs):
    """Análisis de pricing por categoría."""
    if not has_columns(df, ['product_name', 'product_price', 'product_qty']):
        return None

    def extract_category(name):
        if pd.isna(name):
            return 'Sin categoría'
        for sep in [' - ', ' | ', ' / ']:
            if sep in str(name):
                return str(name).split(sep)[0].strip()
        return str(name).split()[0]

    df_valid = df[df['product_name'].notna() & (df['product_price'] > 0)].copy()
    df_valid['category'] = df_valid['product_name'].apply(extract_category)
    df_valid['line_revenue'] = df_valid['product_price'] * df_valid['product_qty'].fillna(1)

    categories = []
    for cat, group in df_valid.groupby('category'):
        if len(group) < 5:
            continue
        avg_price = group['product_price'].mean()
        median_price = group['product_price'].median()

        # Volume-weighted average price
        weighted_price = (group['product_price'] * group['product_qty']).sum() / group['product_qty'].sum()

        # Identify under/over priced products
        products = group.groupby('product_name').agg(
            avg_price=('product_price', 'mean'),
            units=('product_qty', 'sum'),
        ).reset_index()

        under_priced = products[products['avg_price'] < weighted_price * 0.7].nlargest(3, 'units')
        over_priced = products[products['avg_price'] > weighted_price * 1.5].nsmallest(3, 'units')

        categories.append({
            'category': cat,
            'avg_price': round(avg_price, 2),
            'median_price': round(median_price, 2),
            'weighted_price': round(weighted_price, 2),
            'product_count': products['product_name'].nunique(),
            'under_priced': under_priced.to_dict('records') if len(under_priced) > 0 else [],
            'over_priced': over_priced.to_dict('records') if len(over_priced) > 0 else [],
        })

    return {'categories': sorted(categories, key=lambda x: x['product_count'], reverse=True)[:15]}


@safe_analysis
def analysis_38_niche_clusters(df, **kwargs):
    """Identificación de nichos — clustering de clientes."""
    if not has_columns(df, ['email', 'date', 'total']):
        return None

    orders = get_orders(df)
    orders = orders[orders['email'].notna() & orders['date'].notna() & (orders['total'] > 0)]

    max_date = orders['date'].max()

    customer = orders.groupby('email').agg(
        total_spend=('total', 'sum'),
        order_count=('order_id', 'nunique') if 'order_id' in orders.columns else ('email', 'count'),
        aov=('total', 'mean'),
        last_order=('date', 'max'),
    ).reset_index()

    customer['days_since_last'] = (max_date - customer['last_order']).dt.days

    if len(customer) < 20:
        return None

    # Simple quartile-based segmentation (no sklearn needed)
    features = ['total_spend', 'order_count', 'aov', 'days_since_last']
    for f in features:
        customer[f'{f}_q'] = pd.qcut(customer[f].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop').astype(int)

    # K-means with numpy (k=4)
    X = customer[features].values.astype(float)
    # Normalize
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    X_range = X_max - X_min
    X_range[X_range == 0] = 1
    X_norm = (X - X_min) / X_range

    k = min(4, len(customer) // 5)
    if k < 2:
        k = 2

    # Simple k-means
    np.random.seed(42)
    centroids = X_norm[np.random.choice(len(X_norm), k, replace=False)]

    for _ in range(50):
        # Assign clusters
        distances = np.sqrt(((X_norm[:, np.newaxis] - centroids[np.newaxis, :]) ** 2).sum(axis=2))
        labels = distances.argmin(axis=1)

        # Update centroids
        new_centroids = np.array([X_norm[labels == i].mean(axis=0) if (labels == i).any() else centroids[i] for i in range(k)])

        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    customer['cluster'] = labels

    # Profile clusters
    clusters = []
    for c in range(k):
        cluster_data = customer[customer['cluster'] == c]
        clusters.append({
            'cluster': c,
            'size': len(cluster_data),
            'pct': round(len(cluster_data) / len(customer) * 100, 1),
            'avg_spend': round(cluster_data['total_spend'].mean(), 2),
            'avg_orders': round(cluster_data['order_count'].mean(), 2),
            'avg_aov': round(cluster_data['aov'].mean(), 2),
            'avg_recency': round(cluster_data['days_since_last'].mean(), 1),
        })

    # Label clusters
    clusters.sort(key=lambda x: x['avg_spend'], reverse=True)
    cluster_labels = ['High Value', 'Medium-High', 'Medium-Low', 'Low Value']
    for i, c in enumerate(clusters):
        c['label'] = cluster_labels[i] if i < len(cluster_labels) else f'Cluster {c["cluster"]}'

    return {'clusters': clusters, 'total_customers': len(customer)}


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

LITE_ANALYSES = [
    (1, 'Market Basket Analysis', 'Producto', analysis_01_market_basket),
    (2, 'Afinidad entre categorías', 'Producto', analysis_02_category_affinity),
    (3, 'Ranking de productos', 'Producto', analysis_03_product_ranking),
    (4, 'Productos ancla', 'Producto', analysis_04_anchor_products),
    (5, 'Long tail 80/20', 'Producto', analysis_05_long_tail),
    (6, 'Productos con alta tasa de cancelación', 'Producto', analysis_06_cancellation_by_product),
    (7, 'Segmentación RFM', 'Cliente', analysis_07_rfm),
    (8, 'Customer Lifetime Value', 'Cliente', analysis_08_clv),
    (9, 'Análisis de cohortes', 'Cliente', analysis_09_cohorts),
    (10, 'Tasa de recompra', 'Cliente', analysis_10_repurchase_rate),
    (11, 'Evolución revenue mensual', 'Revenue', analysis_11_revenue_evolution),
    (12, 'Ticket promedio', 'Revenue', analysis_12_avg_ticket),
    (13, 'Revenue por categoría', 'Revenue', analysis_13_revenue_by_category),
    (14, 'Impacto de descuentos', 'Revenue', analysis_14_discount_impact),
    (15, 'Heatmap por provincia', 'Geográfico', analysis_15_geo_heatmap),
    (16, 'Costo de envío vs conversión', 'Geográfico', analysis_16_shipping_vs_conversion),
    (17, 'Tasa de cancelación', 'Operativo', analysis_17_cancellation_rate),
    (18, 'Mix de medios de pago', 'Operativo', analysis_18_payment_mix),
    (19, 'Oportunidades de bundling', 'Estratégico', analysis_19_bundling),
    (20, 'Estacionalidad', 'Estratégico', analysis_20_seasonality),
]

FULL_ANALYSES = LITE_ANALYSES + [
    (21, 'Afinidad entre colores', 'Producto', analysis_21_color_affinity),
    (22, 'Afinidad entre talles', 'Producto', analysis_22_size_affinity),
    (23, 'Análisis de SKU/variantes', 'Producto', analysis_23_sku_variants),
    (24, 'Ciclo de vida del producto', 'Producto', analysis_24_product_lifecycle),
    (25, 'Patrón de upgrade', 'Cliente', analysis_25_upgrade_pattern),
    (26, 'Clientes VIP', 'Cliente', analysis_26_vip_customers),
    (27, 'Análisis de churn', 'Cliente', analysis_27_churn),
    (28, 'Revenue por canal', 'Revenue', analysis_28_revenue_by_channel),
    (29, 'Análisis de precio', 'Revenue', analysis_29_price_analysis),
    (30, 'Penetración por ciudad', 'Geográfico', analysis_30_city_penetration),
    (31, 'Medio de envío por zona', 'Geográfico', analysis_31_shipping_by_zone),
    (32, 'Tiempo de fulfillment', 'Operativo', analysis_32_fulfillment_time),
    (33, 'Análisis de canal', 'Operativo', analysis_33_channel_analysis),
    (34, 'Eficiencia de envío gratis', 'Operativo', analysis_34_free_shipping),
    (35, 'Forecast de ventas', 'Estratégico', analysis_35_forecast),
    (36, 'Recomendación de cross-sell', 'Estratégico', analysis_36_cross_sell_recommendations),
    (37, 'Análisis de pricing', 'Estratégico', analysis_37_pricing_analysis),
    (38, 'Identificación de nichos', 'Estratégico', analysis_38_niche_clusters),
]


def run_analyses(df, mode='lite'):
    """Run all analyses for the given mode."""
    analyses = LITE_ANALYSES if mode == 'lite' else FULL_ANALYSES
    results = {}

    # Run Market Basket first (needed by bundling and cross-sell)
    basket_result = analysis_01_market_basket(df)
    results['1'] = {
        'number': 1,
        'name': 'Market Basket Analysis',
        'category': 'Producto',
        'data': basket_result,
    }

    for num, name, category, func in analyses:
        if num == 1:
            continue  # Already ran

        kwargs = {}
        if num in [19, 36]:  # Bundling and cross-sell need basket results
            kwargs['basket_results'] = basket_result

        print(f"  Running #{num}: {name}...", file=sys.stderr)
        result = func(df, **kwargs)

        results[str(num)] = {
            'number': num,
            'name': name,
            'category': category,
            'data': result,
        }

    return results


def compute_summary(df):
    """Compute hero metrics."""
    orders = get_orders(df)
    valid = orders[orders['total'].notna() & (orders['total'] > 0)]

    total_revenue = valid['total'].sum()
    total_orders = len(valid)
    unique_customers = valid['email'].nunique() if 'email' in valid.columns else 0
    avg_ticket = valid['total'].mean()

    # Date range
    date_min = df['date'].min() if 'date' in df.columns else None
    date_max = df['date'].max() if 'date' in df.columns else None

    # Trends (last 3 months vs prior 3 months)
    trends = {}
    if 'date' in valid.columns and valid['date'].notna().any():
        cutoff = date_max - pd.DateOffset(months=3)
        recent = valid[valid['date'] >= cutoff]
        prior = valid[(valid['date'] < cutoff) & (valid['date'] >= cutoff - pd.DateOffset(months=3))]

        for metric, col in [('revenue', 'total'), ('orders', None), ('customers', 'email'), ('ticket', 'total')]:
            if metric == 'orders':
                r_val = len(recent)
                p_val = len(prior)
            elif metric == 'customers':
                r_val = recent[col].nunique() if col in recent.columns else 0
                p_val = prior[col].nunique() if col in prior.columns else 0
            elif metric == 'ticket':
                r_val = recent[col].mean() if len(recent) > 0 else 0
                p_val = prior[col].mean() if len(prior) > 0 else 0
            else:
                r_val = recent[col].sum()
                p_val = prior[col].sum()

            if p_val > 0:
                trends[metric] = round((r_val - p_val) / p_val * 100, 1)
            else:
                trends[metric] = None

    return {
        'total_revenue': round(total_revenue, 2),
        'total_orders': total_orders,
        'unique_customers': unique_customers,
        'avg_ticket': round(avg_ticket, 2),
        'date_min': str(date_min.date()) if date_min is not None and pd.notna(date_min) else None,
        'date_max': str(date_max.date()) if date_max is not None and pd.notna(date_max) else None,
        'trends': trends,
        'total_rows': len(df),
    }


def main():
    parser = argparse.ArgumentParser(description='eCommerce BI Analysis')
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--mode', choices=['lite', 'full'], default='lite', help='Analysis mode')
    parser.add_argument('--output', required=True, help='Output JSON path')
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"ERROR: File not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading CSV: {args.csv}", file=sys.stderr)
    df, platform, encoding, delimiter = load_csv(args.csv)
    print(f"Platform: {platform} | Encoding: {encoding} | Delimiter: '{delimiter}' | Rows: {len(df)}", file=sys.stderr)

    print(f"Computing summary...", file=sys.stderr)
    summary = compute_summary(df)
    summary['platform'] = platform

    print(f"Running {args.mode} analyses...", file=sys.stderr)
    analyses = run_analyses(df, args.mode)

    output = {
        'mode': args.mode,
        'platform': platform,
        'summary': summary,
        'analyses': analyses,
    }

    # Convert any remaining non-serializable types
    def make_serializable(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, (pd.Timestamp,)):
            return str(obj)
        if isinstance(obj, (pd.Period,)):
            return str(obj)
        if pd.isna(obj):
            return None
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
