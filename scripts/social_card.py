#!/usr/bin/env python3
"""Generate a branded 1200x675 RWA Wire social card for an evergreen package."""
import json, pathlib, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: raise SystemExit('Usage: social_card.py <package.json>')
p=(ROOT/sys.argv[1]).resolve(); d=json.loads(p.read_text(encoding='utf-8'))
out=ROOT/'public/generated/social'; out.mkdir(parents=True,exist_ok=True); dest=out/f"{d['id']}.jpg"
W,H=1200,675
im=Image.new('RGB',(W,H),(8,12,16)); draw=ImageDraw.Draw(im)
# restrained RWA Wire terminal/editorial treatment
for x in range(0,W,80): draw.line((x,0,x,H),fill=(15,24,29),width=1)
for y in range(0,H,80): draw.line((0,y,W,y),fill=(15,24,29),width=1)
draw.rectangle((0,0,12,H),fill=(62,232,174)); draw.rectangle((70,70,1130,605),outline=(42,58,64),width=2)
font_candidates=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
bold_candidates=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
def font(paths,size):
 for f in paths:
  if pathlib.Path(f).exists(): return ImageFont.truetype(f,size)
 return ImageFont.load_default()
brand=font(bold_candidates,34); eyebrow=font(bold_candidates,20); headline=font(bold_candidates,58); small=font(font_candidates,22)
draw.text((105,105),'RWA WIRE',font=brand,fill=(235,242,240)); draw.text((105,158),'// INTELLIGENCE FOR TOKENIZED MARKETS',font=eyebrow,fill=(62,232,174))
category=str(d.get('category') or d.get('kind') or 'EVERGREEN').upper(); draw.text((105,235),category,font=eyebrow,fill=(143,158,163))
title=str(d.get('title','')).replace(' Explained','')
# pixel-aware wrapping to prevent long titles escaping the card
words=title.split(); lines=[]; cur=''
for word in words:
 test=(cur+' '+word).strip()
 if draw.textbbox((0,0),test,font=headline)[2] <= 930: cur=test
 else:
  if cur: lines.append(cur)
  cur=word
if cur: lines.append(cur)
lines=lines[:3]
if len(lines)==3 and len(' '.join(lines)) < len(title): lines[-1]=lines[-1].rstrip(' .')+'…'
y=280
for line in lines:
 draw.text((105,y),line,font=headline,fill=(245,248,247)); y+=72
draw.line((105,535,1095,535),fill=(42,58,64),width=2)
draw.text((105,560),'READ THE FULL GUIDE',font=eyebrow,fill=(62,232,174)); draw.text((850,558),'therwawire.com',font=small,fill=(180,192,195))
im.save(dest,'JPEG',quality=92,optimize=True)
print(dest.relative_to(ROOT))
