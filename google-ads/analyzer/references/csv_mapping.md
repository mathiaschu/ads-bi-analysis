# Google Ads CSV & API Field Mapping

Maps Google Ads CSV export columns and MCP API (GAQL) fields to canonical internal names.

---

## Fingerprint Detection

### Campaign Report
**Required columns (at least 3 must be present):**
- "Campaign" or "Campaign name"
- "Impressions"
- "Clicks"
- "Cost" or "Cost (ARS)" or "Cost (USD)"

**Confidence boost:**
- "Conversions", "Conv. rate", "Avg. CPC", "Impr. share"

### Keyword Report
**Required columns:**
- "Keyword" or "Search keyword"
- "Quality score" or "Quality Score"
- "Match type"

### Search Term Report
**Required columns:**
- "Search term"
- "Added / Excluded" or "Keyword / Placement"

### Ad Report
**Required columns:**
- "Ad group"
- "Headline 1" or "Responsive search ad headlines"
- "Ad strength" or "Description 1"

**Detection logic:**
```python
def detect_report_type(headers: list[str]) -> str:
    header_set = {h.strip() for h in headers}

    # Search term report
    if "Search term" in header_set:
        return "search_term"

    # Keyword report
    kw_markers = {"Keyword", "Search keyword", "Quality score", "Quality Score"}
    if len(header_set & kw_markers) >= 2:
        return "keyword"

    # Ad report
    ad_markers = {"Headline 1", "Responsive search ad headlines", "Ad strength", "Description 1"}
    if len(header_set & ad_markers) >= 1 and "Ad group" in header_set:
        return "ad"

    # Campaign report (default)
    return "campaign"
```

---

## Currency Detection

Google Ads CSV exports include currency in parentheses in cost-related headers:
- `Cost (ARS)` → ARS
- `Avg. CPC (USD)` → USD
- `Cost` (sin parenthesis) → buscar en datos o preguntar

```python
import re

def detect_currency(headers: list[str]) -> str:
    for h in headers:
        match = re.search(r'\(([A-Z]{3})\)', h)
        if match:
            return match.group(1)
    return "auto"
```

---

## CSV Column → Canonical Name

### Campaign / Ad Group dimensions

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Campaign | campaign_name | str | |
| Campaign name | campaign_name | str | Alias |
| Campaign ID | campaign_id | str | |
| Campaign type | campaign_type | str | Search, Shopping, PMax, Display, Video |
| Campaign status | campaign_status | str | Enabled, Paused, Removed |
| Campaign subtype | campaign_subtype | str | |
| Ad group | ad_group_name | str | |
| Ad group name | ad_group_name | str | Alias |
| Ad group ID | ad_group_id | str | |
| Ad group status | ad_group_status | str | |
| Ad group type | ad_group_type | str | |
| Network | network | str | Search, Content, YouTube, etc. |
| Network (with search partners) | network_with_partners | str | |

### Date / Time

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Day | date | str | YYYY-MM-DD |
| Date | date | str | Alias |
| Week | week | str | |
| Month | month | str | |
| Quarter | quarter | str | |
| Year | year | str | |
| Day of week | day_of_week | str | Monday, Tuesday, etc. |
| Hour of day | hour_of_day | int | 0-23 |

### Core volume metrics

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Impressions | impressions | int | |
| Clicks | clicks | int | |
| Interactions | interactions | int | |
| Interaction rate | interaction_rate | float | Percentage |

### Cost metrics

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Cost | cost | float | Strip currency, remove separators |
| Cost (ARS) | cost | float | Strip "ARS" |
| Cost (USD) | cost | float | Strip "USD" |
| Avg. CPC | avg_cpc | float | |
| Avg. CPC (ARS) | avg_cpc | float | |
| Avg. CPC (USD) | avg_cpc | float | |
| Avg. CPM | avg_cpm | float | |
| Avg. CPM (ARS) | avg_cpm | float | |
| Avg. cost | avg_cost | float | |

