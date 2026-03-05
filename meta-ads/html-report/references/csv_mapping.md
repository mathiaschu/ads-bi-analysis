# Meta Ads CSV & API Field Mapping

Maps Meta Ads Manager CSV export columns and MCP API JSON fields to canonical internal names.

---

## Fingerprint Detection

How to detect that a file is a Meta Ads Manager export:

**Required columns (at least 2 of these must be present):**
- "Campaign name" or "Ad set name" or "Ad name"
- "Impressions"
- "Amount spent" or "Amount spent (ARS)" or "Amount spent (USD)"

**Confidence boost (optional but common):**
- "Reach", "Frequency", "CPM (cost per 1,000 impressions)"
- "Link clicks", "CTR (link click-through rate)"
- "Purchase ROAS (return on ad spend)"

**Detection logic:**
```python
def is_meta_ads_csv(headers: list[str]) -> bool:
    required_any = [
        {"Campaign name", "Ad set name", "Ad name"},
        {"Impressions"},
    ]
    spend_variants = {"Amount spent", "Amount spent (ARS)", "Amount spent (USD)"}
    header_set = set(headers)
    has_name_col = bool(header_set & required_any[0])
    has_impressions = bool(header_set & required_any[1])
    has_spend = bool(header_set & spend_variants)
    return has_name_col and has_impressions and has_spend
```

---

## CSV Column → Canonical Name

### Dimension / Breakdown columns

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Campaign name | campaign_name | str | |
| Ad set name | adset_name | str | |
| Ad name | ad_name | str | |
| Day | date_start | str | Format: YYYY-MM-DD |
| Date | date_start | str | Alias for "Day" |
| Week | date_start | str | Week-level breakdowns |
| Month | date_start | str | Month-level breakdowns |
| Placement | placement | str | e.g. "Facebook Feed" |
| Platform | platform | str | e.g. "Facebook", "Instagram" |
| Device | device | str | e.g. "Mobile", "Desktop" |
| Country | country | str | ISO 2-letter code |
| Region | region | str | |
| Age | age | str | e.g. "18-24" |
| Gender | gender | str | "Male", "Female", "Unknown" |
| Campaign ID | campaign_id | str | |
| Ad set ID | adset_id | str | |
| Ad ID | ad_id | str | |
| Objective | objective | str | |
| Buying type | buying_type | str | |
| Bid strategy | bid_strategy | str | |
| Delivery | delivery | str | "Active", "Paused", etc. |
| Status | status | str | |
| Reporting starts | date_start | str | Alternative date column |
| Reporting ends | date_stop | str | |

### Spend

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Amount spent (ARS) | spend | float | Strip "ARS", remove thousand separators |
| Amount spent (USD) | spend | float | Strip "USD" |
| Amount spent | spend | float | Generic fallback |

### Core volume metrics

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Impressions | impressions | int | |
| Reach | reach | int | |
| Frequency | frequency | float | |
| Clicks (all) | clicks | int | |
| Link clicks | link_clicks | int | |
| Unique clicks (all) | unique_clicks | int | |
| Unique link clicks | unique_link_clicks | int | |
| Landing page views | landing_page_views | int | |
| Post engagements | post_engagements | int | |
| Post reactions | post_reactions | int | |
| Post comments | post_comments | int | |
| Post shares | post_shares | int | |
| Page likes | page_likes | int | |

### Cost / efficiency metrics

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| CPC (cost per link click) | cpc_link | float | |
| CPC (all) | cpc | float | |
| CPM (cost per 1,000 impressions) | cpm | float | |
| CPP (cost per 1,000 people reached) | cpp | float | |
| CTR (link click-through rate) | ctr_link | float | Percentage, e.g. "2.34" |
| CTR (all) | ctr | float | Percentage |
| Cost per landing page view | cost_per_lpv | float | |
| Cost per unique click (all) | cost_per_unique_click | float | |

### Results (objective-dependent)

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Results | results | float | Depends on campaign objective |
| Cost per result | cost_per_result | float | |
| Result rate | result_rate | float | Percentage |

### eCommerce conversions

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Purchases | purchases | int | |
| Purchase conversion value | purchase_value | float | |
| Purchase ROAS (return on ad spend) | purchase_roas | float | |
| Cost per purchase | cost_per_purchase | float | |
| Adds to cart | add_to_cart | int | |
| Cost per add to cart | cost_per_add_to_cart | float | |
| Checkouts initiated | checkout_initiated | int | |
| Cost per checkout initiated | cost_per_checkout | float | |
| Website purchases | website_purchases | int | |
| Website purchase ROAS | website_purchase_roas | float | |
| Website purchase conversion value | website_purchase_value | float | |

### Lead generation

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Leads | leads | int | |
| Cost per lead | cost_per_lead | float | |
| On-Facebook leads | onsite_leads | int | |
| Lead form opens | lead_form_opens | int | |

### Video metrics

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| ThruPlays | thruplay | int | |
| Cost per ThruPlay | cost_per_thruplay | float | |
| 3-second video plays | video_3s | int | |
| 2-second continuous video plays | video_2s | int | |
| Video plays at 25% | video_p25 | int | |
| Video plays at 50% | video_p50 | int | |
| Video plays at 75% | video_p75 | int | |
| Video plays at 100% | video_p100 | int | |
| Video average play time | video_avg_play_time | float | Seconds |

### Ad quality rankings

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Quality ranking | quality_ranking | str | "Above average", "Average", "Below average" |
| Engagement rate ranking | engagement_ranking | str | Same values |
| Conversion rate ranking | conversion_ranking | str | Same values |

---

