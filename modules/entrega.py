"""Centro de Entrega al Agricultor: WhatsApp, correo, hoja para imprimir y PDF.
Todo el texto proviene de lenguaje_sencillo.guia() (sin tecnicismos)."""
import html
import re
from datetime import date
from urllib.parse import quote

from utils.validaciones import telefono_whatsapp

NUM = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]


def _ha(x: float) -> str:
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".").rstrip("0").rstrip(",")


def _num(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _tec(t) -> dict:
    """Datos del técnico responsable, a partir del objeto Tecnico (o de un texto con su nombre)."""
    if not t:
        return {"nombre": "", "cargo": "", "institucion": "", "telefono": "", "correo": "", "lugar": "", "firma": "", "contacto": ""}
    if isinstance(t, str):
        return {"nombre": t, "cargo": "", "institucion": "", "telefono": "", "correo": "", "lugar": "", "firma": t, "contacto": ""}
    return {"nombre": t.nombre, "cargo": t.cargo or "", "institucion": t.institucion or "", "telefono": t.telefono or "",
            "correo": t.correo or "", "lugar": t.canton_parroquia or "", "firma": t.firma, "contacto": t.contacto}


def _paso_txt(p: dict) -> str:
    return (f"{p['etapa']}: " if p.get("etapa") else "") + p.get("nombre_completo", p["cultivo"])


# ------------------------------------------------------------------ WhatsApp
def mensaje_whatsapp(g: dict, agricultor, parcela, tecnico=None) -> str:
    t = _tec(tecnico)
    l = ["🌱 *Tu plan de siembra" + (" para 12 meses*" if g.get("anual") else "*"),
         f"👤 {agricultor.nombre}" + (f" · {agricultor.comunidad}" if agricultor.comunidad else ""),
         f"🌾 {parcela.nombre} ({_ha(parcela.superficie)} ha)", "", f"*{g.get('titulo_pasos', 'Qué sembrar, en orden')}:*"]
    for p in g["pasos"]:
        etapa = f"_{p['etapa'].split(' (')[0]}_ · " if p.get("etapa") else ""
        l.append(f"{NUM[p['n'] - 1]} {etapa}{p['emoji']} *{p.get('nombre_completo', p['cultivo'])}*: siembra en {p['siembra']}, cosecha en {p['cosecha']} ({p['cantidad']})")
    if g["por_que"]:
        l += ["", f"✅ *Por qué:* {g['por_que'][0]}"]
    l += ["", f"💰 *Ahorro:* {g['ahorro'][0]}"]
    if g.get("vs_testigo"):
        l += ["", f"📈 *Frente a repetir lo mismo:* {g['vs_testigo']['resumen_sencillo']}"]
    l += ["", f"⚠️ *Cuidado:* {g['clima'][0]}"]
    if g.get("respaldo_nasa"):
        l += ["", f"🛰️ *Respaldo satelital:* {g['respaldo_nasa'][0]}"]
    if g.get("validar_campo"):
        l += ["", f"🔎 *Revisar en campo:* {g['validar_campo'][0]}"]
    if t["nombre"]:
        l += ["", f"👨‍🌾 Tu técnico: {t['firma']}"] + ([f"📞 {t['contacto']}"] if t["contacto"] else [])
    return "\n".join(l)


def url_whatsapp(telefono: str | None, texto: str) -> str:
    """wa.me con el número convertido (09XXXXXXXX -> 5939XXXXXXXX). Sin número, WhatsApp pide elegir el contacto."""
    num = telefono_whatsapp(telefono)
    return f"https://wa.me/{num or ''}?text={quote(texto)}"


# ------------------------------------------------------------------ correo
def texto_plano(g: dict, agricultor, parcela, tecnico=None) -> str:
    t = _tec(tecnico)
    l = [f"Hola {agricultor.nombre.split()[0]},", "", f"Este es el plan de siembra para tu terreno «{parcela.nombre}» ({_ha(parcela.superficie)} ha)"
         + (f", {g['periodo']}." if g.get("periodo") else "."), "", g.get("titulo_pasos", "Qué sembrar, en orden").upper() + ":"]
    for p in g["pasos"]:
        l.append(f"{p['n']}. {_paso_txt(p)}: siembra en {p['siembra']}, cosecha en {p['cosecha']}. Cosecha esperada: {p['cantidad']}.")
        l.append(f"   {p['abono']} {p['consejo']}")
    l += ["", "POR QUÉ TE CONVIENE:"] + [f"- {x}" for x in g["por_que"]]
    l += ["", "AHORRO DE AGUA Y DINERO:"] + [f"- {x}" for x in g["ahorro"]]
    if g.get("vs_testigo"):
        l += ["", "FRENTE AL MANEJO ACTUAL (SI REPITES EL MISMO CULTIVO):"] + [f"- {g['vs_testigo']['resumen_sencillo']}"]
    l += ["", "CUIDADOS DEL CLIMA:"] + [f"- {x}" for x in g["clima"]]
    if g.get("respaldo_nasa"):
        l += ["", "RESPALDO SATELITAL NASA:"] + [f"- {x}" for x in g["respaldo_nasa"]]
    if g.get("validar_campo"):
        l += ["", "LIMITACIONES Y QUÉ VALIDAR EN CAMPO:"] + [f"- {x}" for x in g["validar_campo"]]
    l += ["", "Este plan es una guía. Ante cualquier duda, consulta con tu técnico.", "", "Saludos,", t["nombre"] or "Tu técnico agropecuario"]
    l += [x for x in (", ".join(y for y in (t["cargo"], t["institucion"]) if y), t["lugar"], t["contacto"]) if x]
    return "\n".join(l)


def url_correo(correo: str | None, parcela, cuerpo: str) -> str:
    return f"mailto:{correo or ''}?subject={quote('Tu plan de siembra - ' + parcela.nombre)}&body={quote(cuerpo)}"


# ------------------------------------------------------------------ hoja para imprimir (HTML A4)
def html_cartilla(g: dict, agricultor, parcela, tecnico=None, imprimir: bool = True) -> str:
    e = html.escape
    t = _tec(tecnico)
    def paso_html(p):
        nombre = p.get("nombre_completo", p["cultivo"])
        etapa = f"<p class='et'>{e(p['etapa'])}</p>" if p.get("etapa") else ""
        alertas = "".join(f"<p class='al'>⚠️ {e(a)}</p>" for a in p["alertas"])
        return (f"<div class='paso' style='border-color:{p['color']}'><div class='n' style='background:{p['color']}'>{p['n']}</div><div>"
                f"{etapa}<h3>{p['emoji']} {e(nombre)}</h3>"
                f"<p><b>Siembra:</b> {p['siembra']} &nbsp; <b>Cosecha:</b> {p['cosecha']} &nbsp; <b>Cosecha esperada:</b> {p['cantidad']}</p>"
                f"<p>{e(p['abono'])} {e(p['consejo'])}</p>{alertas}</div></div>")
    pasos = "".join(paso_html(p) for p in g["pasos"])
    luces = "".join(f"<span>{s['luz']} <b>{s['titulo']}:</b> {s['texto']}</span>" for s in g["semaforos"])
    lista = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    vs_html = (f"<div class='vs'><b>Frente a repetir el mismo cultivo:</b> {e(g['vs_testigo']['resumen_sencillo'])}</div>"
               if g.get("vs_testigo") else "")
    resp_html = f"<h2>5. Respaldo satelital NASA</h2><ul>{lista(g['respaldo_nasa'][:3])}</ul>" if g.get("respaldo_nasa") else ""
    campo_html = f"<h2>6. Limitaciones y qué validar en campo</h2><ul>{lista(g['validar_campo'][:3])}</ul>" if g.get("validar_campo") else ""
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Plan de siembra - {e(agricultor.nombre)}</title>
<style>@page{{size:A4;margin:10mm}}body{{font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#1f2a1f;margin:0}}
h1{{font-size:22px;margin:0;color:#1f3d26}}h2{{font-size:15px;margin:10px 0 4px;color:#2f6b3a;border-bottom:2px solid #2f6b3a}}
h3{{margin:0 0 2px;font-size:16px}}p{{margin:2px 0}}.cab{{display:flex;justify-content:space-between;border-bottom:3px solid #2f6b3a;padding-bottom:6px}}
.paso{{display:flex;gap:10px;border-left:6px solid;padding:5px 8px;margin:5px 0;background:#f7f5ef;border-radius:6px}}
.n{{min-width:28px;height:28px;border-radius:50%;color:#fff;font-weight:bold;font-size:16px;display:flex;align-items:center;justify-content:center}}
.al{{color:#8a4b12}}.luces{{display:flex;flex-wrap:wrap;gap:6px 14px;margin:6px 0;font-size:12.5px}}ul{{margin:2px 0;padding-left:18px}}
.vs{{background:#ecfdf5;border:1px solid #a7f3d0;border-radius:6px;padding:6px 10px;margin:6px 0;color:#065f46;font-size:12.5px}}
.doscol{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.firmas{{display:flex;justify-content:space-around;margin-top:26px}}.firmas div{{border-top:1px solid #333;width:40%;text-align:center;padding-top:4px}}
.pie{{font-size:10.5px;color:#666;margin-top:8px;text-align:center}}.et{{font-size:11px;font-weight:bold;color:#2f6b3a;text-transform:uppercase;letter-spacing:.4px}}
.tec{{font-size:11.5px;color:#444;margin-top:2px}}h3 small{{font-weight:normal;color:#555;font-size:12px}}
@media screen{{body{{max-width:800px;margin:20px auto}}}}</style></head><body>
<div class="cab"><div><h1>🌱 Mi plan de siembra{' – 12 meses' if g.get('anual') else ''}</h1><p><b>{e(agricultor.nombre)}</b>{' · ' + e(agricultor.comunidad) if agricultor.comunidad else ''}
 · {e(parcela.nombre)} ({_ha(parcela.superficie)} ha) {('· ' + e(g['periodo'])) if g.get('periodo') else ''}</p>
 {f'<p class="tec">Técnico responsable: <b>{e(t["firma"])}</b>' + (f' · {e(t["contacto"])}' if t["contacto"] else '') + '</p>' if t["nombre"] else ''}</div>
 <div style="text-align:right">Fecha: {date.today():%d/%m/%Y}<br>AgroCycle</div></div>
<div class="luces">{luces}</div>
{vs_html}
<h2>1. {e(g.get('titulo_pasos', 'Qué sembrar, en orden'))}</h2>{pasos}
<div class="doscol"><div><h2>2. Por qué te conviene</h2><ul>{lista(g['por_que'])}</ul></div>
<div><h2>3. Ahorro de agua y dinero</h2><ul>{lista(g['ahorro'])}</ul></div></div>
<h2>4. Cuidados del clima</h2><ul>{lista(g['clima'])}</ul>
<div class="doscol"><div>{resp_html}</div><div>{campo_html}</div></div>
<div class="firmas"><div>{e(t['nombre']) if t['nombre'] else 'Firma del técnico'}<br><small>{e(', '.join(x for x in (t['cargo'], t['institucion']) if x))}</small></div>
<div>{e(agricultor.nombre)}<br><small>Agricultor</small></div></div>
<p class="pie">Plan orientativo hecho con datos del clima de la NASA y de tu terreno. No garantiza cosechas ni precios. Consulta con tu técnico.</p>
{'<script>window.onload=()=>setTimeout(()=>window.print(),400)</script>' if imprimir else ''}</body></html>"""


# ------------------------------------------------------------------ PDF (fpdf2, 1 página A4)
def _latin(t: str) -> str:
    """Las fuentes base del PDF solo admiten caracteres latinos: se quitan emojis y símbolos."""
    t = t.replace("→", "-").replace("–", "-").replace("—", "-").replace("≈", "aprox.").replace("³", "3").replace("²", "2")
    return re.sub(r"[^\x20-\x7e\xa0-\xff\n]", "", t).replace("  ", " ").strip()


def _rgb(hexcolor: str) -> tuple[int, int, int]:
    h = hexcolor.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else (47, 107, 58)


LUZ_RGB = {"🟢": (46, 160, 67), "🟡": (230, 180, 30), "🔴": (200, 60, 50)}


def pdf_cartilla(g: dict, agricultor, parcela, tecnico=None) -> bytes:
    from fpdf import FPDF  # pip install fpdf2 (solo hace falta para el PDF)

    tec = _tec(tecnico)
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_margins(14, 10, 14)
    W = 182
    verde = (47, 107, 58)
    pdf.set_fill_color(*verde)
    pdf.rect(0, 0, 210, 29 if tec["nombre"] else 24, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(14, 5)
    pdf.set_font("Helvetica", "B", 19)
    pdf.cell(120, 8, "Mi plan de siembra" + (" - 12 meses" if g.get("anual") else ""))
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(62, 8, f"Fecha: {date.today():%d/%m/%Y}", align="R")
    pdf.set_xy(14, 13.5)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.cell(W, 6.5, _latin(f"{agricultor.nombre}" + (f" - {agricultor.comunidad}" if agricultor.comunidad else "") +
                            f"  |  {parcela.nombre} ({_ha(parcela.superficie)} ha)" + (f"  |  {g['periodo']}" if g.get("periodo") else "")))
    if tec["nombre"]:
        pdf.set_xy(14, 20.5)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(W, 5.5, _latin(f"Técnico responsable: {tec['firma']}" + (f"  |  {tec['contacto']}" if tec["contacto"] else "")))
    pdf.set_text_color(31, 42, 31)
    y = 32 if tec["nombre"] else 27

    # semáforos
    x = 14
    pdf.set_font("Helvetica", "", 8.2)
    for s in g["semaforos"]:
        pdf.set_fill_color(*LUZ_RGB[s["luz"]])
        pdf.ellipse(x, y + 1, 3.2, 3.2, "F")
        txt = _latin(f"{s['titulo']}: {s['texto']}")
        pdf.set_xy(x + 4.2, y)
        pdf.cell(pdf.get_string_width(txt) + 2, 5, txt)
        x += pdf.get_string_width(txt) + 8
        if x > 170:
            x, y = 14, y + 5.5
    y += 7

    if g.get("vs_testigo"):
        pdf.set_fill_color(236, 253, 245)
        pdf.rect(14, y, W, 6.5, "F")
        pdf.set_xy(16, y + 1)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(21, 128, 61)
        pdf.cell(W - 4, 4.5, _latin("Frente a repetir lo mismo: " + g["vs_testigo"]["resumen_sencillo"]))
        pdf.set_text_color(31, 42, 31)
        y += 8.5

    def titulo(t, yy):
        pdf.set_xy(14, yy)
        pdf.set_font("Helvetica", "B", 11.5)
        pdf.set_text_color(*verde)
        pdf.cell(W, 5.8, _latin(t))
        pdf.set_draw_color(*verde)
        pdf.line(14, yy + 5.8, 196, yy + 5.8)
        pdf.set_text_color(31, 42, 31)
        return yy + 7.2

    compacto = len(g["pasos"]) > 3
    y = titulo("1. " + g.get("titulo_pasos", "Qué sembrar, en orden"), y)
    for p in g["pasos"]:
        col = _rgb(p["color"])
        pdf.set_fill_color(247, 245, 239)
        alto = (20 if compacto else 22.5) + 4.0 * len(p["alertas"])
        pdf.rect(14, y, W, alto, "F")
        pdf.set_fill_color(*col)
        pdf.rect(14, y, 2.5, alto, "F")
        pdf.ellipse(18.5, y + 2.2, 8, 8, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11.5)
        pdf.set_xy(18.5, y + 2.8)
        pdf.cell(8, 6.5, str(p["n"]), align="C")
        pdf.set_text_color(31, 42, 31)
        pdf.set_xy(29.5, y + 1.2)
        pdf.set_font("Helvetica", "B", 11.5)
        nombre = p.get("nombre_completo", p["cultivo"])
        if p.get("etapa"):
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*verde)
            pdf.cell(164, 3, _latin(p["etapa"].upper()), align="R")
            pdf.set_xy(29.5, y + 1.2)
            pdf.set_text_color(31, 42, 31)
            pdf.set_font("Helvetica", "B", 11)
        pdf.cell(110, 5.5, _latin(nombre))
        pdf.set_xy(29.5, y + 6.4)
        pdf.set_font("Helvetica", "", 9.2)
        pdf.cell(164, 4.4, _latin(f"Siembra: {p['siembra']}    Cosecha: {p['cosecha']}    Cosecha esperada: {p['cantidad']}"))
        pdf.set_xy(29.5, y + 11.2)
        pdf.set_font("Helvetica", "", 8.3)
        pdf.multi_cell(164, 3.8, _latin(f"{p['abono']} {p['consejo']}"), align="L")
        pdf.set_text_color(138, 75, 18)
        for a in p["alertas"]:
            pdf.set_x(29.5)
            pdf.cell(164, 4.0, _latin("! " + a))
            pdf.ln(4.0)
        pdf.set_text_color(31, 42, 31)
        y += alto + 2.0

    secciones = [
        ("2. Por qué te conviene", g["por_que"][:2]),
        ("3. Ahorro de agua y dinero", g["ahorro"][:2]),
        ("4. Cuidados del clima", g["clima"][:2]),
    ]
    if g.get("respaldo_nasa"):
        secciones.append(("5. Respaldo satelital NASA", g["respaldo_nasa"][:2]))
    if g.get("validar_campo"):
        secciones.append(("6. Limitaciones y qué validar en campo", g["validar_campo"][:2]))

    for t_sec, xs in secciones:
        if y > 250:
            break
        y = titulo(t_sec, y + 0.5)
        pdf.set_font("Helvetica", "", 8.6)
        for item in xs:
            if y > 256:
                break
            pdf.set_xy(15.5, y)
            pdf.multi_cell(179, 4.0, _latin("- " + item), align="L")
            y = pdf.get_y() + 0.4

    # firmas
    y = min(max(y + 8, 260), 276)
    pdf.set_draw_color(60, 60, 60)
    pdf.line(24, y, 94, y)
    pdf.line(116, y, 186, y)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(24, y + 1)
    pdf.cell(70, 4.5, _latin(tec["nombre"]) if tec["nombre"] else "Firma del técnico", align="C")
    if tec["nombre"]:
        pdf.set_xy(24, y + 5.2)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(70, 4, _latin(", ".join(x for x in (tec["cargo"], tec["institucion"]) if x)), align="C")
        pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(116, y + 1)
    pdf.cell(70, 4.5, _latin(agricultor.nombre), align="C")
    pdf.set_xy(116, y + 5.2)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.cell(70, 4, "Agricultor", align="C")
    pdf.set_xy(14, 289)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(W, 4, "Plan orientativo hecho con datos del clima de la NASA y de tu terreno (AgroCycle). No garantiza cosechas ni precios.", align="C")
    return bytes(pdf.output())
