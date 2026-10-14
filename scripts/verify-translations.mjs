import fs from "node:fs";
import assert from "node:assert/strict";
const records = JSON.parse(fs.readFileSync("src/i18n/articles.json", "utf8"));
const seen = new Set();
for (const [id, article] of Object.entries(records)) {
  assert.match(id, /^[a-z0-9-]+$/);
  assert.match(article.path, /^\/(news|rwa|tokenization|institutions|markets|learn)\/[a-z0-9-]+\/$/);
  assert.ok(!seen.has(article.path), "Duplicate translation path"); seen.add(article.path);
  const slug = article.path.split("/").filter(Boolean).at(-1);
  const original = fs.readFileSync(`src/content/articles/${slug}.mdx`, "utf8");
  assert.ok(!/^draft:\s*true\s*$/m.test(original), "Cannot translate a draft");
  assert.ok(original.includes(`category: "${article.path.split("/")[1]}"`), "Original category mismatch");
  const date = original.match(/^pubDate:\s*"([0-9-]+)"/m)?.[1];
  assert.equal(article.date, date, "Translation must retain original date");
  assert.ok(["guide", "news", "research"].includes(article.kind));
  assert.ok(Array.isArray(article.sources));
  for (const source of article.sources) {
    assert.ok(Array.isArray(source) && source.length === 2 && source[0].trim());
    const url = new URL(source[1]);
    assert.equal(url.protocol,"https:"); assert.ok(!url.username && !url.password);
    assert.ok(original.includes(source[1]), "Source must be retained from the English article");
  }
  for (const lang of ["de", "es", "fr"]) {
    const text = article[lang];
    assert.ok(text && typeof text.title === "string" && text.title.trim());
    assert.ok(typeof text.description === "string" && text.description.trim());
    assert.ok(Array.isArray(text.sections) && text.sections.length);
    for (const section of text.sections) assert.ok(Array.isArray(section) && section.length >= 2 && section.every(p=>typeof p === "string" && p.trim()));
  }
}
console.log(`Verified ${seen.size} translation records against English originals; all three languages are complete.`);
