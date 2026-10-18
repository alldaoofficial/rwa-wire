import fs from "node:fs";
import assert from "node:assert/strict";

const base = "https://therwawire.com";
const home = fs.readFileSync("dist/index.html", "utf8");
const news = fs.readFileSync("dist/news/index.html", "utf8");
const sitemap = fs.readFileSync("dist/sitemap.xml", "utf8");
const rss = fs.readFileSync("dist/rss.xml", "utf8");
const structured = html => [...html.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)].map(m => JSON.parse(m[1]));
const website = structured(home).find(d => d["@type"] === "WebSite");
assert.equal(website?.name, "RWA Wire");
assert.equal(website.url, `${base}/`);
assert.match(home, /<title>RWA News &amp; Asset Tokenization Research \| RWA Wire<\/title>/);
assert.match(news, /<title>RWA &amp; Tokenization News \| RWA Wire<\/title>/);

let checked = 0;
for (const file of fs.readdirSync("src/content/articles").filter(f => f.endsWith(".mdx"))) {
  const raw = fs.readFileSync(`src/content/articles/${file}`, "utf8");
  const front = raw.split("---", 3)[1];
  const category = front.match(/^category:\s*"([^"]+)"/m)?.[1];
  const type = front.match(/^type:\s*"([^"]+)"/m)?.[1];
  const route = `/${category}/${file.slice(0, -4)}/`;
  if (/^draft:\s*true\s*$/m.test(front) || /^redirectTo:/m.test(front)) {
    assert.ok(!sitemap.includes(`<loc>${base}${route}</loc>`), `Noncanonical URL in sitemap: ${route}`);
    assert.ok(!rss.includes(`<link>${base}${route}</link>`), `Noncanonical URL in RSS: ${route}`);
    continue;
  }
  if (["NEWS", "RESEARCH"].includes(type) && ["news", "rwa", "tokenization", "institutions", "markets"].includes(category)) {
    assert.ok(news.includes(`href="${route}"`), `Published story missing from news hub: ${route}`);
    const html = fs.readFileSync(`dist${route}index.html`, "utf8");
    assert.ok(html.includes(`rel="canonical" href="${base}${route}"`));
    const article = structured(html).find(d => ["NewsArticle", "Article"].includes(d["@type"]));
    assert.equal(article?.publisher?.["@id"], `${base}/#organization`);
    assert.equal(article?.author?.url, `${base}/about/`);
    if (/^heroImage:/m.test(front)) assert.ok(article?.image?.[0]?.startsWith(`${base}/`));
    checked++;
  }
}
assert.ok(checked > 0);
console.log(`Verified site identity, news hub coverage and structured data for ${checked} published news/research articles.`);
