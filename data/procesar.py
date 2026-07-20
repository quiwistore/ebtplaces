#!/usr/bin/env python3
import json, re, unicodedata, html as H
from collections import defaultdict

STATES = {'CA':'California','AZ':'Arizona','NY':'New York','MI':'Michigan','VA':'Virginia','IL':'Illinois','MD':'Maryland','RI':'Rhode Island','MA':'Massachusetts','NJ':'New Jersey'}

# marcas canonicas (patron -> nombre display). El primero que matchea gana.
BRANDS = [
    (r"mc\s*donald", "McDonald's"), (r"jack\s*in\s*the\s*box", "Jack in the Box"),
    (r"taco\s*bell", "Taco Bell"), (r"carl'?s\s*jr", "Carl's Jr."), (r"burger\s*king", "Burger King"),
    (r"el\s*pollo\s*loco", "El Pollo Loco"), (r"pizza\s*hut", "Pizza Hut"), (r"del\s*taco", "Del Taco"),
    (r"denny'?s", "Denny's"), (r"wendy'?s", "Wendy's"), (r"popeye", "Popeyes"), (r"\bkfc\b|kentucky\s*fried", "KFC"),
    (r"domino'?s", "Domino's"), (r"wingstop", "Wingstop"), (r"yoshinoya", "Yoshinoya"), (r"jamba", "Jamba Juice"),
    (r"papa\s*john", "Papa John's"), (r"baker'?s\s*drive", "Baker's Drive-Thru"), (r"waba\s*grill", "Waba Grill"),
    (r"subway", "Subway"), (r"church'?s\s*chicken|church'?s\s*texas", "Church's Chicken"), (r"panda\s*express", "Panda Express"),
    (r"little\s*caesar", "Little Caesars"), (r"jersey\s*mike", "Jersey Mike's"), (r"jimmy\s*john", "Jimmy John's"),
    (r"in-?n-?out", "In-N-Out"), (r"arby'?s", "Arby's"), (r"sonic", "Sonic"), (r"carl'?s", "Carl's Jr."),
    (r"rally'?s|checkers", "Checkers/Rally's"), (r"panera", "Panera Bread"), (r"quiznos", "Quiznos"),
    (r"dunkin", "Dunkin'"), (r"ihop", "IHOP"), (r"chipotle", "Chipotle"), (r"five\s*guys", "Five Guys"),
]

def slugify(t):
    t = unicodedata.normalize('NFKD', str(t).lower()).encode('ascii','ignore').decode()
    t = t.replace("'", "").replace('"', '')
    return re.sub(r'[^a-z0-9]+','-',t).strip('-')

MINUS = {'of','the','and','on','de','la','del','a','an','at','in'}
def titlecase(t):
    t = re.sub(r'\s+', ' ', str(t)).strip()
    out = []
    for i, w in enumerate(re.split(r'(\s+|-|/)', t)):
        if not w.strip() or w in ('-','/'): out.append(w); continue
        lw = w.lower()
        if i > 0 and lw in MINUS: out.append(lw); continue
        if lw.startswith('mc') and len(lw) > 3: out.append('Mc' + lw[2].upper() + lw[3:])
        elif lw.startswith("o'") and len(lw) > 2: out.append("O'" + lw[2].upper() + lw[3:])
        elif lw in ('st','ste'): out.append(lw.capitalize() + '.')
        elif lw in ('us','ne','nw','se','sw','ii','iii','llc','dba'): out.append(lw.upper())
        else: out.append(lw.capitalize())
    return ''.join(out)

def desescape(s):
    t = H.unescape(str(s)).replace('\u2019', "'").replace('\t',' ')
    return re.sub(r'\s+', ' ', t).strip()