## MCP API JSON → Canonical Name

Fields returned by `mcp__meta-ads__get_insights` response objects.

### Identifiers

| API Field | Canonical Name | Type |
|---|---|---|
| campaign_id | campaign_id | str |
| campaign_name | campaign_name | str |
| adset_id | adset_id | str |
| adset_name | adset_name | str |
| ad_id | ad_id | str |
| ad_name | ad_name | str |
| date_start | date_start | str |
| date_stop | date_stop | str |
| account_id | account_id | str |
| account_name | account_name | str |
| objective | objective | str |

### Core metrics

| API Field | Canonical Name | Type |
|---|---|---|
| spend | spend | float |
| impressions | impressions | int |
| reach | reach | int |
| frequency | frequency | float |
| clicks | clicks | int |
| inline_link_clicks | link_clicks | int |
| unique_clicks | unique_clicks | int |
| unique_inline_link_clicks | unique_link_clicks | int |
| cpc | cpc | float |
| inline_link_clicks / clicks (derived) | cpc_link | float |
| cpm | cpm | float |
| cpp | cpp | float |
| ctr | ctr | float |
| inline_link_click_ctr | ctr_link | float |

### Actions array (nested)

The API returns actions as an array: `[{"action_type": "...", "value": "..."}]`

| action_type value | Canonical Name | Type |
|---|---|---|
| purchase | purchases | int |
| offsite_conversion.fb_pixel_purchase | purchases | int |
| add_to_cart | add_to_cart | int |
| offsite_conversion.fb_pixel_add_to_cart | add_to_cart | int |
| initiate_checkout | checkout_initiated | int |
| offsite_conversion.fb_pixel_initiate_checkout | checkout_initiated | int |
| lead | leads | int |
| offsite_conversion.fb_pixel_lead | leads | int |
| landing_page_view | landing_page_views | int |
| page_engagement | post_engagements | int |
| post_reaction | post_reactions | int |
| comment | post_comments | int |
| post | post_shares | int |
| video_view | video_3s | int |
| video_thruplay_watched | thruplay | int |
| video_p25_watched | video_p25 | int |
| video_p50_watched | video_p50 | int |
| video_p75_watched | video_p75 | int |
| video_p100_watched | video_p100 | int |

### Action values array (nested)

`action_values` array: `[{"action_type": "...", "value": "..."}]`

| action_type value | Canonical Name | Type |
|---|---|---|
| purchase | purchase_value | float |
| offsite_conversion.fb_pixel_purchase | purchase_value | float |

### Cost per action array (nested)

`cost_per_action_type` array.

| action_type value | Canonical Name | Type |
|---|---|---|
| purchase | cost_per_purchase | float |
| lead | cost_per_lead | float |
| landing_page_view | cost_per_lpv | float |
| add_to_cart | cost_per_add_to_cart | float |
| initiate_checkout | cost_per_checkout | float |

### ROAS (nested in `website_purchase_roas`)

| API Field | Canonical Name | Type |
|---|---|---|
| website_purchase_roas[0].value | purchase_roas | float |

### Ad quality (nested in `ad_relevance_diagnostics`)

| API Field | Canonical Name | Type |
|---|---|---|
| quality_score_organic | quality_ranking | str |
| quality_score_ectr | engagement_ranking | str |
| quality_score_ecvr | conversion_ranking | str |

---

## Parsing Notes

### Currency / spend columns
- Strip currency codes and symbols: `$`, `ARS`, `USD`, `€`, `R$`, `MXN`
- Remove thousands separators: `,` (US format) or `.` (AR/EU format)
- Decimal separator: `.` (US) or `,` (AR/EU) — detect by context
- Example: `"$ 1.234,56"` (AR) → `1234.56`
- Example: `"1,234.56"` (US) → `1234.56`

```python
import re

def parse_spend(value: str) -> float:
    if not value or str(value).strip() in ("", "-", "N/A"):
        return 0.0
    # Remove currency symbols and codes
    clean = re.sub(r'[A-Z]{3}|\$|€|£|R\$', '', str(value)).strip()
    # Detect AR/EU format: ends with ,XX (2 digits after last comma)
    if re.search(r',\d{2}$', clean):
        clean = clean.replace('.', '').replace(',', '.')
    else:
        clean = clean.replace(',', '')
    return float(clean) if clean else 0.0
```

### Date formats
- Meta CSV: `YYYY-MM-DD` (standard)
- Occasional: `MM/DD/YYYY` (US locale exports) — detect and convert
- API: always `YYYY-MM-DD`

### Empty / null values
- Metrics (int/float): empty string `""`, `"-"`, `"N/A"`, `None` → `0.0`
- Text / dimension fields: empty string → `None`
- Percentage columns: stored as plain numbers (e.g. `"2.34"` means 2.34%, NOT 0.0234)

### Integer vs float
- Columns that should be integers: impressions, reach, clicks, link_clicks, purchases, leads, add_to_cart, checkout_initiated, video_* counts
- Parse as float first, then cast to int (avoids errors with "1,234.00" format)

### Percentage columns (CTR, result_rate)
- Meta exports as plain percentage: `"2.34"` = 2.34%
- Do NOT divide by 100 when storing; apply division only when displaying as decimal ratio

### ROAS
- Meta exports ROAS as a multiplier: `"3.45"` = 3.45x
- API also returns as multiplier

### Ranking values normalization
- `"Above average (top 10% of ads)"` → `"Above average"`
- `"Average (between 35% - 55%)"` → `"Average"`
- `"Below average (bottom 35% of ads)"` → `"Below average"`
- Strip parenthetical explanations, keep only the label
