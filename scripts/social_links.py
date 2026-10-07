"""Channel attribution for public links; no visitor identifiers or redirects."""
import re
from urllib.parse import urlsplit, urlunsplit, urlencode

def tracking_url(url, channel, campaign):
    u=urlsplit(url)
    if u.scheme!='https' or u.netloc!='therwawire.com' or not re.fullmatch(r'/[a-z0-9/_-]*',u.path):
        raise ValueError('Expected a public RWA Wire URL')
    if channel not in ('x','telegram'): raise ValueError('Unsupported distribution channel')
    campaign=re.sub(r'[^a-z0-9_-]','-',str(campaign).lower()).strip('-')[:160]
    if not campaign: raise ValueError('Missing campaign')
    return urlunsplit((u.scheme,u.netloc,u.path,urlencode({'utm_source':channel,'utm_medium':'social','utm_campaign':campaign}),''))

def social_copy(text, url, channel, campaign, limit=None):
    link=tracking_url(url,channel,campaign)
    canonical=urlunsplit((*urlsplit(url)[:3],'',''))
    body=re.sub(re.escape(canonical)+r'(?:\?[^\s]*)?', '', str(text)).strip()
    # Preserve the editorial copy and keep the complete destination last.
    suffix='\n\n'+link
    if limit is not None:
        budget=limit-len(suffix)
        if budget<40: raise ValueError('Caption limit cannot fit destination')
        if len(body)>budget: body=body[:budget-1].rsplit(' ',1)[0].rstrip()+'…'
    return body+suffix
