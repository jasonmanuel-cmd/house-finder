"""Verify enrichment correctness: DB coords vs Kern County Assessor API.

Checks:
  1. The four APNs that exposed the scramble now have distinct coordinates.
  2. A sample of freshly enriched rows matches county parcel centroids.
  3. No coordinate pair is shared by a batch-sized group of properties
     (small groups are legitimate — sub-parcels share a parent centroid).

Env: SUPABASE_URL, SUPABASE_SECRET_KEY
"""
import collections
import json
import os
import urllib.parse
import urllib.request

from pyproj import Transformer

SUPA = os.environ['SUPABASE_URL']
KEY = os.environ['SUPABASE_SECRET_KEY']
TOKEN = next((a.split('=', 1)[1] for a in os.sys.argv if a.startswith('--token=')),
             'E9-O3Dag0ITeGppzm7iJnQfhh9nbHY12nO88VCrdMXw.')
ARCGIS = ('https://maps.co.kern.ca.us/arcgis/rest/services/Assessor/'
          'Assessor_Public/MapServer/2/query')
_T = Transformer.from_crs('EPSG:2229', 'EPSG:4326', always_xy=True)
FILTER = urllib.parse.quote('source_metadata->>kern_gis', safe='') + '=eq.enriched'
SCRAMBLED = ['429-042-09-00-8', '429-133-04-00-6', '429-151-49-00-9',
             '429-220-13-00-7']


def req(path, method='GET', body=None, timeout=90):
    h = {'apikey': KEY, 'Authorization': f'Bearer {KEY}',
         'Content-Type': 'application/json'}
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(SUPA + '/rest/v1' + path, data=data,
                               method=method, headers=h)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def compact(apn):
    p = apn.split('-')
    return f'{int(p[0]):03d}{int(p[1]):03d}{int(p[2]):02d}'


def county_centroids(compacts):
    inlist = ','.join(f"'{c}'" for c in compacts)
    q = urllib.parse.urlencode({
        'where': f'Assessor_Parcel_No IN ({inlist})',
        'outFields': 'Assessor_Parcel_No', 'returnGeometry': 'true',
        'f': 'json', 'token': TOKEN})
    d = json.loads(urllib.request.urlopen(urllib.request.Request(
        f'{ARCGIS}?{q}', headers={'User-Agent': 'Mozilla/5.0'}),
        timeout=60).read())
    out = {}
    for f in d.get('features', []):
        rings = (f.get('geometry') or {}).get('rings') or []
        if rings:
            xs = [p[0] for r in rings for p in r]
            ys = [p[1] for r in rings for p in r]
            lng, lat = _T.transform(sum(xs) / len(xs), sum(ys) / len(ys))
            out[f['attributes']['Assessor_Parcel_No']] = (round(lat, 6), round(lng, 6))
    return out


def main():
    # 1. The four previously-scrambled APNs must be distinct now.
    four = {r['apn']: (r['latitude'], r['longitude']) for r in req(
        f"/properties?apn=in.({','.join(SCRAMBLED)})&select=apn,latitude,longitude")}
    distinct = len({v for v in four.values() if v != (None, None)})
    print(f'1. scrambled-sample distinct coords: {distinct}/4')
    for a, v in four.items():
        print('   ', a, v)

    # 2. Fresh sample vs county.
    rows = req(f'/properties?select=apn,latitude,longitude&{FILTER}&limit=6')
    if rows:
        centroids = county_centroids([compact(r['apn']) for r in rows])
        ok = 0
        for r in rows:
            exp = centroids.get(compact(r['apn']))
            got = (r['latitude'], r['longitude'])
            match = (exp is not None and got[0] is not None
                     and abs(exp[0] - got[0]) < 1e-4
                     and abs(exp[1] - got[1]) < 1e-4)
            ok += bool(match)
            print(f"    {r['apn']} db={got} county={exp} "
                  f"{'OK' if match else 'MISMATCH'}")
        print(f'2. county cross-check: {ok}/{len(rows)}')
    else:
        print('2. no enriched rows found')

    # 3. Duplicate-coordinate groups (paginated full scan).
    coords, off = [], 0
    while True:
        b = req(f'/properties?select=latitude,longitude&latitude=not.is.null'
                f'&limit=1000&offset={off}')
        coords += b
        if len(b) < 1000:
            break
        off += 1000
    c = collections.Counter((r['latitude'], r['longitude']) for r in coords)
    print(f'3. coords: {len(coords)} rows, {len(c)} unique pairs, '
          f'max group size {max(c.values()) if c else 0}')
    big = [(k, v) for k, v in c.items() if v > 10]
    if big:
        print('   WARNING: batch-sized groups remain:', big[:3])


if __name__ == '__main__':
    main()
