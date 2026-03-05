# Campaign Nomenclatura Parser

Defines how to parse campaign, ad set, and ad names into structured components for creative analysis.

---

## Supported Formats

### 1. Standard Format

**Pattern:** `{Producto} | {Formato} | {Etapa} | {Creador} | {Variacion}`

**Separator:** ` | ` (pipe with a space on each side)

**Example:** `Remera Básica | UGC | TOF | Maria | v1`

**Fields:**

| Position | Field | Description | Examples |
|---|---|---|---|
| 0 | producto | Product name or collection | "Remera Básica", "Campera Puffer", "Pack Verano" |
| 1 | formato | Creative format type | UGC, Estático, Video, Carrusel, Catálogo, Colección |
| 2 | etapa | Funnel stage | TOF, MOF, BOF |
| 3 | creador | Creator or producer name | "Maria", "Juan", "Agencia" |
| 4 | variacion | Version or variant identifier | v1, v2, A, B, C |

**Regex:**
```python
STANDARD_PATTERN = re.compile(
    r'^(?P<producto>.+?)\s*\|\s*(?P<formato>.+?)\s*\|\s*(?P<etapa>.+?)\s*\|\s*(?P<creador>.+?)\s*\|\s*(?P<variacion>.+)$'
)
```

**Partial match (fewer than 5 segments):**
If the name contains ` | ` but fewer than 5 segments, fill what is available left-to-right and leave remaining fields as `None`.

---

### 2. Alternative Format

**Pattern:** `{Etapa}_{Producto}_{Formato}_{Variacion}`

**Separator:** `_` (underscore)

**Example:** `TOF_Campera-Puffer_Video_v2`

**Fields:**

| Position | Field | Description | Examples |
|---|---|---|---|
| 0 | etapa | Funnel stage | TOF, MOF, BOF |
| 1 | producto | Product name (hyphens replace spaces) | "Campera-Puffer", "Remera-Basica" |
| 2 | formato | Creative format type | Video, UGC, Estatico, Carrusel |
| 3 | variacion | Version or variant identifier | v1, v2, A, B |

**Notes:**
- `creador` is not present in this format → `None`
- Hyphens in producto should be replaced with spaces: `"Campera-Puffer"` → `"Campera Puffer"`

**Regex:**
```python
ALTERNATIVE_PATTERN = re.compile(
    r'^(?P<etapa>TOF|MOF|BOF|TOFU|MOFU|BOFU)_(?P<producto>[^_]+)_(?P<formato>[^_]+)_(?P<variacion>[^_]+)$',
    re.IGNORECASE
)
```

---

## Auto-Detection Algorithm

Given a list of names (campaigns, ad sets, or ads), detect which format is in use.

```python
def detect_format(names: list[str]) -> str:
    """
    Returns: "standard", "alternative", or "unknown"
    """
    sample = [n for n in names if n and str(n).strip()][:10]
    if not sample:
        return "unknown"

    pipe_count = sum(1 for n in sample if " | " in str(n))
    underscore_funnel_count = sum(
        1 for n in sample
        if re.match(r'^(TOF|MOF|BOF|TOFU|MOFU|BOFU)_', str(n), re.IGNORECASE)
    )

    pipe_ratio = pipe_count / len(sample)
    underscore_ratio = underscore_funnel_count / len(sample)

    if pipe_ratio > 0.5:
        return "standard"
    if underscore_ratio > 0.5:
        return "alternative"
    return "unknown"
```

**Decision rules:**
1. Take first 10 non-empty names from the dataset (campaign names, ad set names, or ad names — prefer ad names for best signal)
2. If ` | ` appears in more than 50% of the sample → **Standard format**
3. If the name starts with a funnel stage token (`TOF`, `MOF`, `BOF`, `TOFU`, `MOFU`, `BOFU`) followed by `_` in more than 50% of the sample → **Alternative**
4. Otherwise → **unknown** (use raw names, do not attempt parsing)

---

## Custom Format

Users can provide a custom regex with named groups matching the canonical field names.

**Supported named groups:** `producto`, `formato`, `etapa`, `creador`, `variacion`

**Example custom pattern:**
```python
custom_pattern = r'(?P<etapa>\w+)-(?P<producto>[\w\s]+)-(?P<variacion>v\d+)'
```

**Usage:**
```python
def parse_custom(name: str, pattern: str) -> dict:
    match = re.match(pattern, name, re.IGNORECASE)
    if not match:
        return {"raw": name}
    result = match.groupdict()
    # Fill missing canonical fields with None
    for field in ("producto", "formato", "etapa", "creador", "variacion"):
        result.setdefault(field, None)
    return result
```

---

## Field Normalization

Apply these normalizations after parsing, regardless of source format.

### formato

Normalize to the canonical set: `UGC`, `Estático`, `Video`, `Carrusel`, `Catálogo`, `Colección`

| Raw value (case-insensitive) | Normalized |
|---|---|
| ugc, ugc-video | UGC |
| estatico, estático, static, imagen, image | Estático |
| video, vid | Video |
| carrusel, carousel, carrusel-video | Carrusel |
| catalogo, catálogo, catalog, dpa, dco | Catálogo |
| coleccion, colección, collection | Colección |
| reels, reel, short | Video |
| historia, historia-video, story, stories | Video |