### CTR / Rates

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| CTR | ctr | float | Percentage string, e.g. "2.34%" |
| Interaction rate | interaction_rate | float | Percentage |

### Conversion metrics

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Conversions | conversions | float | Primary conversions only |
| All conv. | all_conversions | float | Primary + secondary |
| Conv. rate | conversion_rate | float | Percentage |
| All conv. rate | all_conversion_rate | float | Percentage |
| Cost / conv. | cost_per_conversion | float | CPA |
| Cost / all conv. | cost_per_all_conversion | float | |
| Conv. value | conversion_value | float | Revenue |
| All conv. value | all_conversion_value | float | |
| Conv. value / cost | conv_value_per_cost | float | ROAS |
| All conv. value / cost | all_conv_value_per_cost | float | |
| Value / conv. | value_per_conversion | float | Avg conversion value |
| View-through conv. | view_through_conversions | float | |

### Impression Share metrics

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Search impr. share | search_impression_share | float | Percentage, e.g. "45.23%" or "< 10%" |
| Impr. share | impression_share | float | |
| Search lost IS (rank) | search_lost_is_rank | float | Percentage |
| Search lost IS (budget) | search_lost_is_budget | float | Percentage |
| Display impr. share | display_impression_share | float | |
| Display lost IS (rank) | display_lost_is_rank | float | |
| Display lost IS (budget) | display_lost_is_budget | float | |
| Search top IS | search_top_is | float | |
| Search abs. top IS | search_abs_top_is | float | |
| Search exact match IS | search_exact_match_is | float | |
| Click share | click_share | float | |

### Quality Score (keyword level)

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Quality score | quality_score | int | 1-10 or "--" |
| Quality Score | quality_score | int | Alias capitalization |
| Exp. CTR | expected_ctr | str | Above/Below average |
| Ad relevance | ad_relevance | str | Above/Below average |
| Landing page exp. | landing_page_experience | str | Above/Below average |
| Historical Quality Score | hist_quality_score | int | |

### Keyword / Search Term columns

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Keyword | keyword | str | |
| Search keyword | keyword | str | Alias |
| Match type | match_type | str | Exact, Phrase, Broad |
| Keyword state | keyword_status | str | |
| Search term | search_term | str | |
| Added / Excluded | search_term_status | str | Added, Excluded, None |
| Keyword / Placement | keyword_or_placement | str | |

### Ad / RSA columns

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Headline 1 | headline_1 | str | |
| Headline 2 | headline_2 | str | |
| Headline 3 | headline_3 | str | |
| Description 1 | description_1 | str | |
| Description 2 | description_2 | str | |
| Responsive search ad headlines | rsa_headlines | str | Pipe-separated |
| Responsive search ad descriptions | rsa_descriptions | str | Pipe-separated |
| Ad strength | ad_strength | str | Excellent, Good, Average, Poor |
| Ad type | ad_type | str | |
| Final URL | final_url | str | |
| Ad status | ad_status | str | |

### Bidding

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Bid strategy type | bid_strategy_type | str | tCPA, tROAS, MaxConv, etc. |
| Bid strategy name | bid_strategy_name | str | |
| Target CPA | target_cpa | float | |
| Target ROAS | target_roas | float | Percentage (e.g. "400%") |
| Max CPC limit | max_cpc | float | |

### PMax / Asset Group columns

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Asset group | asset_group_name | str | |
| Asset group name | asset_group_name | str | Alias |
| Asset group status | asset_group_status | str | |
| Listing group | listing_group | str | Shopping |

### Geographic

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Country/Territory | country | str | |
| Region | region | str | |
| City | city | str | |
| Most specific location | location | str | |
| Location type | location_type | str | Physical, Interest |

### Device

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Device | device | str | Computers, Mobile phones, Tablets |

### Auction Insights

| CSV Column | Canonical Name | Type | Notes |
|---|---|---|---|
| Display URL domain | competitor_domain | str | |
| Impression share | auction_is | float | |
| Overlap rate | auction_overlap | float | |
| Outranking share | auction_outranking | float | |
| Position above rate | auction_pos_above | float | |
| Top of page rate | auction_top_rate | float | |
| Abs. top of page rate | auction_abs_top_rate | float | |

