import {hash,unsubscribeToken,selectIssue,renderIssue} from '../../../shared/weekly.mjs';
export function database(env,fetcher) {
 return async(name,args={})=>{const r=await fetcher(`${env('SUPABASE_URL')}/rest/v1/rpc/${name}`,{method:'POST',headers:{apikey:env('SUPABASE_SERVICE_ROLE_KEY'),Authorization:`Bearer ${env('SUPABASE_SERVICE_ROLE_KEY')}`,'Content-Type':'application/json'},body:JSON.stringify(args),signal:AbortSignal.timeout(15000)});if(!r.ok)throw new Error('database_error');const raw=await r.text();return raw?JSON.parse(raw):null;};
}
export function createHandler(env,fetcher=fetch,pause=ms=>new Promise(r=>setTimeout(r,ms)),clock=()=>new Date()) {
 const rpc=database(env,fetcher); const reply=(code,status=200,extra={})=>Response.json({code,...extra},{status});
 return async req=>{
  if(req.method!=='POST')return reply('method_not_allowed',405);
  if(!env('SUPABASE_URL')||!env('SUPABASE_SERVICE_ROLE_KEY'))return reply('unconfigured',503);
  const secret=/^Bearer ([a-f0-9]{64})$/.exec(req.headers.get('authorization')||'')?.[1];
  if(!secret)return reply('unauthorized',401);
  let owner;
  try {
   if(!await rpc('weekly_auth',{p_hash:await hash(secret)}))return reply('unauthorized',401);
   const raw=await req.text();if(raw.length>4096)return reply('too_large',413);
   let body;try{body=JSON.parse(raw);}catch{return reply('invalid_json',400);}
   const mode=body.mode??'preview';if(!['preview','test','send','resume'].includes(mode))return reply('invalid_mode',400);
   const cfg=await rpc('weekly_config');
   if(mode!=='preview' && ((!['test'].includes(mode)&&(!cfg.enabled||!cfg.approved))||![cfg.sender_name,cfg.sender_address,cfg.sender_contact].every(v=>typeof v==='string'&&v.trim())||(mode==='test'&&!cfg.test_email)))return reply('setup_required',409);
   let issue;
   if(mode==='resume'){issue=await rpc('weekly_resume');if(!issue)return reply('nothing_to_resume');}
   else {const f=await fetcher('https://therwawire.com/data/weekly.json',{signal:AbortSignal.timeout(15000)});if(!f.ok)throw new Error('feed_unavailable');issue=selectIssue(await f.json(),clock());}
   if(!issue.stories.length)return reply('no_news');
   const footer={name:cfg.sender_name,address:cfg.sender_address,contact:cfg.sender_contact};
   if(mode==='preview')return reply('preview',200,{issue:issue.id,...renderIssue(issue,footer,'https://therwawire.com/newsletter/')});
   if(!env('RESEND_API_KEY')||!env('NEWSLETTER_FROM'))return reply('unconfigured',503);
   owner=crypto.randomUUID();if(!await rpc('weekly_lock',{p_owner:owner})){owner=undefined;return reply('busy',409);}
   if(mode==='test')issue={...issue,id:`test-${issue.id}-${await hash(JSON.stringify(issue)+renderIssue(issue,footer,'https://therwawire.com/newsletter/').html).then(s=>s.slice(0,16))}`,subject:`[TEST] ${issue.subject}`};
   issue=await rpc('weekly_prepare',{p_issue:issue.id,p_content:issue,p_test:mode==='test'});
   const recipients=await rpc('weekly_candidates',{p_issue:issue.id});let accepted=0;
   const started=performance.now();
   for(const recipient of recipients){
    if(performance.now()-started>80000)break;
    const token=await unsubscribeToken(secret,recipient.email,recipient.consent_at);
    const rendered=renderIssue(issue,footer,`https://therwawire.com/newsletter/#unsubscribe=${token}`);
    const oneClick=`${env('SUPABASE_URL')}/functions/v1/weekly-unsubscribe?token=${token}`;
    const payload=await rpc('weekly_claim',{p_issue:issue.id,p_email:recipient.email,p_hash:await hash(token),p_payload:{from:env('NEWSLETTER_FROM'),to:[recipient.email],...rendered,headers:{'List-Unsubscribe':`<${oneClick}>`,'List-Unsubscribe-Post':'List-Unsubscribe=One-Click'}}});
    if(!payload)continue;
    let status='retry',id=null,error='network_error';
    try{
     const r=await fetcher('https://api.resend.com/emails',{method:'POST',headers:{Authorization:`Bearer ${env('RESEND_API_KEY')}`,'Content-Type':'application/json','Idempotency-Key':`weekly-${await hash(issue.id+':'+recipient.email+':'+recipient.consent_at)}`},body:JSON.stringify(payload),signal:AbortSignal.timeout(15000)});
     if(r.ok){const result=await r.json();if(typeof result.id!=='string')throw new Error('invalid_response');status='accepted';id=result.id;error=null;accepted++;}
     else {status=r.status===429||r.status>=500?'retry':'failed';error=`http_${r.status}`;}
    }catch{/* Ambiguous requests reuse the frozen payload and provider idempotency key. */}
    await rpc('weekly_complete',{p_issue:issue.id,p_email:recipient.email,p_status:status,p_resend_id:id,p_error:error});
    await pause(600);
   }
   return reply('processed',200,{issue:issue.id,accepted,statuses:await rpc('weekly_status',{p_issue:issue.id})});
  }catch(e){return reply(['stale_feed','no_news','feed_unavailable'].includes(e.message)?e.message:'service_unavailable',503);}
  finally{if(owner)try{await rpc('weekly_unlock',{p_owner:owner});}catch{}}
 };
}
