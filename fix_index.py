with open('templates/index.html', encoding='utf-8') as f:
    content = f.read()

form_start = content.find('  <!-- FORM -->')
footer_start = content.find('  <!-- FOOTER -->')

cta = """  <!-- CTA FINAL -->
  <section style="background:#060609;padding:5rem 2rem;text-align:center;border-top:1px solid rgba(255,255,255,0.06);">
    <div style="max-width:560px;margin:0 auto;">
      <div style="font-size:2.2rem;margin-bottom:1rem;">🚀</div>
      <h2 style="font-size:1.8rem;font-weight:900;color:#fff;letter-spacing:-0.03em;margin-bottom:0.75rem;">¿Listo para vender más?</h2>
      <p style="font-size:1rem;color:rgba(255,255,255,0.4);line-height:1.7;margin-bottom:2rem;">Crea tu tarjeta con catálogo digital en 2 minutos. Gratis, sin registro.</p>
      <a href="/qrcard" style="display:inline-flex;align-items:center;gap:0.6rem;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;padding:1rem 2.5rem;border-radius:14px;font-size:1rem;font-weight:700;text-decoration:none;box-shadow:0 4px 20px rgba(99,102,241,0.4);">
        Crear mi catálogo gratis →
      </a>
      <p style="font-size:0.78rem;color:rgba(255,255,255,0.2);margin-top:1rem;">🔒 Gratis · Sin registro · Sin tarjeta de crédito</p>
    </div>
  </section>

"""

new_content = content[:form_start] + cta + content[footer_start:]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Done')
