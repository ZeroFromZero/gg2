with open('app.py', encoding='utf-8') as f:
    content = f.read()

start_marker = '@app.route("/promo/<biz_id>")\ndef promo_image(biz_id):'
end_marker = '@app.route("/card/<biz_id>/set_url"'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

new_func = r'''@app.route("/promo/<biz_id>")
def promo_image(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404

    style = request.args.get('style', 'dark')

    palettes = {
        'dark':   {'bg1':(10,12,28),    'bg2':(25,22,70),   'bg3':(10,12,28),   'acc':(99,102,241),  'brand_bg':(5,150,105)},
        'ocean':  {'bg1':(8,50,80),     'bg2':(2,120,190),  'bg3':(8,50,80),    'acc':(56,189,248),  'brand_bg':(3,105,161)},
        'forest': {'bg1':(10,55,30),    'bg2':(20,150,65),  'bg3':(10,55,30),   'acc':(74,222,128),  'brand_bg':(21,128,61)},
        'rose':   {'bg1':(100,15,45),   'bg2':(210,25,65),  'bg3':(100,15,45),  'acc':(251,113,133), 'brand_bg':(159,18,57)},
        'gold':   {'bg1':(90,40,10),    'bg2':(200,110,5),  'bg3':(90,40,10),   'acc':(251,191,36),  'brand_bg':(180,83,9)},
        'violet': {'bg1':(35,10,85),    'bg2':(110,45,220), 'bg3':(35,10,85),   'acc':(167,139,250), 'brand_bg':(109,40,217)},
    }
    p = palettes.get(style, palettes['dark'])

    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import textwrap

    W, H = 1080, 1920  # 9:16 Android

    img = Image.new("RGB", (W, H), p['bg1'])
    draw = ImageDraw.Draw(img)

    # Degradado vertical
    for y in range(H):
        t = y / H
        mid = 0.45
        if t < mid:
            r = int(p['bg1'][0] + (p['bg2'][0]-p['bg1'][0]) * (t/mid))
            g = int(p['bg1'][1] + (p['bg2'][1]-p['bg1'][1]) * (t/mid))
            b = int(p['bg1'][2] + (p['bg2'][2]-p['bg1'][2]) * (t/mid))
        else:
            r = int(p['bg2'][0] + (p['bg3'][0]-p['bg2'][0]) * ((t-mid)/(1-mid)))
            g = int(p['bg2'][1] + (p['bg3'][1]-p['bg2'][1]) * ((t-mid)/(1-mid)))
            b = int(p['bg2'][2] + (p['bg3'][2]-p['bg2'][2]) * ((t-mid)/(1-mid)))
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Glow arriba
    glow = Image.new("RGB",(W,H),(0,0,0))
    gd = ImageDraw.Draw(glow)
    for i in range(220,0,-1):
        a = int(55*(i/220)**2)
        gd.ellipse([W//2-i*3,-i*2,W//2+i*3,i*2],
                   fill=(min(255,p['bg2'][0]+a),min(255,p['bg2'][1]+a),min(255,p['bg2'][2]+a)))
    glow = glow.filter(ImageFilter.GaussianBlur(55))
    img = Image.blend(img, glow, 0.55)

    # Glow abajo suave
    glow2 = Image.new("RGB",(W,H),(0,0,0))
    gd2 = ImageDraw.Draw(glow2)
    for i in range(160,0,-1):
        a = int(35*(i/160)**2)
        gd2.ellipse([W//2-i*3,H-i,W//2+i*3,H+i*2],
                    fill=(min(255,p['brand_bg'][0]+a),min(255,p['brand_bg'][1]+a),min(255,p['brand_bg'][2]+a)))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, glow2, 0.4)
    draw = ImageDraw.Draw(img)

    # Fuentes
    fb = "C:/Windows/Fonts/arialbd.ttf"
    fr = "C:/Windows/Fonts/arial.ttf"
    try:
        f_huge  = ImageFont.truetype(fb, 110)
        f_big   = ImageFont.truetype(fb, 52)
        f_med   = ImageFont.truetype(fb, 38)
        f_small = ImageFont.truetype(fr, 32)
        f_tiny  = ImageFont.truetype(fr, 26)
        f_brand = ImageFont.truetype(fb, 46)
    except:
        f_huge = f_big = f_med = f_small = f_tiny = f_brand = ImageFont.load_default()

    def ctext(text, font, y, color):
        tw = int(draw.textlength(text, font=font))
        draw.text(((W-tw)//2, y), text, font=font, fill=color)

    # ─── ZONA 1: Logo (y=120..300) ───
    logo_sz = 180
    lx = (W-logo_sz)//2
    ly = 120
    has_logo = False
    if biz.get("logo"):
        lp_path = os.path.join(UPLOAD_FOLDER, biz["logo"])
        if os.path.exists(lp_path):
            try:
                li = Image.open(lp_path).convert("RGBA").resize((logo_sz,logo_sz), Image.LANCZOS)
                mask = Image.new("L",(logo_sz,logo_sz),0)
                ImageDraw.Draw(mask).ellipse([0,0,logo_sz,logo_sz],fill=255)
                draw.ellipse([lx-8,ly-8,lx+logo_sz+8,ly+logo_sz+8],fill=(255,255,255))
                img.paste(li,(lx,ly),mask)
                draw = ImageDraw.Draw(img)
                has_logo = True
            except: pass
    if not has_logo:
        draw.ellipse([lx,ly,lx+logo_sz,ly+logo_sz], fill=p['acc'])
        letter = biz["name"][0].upper()
        try: lf = ImageFont.truetype(fb, 90)
        except: lf = ImageFont.load_default()
        ltw = int(draw.textlength(letter, font=lf))
        draw.text(((W-ltw)//2, ly+40), letter, font=lf, fill=(255,255,255))

    # ─── ZONA 2: Categoría (y=330) ───
    cat = biz.get("category","").upper()
    if cat:
        bw = int(draw.textlength(cat, font=f_tiny)) + 56
        bx = (W-bw)//2
        draw.rounded_rectangle([bx,330,bx+bw,378], radius=24,
                                fill=tuple(max(0,c-60) for c in p['bg2']))
        draw.rounded_rectangle([bx,330,bx+bw,378], radius=24, outline=p['acc'], width=2)
        tw = int(draw.textlength(cat, font=f_tiny))
        draw.text(((W-tw)//2, 340), cat, font=f_tiny, fill=p['acc'])

    # ─── ZONA 3: Nombre (y=410) ───
    lines = textwrap.wrap(biz["name"], width=13)
    y = 410
    for line in lines[:2]:
        ctext(line, f_huge, y, (255,255,255))
        y += 118

    # ─── Separador ───
    sep_y = y + 20
    draw.line([(100,sep_y),(W-100,sep_y)], fill=(40,45,80), width=2)

    # ─── ZONA 4: QR grande centrado (y=sep+40) ───
    profile_url = f"https://zuppon.es/p/{biz_id}"
    qr_obj = qrcode.QRCode(box_size=12, border=2)
    qr_obj.add_data(profile_url)
    qr_obj.make(fit=True)
    qr_pil = qr_obj.make_image(fill_color="#0a0c1e", back_color="white").convert("RGB")
    qr_sz = 500
    qr_pil = qr_pil.resize((qr_sz,qr_sz), Image.LANCZOS)
    pad = 26
    qx = (W-qr_sz)//2
    qy = sep_y + 50
    draw.rounded_rectangle([qx-pad,qy-pad,qx+qr_sz+pad,qy+qr_sz+pad], radius=28, fill=(255,255,255))
    img.paste(qr_pil,(qx,qy))
    draw = ImageDraw.Draw(img)

    y = qy + qr_sz + pad + 50

    # ─── ZONA 5: CTA ───
    ctext("Escanea para ver nuestros productos", f_small, y, (180,190,215))
    y += 52

    # URL
    url_short = profile_url.replace("https://","")
    uw = int(draw.textlength(url_short, font=f_med)) + 60
    ux = (W-uw)//2
    draw.rounded_rectangle([ux,y,ux+uw,y+56], radius=28,
                            fill=tuple(max(0,c-50) for c in p['bg2']))
    draw.rounded_rectangle([ux,y,ux+uw,y+56], radius=28, outline=p['acc'], width=2)
    tw = int(draw.textlength(url_short, font=f_med))
    draw.text(((W-tw)//2, y+8), url_short, font=f_med, fill=p['acc'])
    y += 80

    # ─── ZONA 6: Contacto ───
    if biz.get("phone"):
        ctext("📞  " + biz["phone"], f_small, y, (203,213,225))
        y += 46
    if biz.get("address"):
        addr = biz["address"][:40]
        ctext("📍  " + addr, f_small, y, (203,213,225))
        y += 46
    if biz.get("instagram"):
        ctext("📸  " + biz["instagram"], f_small, y, (203,213,225))

    # ─── ZONA 7: Branding fijo al fondo ───
    footer_h = 130
    draw.rectangle([0, H-footer_h, W, H], fill=p['brand_bg'])
    # Línea superior del footer
    draw.line([(0,H-footer_h),(W,H-footer_h)], fill=(255,255,255,30) if False else (255,255,255), width=1)
    ctext("Zuppon", f_brand, H-footer_h+18, (255,255,255))
    ctext("Tu negocio digital", f_tiny, H-footer_h+72, (200,240,220))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    safe_name = biz["name"].replace(" ","_")
    response.headers["Content-Disposition"] = f'attachment; filename="{safe_name}_estado_{style}.png"'
    return response

'''

new_content = content[:start_idx] + new_func + content[end_idx:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Done')
