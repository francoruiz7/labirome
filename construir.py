"""Arma el sitio de La Birome a partir de las notas guardadas en la carpeta "notas".

Cada archivo de esa carpeta es una nota. Si se borra un archivo, la nota desaparece del sitio
la próxima vez que se ejecuta este programa. El resultado queda en la carpeta "sitio".

Uso:  python construir.py
"""

import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

import config

AQUI = Path(__file__).parent
SALIDA = AQUI / "sitio"
P = config.RUTA_BASE.rstrip("/")
e = html.escape

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
SERVICIOS = [
    ("Clima", "https://weather.com/es-AR/tiempo/hoy/l/ARBA0009:1:AR"),
    ("Dólar", "https://dolarhoy.com/"),
    ("Subte", "https://www.enelsubte.com/estado/"),
    ("Cripto", "https://coinmarketcap.com/es/"),
    ("Boletín Oficial", "https://www.boletinoficial.gob.ar/"),
    ("Cómo llegar", "https://moovitapp.com/"),
    ("Hora mundial", "https://www.horamundial.com/"),
]
LUPA = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
        'stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/>'
        '<line x1="15.6" y1="15.6" x2="21" y2="21"/></svg>')


# ---------- Utilidades ----------

def slugificar(texto):
    texto = texto.lower().translate(str.maketrans("áéíóúñü", "aeiounu"))
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")


def fecha_larga(iso):
    d = dt.datetime.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def url_nota(nota):
    return f"{P}/notas/{nota['slug']}/"


def url_seccion(nombre):
    return f"{P}/seccion/{slugificar(nombre)}/"


def cargar_notas():
    notas = []
    for ruta in sorted((AQUI / "notas").glob("*.json")):
        try:
            nota = json.loads(ruta.read_text(encoding="utf-8"))
            for campo in ("slug", "titulo", "cuerpo", "seccion", "fecha"):
                if not nota.get(campo):
                    raise ValueError(f"falta el campo {campo}")
            dt.datetime.fromisoformat(nota["fecha"])
        except (ValueError, json.JSONDecodeError) as error:
            print(f"  [se saltea] {ruta.name}: {error}")
            continue
        notas.append(nota)
    notas.sort(key=lambda n: n["fecha"], reverse=True)
    return notas


# ---------- Piezas de página ----------

def foto(nota, perezosa=True):
    img = ""
    imagen = nota.get("imagen") or {}
    if imagen.get("url"):
        carga = ' loading="lazy"' if perezosa else ""
        img = f'<img src="{e(imagen["url"])}" alt=""{carga} onerror="this.remove()">'
    return f'<a class="foto" href="{e(url_nota(nota))}" tabindex="-1" aria-hidden="true">{img}</a>'


def etiqueta(nota):
    return f'<a class="etiqueta" href="{e(url_seccion(nota["seccion"]))}">{e(nota["seccion"])}</a>'


def fecha(nota):
    return f'<time class="fecha" datetime="{e(nota["fecha"])}">{e(fecha_larga(nota["fecha"]))}</time>'


def tarjeta(nota, clase="tarjeta", nivel="h3"):
    return (f'<article class="{clase}">{foto(nota)}<div>{etiqueta(nota)}'
            f'<{nivel}><a href="{e(url_nota(nota))}">{e(nota["titulo"])}</a></{nivel}>{fecha(nota)}</div></article>')


def menu_secciones(actual=None):
    items = ""
    for s in config.SECCIONES:
        clase = ' class="current-cat"' if s == actual else ""
        items += f'<li{clase}><a href="{e(url_seccion(s))}">{e(s)}</a></li>'
    return f"<ul>{items}</ul>"


def identidad():
    return (f'<a class="identidad" href="{P}/"><img src="{P}/estatico/logo.png" alt="{e(config.NOMBRE)}" '
            f'width="800" height="217"></a>')


def formulario_busqueda(valor=""):
    return (f'<form class="form-buscar" role="search" method="get" action="{P}/buscar/">'
            f'<input type="search" name="q" value="{e(valor)}" placeholder="Buscar una noticia" '
            f'aria-label="Buscar una noticia" required>'
            f'<button type="submit" class="boton boton-celeste">Buscar</button></form>')


