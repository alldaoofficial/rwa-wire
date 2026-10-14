import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

// Integration checks against built pages, independent of the routing helpers.
const paths = ["/", "/learn/rwa-crypto-explained/", "/newsletter/", "/bitunix/"];
const langs = ["en", "de", "es", "fr"];
const sitemap = fs.readFileSync("dist/sitemap.xml", "utf8");
const fileFor = route => path.join("dist", route, "index.html");
let checked = 0;
for (const original of paths) {
  const routes = langs.map(lang => lang === "en" ? original : `/${lang}${original}`);
  for (let i = 0; i < langs.length; i++) {
    const html = fs.readFileSync(fileFor(routes[i]), "utf8");
    assert.match(html, new RegExp(`<html[^>]+lang="${langs[i]}"`), `HTML language: ${routes[i]}`);
    assert.ok(html.includes(`rel="canonical" href="https://therwawire.com${routes[i]}"`), `Self canonical: ${routes[i]}`);
    for (let j = 0; j < langs.length; j++) {
      assert.ok(html.includes(`hreflang="${langs[j]}" href="https://therwawire.com${routes[j]}"`), `Reciprocal alternate ${langs[j]} on ${routes[i]}`);
      assert.ok(fs.existsSync(fileFor(routes[j])), `Alternate resolves: ${routes[j]}`);
    }
    assert.ok(html.includes(`hreflang="x-default" href="https://therwawire.com${original}"`));
    assert.ok(sitemap.includes(`<loc>https://therwawire.com${routes[i]}</loc>`), `Sitemap: ${routes[i]}`);
    for (const match of html.matchAll(/href="(\/(?:de|es|fr)\/[^"?#]*)"/g)) {
      assert.ok(fs.existsSync(fileFor(match[1])), `Localized link resolves: ${routes[i]} → ${match[1]}`);
    }
    if (original === "/bitunix/" && i > 0) {
      assert.ok(html.includes("vipCode=0xcrlt") && html.includes("sponsored"), "Affiliate attribution/disclosure link retained");
    }
    if (original === "/newsletter/" && html.includes("data-newsletter-form")) {
      assert.match(html, /name="consent"[^>]*required/);
      assert.doesNotMatch(html, /name="consent"[^>]*checked/);
      assert.ok(html.includes("data-messages="), "Localized status messages provided");
    }
    checked++;
  }
}
const untranslated = fs.readFileSync("dist/news/index.html", "utf8");
assert.doesNotMatch(untranslated, /<link[^>]+hreflang="(?:de|es|fr)"/, "Do not advertise untranslated news as translated");
console.log(`Verified ${checked} language variants, reciprocal alternates, canonicals, sitemap and localized links.`);
