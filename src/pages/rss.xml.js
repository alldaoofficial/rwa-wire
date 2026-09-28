import { getCollection } from "astro:content";
import { SITE } from "@/config/site";

export async function GET() {
  const articles=(await getCollection("articles",({data})=>!data.draft))
    .sort((a,b)=>b.data.pubDate.valueOf()-a.data.pubDate.valueOf()).slice(0,50);
  const esc=(s)=>s.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
  const items=articles.map(a=>`<item><title>${esc(a.data.title)}</title><link>${SITE.url}/${a.data.category}/${a.slug}/</link><guid isPermaLink="true">${SITE.url}/${a.data.category}/${a.slug}/</guid><pubDate>${a.data.pubDate.toUTCString()}</pubDate><description>${esc(a.data.description)}</description></item>`).join("");
  const xml=`<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>RWA Wire</title><link>${SITE.url}/</link><description>${esc(SITE.description)}</description><language>en</language><lastBuildDate>${articles[0]?.data.pubDate.toUTCString()??new Date().toUTCString()}</lastBuildDate>${items}</channel></rss>`;
  return new Response(xml,{headers:{"Content-Type":"application/rss+xml; charset=utf-8","Cache-Control":"public, max-age=3600"}});
}