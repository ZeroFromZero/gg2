with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Find start and end of promo_image function
start_marker = '@app.route("/promo/<biz_id>")\ndef promo_image(biz_id):'
end_marker = '@app.route("/card/<biz_id>/set_url"'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

new_func = '''@app.route("/promo/<biz_id>")
def promo_image(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404

    style = request.args.get('style', 'dark')

    palettes = {
        'dark':   {'bg1':(15,23,42),   'bg2':(30,27,75),   'acc':(99,102,241),  'brand_bg':(5,150,105)},
        'ocean':  {'bg1':(12,74,110),  'bg2':(2,132,199),  'acc':(56,189,248),  'brand_bg':(3,105,161)},
        'forest': {'bg1':(20,83,45),   'bg2':(22,163,74),  'acc':(74,222,128),  'brand_bg':(21,128,61)},
        'rose':   {'bg1':(136,19,55),  'bg2':(225,29,72),  'acc':(251,113,133), 'brand_bg':(159,18,57)},
        'gold':   {'bg1':(120,53,15),  'bg2':(217,119,6),  'acc':(251,191,36),  'brand_bg':(180,83,9)},
        'violet': {'bg1':(46,16,101),  'bg2':(124,58,237), 'acc':(167,139,250), 'brand_bg':(109,40,217)},
    }
    p = palettes.get(style, palettes['dark'])

    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import textwrap

    # 1080x1080 — formato cuadrado para estados de WhatsApp
    S = 1080
    img = Image.new("RGB", (S, S), p['bg1'])
    draw = ImageDraw.Draw(img)

    # Fondo degradado
    for y in range(S):
        t = y / S
        r = int(p['bg1'][0] + (p['bg2'][0]-p['bg1'][0]) * t)
        g = int(p['bg1'][1] + (p['bg2'][1]-p['bg1'][1]) * t)
        b = int(p['bg1'][2] + (p['bg2'][2]-p['bg1'][2]) * t)
        draw.line([(0,y),(S,y)], fill=(r,g,b))

    # Glow
    glow = Image.new("RGB", (S,S), (0,0,0))
    gd = ImageDraw.Draw(glow)
    for i in range(180,0,-1):
        a = int(60*(i/180)**2)
        gd.ellipse([S//2-i*3,-i*2,S//2+i*3,i*2],
                   fill=(min(255,p['bg2'][0]+a),min(255,p['bg2'][1]+a),min(255,p['bg2'][2]+a)))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img = Image.blend(img, glow, 0.5)
    draw = ImageDraw.Draw(img)

    # Fuentes
    fb = "C:/Windows/Fonts/arialbd.ttf"
    fr = "C:/Windows/Fonts/arial.ttf"
    try:
        f_name  = ImageFont.truetype(fb, 80)
        f_med   = ImageFont.truetype(fb, 32)
        f_small = ImageFont.truetype(fr, 26)
        f_tiny  = ImageFont.truetype(fr, 22)
        f_brand = ImageFont.truetype(fb, 38)
    except:
        f_name = f_med = f_small = f_tiny = f_brand = ImageFont.load_default()

    def cx(text, font, y, color):
        tw = int(draw.textlength(text, font=font))
        draw.text(((S-tw)//2, y), text, font=font, fill=color)

    # ── Logo ──
    logo_sz = 140
    lx = (S - logo_sz) // 2
    ly = 60
    has_logo = False
    if biz.get("logo"):
        lp_path = os.path.join(UPLOAD_FOLDER, biz["logo"])
        if os.path.exists(lp_path):
            try:
                li = Image.open(lp_path).convert("RGBA").resize((logo_sz,logo_sz), Image.LANCZOS)
                mask = Image.new("L",(logo_sz,logo_sz),0)
                ImageDraw.Draw(mask).ellipse([0,0,logo_sz,logo_sz],fill=255)
                draw.ellipse([lx-6,ly-6,lx+logo_sz+6,ly+logo_sz+6],fill=(255,255,255))
                img.paste(li,(lx,ly),mask)
                draw = ImageDraw.Draw(img)
                has_logo = True
            except: pass
    if not has_logo:
        draw.ellipse([lx,ly,lx+logo_sz,ly+logo_sz], fill=p['acc'])
        letter = biz["name"][0].upper()
        try: lf = ImageFont.truetype(fb, 72)
        except: lf = ImageFont.load_default()
        ltw = int(draw.textlength(letter, font=lf))
        draw.text(((S-ltw)//2, ly+28), letter, font=lf, fill=(255,255,255))

    # ── Categoría ──
    cat = biz.get("category","").upper()
    if cat:
        bw = int(draw.textlength(cat, font=f_tiny)) + 48
        bx = (S-bw)//2
        draw.rounded_rectangle([bx,230,bx+bw,272], radius=21, fill=(*p['acc'],60) if False else tuple(max(0,c-80) for c in p['bg2']))
        draw.rounded_rectangle([bx,230,bx+bw,272], radius=21, outline=p['acc'], width=2)
        tw = int(draw.textlength(cat, font=f_tiny))
        draw.text(((S-tw)//2, 238), cat, font=f_tiny, fill=p['acc'])

    # ── Nombre ──
    lines = textwrap.wrap(biz["name"], width=14)
    y = 290
    for line in lines[:2]:
        cx(line, f_name, y, (255,255,255))
        y += 90

    # ── Separador ──
    draw.line([(80,y+10),(S-80,y+10)], fill=(40,45,80), width=2)
    y += 30

    # ── QR ──
    profile_url = f"https://zuppon.es/p/{biz_id}"
    qr_obj = qrcode.QRCode(box_size=10, border=2)
    qr_obj.add_data(profile_url)
    qr_obj.make(fit=True)
    qr_pil = qr_obj.make_image(fill_color="#0f172a", back_color="white").convert("RGB")
    qr_sz = 340
    qr_pil = qr_pil.resize((qr_sz,qr_sz), Image.LANCZOS)
    pad = 20
    qx = (S-qr_sz)//2
    qy = y + 20
    draw.rounded_rectangle([qx-pad,qy-pad,qx+qr_sz+pad,qy+qr_sz+pad], radius=20, fill=(255,255,255))
    img.paste(qr_pil,(qx,qy))
    draw = ImageDraw.Draw(img)

    y = qy + qr_sz + pad + 30

    # ── Escanea ──
    cx("Escanea para ver nuestros productos", f_small, y, (148,163,184))
    y += 40

    # ── URL ──
    url_short = profile_url.replace("https://","")
    cx(url_short, f_med, y, p['acc'])
    y += 50

    # ── Contacto ──
    if biz.get("phone"):
        cx("📞 " + biz["phone"], f_small, y, (203,213,225))
        y += 36

    # ── Branding ──
    brand_y = S - 90
    btext = "Zuppon · Tu negocio digital"
    btw = int(draw.textlength(btext, font=f_brand)) + 60
    bpx = (S-btw)//2
    draw.rounded_rectangle([bpx, brand_y-8, bpx+btw, brand_y+52], radius=30, fill=p['brand_bg'])
    cx(btext, f_brand, brand_y, (255,255,255))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    safe_name = biz["name"].replace(" ","_")
    response.headers["Content-Disposition"] = f\'attachment; filename="{safe_name}_estado_{style}.png"\'
    return response

'''

new_content = content[:start_idx] + new_func + content[end_idx:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Done')