def pagina(titulo, cuerpo, ruta, ultimas, descripcion=None, imagen=None, seccion_actual=None, version="1"):
    descripcion = descripcion or config.DESCRIPCION
    canonica = config.URL_SITIO.rstrip("/") + ruta
    servicios = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(n)}</a></li>' for n, u in SERVICIOS)

    cinta = ""
    if ultimas:
        # Con pocas notas, los titulares se repiten hasta llenar el ancho de la pantalla.
        titulares = ultimas[:6]
        tramo = [titulares[i % len(titulares)] for i in range(max(6, len(titulares)))]
        enlaces = ""
        for repetida in (False, True):  # el tramo va dos veces para que el recorrido no tenga corte
            for posicion, n in enumerate(tramo):
                oculto = repetida or posicion >= len(titulares)
                extra = ' aria-hidden="true" tabindex="-1"' if oculto else ""
                enlaces += f'<a href="{e(url_nota(n))}"{extra}>{e(n["titulo"])}</a>'
        # La duración depende del largo del texto, para que la velocidad sea siempre la misma.
        segundos = max(24, round(sum(len(n["titulo"]) + 6 for n in tramo) / 9))
        cinta = (f'<div class="cinta sobre-negro" aria-label="Últimas noticias"><div class="cinta-rotulo">Últimas noticias</div>'
                 f'<div class="cinta-pista"><div class="cinta-lista" style="animation-duration:{segundos}s">{enlaces}</div></div></div>')

    robots = "" if config.INDEXABLE else '<meta name="robots" content="noindex, nofollow">\n'
    og_imagen = f'<meta property="og:image" content="{e(imagen)}">\n' if imagen else ""
    return f"""<!DOCTYPE html>
<html lang="es-AR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
{robots}<link rel="canonical" href="{e(canonica)}">
<meta property="og:site_name" content="{e(config.NOMBRE)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<meta property="og:url" content="{e(canonica)}">
{og_imagen}<link rel="icon" href="{P}/estatico/favicon.png">
<link rel="apple-touch-icon" href="{P}/estatico/icono-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Chivo:wght@400;500;700;900&family=Faustina:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{P}/estatico/estilo.css?v={version}">
</head>
<body>
<a class="saltar" href="#contenido">Ir al contenido</a>

<div class="servicios sobre-negro">
  <div class="contenedor">
    <time id="reloj"></time>
    <ul aria-label="Lo que necesitás saber">{servicios}</ul>
  </div>
</div>

<header class="cabecera sobre-negro">
  <div class="contenedor">
    {identidad()}
    <div class="cabecera-acciones">
      <button type="button" class="boton boton-contorno" id="abrir-buscador" aria-expanded="false" aria-controls="buscador">{LUPA}Buscar</button>
    </div>
  </div>
</header>

<div class="buscador sobre-negro" id="buscador" hidden>
  <div class="contenedor">{formulario_busqueda()}</div>
</div>

<nav class="secciones" aria-label="Secciones">
  <div class="contenedor">{menu_secciones(seccion_actual)}</div>
</nav>

{cinta}

<main id="contenido">
{cuerpo}
</main>

<footer class="pie sobre-negro">
  <div class="contenedor">
    <div>{identidad()}</div>
    <div>
      <h2>Secciones</h2>
      {menu_secciones()}
    </div>
    <div>
      <h2>Sobre {e(config.NOMBRE)}</h2>
      <p>{e(config.SOBRE)}</p>
    </div>
  </div>
  <p class="legal">© {dt.date.today().year} {e(config.NOMBRE)}</p>
</footer>

<script>window.LB = {{ base: "{P}" }};</script>
<script src="{P}/estatico/main.js?v={version}"></script>
</body>
</html>
"""


# ---------- Páginas ----------