---

## MCP API (GAQL) → Canonical Name

Fields returned by `mcp__google-ads__search` queries.

### Campaign metrics (from `campaign` resource)

| GAQL Field | Canonical Name | Type | Notes |
|---|---|---|---|
| campaign.name | campaign_name | str | |
| campaign.id | campaign_id | str | |
| campaign.status | campaign_status | str | ENABLED, PAUSED, REMOVED |
| campaign.advertising_channel_type | campaign_type | str | SEARCH, SHOPPING, PERFORMANCE_MAX, etc. |
| campaign.bidding_strategy_type | bid_strategy_type | str | TARGET_CPA, TARGET_ROAS, etc. |
| campaign.target_cpa.target_cpa_micros | target_cpa | float | **÷ 1,000,000** |
| campaign.target_roas.target_roas | target_roas | float | Multiplier (e.g. 4.0 = 400%) |
| metrics.impressions | impressions | int | |
| metrics.clicks | clicks | int | |
| metrics.cost_micros | cost | float | **÷ 1,000,000** |
| metrics.ctr | ctr | float | Decimal (0.0234 = 2.34%) — **× 100 for display** |
| metrics.average_cpc | avg_cpc | float | **Micros ÷ 1,000,000** |
| metrics.average_cpm | avg_cpm | float | **Micros ÷ 1,000,000** |
| metrics.conversions | conversions | float | Primary only |
| metrics.all_conversions | all_conversions | float | Primary + secondary |
| metrics.conversions_value | conversion_value | float | |
| metrics.all_conversions_value | all_conversion_value | float | |
| metrics.cost_per_conversion | cost_per_conversion | float | **Micros ÷ 1,000,000** |
| metrics.cost_per_all_conversions | cost_per_all_conversion | float | **Micros ÷ 1,000,000** |
| metrics.conversions_from_interactions_rate | conversion_rate | float | Decimal — **× 100** |
| metrics.value_per_conversion | value_per_conversion | float | |

### Impression Share (from `campaign` resource)

| GAQL Field | Canonical Name | Type | Notes |
|---|---|---|---|
| metrics.search_impression_share | search_impression_share | float | Decimal — **× 100** |
| metrics.search_budget_lost_impression_share | search_lost_is_budget | float | Decimal — **× 100** |
| metrics.search_rank_lost_impression_share | search_lost_is_rank | float | Decimal — **× 100** |
| metrics.search_top_impression_share | search_top_is | float | Decimal — **× 100** |
| metrics.search_absolute_top_impression_share | search_abs_top_is | float | Decimal — **× 100** |
| metrics.search_exact_match_impression_share | search_exact_match_is | float | Decimal — **× 100** |

### Keyword metrics (from `keyword_view` resource)

| GAQL Field | Canonical Name | Type | Notes |
|---|---|---|---|
| ad_group_criterion.keyword.text | keyword | str | |
| ad_group_criterion.keyword.match_type | match_type | str | EXACT, PHRASE, BROAD |
| ad_group_criterion.quality_info.quality_score | quality_score | int | 1-10 |
| ad_group_criterion.quality_info.creative_quality_score | ad_relevance | str | ABOVE_AVERAGE, AVERAGE, BELOW_AVERAGE |
| ad_group_criterion.quality_info.search_predicted_ctr | expected_ctr | str | ABOVE_AVERAGE, AVERAGE, BELOW_AVERAGE |
| ad_group_criterion.quality_info.post_click_quality_score | landing_page_experience | str | ABOVE_AVERAGE, AVERAGE, BELOW_AVERAGE |

### Search Term metrics (from `search_term_view` resource)

| GAQL Field | Canonical Name | Type | Notes |
|---|---|---|---|
| search_term_view.search_term | search_term | str | |
| search_term_view.status | search_term_status | str | ADDED, EXCLUDED, NONE |

### Asset Group metrics (PMax, from `asset_group` resource)

