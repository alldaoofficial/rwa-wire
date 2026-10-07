import {test} from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
globalThis.crypto??=webcrypto;
import {selectIssue,renderIssue,weeklyKey,hash,unsubscribeToken} from '../shared/weekly.mjs';
import {createHandler,database} from '../supabase/functions/weekly-newsletter/handler.mjs';
import {verifyWebhook,createWebhookHandler} from '../supabase/functions/weekly-webhook/handler.mjs';
import {createUnsubscribeHandler} from '../supabase/functions/weekly-unsubscribe/handler.mjs';
const now=new Date('2026-10-09T07:00:00Z');
const article={type:'NEWS',category:'news',title:'Title <script>',description:'Description & context',keyTakeaways:['Published takeaway'],pubDate:'2026-10-08',url:'https://therwawire.com/news/example/'};
const feed={generatedAt:now.toISOString(),articles:[article]};
const issue=selectIssue(feed,now);
const env={SUPABASE_URL:'https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'key',RESEND_API_KEY:'mail',NEWSLETTER_FROM:'Editorial <news@therwawire.com>'};
const secret='a'.repeat(64);
const request=(mode='send')=>new Request('https://example/weekly',{method:'POST',headers:{authorization:`Bearer ${secret}`},body:JSON.stringify({mode})});
function setup(options={}){
 const calls=[];const cfg={enabled:true,approved:true,sender_name:'Editorial',sender_address:'Business address',sender_contact:'contact@example.com',test_email:'reader@example.com',...options.config};
 const fetcher=async(url,o={})=>{calls.push({url,options:o});const name=url.split('/').pop(),body=o.body?JSON.parse(o.body):{};
 if(url.includes('/rpc/')){const result={weekly_auth:options.authorized??true,weekly_config:cfg,weekly_lock:true,weekly_unlock:null,weekly_prepare:body.p_content,weekly_candidates:options.recipients??[{email:'reader@example.com',consent_at:'2026-10-07T12:00:00Z'}],weekly_claim:options.claimed===false?null:options.frozen??body.p_payload,weekly_complete:null,weekly_status:{accepted:1},weekly_resume:null}[name];return Response.json(result);}
 if(url.includes('/data/'))return Response.json(options.feed??feed);
 if(url.includes('api.resend.com')){if(options.network)throw new Error('network');return Response.json({id:'provider-id'},{status:options.mailStatus??200});}
 throw new Error(url);
 };return {handler:createHandler(k=>env[k],fetcher,async()=>{},()=>now),calls};
}
test('selects only recent published news; deduplicates and caps five',()=>{
 const articles=[...Array.from({length:8},(_,i)=>({...article,title:`${i}`,url:`https://therwawire.com/news/item-${i}/`})),article,{...article,draft:true,url:'/news/draft/'},{...article,pubDate:'2026-10-10',url:'/news/future/'},{...article,pubDate:'2026-09-01',url:'/news/old/'}];
 assert.equal(selectIssue({...feed,articles},now).stories.length,5);assert.throws(()=>selectIssue({...feed,generatedAt:'2026-10-01'},now),/stale/);assert.throws(()=>selectIssue({...feed,articles:[{...article,url:'https://evil.test/news/example/'}]},now),/invalid_article_url/);
});
test('weekly label handles Berlin date, month and DST boundaries',()=>{assert.equal(weeklyKey(now),'weekly-2026-10-09');assert.equal(weeklyKey(new Date('2026-10-31T23:30:00Z')),'weekly-2026-11-06');});
test('render escapes article and sender HTML and includes plain text unsubscribe',()=>{const r=renderIssue(issue,{name:'<sender>',address:'Address',contact:'mail'},'https://example/unsub');assert.ok(r.html.includes('Title &lt;script&gt;'));assert.ok(r.html.includes('&lt;sender&gt;'));assert.ok(!r.html.includes('<script>'));assert.ok(r.text.includes('Unsubscribe:'));});
test('tokens persist across issues and expire upon reconsent',async()=>{const a=await unsubscribeToken(secret,'a@example.com','1');assert.equal(a,await unsubscribeToken(secret,'a@example.com','1'));assert.notEqual(a,await unsubscribeToken(secret,'a@example.com','2'));assert.notEqual(a,await unsubscribeToken(secret,'b@example.com','1'));});
test('authentication and readiness fail closed',async()=>{for(const o of [{authorized:false},{config:{enabled:false}},{config:{approved:false}},{config:{sender_address:''}}]){const {handler,calls}=setup(o);assert.ok((await handler(request())).status>=400);assert.ok(!calls.some(c=>c.url.includes('api.resend.com')));}});
test('preview works with disabled send controls, without audience or email',async()=>{const {handler,calls}=setup({config:{enabled:false,approved:false}});const r=await handler(request('preview'));assert.equal(r.status,200);assert.equal((await r.json()).code,'preview');assert.ok(!calls.some(c=>c.url.includes('weekly_candidates')||c.url.includes('api.resend.com')));});
test('empty audience or revoked consent does not send',async()=>{for(const o of [{recipients:[]},{claimed:false}]){const {handler,calls}=setup(o);assert.equal((await handler(request())).status,200);assert.ok(!calls.some(c=>c.url.includes('api.resend.com')));}});
test('one recipient, hashed token, stable provider key and frozen payload',async()=>{const sends=[];for(let i=0;i<2;i++){const {handler,calls}=setup();assert.equal((await handler(request())).status,200);const c=calls.find(c=>c.url.includes('api.resend.com'));const payload=JSON.parse(c.options.body);assert.deepEqual(payload.to,['reader@example.com']);assert.equal(payload.headers['List-Unsubscribe-Post'],'List-Unsubscribe=One-Click');const raw=/token=([a-f0-9]{64})/.exec(payload.headers['List-Unsubscribe'])[1];const claim=JSON.parse(calls.find(c=>c.url.includes('weekly_claim')).options.body);assert.equal(claim.p_hash,await hash(raw));sends.push(c);}assert.equal(sends[0].options.headers['Idempotency-Key'],sends[1].options.headers['Idempotency-Key']);assert.equal(sends[0].options.body,sends[1].options.body);
 const frozen={from:'Saved',to:['reader@example.com'],subject:'Original frozen content',text:'Saved',html:'Saved',headers:{}};const {handler,calls}=setup({frozen});await handler(request());assert.deepEqual(JSON.parse(calls.find(c=>c.url.includes('api.resend.com')).options.body),frozen);
});
test('transient and ambiguous errors retry; permanent errors fail',async()=>{for(const [o,status] of [[{mailStatus:429},'retry'],[{mailStatus:503},'retry'],[{network:true},'retry'],[{mailStatus:400},'failed']]){const {handler,calls}=setup(o);await handler(request());assert.equal(JSON.parse(calls.find(c=>c.url.includes('weekly_complete')).options.body).p_status,status);assert.ok(calls.some(c=>c.url.includes('weekly_unlock')));}});
async function signed(raw,time=Date.now()){const keyBytes=new TextEncoder().encode('test-secret');const key=await crypto.subtle.importKey('raw',keyBytes,{name:'HMAC',hash:'SHA-256'},false,['sign']);const timestamp=String(Math.floor(time/1000));const mac=await crypto.subtle.sign('HMAC',key,new TextEncoder().encode(`receipt.${timestamp}.${raw}`));return {secret:'whsec_'+btoa(String.fromCharCode(...keyBytes)),headers:new Headers({'svix-id':'receipt','svix-timestamp':timestamp,'svix-signature':'v1,'+btoa(String.fromCharCode(...new Uint8Array(mac)))})};}
test('webhook verifies raw bytes, rejects tampering and replay timestamps',async()=>{const raw='{"type":"email.bounced"}',s=await signed(raw);assert.equal(await verifyWebhook(raw,s.headers,s.secret),true);assert.equal(await verifyWebhook(raw+' ',s.headers,s.secret),false);assert.equal(await verifyWebhook(raw,s.headers,s.secret,Date.now()+301000),false);});
test('unsigned webhooks cannot change delivery state',async()=>{const calls=[];const handler=createWebhookHandler(k=>env[k],async(url)=>{calls.push(url);return Response.json({webhook_secret:'whsec_dGVzdA=='});});assert.equal((await handler(new Request('https://example',{method:'POST',body:'{}'}))).status,401);assert.equal(calls.length,1);});
test('GET unsubscribe is passive; one-click POST hashes capability',async()=>{const calls=[];const handler=createUnsubscribeHandler(k=>env[k],async(url,o)=>{calls.push(JSON.parse(o.body));return Response.json(true);});const url=`https://example/unsubscribe?token=${secret}`;assert.equal((await handler(new Request(url))).status,302);assert.equal(calls.length,0);assert.equal((await handler(new Request(url,{method:'POST',body:'List-Unsubscribe=One-Click'}))).status,200);assert.deepEqual(calls[0],{p_action:'unsubscribe',p_hash:await hash(secret)});});

test('void database RPC responses succeed without JSON parsing errors',async()=>{const rpc=database(k=>env[k],async()=>new Response(null,{status:204}));assert.equal(await rpc('weekly_complete'),null);});