def portada(notas):
    if not notas:
        return '<section class="listado"><div class="contenedor"><p class="sin-resultados">Todavía no hay notas publicadas.</p></div></section>'

    principal, secundarias, resto = notas[0], notas[1:5], notas[5:]
    usadas = [n["slug"] for n in notas[:5]]

    # Tendencias: los temas más cubiertos por los medios en las últimas 48 horas.
    limite = dt.datetime.fromisoformat(principal["fecha"]) - dt.timedelta(hours=48)
    recientes = [n for n in notas[1:] if dt.datetime.fromisoformat(n["fecha"]) >= limite]
    recientes.sort(key=lambda n: (n.get("importancia", 0), len(n.get("fuentes", []))), reverse=True)
    tendencias = (recientes + [n for n in notas[1:] if n not in recientes])[:5]

    bajada = f'<p class="bajada">{e(principal.get("bajada", ""))}</p>' if principal.get("bajada") else ""
    filtros = f'<a href="{P}/" data-seccion="" aria-current="true">Todas</a>' + "".join(
        f'<a href="{e(url_seccion(s))}" data-seccion="{e(s)}" aria-current="false">{e(s)}</a>'
        for s in config.SECCIONES if any(n["seccion"] == s for n in resto)
    )
    mas = ('<div class="mas"><a class="boton" id="cargar-mas" href="#">Cargar más noticias</a></div>'
           if len(resto) > 9 else "")
    bloque_tendencias = ""
    if tendencias:
        items = "".join(f'<li><a href="{e(url_nota(n))}">{e(n["titulo"])}</a></li>' for n in tendencias)
        bloque_tendencias = f'<div class="tendencias sobre-negro"><h2>Tendencias</h2><ol>{items}</ol></div>'

    return f"""
<section class="portada">
  <div class="contenedor">
    <article class="principal">
      {foto(principal, perezosa=False)}
      {etiqueta(principal)}
      <h1><a href="{e(url_nota(principal))}">{e(principal["titulo"])}</a></h1>
      {bajada}
      {fecha(principal)}
    </article>
    <div class="secundarias">{"".join(tarjeta(n, "secundaria", "h2") for n in secundarias)}</div>
  </div>
</section>

<section class="cuerpo">
  <div class="contenedor">
    <div>
      <h2 class="titulo-seccion">Más noticias</h2>
      <div class="filtros" id="filtros" role="group" aria-label="Filtrar por sección">{filtros}</div>
      <div class="grilla" id="grilla" aria-live="polite" data-excluir="{e(",".join(usadas))}" data-tanda="9">{"".join(tarjeta(n) for n in resto[:9])}</div>
      {mas}
    </div>
    <aside class="lateral">
      {bloque_tendencias}
      <div class="newsletter">
        <h2>Suscribite a nuestro newsletter</h2>
        <p>Las noticias del día en tu correo.</p>
        <form id="form-newsletter">
          <label for="correo">Tu correo electrónico</label>
          <input type="email" id="correo" autocomplete="email" required>
          <button type="submit" class="boton">Suscribirme</button>
          <p class="aviso" id="aviso-newsletter" hidden role="status">El newsletter arranca pronto. Gracias por el interés.</p>
        </form>
      </div>
    </aside>
  </div>
</section>
"""


def pagina_nota(nota, notas):
    imagen = nota.get("imagen") or {}
    figura = ""
    if imagen.get("url"):
        credito = e(imagen.get("credito", ""))
        if imagen.get("enlace"):
            credito = f'<a href="{e(imagen["enlace"])}" target="_blank" rel="noopener">{credito}</a>'
        licencia = f' ({e(imagen["licencia"])})' if imagen.get("licencia") else ""
        figura = (f'<figure class="nota-foto"><img src="{e(imagen["url"])}" alt="" onerror="this.parentNode.remove()">'
                  f'<figcaption>Foto de archivo: {credito}{licencia}</figcaption></figure>')

    bajada = f'<p class="bajada">{e(nota["bajada"])}</p>' if nota.get("bajada") else ""
    cuerpo = "".join(f"<p>{e(p)}</p>\n" for p in nota["cuerpo"])
    fuentes = "".join(
        f'<li><a href="{e(f["link"])}" target="_blank" rel="nofollow noopener">{e(f["medio"])}: {e(f["titulo"])}</a></li>'
        for f in nota.get("fuentes", [])
    )
    enlace = config.URL_SITIO.rstrip("/") + url_nota(nota)[len(P):]
    t, u = quote(nota["titulo"]), quote(enlace, safe="")
    relacionadas = [n for n in notas if n["seccion"] == nota["seccion"] and n["slug"] != nota["slug"]][:3]
    bloque_rel = ""
    if relacionadas:
        bloque_rel = (f'<section class="relacionadas"><h2 class="titulo-seccion">Más de {e(nota["seccion"])}</h2>'
                      f'<div class="grilla">{"".join(tarjeta(n) for n in relacionadas)}</div></section>')

    return f"""
<div class="nota">
  <div class="contenedor">
    <article class="nota-columna">
      <header class="nota-cabeza">
        {etiqueta(nota)}
        <h1>{e(nota["titulo"])}</h1>
        {bajada}
        {fecha(nota)}
      </header>
      {figura}
      <div class="nota-texto">
{cuerpo}      </div>
      <div class="fuentes"><h2>Fuentes</h2><ul>{fuentes}</ul><p class="aviso-ia">{e(config.AVISO_IA)}</p></div>
      <div class="compartir">
        <span>Compartir</span>
        <a href="https://wa.me/?text={t}%20{u}" target="_blank" rel="noopener">WhatsApp</a>
        <a href="https://twitter.com/intent/tweet?text={t}&amp;url={u}" target="_blank" rel="noopener">X</a>
        <a href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Facebook</a>
      </div>
    </article>
    {bloque_rel}
  </div>
</div>
"""


