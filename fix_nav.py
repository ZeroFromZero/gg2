import glob, re

# El nav inline que usan edit.html, products.html, admin.html, profile.html
# Los reemplazamos por el estilo consistente de negocios.html

# Patron: nav con style inline que empieza con background:linear-gradient
INLINE_NAV_PATTERN = re.compile(
    r'<nav style="background:linear-gradient[^"]*"[^>]*>.*?</nav>',
    re.DOTALL
)

def make_nav(links_html):
    return f'''<nav style="background:linear-gradient(135deg,#0284c7,#0ea5e9);padding:0 72px;height:100px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 4px 20px rgba(2,132,199,0.3);">
    <a href="/" style="display:flex;align-items:center;gap:16px;text-decoration:none;">
      <img src="/static/logo.jpeg" alt="Zuppon" style="height:62px;object-fit:contain;">
      <span style="font-size:30px;font-weight:800;color:#fff;letter-spacing:-0.5px;">Zuppon</span>
    </a>
    <div style="display:flex;align-items:center;gap:6px;">
      {links_html}
    </div>
  </nav>'''

# Links por template
nav_links = {
    'templates/edit.html': '<a href="/zuppon" style="color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;">Tiendas</a>\n      <a href="{{ url_for(\'card\', biz_id=biz_id) }}" style="background:#fff;color:#0ea5e9;padding:10px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">← Volver a mi tarjeta</a>',
    'templates/products.html': '<a href="/negocios" style="color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;">Directorio</a>\n      <a href="{{ url_for(\'card\', biz_id=biz_id) }}" style="color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;">← Mi tarjeta</a>\n      <a href="/qrcard" style="background:#fff;color:#0ea5e9;padding:10px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">+ Nueva tarjeta</a>',
    'templates/admin.html': '<a href="/negocios" style="color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;">Directorio</a>\n      <a href="/" style="color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;">← Inicio</a>\n      <a href="/admin/logout" style="background:#fff;color:#0ea5e9;padding:10px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">Cerrar sesión</a>',
    'templates/profile.html': '<a href="/negocios" style="color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;">Directorio</a>\n      <a href="/qrcard" style="background:#fff;color:#0ea5e9;padding:10px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">Crear tarjeta gratis</a>',
    'templates/public_products.html': '<a href="/negocios" style="color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;">Directorio</a>\n      <a href="{{ url_for(\'profile\', biz_id=biz_id) }}" style="background:#fff;color:#0ea5e9;padding:10px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;">← Ver perfil</a>',
}

for path, links in nav_links.items():
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        new_nav = make_nav(links)
        new_content = INLINE_NAV_PATTERN.sub(new_nav, content, count=1)
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated: {path}')
        else:
            print(f'No match: {path}')
    except Exception as e:
        print(f'Error {path}: {e}')

print('Done')
