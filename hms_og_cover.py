#!/usr/bin/env python3
"""hms_og_cover.py — generate og-cover.jpg (1200x630) for hms-site OG/Twitter cards.
Uses the site's dark + gold aesthetic. PIL only, tokenless."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
img = Image.new('RGB', (W, H), (12, 14, 18))
d = ImageDraw.Draw(img)

# subtle gold gradient band at bottom
for y in range(H - 200, H):
    t = (y - (H - 200)) / 200
    r = int(12 + t * 3); g = int(14 + t * 2); b = int(18 + t * 2)
    d.line([(0, y), (W, y)], fill=(r, g, b))

# gold accent bar
d.rectangle([80, 150, 160, 158], fill=(212, 175, 55))

# try system fonts
font_paths = [
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/System/Library/Fonts/Helvetica.ttc',
    '/Library/Fonts/Arial.ttf',
]
title_font = body_font = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            title_font = ImageFont.truetype(fp, 84)
            body_font = ImageFont.truetype(fp, 34)
            break
        except Exception:
            pass
if not title_font:
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

# wordmark
d.text((80, 200), "Hightower", fill=(240, 240, 235), font=title_font)
d.text((80, 290), "Marketing Strategies", fill=(212, 175, 55), font=ImageFont.truetype(font_paths[0], 56) if os.path.exists(font_paths[0]) else title_font)

# tagline
d.text((80, 430), "AI-powered marketing that shows real ROI.", fill=(200, 200, 195), font=body_font)
d.text((80, 480), "Digital strategy  ·  Video ads  ·  Automation", fill=(160, 160, 155), font=body_font)

# url
d.text((80, 555), "hightower-marketing.com", fill=(212, 175, 55), font=body_font)

out = os.path.expanduser('~/projects/hms-site/og-cover.jpg')
img.save(out, 'JPEG', quality=88)
print('saved', out, img.size)