```python
FORMAT_MAP = {
    "ugc": "UGC",
    "ugc-video": "UGC",
    "estatico": "Estático",
    "estático": "Estático",
    "static": "Estático",
    "imagen": "Estático",
    "image": "Estático",
    "video": "Video",
    "vid": "Video",
    "reels": "Video",
    "reel": "Video",
    "short": "Video",
    "historia": "Video",
    "historia-video": "Video",
    "story": "Video",
    "stories": "Video",
    "carrusel": "Carrusel",
    "carousel": "Carrusel",
    "carrusel-video": "Carrusel",
    "catalogo": "Catálogo",
    "catálogo": "Catálogo",
    "catalog": "Catálogo",
    "dpa": "Catálogo",
    "dco": "Catálogo",
    "coleccion": "Colección",
    "colección": "Colección",
    "collection": "Colección",
}

def normalize_formato(raw: str) -> str:
    if not raw:
        return raw
    return FORMAT_MAP.get(raw.strip().lower(), raw.strip())
```

### etapa

Normalize to: `TOF`, `MOF`, `BOF`

| Raw value (case-insensitive) | Normalized |
|---|---|
| tof, tofu, top, top-of-funnel | TOF |
| mof, mofu, mid, middle, middle-of-funnel | MOF |
| bof, bofu, bottom, bottom-of-funnel, retargeting, retarget, ret | BOF |

```python
STAGE_MAP = {
    "tof": "TOF",
    "tofu": "TOF",
    "top": "TOF",
    "top-of-funnel": "TOF",
    "mof": "MOF",
    "mofu": "MOF",
    "mid": "MOF",
    "middle": "MOF",
    "middle-of-funnel": "MOF",
    "bof": "BOF",
    "bofu": "BOF",
    "bottom": "BOF",
    "bottom-of-funnel": "BOF",
    "retargeting": "BOF",
    "retarget": "BOF",
    "ret": "BOF",
}

def normalize_etapa(raw: str) -> str:
    if not raw:
        return raw
    return STAGE_MAP.get(raw.strip().lower(), raw.strip().upper())
```

### creador

Apply title case.

```python
def normalize_creador(raw: str) -> str:
    if not raw:
        return raw
    return raw.strip().title()
```

### producto

Apply title case. If format is Alternative (hyphens as separators), replace hyphens with spaces first.

```python
def normalize_producto(raw: str, source_format: str = "standard") -> str:
    if not raw:
        return raw
    value = raw.strip()
    if source_format == "alternative":
        value = value.replace("-", " ")
    return value.title()
```

### variacion

Keep as-is but strip whitespace. Lowercase `V` prefix if followed by digits for consistency.

```python
def normalize_variacion(raw: str) -> str:
    if not raw:
        return raw
    value = raw.strip()
    # Normalize: "V1" → "v1", "V 1" → "v1"
    value = re.sub(r'^[Vv]\s*(\d+)$', lambda m: f"v{m.group(1)}", value)
    return value
```

---

## Parsed Output Structure

All parsers return a dict with this schema:

```python
{
    "raw": str,           # Original unmodified name
    "format": str,        # "standard", "alternative", "custom", or "unknown"
    "producto": str | None,
    "formato": str | None,  # Normalized
    "etapa": str | None,    # Normalized: TOF, MOF, BOF
    "creador": str | None,  # Normalized: title case
    "variacion": str | None,
    "parsed": bool,       # True if at least 2 fields were extracted
}
```

**Example outputs:**

```python
# Standard
parse("Remera Básica | UGC | TOF | Maria | v1")
# → {
#     "raw": "Remera Básica | UGC | TOF | Maria | v1",
#     "format": "standard",
#     "producto": "Remera Básica",
#     "formato": "UGC",
#     "etapa": "TOF",
#     "creador": "Maria",
#     "variacion": "v1",
#     "parsed": True
# }

# Alternative
parse("TOF_Campera-Puffer_Video_v2")
# → {
#     "raw": "TOF_Campera-Puffer_Video_v2",
#     "format": "alternative",
#     "producto": "Campera Puffer",
#     "formato": "Video",
#     "etapa": "TOF",
#     "creador": None,
#     "variacion": "v2",
#     "parsed": True
# }

# Unknown
parse("agosto retargeting dinamico")
# → {
#     "raw": "agosto retargeting dinamico",
#     "format": "unknown",
#     "producto": None,
#     "formato": None,
#     "etapa": None,
#     "creador": None,
#     "variacion": None,
#     "parsed": False
# }
```

---

## Usage in Creative Analysis

When analyzing creative performance across a dataset:

1. Detect format once using `detect_format()` on ad names (preferred) or campaign names
2. Parse all names using the detected format
3. Group and aggregate metrics by `formato`, `etapa`, `producto`, or `creador`
4. For rows with `parsed: False`, group them under a single "Sin nomenclatura" bucket
5. Flag clients with low parse rate (<50% parsed) so they can be advised to adopt a standard naming convention
