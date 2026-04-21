import re

NAV_STYLE = 'background:linear-gradient(135deg,#0284c7,#0ea5e9);padding:0 72px;height:100px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 4px 20px rgba(2,132,199,0.3);'
BRAND = '<a href="/" style="display:flex;align-items:center;gap:16px;text-decoration:none;"><img src="/static/logo.jpeg" alt="Zuppon" style="height:62px;object-fit:contain;"><span style="font-size:30px;font-weight:800;color:#fff;letter-spacing:-0.5px;">Zuppon</span></a>'
LINK_STYLE = 'color:rgba(255,255,255,0.85);font-size:15px;font-weight:500;padding:10px 18px;border-radius:8px;text-decoration:none;'
BTN_STYLE = 'background:#fff;color:#0ea5e9;padding:10px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;'

def nav(links):
    return f'<nav style="{NAV_STYLE}">\n    {BRAND}\n    <div style="display:flex;align-items:center;gap:6px;">\n      {links}\n    </div>\n  </nav>'

fixes = {
    'templates/edit.html': {
        'old': re.compile(r'<nav class="nav">.*?</nav>', re.DOTALL),
        'new': nav(f'<a href="/negocios" style="{LINK_STYLE}">Directorio</a>\n      <a href="{{{{ url_for(\'card\', biz_id=biz_id) }}}}" style="{BTN_STYLE}">← Volver a mi tarjeta</a>')
    },
    'templates/products.html': {
        'old': re.compile(r'<nav style="background:linear-gradient.*?</nav>', re.DOTALL),
        'new': nav(f'<a href="/negocios" style="{LINK_STYLE}">Directorio</a>\n      <a href="{{{{ url_for(\'card\', biz_id=biz_id) }}}}" style="{LINK_STYLE}">← Mi tarjeta</a>\n      <a href="/qrcard" style="{BTN_STYLE}">+ Nueva tarjeta</a>')
    },
    'templates/admin.html': {
        'old': re.compile(r'<nav style="background:linear-gradient.*?</nav>', re.DOTALL),
        'new': nav(f'<a href="/negocios" style="{LINK_STYLE}">Directorio</a>\n      <a href="/" style="{LINK_STYLE}">← Inicio</a>\n      <a href="/admin/logout" style="{BTN_STYLE}">Cerrar sesión</a>')
    },
    'templates/admin_login.html': {
        'old': re.compile(r'<div class="login-logo">.*?</div>', re.DOTALL),
        'new': '<div class="login-logo"><img src="/static/logo.jpeg" alt="Zuppon" style="height:48px;object-fit:contain;"><span>Zuppon</span></div>'
    },
}

for path, fix in fixes.items():
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        new_content = fix['old'].sub(fix['new'], content, count=1)
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated: {path}')
        else:
            print(f'No match: {path}')
    except Exception as e:
        print(f'Error {path}: {e}')

# edit.html CSS fix - replace dark nav CSS with transparent
for path in ['templates/edit.html']:
    with open(path, encoding='utf-8') as f:
        c = f.read()
    c = c.replace(
        '.nav { background: rgba(15,17,23,0.95); border-bottom: 1px solid rgba(255,255,255,0.06); padding: 0 2rem; height: 60px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 10; }',
        '.nav { display: none; }'
    )
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print(f'CSS fixed: {path}')

print('Done')
