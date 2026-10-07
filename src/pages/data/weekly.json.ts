import {getCollection} from 'astro:content';
export async function GET() {
 const articles=(await getCollection('articles',({data})=>!data.draft)).filter(a=>a.data.category==='news'||a.data.category==='learn').map(a=>({slug:a.slug,type:a.data.type,category:a.data.category,title:a.data.title,description:a.data.description,pubDate:a.data.pubDate.toISOString(),keyTakeaways:a.data.keyTakeaways,url:`https://therwawire.com/${a.data.category}/${a.slug}/`}));
 return new Response(JSON.stringify({generatedAt:new Date().toISOString(),articles}),{headers:{'content-type':'application/json','cache-control':'public,max-age=300'}});
}