| GAQL Field | Canonical Name | Type | Notes |
|---|---|---|---|
| asset_group.name | asset_group_name | str | |
| asset_group.status | asset_group_status | str | |
| asset_group.ad_strength | ad_strength | str | EXCELLENT, GOOD, AVERAGE, POOR |

### Segments

| GAQL Field | Canonical Name | Type | Notes |
|---|---|---|---|
| segments.date | date | str | YYYY-MM-DD |
| segments.day_of_week | day_of_week | str | MONDAY, TUESDAY, etc. |
| segments.device | device | str | MOBILE, DESKTOP, TABLET |
| segments.hour | hour_of_day | int | 0-23 |
| segments.ad_network_type | network | str | SEARCH, CONTENT, etc. |

### Geographic (from `geographic_view` resource)

| GAQL Field | Canonical Name | Type | Notes |
|---|---|---|---|
| geographic_view.country_criterion_id | country_id | str | |
| geographic_view.location_type | location_type | str | |

---

## Parsing Notes

### Cost / micros
- **GAQL API**: all cost fields are in **micros** (cost_micros, average_cpc, etc.) — **ALWAYS divide by 1,000,000**
- **CSV export**: cost is already in display currency (no micros conversion needed)

### Percentage columns
- **CSV**: exported as strings like `"2.34%"` or `"2.34"` — strip `%` and parse as float
- **GAQL API**: returned as decimals (0.0234) — **multiply by 100** for display
- Special: `"< 10%"` for low impression share — parse as `10.0` with a `"<"` flag

### Quality Score
- CSV may show `"--"` for keywords without QS data — treat as `None`
- GAQL returns `0` for unknown — treat as `None`

### Impression Share special values
- `"< 10%"` → flag as approximate, store as 10.0
- `"--"` → `None` (no data)

### Currency / cost columns in CSV
- Strip currency codes and symbols: `$`, `ARS`, `USD`, `€`
- Remove thousands separators: `,` (US) or `.` (AR/EU)
- Decimal separator: `.` (US) or `,` (AR/EU) — detect by context

```python
import re

def parse_cost(value: str) -> float:
    if not value or str(value).strip() in ("", "-", "--", "N/A"):
        return 0.0
    clean = re.sub(r'[A-Z]{3}|\$|€|£', '', str(value)).strip()
    clean = clean.replace('%', '')
    # Detect AR/EU format: ends with ,XX
    if re.search(r',\d{2}$', clean):
        clean = clean.replace('.', '').replace(',', '.')
    else:
        clean = clean.replace(',', '')
    return float(clean) if clean else 0.0


def parse_percentage(value: str) -> tuple[float, bool]:
    """Returns (value, is_approximate)."""
    if not value or str(value).strip() in ("", "-", "--", "N/A"):
        return None, False
    s = str(value).strip()
    approx = s.startswith("<") or s.startswith(">")
    clean = re.sub(r'[<>%\s]', '', s)
    try:
        return float(clean), approx
    except ValueError:
        return None, False
```

### Date formats
- CSV: usually `YYYY-MM-DD` or `MMM DD, YYYY` (e.g. "Jan 15, 2024") or `MM/DD/YYYY`
- GAQL API: always `YYYY-MM-DD`

### Empty / null values
- Metrics (int/float): `""`, `"-"`, `"--"`, `"N/A"`, `None` → `0.0`
- Text/dimension fields: empty → `None`
- Percentage: `"--"` → `None` (no data available)

### Campaign type normalization
- `SEARCH` → "Search"
- `SHOPPING` → "Shopping"
- `PERFORMANCE_MAX` → "PMax"
- `DISPLAY` → "Display"
- `VIDEO` → "Video"
- `DEMAND_GEN` → "Demand Gen"
- CSV: "Search", "Performance Max", "Shopping", etc. — normalize to short names

### QS component normalization
- `ABOVE_AVERAGE` → "Above average"
- `AVERAGE` → "Average"
- `BELOW_AVERAGE` → "Below average"
