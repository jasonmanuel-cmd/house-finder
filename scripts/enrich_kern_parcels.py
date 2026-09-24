"""Enrich APN-only properties in Supabase with situs address + parcel centroid
from the Kern County Assessor ArcGIS service (batched).

For each property where address_line_1 IS NULL or starts with 'APN':
  1. Convert APN '227-071-17-00-1' -> compact '22707117' (book+page+parcel).
  2. Batch-query the Assessor parcels layer (25 APNs per IN() call) for
     Situs_Address + geometry.
  3. PATCH the properties rows: address, lat/lng (converted from EPSG:2229
     state-plane feet to WGS84), source_metadata.kern_gis = 'enriched'.

Env: SUPABASE_URL, SUPABASE_SECRET_KEY.
Usage: python enrich_kern_parcels.py [--dry-run] [--limit N] [--batch N]
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from pyproj import Transformer

# Kern County Assessor parcels are EPSG:2229 (NAD83 CA State Plane Zone 5, ft).
_TO_WGS84 = Transformer.from_crs('EPSG:2229', 'EPSG:4326', always_xy=True)

SUPA_URL = os.environ['SUPABASE_URL']
SUPA_KEY = os.environ['SUPABASE_SECRET_KEY']
ARCGIS = ('https://maps.co.kern.ca.us/arcgis/rest/services/Assessor/'
          'Assessor_Public/MapServer/2/query')
# Public token minted by the Kern GIS viewer per session (expires — refresh by
# loading https://maps.kerncounty.com/H5/index.html?viewer=KCPublic and grabbing
# a token= param from its network calls). Override with --token=XXX.
TOKEN = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--token=')),
             'E9-O3Dag0ITeGppzm7iJnQfhh9nbHY12nO88VCrdMXw.')
DRY_RUN = '--dry-run' in sys.argv
LIMIT = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--limit=')), '0'))
BATCH = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--batch=')), '25'))


def req(url, method='GET', body=None, timeout=60, headers=None):
    # NOTE: no User-Agent header — Supabase REST 401s browser UAs.
    h = {
        'apikey': SUPA_KEY,
        'Authorization': f'Bearer {SUPA_KEY}',
        'Content-Type': 'application/json',
    }
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def compact_apn(apn):
    """'227-071-17-00-1' -> '22707117' (drop sub-parcel suffix)."""
    if not apn:
        return None
    parts = apn.split('-')
    if len(parts) < 3:
        return None
    book, page, parcel = parts[0], parts[1], parts[2]
    try:
        return f'{int(book):03d}{int(page):03d}{int(parcel):02d}'
    except ValueError:
        return None


def stateplane_to_latlng(x, y):
    """EPSG:2229 state-plane feet -> WGS84 lat/lng."""
    lng, lat = _TO_WGS84.transform(x, y)
    return round(lat, 6), round(lng, 6)


def arcgis_batch(compacts):
    """Query parcels for a list of compact APNs. Returns {compact: feature}."""
    inlist = ','.join(f"'{c}'" for c in compacts)
    q = urllib.parse.urlencode({
        'where': f'Assessor_Parcel_No IN ({inlist})',
        'outFields': 'Assessor_Parcel_No,Situs_Address',
        'returnGeometry': 'true',
        'f': 'json',
        'token': TOKEN,
    })
    for attempt in range(4):
        try:
            d = json.loads(urllib.request.urlopen(
                urllib.request.Request(f'{ARCGIS}?{q}',
                                       headers={'User-Agent': 'Mozilla/5.0'}),
                timeout=60).read())
            return {f['attributes']['Assessor_Parcel_No']: f
                    for f in d.get('features', [])}
        except Exception as e:
            if attempt == 3:
                print(f'  batch error: {e}')
                return {}
            time.sleep(2 * (attempt + 1))


def main():
    # Fetch properties needing enrichment (APN-only, no coordinates).
    params = ('select=id,apn,address_line_1'
              '&or=(address_line_1.is.null,address_line_1.like.APN*)'
              '&latitude=is.null&limit=' + str(LIMIT or 4000))
    props = req(f'{SUPA_URL}/rest/v1/properties?{urllib.parse.quote(params, safe="=&(),.*")}')
    print(f'properties to enrich: {len(props)}')
    if not props:
        return

    # Build work list: [(property, compact_apn)]
    work = [(p, c) for p in props if (c := compact_apn(p.get('apn')))]
    print(f'with convertible APNs: {len(work)}')

    enriched = 0
    t0 = time.time()
    for i in range(0, len(work), BATCH):
        chunk = work[i:i + BATCH]
        feats = arcgis_batch([c for _, c in chunk])
        updates = []
        for p, compact in chunk:
            f = feats.get(compact)
            if not f:
                continue
            attrs = f.get('attributes', {})
            situs = (attrs.get('Situs_Address') or '').strip()
            rings = (f.get('geometry') or {}).get('rings') or []
            update = {}
            if rings:
                xs = [pt[0] for ring in rings for pt in ring]
                ys = [pt[1] for ring in rings for pt in ring]
                lat, lng = stateplane_to_latlng(sum(xs) / len(xs), sum(ys) / len(ys))
                update['latitude'] = lat
                update['longitude'] = lng
            if situs:
                parts = situs.rsplit(',', 1)
                update['address_line_1'] = parts[0].strip()
                if len(parts) == 2:
                    update['city'] = parts[1].strip().title()
            if 'latitude' in update or 'address_line_1' in update:
                update['id'] = p['id']
                update['source_metadata'] = {'kern_gis': 'enriched',
                                             'compact_apn': compact}
                updates.append(update)
        if DRY_RUN:
            for u in updates:
                print(' ', u.get('address_line_1', '(geom only)'),
                      u.get('latitude'), u.get('longitude'))
        elif updates:
            # Per-row PATCH: one request per row, filtered by its own id.
            # A single-object PATCH on a single matched row cannot scramble.
            # (Array-body PATCH with id=in.() applies values positionally and
            # POST-upsert fails NOT NULL checks on partial payloads.)
            for u in updates:
                try:
                    body = {k: v for k, v in u.items() if k != 'id'}
                    req(f"{SUPA_URL}/rest/v1/properties?id=eq.{u['id']}",
                        'PATCH', body)
                    enriched += 1
                except Exception as e:
                    print(f"  row {u['id'][:8]} patch error: {e}")
        done = min(i + BATCH, len(work))
        rate = done / max(time.time() - t0, 1)
        print(f'  {done}/{len(work)} scanned, {enriched} enriched '
              f'({rate:.1f}/s, ~{int((len(work) - done) / max(rate, 0.1) / 60)} min left)')
        time.sleep(0.5)  # be polite to the county API

    print(f'done: {enriched}/{len(work)} enriched in {int(time.time() - t0)}s')


if __name__ == '__main__':
    main()