def pagina_listado(titulo, notas, vacio):
    contenido = (f'<div class="grilla grilla-ancha">{"".join(tarjeta(n, "tarjeta", "h2") for n in notas)}</div>'
                 if notas else f'<p class="sin-resultados">{e(vacio)}</p>')
    return (f'<section class="listado"><div class="contenedor"><header class="listado-cabeza"><h1>{e(titulo)}</h1></header>'
            f'{contenido}</div></section>')


def pagina_buscar():
    return (f'<section class="listado"><div class="contenedor"><header class="listado-cabeza">'
            f'<h1 id="titulo-busqueda">Buscar</h1></header>{formulario_busqueda()}'
            f'<div class="grilla grilla-ancha" id="resultados" style="margin-top:2rem" aria-live="polite"></div></div></section>')


def pagina_404():
    return (f'<section class="listado"><div class="contenedor"><header class="listado-cabeza"><h1>Esta página no existe</h1>'
            f'<p>Puede que la dirección esté mal escrita o que la nota ya no esté publicada. Buscala por título o volvé a la portada.</p>'
            f'</header>{formulario_busqueda()}<p style="margin-top:1.5rem"><a class="boton" href="{P}/">Ir a la portada</a></p>'
            f'</div></section>')


# ---------- Armado ----------

def escribir(ruta, contenido):
    destino = SALIDA / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")


def main():
    notas = cargar_notas()
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    shutil.copytree(AQUI / "estatico", SALIDA / "estatico")
    version = dt.datetime.now().strftime("%Y%m%d%H%M")

    def armar(titulo, cuerpo, ruta, **extra):
        return pagina(titulo, cuerpo, ruta, notas, version=version, **extra)

    escribir("index.html", armar(f"{config.NOMBRE} | Noticias", portada(notas), "/"))

    for nota in notas:
        escribir(f"notas/{nota['slug']}/index.html", armar(
            f"{nota['titulo']} | {config.NOMBRE}", pagina_nota(nota, notas), f"/notas/{nota['slug']}/",
            descripcion=nota.get("bajada") or None, imagen=(nota.get("imagen") or {}).get("url"),
            seccion_actual=nota["seccion"],
        ))

    for seccion in config.SECCIONES:
        de_seccion = [n for n in notas if n["seccion"] == seccion][:60]
        escribir(f"seccion/{slugificar(seccion)}/index.html", armar(
            f"{seccion} | {config.NOMBRE}", pagina_listado(seccion, de_seccion, "Todavía no hay notas en esta sección."),
            f"/seccion/{slugificar(seccion)}/", seccion_actual=seccion,
        ))

    escribir("buscar/index.html", armar(f"Buscar | {config.NOMBRE}", pagina_buscar(), "/buscar/"))
    escribir("404.html", armar(f"Página no encontrada | {config.NOMBRE}", pagina_404(), "/404.html"))

    # Índice que usa el sitio para filtrar, cargar más y buscar.
    indice = [{
        "g": n["slug"], "t": n["titulo"], "b": n.get("bajada", ""), "u": url_nota(n), "s": n["seccion"],
        "su": url_seccion(n["seccion"]), "f": fecha_larga(n["fecha"]), "d": n["fecha"],
        "i": (n.get("imagen") or {}).get("url", ""),
    } for n in notas[:600]]
    escribir("indice.json", json.dumps(indice, ensure_ascii=False))

    base = config.URL_SITIO.rstrip("/")
    if config.INDEXABLE:
        urls = [f"{base}/"] + [base + url_nota(n)[len(P):] for n in notas] + [base + url_seccion(s)[len(P):] for s in config.SECCIONES]
        escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                 + "".join(f"<url><loc>{e(u)}</loc></url>\n" for u in urls) + "</urlset>\n")
        escribir("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    else:
        escribir("robots.txt", "User-agent: *\nDisallow: /\n")

    if config.DOMINIO and not P:
        escribir("CNAME", config.DOMINIO + "\n")
    escribir(".nojekyll", "")
    print(f"Sitio armado en {SALIDA} con {len(notas)} notas.")


if __name__ == "__main__":
    main()
