import {database} from '../weekly-newsletter/handler.mjs';
export async function verifyWebhook(raw,headers,secret,now=Date.now()) {
 const id=headers.get('svix-id'),timestamp=headers.get('svix-timestamp');
 if(!id||!/^\d+$/.test(timestamp||'')||Math.abs(now/1000-Number(timestamp))>300||!secret.startsWith('whsec_'))return false;
 try{
 const key=await crypto.subtle.importKey('raw',Uint8Array.from(atob(secret.slice(6)),c=>c.charCodeAt(0)),{name:'HMAC',hash:'SHA-256'},false,['verify']);
 const data=new TextEncoder().encode(`${id}.${timestamp}.${raw}`);
 for(const entry of (headers.get('svix-signature')||'').split(' ')){const [version,value]=entry.split(',');if(version==='v1'&&value&&await crypto.subtle.verify('HMAC',key,Uint8Array.from(atob(value),c=>c.charCodeAt(0)),data))return true;}
 }catch{}return false;
}
export function createWebhookHandler(env,fetcher=fetch){const rpc=database(env,fetcher);return async req=>{
 if(req.method!=='POST')return new Response(null,{status:405});
 try{const raw=await req.text();if(raw.length>32768)return new Response(null,{status:413});
 const cfg=await rpc('weekly_config');if(!cfg.webhook_secret)return new Response(null,{status:503});
 if(!await verifyWebhook(raw,req.headers,cfg.webhook_secret))return new Response(null,{status:401});
 const event=JSON.parse(raw);const types=['email.delivered','email.delivery_delayed','email.bounced','email.complained','email.failed','email.suppressed'];
 if(types.includes(event.type)&&typeof event.data?.email_id==='string')await rpc('weekly_event',{p_receipt:req.headers.get('svix-id'),p_type:event.type,p_resend_id:event.data.email_id});
 return new Response(null,{status:200});}catch{return new Response(null,{status:503});}
};}
