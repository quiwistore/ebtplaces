#!/usr/bin/env python3
import json, subprocess, time
UA = "Mozilla/5.0 (Macintosh) Chrome/126.0"
SRV = "https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0/query"
FIELDS = "Record_ID,Store_Name,Store_Street_Address,Additonal_Address,City,State,Zip_Code,County,Latitude,Longitude"
todos, offset, PAGE = [], 0, 1000
while True:
    args = ['curl', '-s', '--max-time', '60', '-A', UA,
        '--data-urlencode', "where=Store_Type='Restaurant Meals Program'",
        '--data-urlencode', f'outFields={FIELDS}',
        '--data-urlencode', 'orderByFields=Record_ID',
        '--data-urlencode', f'resultOffset={offset}',
        '--data-urlencode', f'resultRecordCount={PAGE}',
        '--data-urlencode', 'f=json', SRV]
    r = subprocess.run(args, capture_output=True, text=True, timeout=75)
    d = json.loads(r.stdout)
    feats = d.get('features', [])
    if not feats: break
    todos += [f['attributes'] for f in feats]
    print(f'  offset {offset}: +{len(feats)} (total {len(todos)})', flush=True)
    if len(feats) < PAGE: break
    offset += PAGE
    time.sleep(1)
json.dump(todos, open('rmp-raw.json', 'w'))
print(f'FIN: {len(todos)} restaurantes RMP')
