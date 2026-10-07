import {database} from '../weekly-newsletter/handler.mjs';
import {hash} from '../../../shared/weekly.mjs';
export function createUnsubscribeHandler(env,fetcher=fetch){const rpc=database(env,fetcher);return async req=>{
 const token=new URL(req.url).searchParams.get('token');if(!/^[a-f0-9]{64}$/.test(token||''))return new Response(null,{status:400});
 if(req.method==='GET')return Response.redirect(`https://therwawire.com/newsletter/#unsubscribe=${token}`,302);
 if(req.method!=='POST')return new Response(null,{status:405});
 if((await req.text())!=='List-Unsubscribe=One-Click')return new Response(null,{status:400});
 try{await rpc('newsletter_token_action',{p_action:'unsubscribe',p_hash:await hash(token)});return new Response(null,{status:200});}catch{return new Response(null,{status:503});}
};}
