import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const ARTICLES = path.join(ROOT, "src/content/articles");
const OUT = path.join(ROOT, "public/sitemap.xml");
const BASE = "https://therwawire.com";

const staticPaths = [
  "/", "/news/", "/rwa/", "/tokenization/", "/institutions/", "/markets/",
  "/map/", "/glossary/", "/projects/", "/projects/compare/", "/assets/", "/assets/buidl/", "/assets/benji/", "/assets/jpm-coin/", "/institutions/intelligence/blackrock/", "/institutions/intelligence/jpmorgan/", "/institutions/intelligence/dtcc/", "/institutions/intelligence/securitize/", "/institutions/intelligence/franklin-templeton/", "/topics/", "/topics/real-world-assets/", "/topics/tokenized-treasuries/", "/topics/tokenized-securities/", "/topics/private-credit/", "/topics/institutional-tokenization/", "/learn/", "/tools/", "/about/", "/contact/", "/privacy/",
  "/terms/", "/affiliate-disclosure/",
  "/tools/position-size-calculator/", "/tools/risk-reward-calculator/",
  "/tools/leverage-calculator/", "/tools/trading-fee-calculator/"
];

const translations = JSON.parse(fs.readFileSync(path.join(ROOT, "src/i18n/articles.json"), "utf8"));
for (const lang of ["de", "es", "fr"]) {
  for (const suffix of ["/", "/learn/rwa-crypto-explained/", "/newsletter/", "/bitunix/", "/news/", ...Object.values(translations).map(article => article.path)]) staticPaths.push(`/${lang}${suffix}`);
}
staticPaths.push("/newsletter/", "/bitunix/");

const urls = new Set(staticPaths.map(p => BASE + p));
for (const file of fs.readdirSync(ARTICLES).filter(f => f.endsWith(".mdx"))) {
  const raw = fs.readFileSync(path.join(ARTICLES, file), "utf8");
  const fm = raw.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!fm) continue;
  const front = fm[1];
  if (/^draft:\s*true\s*$/m.test(front)) continue;
  const cat = front.match(/^category:\s*["']?([^"'\n]+)["']?\s*$/m)?.[1]?.trim();
  if (!cat) continue;
  const slug = file.replace(/\.mdx$/, "");
  urls.add(`${BASE}/${cat}/${slug}/`);
}

const esc = s => s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const xml = '<?xml version="1.0" encoding="UTF-8"?>\n' +
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  [...urls].sort().map(u => `  <url><loc>${esc(u)}</loc></url>`).join("\n") +
  '\n</urlset>\n';
fs.writeFileSync(OUT, xml);
console.log(`Generated sitemap with ${urls.size} URLs.`);
