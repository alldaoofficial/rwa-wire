import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHandler, digest} from '../supabase/functions/newsletter/handler.mjs';
const config={SUPABASE_URL:'https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'server-secret',NEWSLETTER_ENABLED:'true',RESEND_API_KEY:'mail-secret',NEWSLETTER_FROM:'RWA Wire <news@therwawire.com>',TURNSTILE_SECRET_KEY:'captcha-secret'};
const request=(data,origin='https://therwawire.com')=>new Request('https://example/newsletter',{method:'POST',headers:{origin,'content-type':'application/json'},body:JSON.stringify(data)});
const valid={action:'subscribe',email:'reader@example.com',consent:true,placement:'article-newsletter',captcha:'captcha-token'};
function setup(overrides={}, env=config) {
 const calls=[];
 const handler=createHandler(k=>env[k],async(url,options)=>{
  calls.push({url,options});
  if(url.includes('siteverify'))return Response.json(overrides.captcha??{success:true,hostname:'therwawire.com',action:'newsletter'});
  if(url.includes('newsletter_rate_limit'))return Response.json(overrides.rate??true);
  if(url.includes('newsletter_reserve'))return Response.json(overrides.reserve??true);
  if(url.includes('newsletter_token_action'))return Response.json(overrides.token??true);
  if(url.includes('resend.com'))return new Response('{}',{status:overrides.mailStatus??200});
  throw new Error('unexpected request');
 });return {handler,calls};
}
test('rejects foreign origins without storage or email',async()=>{const {handler,calls}=setup();assert.equal((await handler(request(valid,'https://evil.example'))).status,403);assert.equal(calls.length,0);});
test('requires consent, placement, email and captcha',async()=>{for(const change of [{consent:false},{email:'bad'},{placement:'made-up'},{captcha:''}]){const {handler,calls}=setup();assert.equal((await handler(request({...valid,...change}))).status,400);assert.equal(calls.length,0);}});
test('unconfigured service fails closed',async()=>{const {handler,calls}=setup({}, {...config,RESEND_API_KEY:undefined});assert.equal((await handler(request(valid))).status,503);assert.equal(calls.length,0);});
test('captcha cannot be reused from another hostname/action',async()=>{for(const captcha of [{success:false},{success:true,hostname:'evil.example',action:'newsletter'},{success:true,hostname:'therwawire.com',action:'login'}]){const {handler,calls}=setup({captcha});assert.equal((await handler(request(valid))).status,400);assert.equal(calls.length,1);}});
test('rate limit prevents reservation and mail',async()=>{const {handler,calls}=setup({rate:false});assert.equal((await handler(request(valid))).status,429);assert.equal(calls.length,2);});
test('duplicate response is identical and does not send mail',async()=>{const {handler,calls}=setup({reserve:false});assert.equal((await handler(request(valid))).status,202);assert.equal(calls.some(c=>c.url.includes('resend.com')),false);});
test('only hashed tokens reach storage, raw tokens go into email fragments',async()=>{const {handler,calls}=setup();assert.equal((await handler(request({...valid,email:' READER@example.com '}))).status,202);const row=JSON.parse(calls.find(c=>c.url.includes('newsletter_reserve')).options.body);const email=JSON.parse(calls.find(c=>c.url.includes('resend.com')).options.body);const token=/#confirm=([a-f0-9]{64})/.exec(email.text)[1];assert.equal(row.p_hash,await digest(token));assert.equal(row.p_email,'reader@example.com');assert.equal(row.p_consent_version,'2026-10-07-v2-weekly');assert.equal(JSON.stringify(row).includes(token),false);assert.equal(calls.some(c=>c.url.includes('growth-event')),false);});
test('mail failure never reports success',async()=>{const {handler}=setup({mailStatus:503});assert.equal((await handler(request(valid))).status,503);});
test('token actions require valid capability and hash it before RPC',async()=>{for(const action of ['confirm','unsubscribe']){const {handler,calls}=setup();const token='a'.repeat(64);assert.equal((await handler(request({action,token}))).status,200);assert.deepEqual(JSON.parse(calls[0].options.body),{p_action:action,p_hash:await digest(token)});assert.equal((await handler(request({action,token:'bad'}))).status,400);}});
test('expired or consumed tokens return invalid_link',async()=>{const {handler}=setup({token:false});const result=await handler(request({action:'confirm',token:'b'.repeat(64)}));assert.equal(result.status,400);assert.equal((await result.json()).code,'invalid_link');});

test('malformed JSON and oversized bodies are rejected before storage',async()=>{const {handler,calls}=setup();for(const [body,status] of [['{',400],['x'.repeat(4097),413]]){const response=await handler(new Request('https://example/newsletter',{method:'POST',headers:{origin:'https://therwawire.com','content-type':'application/json'},body}));assert.equal(response.status,status);}assert.equal(calls.length,0);});
