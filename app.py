from flask import Flask, render_template, request, redirect, url_for, session, make_response
from datetime import datetime, timedelta
import qrcode, io, base64, json, os, uuid
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

app = Flask(__name__)
app.secret_key = "qrcard-secret-2025"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
DATA_FILE = "businesses.json"
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_businesses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_businesses(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def generate_qr(url):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def track(biz_id, event):
    """Registra un evento solo 1 vez por IP cada 30 minutos."""
    businesses = load_businesses()
    if biz_id not in businesses:
        return

    ip = request.remote_addr or "unknown"
    now = datetime.now()
    cooldown = timedelta(minutes=30)

    # Clave de sesión única por negocio+evento
    session_key = f"last_{event}_{biz_id}"
    last_str = session.get(session_key)

    if last_str:
        last_time = datetime.fromisoformat(last_str)
        if now - last_time < cooldown:
            return  # Ya contó en los últimos 30 min, ignorar

    # Registrar en sesión
    session[session_key] = now.isoformat()

    stats = businesses[biz_id].setdefault("stats", {"profile_views": 0, "qr_scans": 0, "last_seen": None})
    if event == "profile_view":
        stats["profile_views"] = stats.get("profile_views", 0) + 1
    elif event == "qr_scan":
        stats["qr_scans"] = stats.get("qr_scans", 0) + 1
    stats["last_seen"] = now.strftime("%d/%m/%Y %H:%M")
    businesses[biz_id]["stats"] = stats
    save_businesses(businesses)

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        # Acceso por nombre + código
        if "access_code" in request.form:
            code = request.form["access_code"].strip().upper()
            name = request.form.get("access_name", "").strip().lower()
            businesses = load_businesses()
            for biz_id, biz in businesses.items():
                if (biz.get("access_code", "").upper() == code and
                        biz.get("name", "").strip().lower() == name):
                    return redirect(url_for("card", biz_id=biz_id))
            error = "Nombre o código incorrecto. Verifica e intenta de nuevo."
            return render_template("index.html", error=error)

        # Crear nueva tarjeta
        biz_id = str(uuid.uuid4())[:8]
        logo_filename = None
        file = request.files.get("logo")
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            logo_filename = f"{biz_id}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, logo_filename))

        businesses = load_businesses()
        businesses[biz_id] = {
            "name": request.form["name"],
            "category": request.form["category"],
            "phone": request.form["phone"],
            "email": request.form["email"],
            "address": request.form["address"],
            "website": request.form.get("website", ""),
            "maps_url": request.form.get("maps_url", ""),
            "description": request.form.get("description", ""),
            "instagram": request.form.get("instagram", ""),
            "facebook": request.form.get("facebook", ""),
            "tiktok": request.form.get("tiktok", ""),
            "wifi_ssid": request.form.get("wifi_ssid", ""),
            "wifi_password": request.form.get("wifi_password", ""),
            "access_code": request.form.get("access_code_new", "").strip().upper(),
            "logo": logo_filename,
            "stats": {"profile_views": 0, "qr_scans": 0, "last_seen": None},
            "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        save_businesses(businesses)
        return redirect(url_for("card", biz_id=biz_id))
    return render_template("index.html", error=error)

@app.route("/card/<biz_id>")
def card(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404
    profile_url = f"https://zuppon.es/p/{biz_id}"
    # El QR del perfil lleva a /scan/ para registrar el escaneo antes de redirigir
    scan_url = f"https://zuppon.es/scan/{biz_id}"
    qr_profile = generate_qr(scan_url)
    qr_wifi = None
    wifi_ssid = biz.get("wifi_ssid", "")
    wifi_pass = biz.get("wifi_password", "")
    if wifi_ssid:
        qr_wifi = generate_qr(f"WIFI:T:WPA;S:{wifi_ssid};P:{wifi_pass};;")
    return render_template("card.html", biz=biz, qr_img=qr_profile, qr_wifi=qr_wifi, profile_url=profile_url, biz_id=biz_id, shared=False)

@app.route("/print/<biz_id>")
def print_public(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Tarjeta no encontrada", 404
    scan_url = f"https://zuppon.es/scan/{biz_id}"
    qr_img = generate_qr(scan_url)
    profile_url = f"https://zuppon.es/p/{biz_id}"
    return render_template("card.html", biz=biz, biz_id=biz_id, qr_img=qr_img, profile_url=profile_url, shared=True)

@app.route("/scan/<biz_id>")
def scan(biz_id):
    """Registra escaneo QR y redirige al perfil"""
    track(biz_id, "qr_scan")
    return redirect(url_for("profile", biz_id=biz_id))

@app.route("/p/<biz_id>/productos")
def public_products(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404
    return render_template("public_products.html", biz=biz, biz_id=biz_id)

@app.route("/p/<biz_id>")
def profile(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404
    track(biz_id, "profile_view")
    return render_template("profile.html", biz=biz, biz_id=biz_id)

@app.route("/card/<biz_id>/pdf")
def download_pdf(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404

    # QR
    scan_url = f"https://zuppon.es/scan/{biz_id}"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(scan_url)
    qr.make(fit=True)
    qr_pil = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_buf = io.BytesIO()
    qr_pil.save(qr_buf, format="PNG")

    buf = io.BytesIO()
    page_w, page_h = letter  # 612 x 792 pt
    c = canvas.Canvas(buf, pagesize=letter)

    card_w = 105 * mm
    card_h = 68 * mm
    gap     = 10 * mm
    x = (page_w - card_w) / 2
    # Centrar las 3 tarjetas verticalmente en la página
    total = 3 * card_h + 2 * gap
    start_y = (page_h + total) / 2 - card_h  # top de la primera tarjeta

    # Ancho columna derecha (QR)
    right_col = 38 * mm
    sep_x = x + card_w - right_col

    for i in range(3):
        # y = esquina inferior izquierda de la tarjeta (ReportLab usa bottom-left)
        card_y = start_y - i * (card_h + gap)

        # ── Fondo ──
        c.setFillColor(colors.HexColor("#0f172a"))
        c.roundRect(x, card_y, card_w, card_h, 4 * mm, fill=1, stroke=0)

        # ── Separador ──
        c.setFillColor(colors.HexColor("#334155"))
        c.rect(sep_x, card_y + 6 * mm, 0.5, card_h - 12 * mm, fill=1, stroke=0)

        # ── IZQUIERDA: posiciones absolutas desde arriba ──
        lx = x + 6 * mm          # left margin
        top = card_y + card_h     # top de la tarjeta

        # Logo — 5mm desde arriba
        logo_sz = 11 * mm
        logo_y  = top - 5 * mm - logo_sz
        if biz.get("logo"):
            lp = os.path.join(UPLOAD_FOLDER, biz["logo"])
            if os.path.exists(lp):
                c.setFillColor(colors.white)
                c.roundRect(lx, logo_y, logo_sz, logo_sz, 2 * mm, fill=1, stroke=0)
                c.drawImage(ImageReader(lp), lx, logo_y, logo_sz, logo_sz,
                            preserveAspectRatio=True, mask='auto')
        else:
            c.setFillColor(colors.HexColor("#6366f1"))
            c.roundRect(lx, logo_y, logo_sz, logo_sz, 2 * mm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(lx + logo_sz / 2, logo_y + 2.5 * mm, biz["name"][0].upper())

        # Nombre — debajo del logo con 2.5mm de gap
        name_y = logo_y - 2.5 * mm - 4 * mm   # -4mm = altura aprox del texto 11pt
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(lx, name_y, biz["name"][:22])

        # Categoría — 3mm debajo del nombre
        cat_y = name_y - 3 * mm - 2.5 * mm
        c.setFillColor(colors.HexColor("#a5b4fc"))
        c.setFont("Helvetica", 6)
        c.drawString(lx, cat_y, biz.get("category", "")[:24].upper())

        # Contactos — 4mm debajo de categoría, cada línea 3.8mm
        contacts = [
            ("#e2e8f0", "📞", biz.get("phone", "")),
            ("#fce7f3", "✉", biz.get("email", "")),
            ("#dcfce7", "📍", biz.get("address", "")),
        ]
        if biz.get("website"):
            contacts.append(("#ede9fe", "🌐", biz["website"].replace("https://","").replace("http://","")))

        cy = cat_y - 4 * mm
        dot_sz = 2 * mm
        dot_colors = ["#3b82f6", "#a855f7", "#22c55e", "#f97316"]
        for idx, (_, _icon, val) in enumerate(contacts):
            if cy < card_y + 3 * mm:
                break
            # Punto de color en vez de emoji
            c.setFillColor(colors.HexColor(dot_colors[idx % len(dot_colors)]))
            c.circle(lx + dot_sz / 2, cy + dot_sz / 2, dot_sz / 2, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#cbd5e1"))
            c.setFont("Helvetica", 6.5)
            c.drawString(lx + dot_sz + 2 * mm, cy, str(val)[:30])
            cy -= 3.8 * mm

        # ── DERECHA: QR centrado ──
        qr_sz = 26 * mm
        qr_x  = sep_x + (right_col - qr_sz) / 2
        qr_y  = card_y + (card_h - qr_sz) / 2 + 3 * mm  # ligeramente arriba del centro

        # Fondo blanco QR
        pad = 1.5 * mm
        c.setFillColor(colors.white)
        c.roundRect(qr_x - pad, qr_y - pad, qr_sz + 2*pad, qr_sz + 2*pad, 2*mm, fill=1, stroke=0)

        # QR image
        qr_buf.seek(0)
        c.drawImage(ImageReader(qr_buf), qr_x, qr_y, qr_sz, qr_sz)

        # Texto bajo QR
        text_y = qr_y - 5 * mm
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(sep_x + right_col / 2, text_y, "Página Web")
        c.setFont("Helvetica", 5)
        c.drawCentredString(sep_x + right_col / 2, text_y - 4 * mm, "Escanea el QR")

        # Brand
        c.setFillColor(colors.HexColor("#475569"))
        c.setFont("Helvetica", 4)
        c.drawCentredString(sep_x + right_col / 2, card_y + 2.5 * mm, "QRCard")

    c.save()
    buf.seek(0)
    response = make_response(buf.read())
    response.headers["Content-Type"] = "application/pdf"
    safe_name = biz["name"].replace(" ", "_")
    response.headers["Content-Disposition"] = f'attachment; filename="{safe_name}_tarjeta.pdf"'
    return response

@app.route("/edit/<biz_id>", methods=["GET", "POST"])
def edit(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404

    if request.method == "POST":
        # Logo
        file = request.files.get("logo")
        if file and file.filename and allowed_file(file.filename):
            # borrar logo anterior
            if biz.get("logo"):
                old = os.path.join(UPLOAD_FOLDER, biz["logo"])
                if os.path.exists(old):
                    os.remove(old)
            ext = file.filename.rsplit(".", 1)[1].lower()
            logo_filename = f"{biz_id}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, logo_filename))
            biz["logo"] = logo_filename

        biz["name"]        = request.form.get("name", biz["name"])
        biz["category"]    = request.form.get("category", biz["category"])
        biz["description"] = request.form.get("description", biz.get("description", ""))
        biz["phone"]       = request.form.get("phone", biz["phone"])
        biz["email"]       = request.form.get("email", biz["email"])
        biz["address"]     = request.form.get("address", biz["address"])
        biz["website"]     = request.form.get("website", biz.get("website", ""))
        biz["maps_url"]    = request.form.get("maps_url", biz.get("maps_url", ""))
        biz["instagram"]   = request.form.get("instagram", biz.get("instagram", ""))
        biz["facebook"]    = request.form.get("facebook", biz.get("facebook", ""))
        biz["tiktok"]      = request.form.get("tiktok", biz.get("tiktok", ""))
        print("DEBUG tiktok:", repr(request.form.get("tiktok")))
        print("DEBUG form keys:", list(request.form.keys()))
        businesses[biz_id] = biz
        save_businesses(businesses)
        return redirect(url_for("card", biz_id=biz_id))

    return render_template("edit.html", biz=biz, biz_id=biz_id)

ADMIN_USER = "AdminL"
ADMIN_PASS = "Caacupe2025"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin_logged_in"):
        error = None
        if request.method == "POST":
            u = request.form.get("username", "")
            p = request.form.get("password", "")
            if u == ADMIN_USER and p == ADMIN_PASS:
                session["admin_logged_in"] = True
                return redirect(url_for("admin"))
            error = "Credenciales incorrectas"
        return render_template("admin_login.html", error=error)
    businesses = load_businesses()
    return render_template("admin.html", businesses=businesses)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("index"))


@app.route("/admin/delete/<biz_id>", methods=["POST"])
def delete_business(biz_id):
    businesses = load_businesses()
    biz = businesses.pop(biz_id, None)
    if biz and biz.get("logo"):
        logo_path = os.path.join(UPLOAD_FOLDER, biz["logo"])
        if os.path.exists(logo_path):
            os.remove(logo_path)
    save_businesses(businesses)
    return redirect(url_for("admin"))

@app.route("/products/<biz_id>", methods=["GET", "POST"])
def products(biz_id):
    businesses = load_businesses()
    biz = businesses.get(biz_id)
    if not biz:
        return "Negocio no encontrado", 404

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            product_id = str(uuid.uuid4())[:8]
            img_filename = None
            file = request.files.get("product_img")
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                img_filename = f"prod_{product_id}.{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, img_filename))

            product = {
                "id": product_id,
                "name": request.form.get("name", "").strip(),
                "description": request.form.get("description", "").strip(),
                "price": request.form.get("price", "").strip(),
                "image": img_filename,
            }
            businesses[biz_id].setdefault("products", []).append(product)
            save_businesses(businesses)

        elif action == "delete":
            pid = request.form.get("product_id")
            prods = businesses[biz_id].get("products", [])
            to_del = next((p for p in prods if p["id"] == pid), None)
            if to_del:
                if to_del.get("image"):
                    img_path = os.path.join(UPLOAD_FOLDER, to_del["image"])
                    if os.path.exists(img_path):
                        os.remove(img_path)
                businesses[biz_id]["products"] = [p for p in prods if p["id"] != pid]
                save_businesses(businesses)

        return redirect(url_for("products", biz_id=biz_id))

    return render_template("products.html", biz=biz, biz_id=biz_id)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
