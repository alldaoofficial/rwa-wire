import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const ARTICLES = path.join(ROOT, "src/content/articles");
const OUT = path.join(ROOT, "public/sitemap.xml");
const BASE = "https://alldaoofficial.github.io/rwa-wire";

const staticPaths = [
  "/", "/news/", "/rwa/", "/tokenization/", "/institutions/", "/markets/",
  "/projects/", "/learn/", "/tools/", "/about/", "/contact/", "/privacy/",
  "/terms/", "/affiliate-disclosure/",
  "/tools/position-size-calculator/", "/tools/risk-reward-calculator/",
  "/tools/leverage-calculator/", "/tools/trading-fee-calculator/"
];

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
