export const origins = new Set(['https://therwawire.com', 'https://www.therwawire.com']);
export const placements = new Set(['homepage-newsletter', 'article-newsletter', 'newsletter-page']);
export const consentVersion = '2026-10-07-v1';
export async function digest(value) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))].map(x => x.toString(16).padStart(2, '0')).join('');
}
export function createHandler(env, fetcher = fetch) {
  return async req => {
    const origin = req.headers.get('origin') || '';
    const headers = {'content-type':'application/json', 'cache-control':'no-store', 'Vary':'Origin', 'Access-Control-Allow-Origin': origins.has(origin) ? origin : 'https://therwawire.com', 'Access-Control-Allow-Headers':'content-type', 'Access-Control-Allow-Methods':'POST, OPTIONS'};
    const reply = (status, code) => new Response(JSON.stringify({code}), {status, headers});
    if (!origins.has(origin)) return reply(403, 'forbidden');
    if (req.method === 'OPTIONS') return new Response(null, {status:204, headers});
    if (req.method !== 'POST') return reply(405, 'method_not_allowed');
    if (!(req.headers.get('content-type') || '').startsWith('application/json')) return reply(415, 'invalid_content_type');
    try {
      const raw = await req.text();
      if (raw.length > 4096) return reply(413, 'too_large');
      let body;
      try { body = JSON.parse(raw); } catch { return reply(400, 'invalid_request'); }
      if (!body || typeof body !== 'object') return reply(400, 'invalid_request');
      const url = env('SUPABASE_URL'), key = env('SUPABASE_SERVICE_ROLE_KEY');
      if (!url || !key) return reply(503, 'unavailable');
      const dbHeaders = {apikey:key, authorization:`Bearer ${key}`, 'content-type':'application/json'};
      const rpc = async (name, data) => {
        const result = await fetcher(`${url}/rest/v1/rpc/${name}`, {method:'POST', headers:dbHeaders, body:JSON.stringify(data)});
        if (!result.ok) throw new Error('storage');
        return result.json();
      };
      if (body.action === 'confirm' || body.action === 'unsubscribe') {
        if (typeof body.token !== 'string' || !/^[a-f0-9]{64}$/.test(body.token)) return reply(400, 'invalid_link');
        const ok = await rpc('newsletter_token_action', {p_action:body.action, p_hash:await digest(body.token)});
        return reply(ok ? 200 : 400, ok ? body.action === 'confirm' ? 'confirmed' : 'unsubscribed' : 'invalid_link');
      }
      if (body.action !== 'subscribe') return reply(400, 'invalid_action');
      const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
      if (email.length > 254 || !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(email) || body.consent !== true || !placements.has(body.placement)) return reply(400, 'invalid_request');
      if (body.website) return reply(202, 'check_email');
      const apiKey = env('RESEND_API_KEY'), from = env('NEWSLETTER_FROM'), captchaSecret = env('TURNSTILE_SECRET_KEY');
      if (env('NEWSLETTER_ENABLED') !== 'true' || !apiKey || !from || !captchaSecret) return reply(503, 'unavailable');
      if (typeof body.captcha !== 'string' || !body.captcha || body.captcha.length > 2048) return reply(400, 'captcha_required');
      const captcha = await fetcher('https://challenges.cloudflare.com/turnstile/v0/siteverify', {method:'POST', body:new URLSearchParams({secret:captchaSecret, response:body.captcha})});
      if (!captcha.ok) return reply(503, 'unavailable');
      const verified = await captcha.json();
      if (!verified.success || !['therwawire.com','www.therwawire.com'].includes(verified.hostname) || verified.action !== 'newsletter') return reply(400, 'captcha_failed');
      // The gateway sets x-forwarded-for. Persist only a daily, secret-salted hash.
      const ip = (req.headers.get('x-forwarded-for') || 'unknown').split(',')[0].trim();
      const bucket = await digest(`${key}:${new Date().toISOString().slice(0,10)}:${ip}`);
      if (!await rpc('newsletter_rate_limit', {p_bucket:bucket})) return reply(429, 'rate_limited');
      const token = [...crypto.getRandomValues(new Uint8Array(32))].map(x=>x.toString(16).padStart(2,'0')).join('');
      const unsubscribeToken = [...crypto.getRandomValues(new Uint8Array(32))].map(x=>x.toString(16).padStart(2,'0')).join('');
      const hash = await digest(token);
      const reserved = await rpc('newsletter_reserve', {p_email:email, p_hash:hash, p_unsubscribe_hash:await digest(unsubscribeToken), p_placement:body.placement, p_consent_version:consentVersion});
      // Identical response for existing subscribers and cooldowns prevents enumeration.
      if (!reserved) return reply(202, 'check_email');
      const confirmUrl = `https://therwawire.com/newsletter/#confirm=${token}`;
      const unsubscribeUrl = `https://therwawire.com/newsletter/#unsubscribe=${unsubscribeToken}`;
      const sent = await fetcher('https://api.resend.com/emails', {method:'POST', headers:{authorization:`Bearer ${apiKey}`, 'content-type':'application/json', 'Idempotency-Key':`newsletter-${hash}`}, body:JSON.stringify({from, to:[email], subject:'Confirm your RWA Wire newsletter subscription', text:`You requested RWA Wire news, research and explainers by email. Confirm within 24 hours:\n${confirmUrl}\n\nIf you did not request this, ignore this email.\nCancel this request or unsubscribe:\n${unsubscribeUrl}`, html:`<h1>Confirm your RWA Wire subscription</h1><p>You requested news, research and explainers from RWA Wire.</p><p><a href="${confirmUrl}">Confirm subscription</a> (expires in 24 hours)</p><p>If you did not request this, ignore this email.</p><p><a href="${unsubscribeUrl}">Cancel or unsubscribe</a></p>`})});
      if (!sent.ok) return reply(503, 'unavailable');
      return reply(202, 'check_email');
    } catch { return reply(503, 'unavailable'); }
  };
}
