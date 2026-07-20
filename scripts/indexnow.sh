#!/bin/bash
# IndexNow submit para ebtplaces.com — lotes de 10k
set -e
KEY="cddee273d50f49ca8e6082ccf314ddc7"
HOST="ebtplaces.com"
cd "$(dirname "$0")/.."
# guard: la clave debe estar viva en produccion
CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${HOST}/${KEY}.txt")
if [ "$CODE" != "200" ]; then echo "ABORT: key .txt devuelve $CODE (debe ser 200). Deploy primero."; exit 1; fi
echo "Key viva (200). Extrayendo URLs del sitemap..."
grep -oE 'https://[^<]+' dist/sitemap.xml > /tmp/ebt-urls.txt
TOTAL=$(wc -l < /tmp/ebt-urls.txt | tr -d ' ')
echo "URLs: $TOTAL"
split -l 10000 /tmp/ebt-urls.txt /tmp/ebt-lote-
for L in /tmp/ebt-lote-*; do
  URLS=$(python3 -c "import json,sys;print(json.dumps([l.strip() for l in open('$L')]))")
  BODY=$(python3 -c "import json;print(json.dumps({'host':'${HOST}','key':'${KEY}','keyLocation':'https://${HOST}/${KEY}.txt','urlList':json.loads('''$URLS''')}))")
  echo -n "  lote $(wc -l < $L | tr -d ' ') urls -> "
  curl -s -o /dev/null -w "%{http_code}\n" -X POST "https://api.indexnow.org/indexnow" -H "Content-Type: application/json" -d "$BODY"
  sleep 2
done
echo "IndexNow OK"
