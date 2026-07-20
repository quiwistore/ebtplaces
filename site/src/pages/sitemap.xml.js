import places from '../data/places.json';
import { guides } from '../data/guides.js';
const BASE = 'https://ebtplaces.com';
export function GET() {
  const r = ['/', '/find/', '/chains/', '/states/', '/about/', '/contact/', '/privacy/'];
  for (const g of guides) r.push(`/${g.slug}/`);
  const st = new Set(), ci = new Set(), br = {};
  for (const p of places) {
    r.push(`/restaurant/${p.slug}/`);
    st.add(p.stateSlug); ci.add(`${p.stateSlug}/${p.citySlug}`);
    br[p.brandSlug] = (br[p.brandSlug]||0)+1;
  }
  for (const s of st) r.push(`/${s}/`);
  for (const c of ci) r.push(`/${c}/`);
  for (const b in br) if (br[b] >= 5) r.push(`/chain/${b}/`);
  const u = [...new Set(r)];
  const today = new Date().toISOString().split('T')[0];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    u.map(x => `<url><loc>${BASE}${x}</loc><lastmod>${today}</lastmod></url>`).join('\n') + `\n</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
}