KNOWN = {d for _, d in BRANDS}
def marca(nombre):
    n = nombre.lower()
    for pat, disp in BRANDS:
        if re.search(pat, n): return disp
    # cadena independiente: limpiar
    c = re.sub(r'\s*#?\s*\d.*$', '', nombre)
    c = re.sub(r'\s+(llc|inc|corp).*$', '', c, flags=re.I)
    c = re.sub(r'\bdba\b.*$', '', c, flags=re.I)
    c = desescape(c).strip(' -,')
    return titlecase(c) if c and len(c) > 2 else titlecase(desescape(nombre))

ABREV = {'st':'street','rd':'road','ave':'avenue','av':'avenue','blvd':'boulevard','hwy':'highway','dr':'drive','ln':'lane','ct':'court','pl':'place','pkwy':'parkway','cir':'circle','n':'north','s':'south','e':'east','w':'west','ste':'suite'}
def norm_calle(s):
    s = re.sub(r'[^a-z0-9 ]', ' ', str(s).lower())
    s = re.sub(r'^(\d+)[a-z]\b', r'\1', s.strip())
    return ' '.join(ABREV.get(w, w) for w in s.split())

raw = json.load(open('rmp-raw.json'))
items, usados, vistos = [], {}, set()
brand_count = defaultdict(int)
for v in raw:
    st = v.get('State')
    if st not in STATES or not v.get('Store_Name') or not v.get('City'): continue
    br = marca(v['Store_Name'])
    ncalle = norm_calle(v['Store_Street_Address'])
    zc = str(v.get('Zip_Code','')).strip()[:5]
    cityl = str(v['City']).strip().lower()
    if br in KNOWN:
        ident = ('B:'+br, ncalle, cityl)              # cadena: ignora store number y zip
    else:
        ident = (desescape(v['Store_Name']).lower(), ncalle, cityl, zc)
    if ident in vistos: continue
    vistos.add(ident)
    name = desescape(v['Store_Name'])
    mdba = re.search(r'\bdba\b\s+(.+)$', name, re.I)
    if mdba: name = mdba.group(1).strip()
    name = titlecase(name) if name.isupper() or name.islower() else name
    name = name.replace("'S ", "'s ").replace("'S", "'s") if re.search(r"[a-z]'S\b", name) else name
    city = titlecase(v['City'])
    street = titlecase(desescape(v['Store_Street_Address'])) if v['Store_Street_Address'] else ''
    if br in KNOWN:
        name = br  # cadena conocida: nombre canonico, sin razon social
    brand_count[br] += 1
    base = slugify(f"{name}-{v.get('Store_Street_Address','')[:14]}")[:60] or 'restaurant'
    slug = base
    i = 2
    while slug in usados: slug = f'{base}-{i}'; i += 1
    usados[slug] = 1
    items.append({
        'slug': slug, 'name': name, 'street': street, 'city': city,
        'state': st, 'stateName': STATES[st], 'zip': str(v.get('Zip_Code','')).strip(),
        'county': titlecase(v['County']) if v.get('County') else '',
        'lat': round(float(v['Latitude']), 6), 'lng': round(float(v['Longitude']), 6),
        'brand': br, 'brandSlug': slugify(br),
        'citySlug': slugify(v['City']), 'stateSlug': slugify(STATES[st]),
    })

# marcas con pagina propia (>=5 locales)
big = {b for b, n in brand_count.items() if n >= 5}
bigslug = {slugify(b) for b in big}
for x in items:
    x['bp'] = x['brandSlug'] in bigslug
json.dump(items, open('../site/src/data/places.json','w'), ensure_ascii=False)
cities = set((x['stateSlug'], x['citySlug']) for x in items)
brands_big = {b: n for b, n in brand_count.items() if n >= 5}
print(f'restaurantes: {len(items)} | estados: {len(set(x["state"] for x in items))} | ciudades: {len(cities)}')
print(f'cadenas totales: {len(brand_count)} | con >=5 locales (pagina propia): {len(brands_big)}')
print('top marcas consolidadas:')
for b, n in sorted(brand_count.items(), key=lambda x:-x[1])[:16]: print(f'  {n:>4}  {b}')
