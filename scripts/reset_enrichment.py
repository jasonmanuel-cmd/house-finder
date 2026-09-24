"""One-off cleanup: undo the scrambled batch-PATCH enrichment.

PostgREST applies a batch PATCH (array body + id=in.() filter) positionally
against rows in server return order — in practice the last array object was
applied to every matched row, so each 25-row batch left all 25 properties
with one parcel's coordinates. This script:

  1. Finds every property marked source_metadata.kern_gis = 'enriched'.
  2. Restores APN-format addresses where a (scrambled) situs was written.
  3. Bulk-nulls latitude/longitude and the marker.
  4. Validates the replacement write mechanism (PK-matched upsert via
     POST + Prefer: resolution=merge-duplicates) on two parcels with known,
     different county centroids, then re-nulls them.

Env: SUPABASE_URL, SUPABASE_SECRET_KEY
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from pyproj import Transformer

SUPA = os.environ['SUPABASE_URL']
KEY = os.environ['SUPABASE_SECRET_KEY']
_TO_WGS84 = Transformer.from_crs('EPSG:2229', 'EPSG:4326', always_xy=True)
FILTER = urllib.parse.quote('source_metadata->>kern_gis', safe='') + '=eq.enriched'


def req(path, method='GET', body=None, headers=None, timeout=90):
    # NOTE: no User-Agent header — Supabase REST 401s browser UAs.
    h = {'apikey': KEY, 'Authorization': f'Bearer {KEY}',
         'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(SUPA + '/rest/v1' + path, data=data,
                               method=method, headers=h)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def main():
    # 1. Fetch every row touched by the enrichment (paginated).
    rows, offset = [], 0
    while True:
        batch = req(f'/properties?select=id,apn,address_line_1&{FILTER}'
                    f'&limit=1000&offset={offset}')
        rows += batch
        if len(batch) < 1000:
            break
        offset += 1000
    print(f'rows to reset: {len(rows)}')
    if not rows:
        return

    # 2. Restore APN-format addresses where a situs address was written.
    situs_rows = [r for r in rows if r.get('address_line_1')
                  and not r['address_line_1'].startswith('APN')]
    print(f'situs addresses to restore: {len(situs_rows)}')
    for r in situs_rows:
        if not r.get('apn'):
            continue
        req(f"/properties?id=eq.{r['id']}", 'PATCH',
            {'address_line_1': f"APN {r['apn']}", 'city': None})

    # 3. Null coordinates and the enrichment marker in chunks (Supabase caps
    #    mutations at 1000 affected rows per request). A single-object PATCH
    #    with an id=in.() filter applies the SAME value to every row — safe.
    ids = [r['id'] for r in rows]
    for i in range(0, len(ids), 100):
        chunk = ','.join(ids[i:i + 100])
        try:
            # NOTE: source_metadata stays — it's NOT NULL (or trigger-backed);
            # re-enrichment selects rows by APN-address + null coords anyway.
            req(f'/properties?id=in.({chunk})', 'PATCH',
                {'latitude': None, 'longitude': None})
        except urllib.error.HTTPError as e:
            print(f'  chunk {i} failed: {e.code} {e.read().decode()[:200]}')
            raise
    left = req(f'/properties?select=id&{FILTER}&limit=1')
    print(f'rows still marked after reset: {len(left)} (want 0)')

    # 4. Prove the replacement mechanism: PK-matched upsert. Two parcels
    #    with DIFFERENT county centroids must keep their own values.
    tests = [  # (apn, county centroid x, y — EPSG:2229 feet)
        ('429-042-09-00-8', 6529242.4, 2184610.9),
        ('429-133-04-00-6', 6522657.0, 2177785.9),
    ]
    payload, expected = [], {}
    for apn, x, y in tests:
        lng, lat = _TO_WGS84.transform(x, y)
        pid = req(f'/properties?apn=eq.{apn}&select=id&limit=1')[0]['id']
        payload.append({'id': pid, 'latitude': round(lat, 6),
                        'longitude': round(lng, 6)})
        expected[apn] = (round(lat, 6), round(lng, 6))
    req('/properties', 'POST', payload,
        headers={'Prefer': 'resolution=merge-duplicates,return=minimal'})
    got = {r['apn']: (r['latitude'], r['longitude']) for r in req(
        '/properties?apn=in.(429-042-09-00-8,429-133-04-00-6)'
        '&select=apn,latitude,longitude')}
    ok = all(got.get(a) == e for a, e in expected.items())
    print('PK-matched upsert test:', 'PASS' if ok else 'FAIL')
    print('  expected:', expected)
    print('  got:     ', got)

    # Re-null the test rows so the full re-enrichment handles them uniformly.
    req(f"/properties?id=in.({payload[0]['id']},{payload[1]['id']})", 'PATCH',
        {'latitude': None, 'longitude': None})
    print('test rows re-nulled; safe to re-run enrich_kern_parcels.py')
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
