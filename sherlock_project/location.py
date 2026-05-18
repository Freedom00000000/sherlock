"""Sherlock Location Detection Module

Extracts location data from social media profile pages.
Inspired by:
  - detect.location (github.com/KrauseFx/detect.location)
  - apple-corelocation-experiments (github.com/acheong08/apple-corelocation-experiments)
  - Phone-number-location-tracker-using-python
    (github.com/problemsolvewithridoy/Phone-number-location-tracker-using-python)
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional

try:
    import phonenumbers
    import phonenumbers.geocoder as _pn_geocoder
    import phonenumbers.carrier as _pn_carrier
    _PHONENUMBERS_AVAILABLE = True
except ImportError:
    _PHONENUMBERS_AVAILABLE = False


@dataclass
class LocationResult:
    """Holds all location data extracted from a profile page."""
    coordinates: Optional[tuple[float, float]] = None  # (latitude, longitude)
    place_name: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    raw_text: Optional[str] = None        # free-form location text from profile
    phone_numbers: list[str] = field(default_factory=list)  # E.164 phone numbers found
    phone_location: Optional[str] = None  # location string derived from a phone number
    phone_carrier: Optional[str] = None   # carrier name derived from a phone number

    def __bool__(self) -> bool:
        return any([
            self.coordinates,
            self.place_name,
            self.region,
            self.country,
            self.raw_text,
            self.phone_numbers,
            self.phone_location,
        ])

    def __str__(self) -> str:
        parts: list[str] = []
        if self.coordinates:
            lat, lon = self.coordinates
            parts.append(f"{lat:.5f}, {lon:.5f}")
        if self.place_name:
            parts.append(self.place_name)
        if self.region:
            parts.append(self.region)
        # Show country only when it adds info beyond what phone_location already covers
        if self.country and not (
            self.phone_location
            and (self.country in self.phone_location or len(self.country) == 2)
        ):
            parts.append(self.country)
        if self.phone_location and self.phone_location not in parts:
            parts.append(f"[phone] {self.phone_location}")
        if self.raw_text and not parts:
            parts.append(self.raw_text)
        return " | ".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Regex patterns for HTML geo meta tags
# ---------------------------------------------------------------------------

_META_CONTENT = r'content=["\']([^"\']+)["\']'

_GEO_POSITION_RE = re.compile(
    r'<meta[^>]+name=["\']geo\.position["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_GEO_POSITION_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+name=["\']geo\.position["\']', re.IGNORECASE)
_ICBM_RE = re.compile(
    r'<meta[^>]+name=["\']ICBM["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_ICBM_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+name=["\']ICBM["\']', re.IGNORECASE)
_GEO_PLACENAME_RE = re.compile(
    r'<meta[^>]+name=["\']geo\.placename["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_GEO_PLACENAME_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+name=["\']geo\.placename["\']', re.IGNORECASE)
_GEO_REGION_RE = re.compile(
    r'<meta[^>]+name=["\']geo\.region["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_GEO_REGION_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+name=["\']geo\.region["\']', re.IGNORECASE)
_OG_LOCALITY_RE = re.compile(
    r'<meta[^>]+property=["\']og:locality["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_OG_LOCALITY_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+property=["\']og:locality["\']', re.IGNORECASE)
_OG_REGION_RE = re.compile(
    r'<meta[^>]+property=["\']og:region["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_OG_REGION_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+property=["\']og:region["\']', re.IGNORECASE)
_OG_COUNTRY_RE = re.compile(
    r'<meta[^>]+property=["\']og:country-name["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_OG_COUNTRY_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+property=["\']og:country-name["\']', re.IGNORECASE)
_PLACE_LAT_RE = re.compile(
    r'<meta[^>]+property=["\']place:location:latitude["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_PLACE_LAT_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+property=["\']place:location:latitude["\']', re.IGNORECASE)
_PLACE_LON_RE = re.compile(
    r'<meta[^>]+property=["\']place:location:longitude["\'][^>]+' + _META_CONTENT, re.IGNORECASE)
_PLACE_LON_REV = re.compile(
    r'<meta[^>]+' + _META_CONTENT + r'[^>]+property=["\']place:location:longitude["\']', re.IGNORECASE)

_JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

# Coordinate pair: "lat, lon" or "lat;lon"
_COORD_RE = re.compile(r'(-?\d{1,3}\.\d+)[,;\s]+(-?\d{1,3}\.\d+)')

# Phone numbers in international format: +<country_code><number>
# Also matches formats like (123) 456-7890 for US numbers (parsed with default region)
_PHONE_E164_RE = re.compile(r'\+\d[\d\s\-().]{6,18}\d')
# Strips HTML tags and whitespace for cleaner phone parsing
_HTML_TAG_RE = re.compile(r'<[^>]+>')


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _first_match(*patterns: re.Pattern, text: str) -> Optional[str]:
    for pattern in patterns:
        m = pattern.search(text)
        if m:
            return m.group(1).strip()
    return None


def _parse_coordinate_pair(raw: str) -> Optional[tuple[float, float]]:
    m = _COORD_RE.search(raw)
    if m:
        try:
            lat, lon = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except ValueError:
            pass
    return None


def _extract_from_json_ld(html: str) -> LocationResult:
    """Extract location from JSON-LD structured data blocks."""
    result = LocationResult()
    for m in _JSON_LD_RE.finditer(html):
        try:
            data = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue

            location_obj = (
                item.get("homeLocation")
                or item.get("workLocation")
                or item.get("address")
            )
            if location_obj and isinstance(location_obj, dict):
                result.place_name = (
                    location_obj.get("addressLocality")
                    or location_obj.get("name")
                    or result.place_name
                )
                result.region = location_obj.get("addressRegion") or result.region
                result.country = location_obj.get("addressCountry") or result.country

            geo = item.get("geo")
            if geo and isinstance(geo, dict) and result.coordinates is None:
                try:
                    lat = float(geo.get("latitude", ""))
                    lon = float(geo.get("longitude", ""))
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        result.coordinates = (lat, lon)
                except (ValueError, TypeError):
                    pass

            if result:
                break

    return result


# ---------------------------------------------------------------------------
# Phone number location (inspired by Phone-number-location-tracker-using-python)
# ---------------------------------------------------------------------------

def location_from_phone(number: str, default_region: Optional[str] = None) -> LocationResult:
    """Resolve a phone number string to a LocationResult.

    Uses the `phonenumbers` library (must be installed) to derive the
    geographic region and carrier associated with the number.

    Args:
        number: Phone number string in any format (E.164 preferred).
        default_region: ISO 3166-1 alpha-2 region code used when the number
            lacks a country prefix (e.g. "US").

    Returns:
        A LocationResult populated from the phone number metadata, or an
        empty (falsy) LocationResult if parsing fails or the library is
        unavailable.
    """
    result = LocationResult()

    if not _PHONENUMBERS_AVAILABLE:
        return result

    try:
        parsed = phonenumbers.parse(number, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return result

        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        result.phone_numbers = [e164]

        geo = _pn_geocoder.description_for_number(parsed, "en")
        if geo:
            result.phone_location = geo

        carrier = _pn_carrier.name_for_number(parsed, "en")
        if carrier:
            result.phone_carrier = carrier

        region = phonenumbers.region_code_for_number(parsed)
        if region and region != "ZZ":
            result.country = result.country or region

    except Exception:
        pass

    return result


def _extract_phone_locations(html: str) -> LocationResult:
    """Scan HTML text for phone numbers and resolve the first valid one."""
    result = LocationResult()

    if not _PHONENUMBERS_AVAILABLE:
        return result

    plain = _HTML_TAG_RE.sub(" ", html)
    candidates = _PHONE_E164_RE.findall(plain)

    for raw in candidates:
        raw_clean = re.sub(r'[\s\-().]', '', raw)
        loc = location_from_phone(raw_clean)
        if loc:
            return loc

    return result


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def extract_location(html: str) -> LocationResult:
    """Extract location information from an HTML profile page.

    Checks (in order):
    1. Standard geo meta tags (geo.position, ICBM, geo.placename, geo.region)
    2. OpenGraph location properties (og:locality, og:region, og:country-name)
    3. Facebook place coordinates (place:location:latitude/longitude)
    4. JSON-LD structured data (schema.org Person/Place)
    5. Phone numbers in page text (resolved via phonenumbers library)

    Returns a LocationResult (falsy if nothing was found).
    """
    result = LocationResult()

    # --- coordinates from geo.position or ICBM ---
    raw_pos = _first_match(_GEO_POSITION_RE, _GEO_POSITION_REV, text=html)
    if raw_pos is None:
        raw_pos = _first_match(_ICBM_RE, _ICBM_REV, text=html)
    if raw_pos:
        result.coordinates = _parse_coordinate_pair(raw_pos)

    # --- coordinates from og:place properties ---
    if result.coordinates is None:
        raw_lat = _first_match(_PLACE_LAT_RE, _PLACE_LAT_REV, text=html)
        raw_lon = _first_match(_PLACE_LON_RE, _PLACE_LON_REV, text=html)
        if raw_lat and raw_lon:
            try:
                lat, lon = float(raw_lat), float(raw_lon)
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    result.coordinates = (lat, lon)
            except ValueError:
                pass

    # --- place name ---
    result.place_name = _first_match(
        _GEO_PLACENAME_RE, _GEO_PLACENAME_REV,
        _OG_LOCALITY_RE, _OG_LOCALITY_REV,
        text=html,
    )

    # --- region ---
    result.region = _first_match(
        _GEO_REGION_RE, _GEO_REGION_REV,
        _OG_REGION_RE, _OG_REGION_REV,
        text=html,
    )

    # --- country ---
    result.country = _first_match(_OG_COUNTRY_RE, _OG_COUNTRY_REV, text=html)

    # --- JSON-LD fallback / enrichment ---
    ld = _extract_from_json_ld(html)
    result.place_name = result.place_name or ld.place_name
    result.region = result.region or ld.region
    result.country = result.country or ld.country
    result.coordinates = result.coordinates or ld.coordinates

    # --- phone number fallback / enrichment ---
    ph = _extract_phone_locations(html)
    if ph:
        result.phone_numbers = ph.phone_numbers
        result.phone_location = result.phone_location or ph.phone_location
        result.phone_carrier = result.phone_carrier or ph.phone_carrier
        result.country = result.country or ph.country

    return result
