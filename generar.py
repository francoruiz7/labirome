"""Redacción automática de La Birome.

Lee titulares de varios medios, detecta los temas del momento, redacta notas propias citando
las fuentes, las revisa, les busca una foto con licencia libre y las guarda en la carpeta "notas".
Después, construir.py arma el sitio con lo que haya en esa carpeta.

Uso:  python generar.py
"""

import datetime as dt
import html
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import feedparser
import requests
import trafilatura
from openai import OpenAI

import config

AQUI = Path(__file__).parent
CARPETA_NOTAS = AQUI / "notas"
CARPETA_RETENIDAS = AQUI / "retenidas"
ARCHIVO_VISTOS = AQUI / "vistos.json"
ARGENTINA = dt.timezone(dt.timedelta(hours=-3))
NAVEGADOR = {"User-Agent": "Mozilla/5.0 (lector de titulares de La Birome)"}
IDENTIFICACION = {"User-Agent": f"LaBirome/1.0 ({config.URL_SITIO})"}


# ---------- Configuración y cliente ----------

def cargar_env():
    """Lee el archivo .env (CLAVE=valor) cuando se ejecuta en una compu. En GitHub no hace falta."""
    ruta = AQUI / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            if valor.strip():
                os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def elegir_modelo(cliente):
    forzado = os.environ.get("MODELO", "").strip()
    if forzado:
        return forzado
    disponibles = {m.id for m in cliente.models.list()}
    for nombre in config.MODELOS_PREFERIDOS:
        if nombre in disponibles:
            return nombre
    sys.exit("No encontré ninguno de los modelos preferidos en la cuenta. Definí MODELO con el nombre de un modelo de chat.")


def pedir_json(cliente, modelo, sistema, usuario):
    """Llama al modelo pidiendo JSON. Reintenta una vez si la respuesta no se puede leer."""
    for intento in (1, 2):
        respuesta = cliente.chat.completions.create(
            model=modelo,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
        )
        try:
            return json.loads(respuesta.choices[0].message.content)
        except (json.JSONDecodeError, TypeError):
            if intento == 2:
                raise
            time.sleep(2)


# ---------- Paso 1: leer titulares ----------

def limpiar(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()


def leer_fuentes():
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=config.VENTANA_HORAS)
    titulares = []
    for medio, url in config.FUENTES:
        try:
            crudo = requests.get(url, headers=NAVEGADOR, timeout=20)
            crudo.raise_for_status()
            feed = feedparser.parse(crudo.content)
        except requests.RequestException as error:
            print(f"  [sin respuesta] {medio}: {error.__class__.__name__}")
            continue

        cantidad = 0
        for entrada in feed.entries:
            momento = entrada.get("published_parsed") or entrada.get("updated_parsed")
            if momento and dt.datetime(*momento[:6], tzinfo=dt.timezone.utc) < limite:
                continue
            titulo, enlace = limpiar(entrada.get("title")), entrada.get("link", "")
            if not titulo or not enlace:
                continue
            titulares.append({
                "medio": medio, "titulo": titulo, "link": enlace,
                "resumen": limpiar(entrada.get("summary"))[:400],
            })
            cantidad += 1
            if cantidad >= config.MAX_TITULARES_POR_MEDIO:
                break
        print(f"  {medio}: {cantidad} titulares")
    return titulares


# ---------- Paso 2: detectar los temas del momento ----------

def titulos_recientes(horas=48):
    """Títulos ya publicados, para no repetir temas entre una corrida y la siguiente."""
    limite = dt.datetime.now(ARGENTINA) - dt.timedelta(hours=horas)
    titulos = []
    for carpeta in (CARPETA_NOTAS, CARPETA_RETENIDAS):
        for ruta in carpeta.glob("*.json"):
            try:
                nota = json.loads(ruta.read_text(encoding="utf-8"))
                if dt.datetime.fromisoformat(nota["fecha"]) >= limite:
                    titulos.append(nota["titulo"])
            except (ValueError, KeyError, json.JSONDecodeError):
                continue
    return titulos


def agrupar_temas(cliente, modelo, titulares, ya_publicados):
    lista = "\n".join(f"{i} | {t['medio']} | {t['titulo']}" for i, t in enumerate(titulares))
    sistema = (
        "Sos el jefe de redacción de un medio argentino de noticias generales. "
        "Recibís titulares de varios medios, uno por línea, con el formato 'id | medio | titular'. "
        "Agrupá los titulares que hablan del MISMO hecho puntual, no solo del mismo tema general. "
        f"Descartá estos temas: {'; '.join(config.TEMAS_A_EVITAR)}. "
        "Descartá también los hechos que el medio ya publicó (se listan al final), salvo que haya una novedad importante. "
        f"Asigná a cada grupo una sección de esta lista: {', '.join(config.SECCIONES)}. "
        "Puntuá la importancia para el público argentino del 1 al 10. "
        'Respondé solo con JSON: {"temas": [{"tema": "frase corta", "ids": [números], '
        '"seccion": "una de la lista", "importancia": número}]}. '
        "Incluí únicamente grupos con titulares de al menos dos medios distintos."
    )
    usuario = lista + "\n\nYA PUBLICADO POR EL MEDIO:\n" + ("\n".join(f"- {t}" for t in ya_publicados) or "(nada)")
    datos = pedir_json(cliente, modelo, sistema, usuario)

    temas = []
    for tema in datos.get("temas", []):
        ids = [i for i in tema.get("ids", []) if isinstance(i, int) and 0 <= i < len(titulares)]
        por_medio = {}
        for i in ids:
            por_medio.setdefault(titulares[i]["medio"], titulares[i])
        if len(por_medio) < config.MIN_MEDIOS:
            continue
        importancia = tema.get("importancia", 0)
        temas.append({
            "tema": str(tema.get("tema", "")).strip(),
            "seccion": tema.get("seccion") if tema.get("seccion") in config.SECCIONES else "Sociedad",
            "importancia": importancia if isinstance(importancia, (int, float)) else 0,
            "fuentes": list(por_medio.values())[: config.MAX_FUENTES_POR_NOTA],
        })
    temas.sort(key=lambda t: (t["importancia"], len(t["fuentes"])), reverse=True)
    return temas[: config.N_NOTAS + getattr(config, "TEMAS_DE_RESERVA", 0)]


# ---------- Paso 3: juntar el material ----------

def bajar_texto(fuente):
    """Texto principal del artículo. Si no se puede leer, usa el resumen del titular."""
    texto = ""
    try:
        pagina = trafilatura.fetch_url(fuente["link"])
        if pagina:
            texto = trafilatura.extract(pagina, include_comments=False, include_tables=False) or ""
    except Exception:  # la lectura de una página nunca debe frenar la corrida
        texto = ""
    return (texto.strip() or fuente["resumen"])[: config.MAX_CARACTERES_POR_FUENTE]


def armar_material(fuentes):
    return "\n\n".join(
        f"[FUENTE {n}] {f['medio']} | {f['titulo']}\n{f['texto']}" for n, f in enumerate(fuentes, start=1)
    )


# ---------- Paso 4: redactar ----------

REGLAS = """Sos redactor de un medio argentino de noticias generales. Escribís una nota PROPIA a partir del material de otras fuentes.

Reglas que no se negocian:
1. Usá únicamente hechos que estén en el material. No agregues datos, cifras, nombres ni contexto de tu memoria.
2. Escribí con tus palabras y con tu propia estructura de oraciones. No copies frases del material ni las reordenes apenas: contá los hechos de nuevo, como si se los explicaras a alguien. Las únicas citas textuales permitidas son declaraciones de personas, entre comillas y con atribución.
3. Atribuí la información: "según informó [medio]", "de acuerdo con [organismo]". Si las fuentes se contradicen, decilo.
4. En hechos policiales o judiciales, no nombres a personas que no estén condenadas: usá descripciones ("un hombre de 34 años"). Los funcionarios y figuras públicas en ejercicio de su rol sí se nombran.
5. Nunca identifiques a menores de edad ni a víctimas de delitos sexuales.
6. Si el material no alcanza para una nota sólida, devolvé "descartar": true y explicá el motivo.

Para la foto de archivo, completá "imagen":
- "entidad": el nombre, tal como figura en Wikipedia, de la figura pública, club, organismo, empresa o lugar que protagoniza la nota. Dejalo vacío si no hay uno claro o si el protagonista es una persona privada.
- "generica": dos o tres palabras en inglés que describan una foto de banco neutra para el tema (por ejemplo "argentine pesos banknotes", "football stadium", "courtroom").

Respondé solo con JSON:
{"descartar": false, "motivo": "", "titulo": "", "bajada": "", "cuerpo": ["párrafo 1", "párrafo 2"], "seccion": "", "etiquetas": ["", ""], "imagen": {"entidad": "", "generica": ""}}
"""


def redactar(cliente, modelo, tema, guia):
    sistema = REGLAS + f"\nSecciones posibles: {', '.join(config.SECCIONES)}.\n\nGuía de estilo del medio:\n{guia}"
    usuario = f"Tema detectado: {tema['tema']}\n\nMaterial:\n\n{armar_material(tema['fuentes'])}"
    return pedir_json(cliente, modelo, sistema, usuario)


# ---------- Paso 5: revisar ----------

def verificar(cliente, modelo, nota, tema):
    sistema = (
        "Sos verificador de datos. Recibís una nota y el material en que se basó. "
        "Revisá cada cifra, fecha, nombre propio, cargo y cita textual de la nota y comprobá que figure en el material. "
        "Un dato está respaldado si aparece en AL MENOS UNA de las fuentes, aunque la nota lo atribuya a otra o a varias. "
        "Clasificá cada problema con una gravedad:\n"
        "- 'grave': el dato no aparece en ninguna fuente o la contradice (cifra, fecha, nombre, cargo o cita inventados o cambiados); "
        "la nota da el nombre y apellido de una persona privada no condenada en un hecho policial o judicial; "
        "o da el nombre de un menor de edad o datos que permitan ubicarlo.\n"
        "- 'menor': atribución imprecisa entre medios, redondeos, matices de redacción, detalles de estilo.\n"
        "No es un problema mencionar a menores sin nombrarlos (por ejemplo 'sus hijos', 'un nene de 8 años'), "
        "ni nombrar a funcionarios y figuras públicas. "
        'Respondé solo con JSON: {"observaciones": [{"dato": "lo que dice la nota", "problema": "por qué", "gravedad": "grave o menor"}]}. '
        "Si todo está respaldado, devolvé la lista vacía."
    )
    texto_nota = f"{nota['titulo']}\n{nota['bajada']}\n\n" + "\n\n".join(nota["cuerpo"])
    datos = pedir_json(cliente, modelo, sistema, f"NOTA:\n{texto_nota}\n\nMATERIAL:\n\n{armar_material(tema['fuentes'])}")
    return [o for o in datos.get("observaciones", []) if isinstance(o, dict) and o.get("dato")]


def graves(observaciones):
    return [o for o in observaciones if str(o.get("gravedad", "grave")).strip().lower() != "menor"]


def corregir(cliente, modelo, nota, observaciones, tema):
    """Devuelve la nota sin los datos que el verificador no encontró en las fuentes."""
    sistema = (
        "Sos editor de un medio argentino. Recibís una nota, el material en que se basó y una lista de datos "
        "que no están respaldados por ese material. Corregí cada uno: si el material trae el dato correcto, usalo; "
        "si no, sacá el dato y acomodá la oración. No agregues información que no esté en el material y dejá "
        "el resto de la nota como está. "
        'Respondé solo con JSON: {"titulo": "", "bajada": "", "cuerpo": ["párrafo 1", "párrafo 2"]}.'
    )
    usuario = ("DATOS A CORREGIR:\n" + "\n".join(f"- {o.get('dato')}: {o.get('problema', '')}" for o in observaciones)
               + f"\n\nNOTA:\nTítulo: {nota['titulo']}\nBajada: {nota['bajada']}\n\n" + "\n\n".join(nota["cuerpo"])
               + "\n\nMATERIAL:\n\n" + armar_material(tema["fuentes"]))
    datos = pedir_json(cliente, modelo, sistema, usuario)
    cuerpo = [str(p).strip() for p in datos.get("cuerpo", []) if str(p).strip()]
    if cuerpo:
        nota["cuerpo"] = cuerpo
        nota["titulo"] = str(datos.get("titulo") or nota["titulo"]).strip()
        nota["bajada"] = str(datos.get("bajada") or nota["bajada"]).strip()
    return nota


def palabras(texto):
    return re.findall(r"[a-záéíóúñü0-9]+", texto.lower())


COMILLAS = re.compile(r"“[^”]*”|«[^»]*»|\"[^\"]*\"")


def copias_textuales(nota, tema, largo=12):
    """Secuencias de 12 o más palabras seguidas que la nota comparte con alguna fuente.

    Las declaraciones entre comillas no cuentan: citar textualmente a una persona está permitido.
    """
    cuerpo = palabras(COMILLAS.sub(" | ", " ".join(nota["cuerpo"])).replace("|", " corte "))
    hallazgos = []
    for fuente in tema["fuentes"]:
        origen = palabras(fuente["texto"])
        gramas = {tuple(origen[i:i + largo]) for i in range(len(origen) - largo + 1)}
        i = 0
        while i <= len(cuerpo) - largo:
            if tuple(cuerpo[i:i + largo]) in gramas:
                hallazgos.append({"medio": fuente["medio"], "fragmento": " ".join(cuerpo[i:i + largo]) + "…"})
                i += largo
            else:
                i += 1
    return hallazgos[:5]


def reescribir(cliente, modelo, nota, copias):
    """Devuelve el cuerpo de la nota con las frases copiadas dichas de otra manera."""
    sistema = (
        "Sos editor de un medio argentino. Recibís el cuerpo de una nota y una lista de frases que quedaron "
        "demasiado parecidas a las de otros medios. Reescribí esas partes con otras palabras y otra estructura, "
        "sin cambiar ningún hecho, cifra, nombre ni cita entre comillas, y sin agregar información. "
        "El resto del texto dejalo como está. "
        'Respondé solo con JSON: {"cuerpo": ["párrafo 1", "párrafo 2"]}.'
    )
    usuario = ("FRASES A CAMBIAR:\n" + "\n".join(f"- {c['fragmento']}" for c in copias)
               + "\n\nCUERPO:\n" + "\n\n".join(nota["cuerpo"]))
    datos = pedir_json(cliente, modelo, sistema, usuario)
    cuerpo = [str(p).strip() for p in datos.get("cuerpo", []) if str(p).strip()]
    return cuerpo or nota["cuerpo"]


# ---------- Paso 6: foto de archivo con licencia libre ----------

LICENCIAS_LIBRES = re.compile(r"^(cc0|cc[ -]by([ -]sa)?\b|public domain|pd\b|dominio público)", re.I)


def imagen_wikipedia(entidad):
    """Foto principal del artículo de Wikipedia de la entidad, con sus datos de licencia en Wikimedia Commons."""
    if not entidad:
        return None
    resp = requests.get("https://es.wikipedia.org/w/api.php", headers=IDENTIFICACION, timeout=20, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": entidad, "gsrlimit": 3,
        "prop": "pageimages", "piprop": "name", "pilicense": "free",
    }).json()
    paginas = sorted(resp.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    pedido = set(palabras(entidad))
    for pagina in paginas:
        # El artículo encontrado tiene que corresponder a la entidad pedida y tener foto libre.
        hallado = set(palabras(pagina.get("title", "")))
        if pagina.get("pageimage") and pedido and len(pedido & hallado) * 2 >= len(pedido):
            imagen = foto_de_commons("File:" + pagina["pageimage"])
            if imagen:
                return imagen
    return None


def foto_de_commons(archivo):
    resp = requests.get("https://commons.wikimedia.org/w/api.php", headers=IDENTIFICACION, timeout=20, params={
        "action": "query", "format": "json", "titles": archivo, "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata", "iiurlwidth": 1280,
    }).json()
    for pagina in resp.get("query", {}).get("pages", {}).values():
        for info in pagina.get("imageinfo", []):
            meta = info.get("extmetadata", {})
            licencia = limpiar(meta.get("LicenseShortName", {}).get("value", ""))
            if info.get("mime") != "image/jpeg" or info.get("width", 0) < 500 or not LICENCIAS_LIBRES.match(licencia):
                return None
            autor = limpiar(meta.get("Artist", {}).get("value", ""))[:80]
            return {
                "url": info.get("thumburl") or info["url"],
                "credito": f"{autor} / Wikimedia Commons" if autor else "Wikimedia Commons",
                "licencia": licencia,
                "enlace": info.get("descriptionurl", ""),
            }
    return None


def imagen_pexels(consulta):
    """Foto de banco para notas sin protagonista. Requiere la clave gratuita PEXELS_API_KEY."""
    clave = os.environ.get("PEXELS_API_KEY", "").strip()
    if not clave or not consulta:
        return None
    resp = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": clave}, timeout=20, params={
        "query": consulta, "orientation": "landscape", "per_page": 5,
    }).json()
    fotos = [f for f in resp.get("photos", []) if f.get("src", {}).get("landscape")]
    if not fotos:
        return None
    foto = random.choice(fotos)
    return {
        "url": foto["src"]["landscape"],
        "credito": f"{foto.get('photographer', 'Pexels')} / Pexels",
        "licencia": "",
        "enlace": foto.get("url", ""),
    }


def imagen_commons(consulta):
    """Foto de archivo buscada por tema en Wikimedia Commons. No necesita ninguna clave."""
    if not consulta:
        return None
    resp = requests.get("https://commons.wikimedia.org/w/api.php", headers=IDENTIFICACION, timeout=20, params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 12,
        "gsrsearch": f"{consulta} filetype:bitmap", "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata", "iiurlwidth": 1280,
    }).json()
    candidatas = []
    for pagina in sorted(resp.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        for info in pagina.get("imageinfo", []):
            ancho, alto = info.get("width", 0), info.get("height", 1) or 1
            meta = info.get("extmetadata", {})
            licencia = limpiar(meta.get("LicenseShortName", {}).get("value", ""))
            # Solo fotos apaisadas, de buen tamaño y con licencia libre.
            if info.get("mime") != "image/jpeg" or ancho < 800 or not 1.1 <= ancho / alto <= 2.4:
                continue
            if not LICENCIAS_LIBRES.match(licencia):
                continue
            autor = limpiar(meta.get("Artist", {}).get("value", ""))[:80]
            candidatas.append({
                "url": info.get("thumburl") or info["url"],
                "credito": f"{autor} / Wikimedia Commons" if autor else "Wikimedia Commons",
                "licencia": licencia,
                "enlace": info.get("descriptionurl", ""),
            })
    return random.choice(candidatas[:5]) if candidatas else None


def buscar_imagen(pedido, seccion=""):
    """Prueba de lo más específico a lo más general. La última opción es una foto de archivo de la sección."""
    pedido = pedido if isinstance(pedido, dict) else {}
    entidad = str(pedido.get("entidad") or "").strip()
    generica = str(pedido.get("generica") or "").strip()
    corta = " ".join(generica.split()[:2])
    buscadores = [
        (imagen_wikipedia, entidad),
        (imagen_commons, entidad),
        (imagen_pexels, generica),
        (imagen_commons, generica),
        (imagen_commons, corta if corta != generica else ""),
    ]
    respaldo = list(getattr(config, "FOTOS_POR_SECCION", {}).get(seccion, []))
    random.shuffle(respaldo)
    buscadores += [(imagen_commons, consulta) for consulta in respaldo]
    for buscador, consulta in buscadores:
        if not consulta:
            continue
        try:
            imagen = buscador(consulta)
            if imagen:
                print(f"     foto: {buscador.__name__} con '{consulta}'")
                return imagen
            print(f"     foto: {buscador.__name__} sin resultado para '{consulta}'")
        except Exception as error:  # una foto que falla no debe impedir la nota
            print(f"     foto: {buscador.__name__} falló ({str(error)[:80]})")
    return None


# ---------- Paso 7: guardar ----------

def slugificar(texto):
    texto = texto.lower().translate(str.maketrans("áéíóúñü", "aeiounu"))
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")[:80].strip("-")


def guardar(nota, carpeta):
    base = nota["slug"]
    existentes = {r.stem.split("_", 1)[-1] for c in (CARPETA_NOTAS, CARPETA_RETENIDAS) for r in c.glob("*.json")}
    numero = 2
    while nota["slug"] in existentes:
        nota["slug"] = f"{base}-{numero}"
        numero += 1
    ruta = carpeta / f"{nota['fecha'][:10]}_{nota['slug']}.json"
    ruta.write_text(json.dumps(nota, ensure_ascii=False, indent=1), encoding="utf-8")
    return ruta


# ---------- Programa principal ----------

def main():
    cargar_env()
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Falta la clave OPENAI_API_KEY.")
    for carpeta in (CARPETA_NOTAS, CARPETA_RETENIDAS):
        carpeta.mkdir(exist_ok=True)

    # Notas ya publicadas que quedaron sin foto: se les busca una de archivo de su sección.
    for ruta in sorted(CARPETA_NOTAS.glob("*.json"))[-20:]:
        vieja = json.loads(ruta.read_text(encoding="utf-8"))
        if not vieja.get("imagen"):
            print(f"Buscando foto para: {vieja.get('titulo')}")
            vieja["imagen"] = buscar_imagen({}, vieja.get("seccion", ""))
            if vieja["imagen"]:
                ruta.write_text(json.dumps(vieja, ensure_ascii=False, indent=1), encoding="utf-8")

    cliente = OpenAI()
    modelo = elegir_modelo(cliente)
    guia = (AQUI / "guia_estilo.md").read_text(encoding="utf-8")
    historial = json.loads(ARCHIVO_VISTOS.read_text(encoding="utf-8")) if ARCHIVO_VISTOS.exists() else []
    vistos = set(historial)
    print(f"Modelo: {modelo}")
    print(f"Fotos: Wikipedia y Wikimedia Commons{', más Pexels' if os.environ.get('PEXELS_API_KEY') else ''}")

    print("\n1. Leyendo titulares...")
    titulares = [t for t in leer_fuentes() if t["link"] not in vistos]
    medios = {t["medio"] for t in titulares}
    if len(medios) < config.MIN_MEDIOS:
        print("No hay titulares nuevos de suficientes medios. No se generan notas en esta corrida.")
        return

    print(f"\n2. Detectando temas entre {len(titulares)} titulares de {len(medios)} medios...")
    temas = agrupar_temas(cliente, modelo, titulares, titulos_recientes())
    if not temas:
        print("No hay temas nuevos cubiertos por al menos dos medios. No se generan notas en esta corrida.")
        return

    publicadas = retenidas = 0
    for numero, tema in enumerate(temas, start=1):
        if publicadas >= config.N_NOTAS:  # los temas que sobran eran de reserva
            break
        print(f"\n3.{numero} {tema['tema']} ({', '.join(f['medio'] for f in tema['fuentes'])})")
        for fuente in tema["fuentes"]:
            fuente["texto"] = bajar_texto(fuente)

        try:
            borrador = redactar(cliente, modelo, tema, guia)
        except Exception as error:  # un tema que falla no debe cortar los demás
            print(f"     error al redactar: {str(error)[:120]}")
            continue
        for f in tema["fuentes"]:
            if f["link"] not in vistos:
                vistos.add(f["link"])
                historial.append(f["link"])
        if borrador.get("descartar") or not borrador.get("titulo") or not borrador.get("cuerpo"):
            print(f"     descartada: {borrador.get('motivo') or 'material insuficiente'}")
            continue

        nota = {
            "slug": slugificar(str(borrador["titulo"])),
            "titulo": str(borrador["titulo"]).strip(),
            "bajada": str(borrador.get("bajada", "")).strip(),
            "cuerpo": [str(p).strip() for p in borrador["cuerpo"] if str(p).strip()],
            "seccion": borrador.get("seccion") if borrador.get("seccion") in config.SECCIONES else tema["seccion"],
            "etiquetas": [str(x).strip() for x in borrador.get("etiquetas", []) if str(x).strip()][:6],
            "fecha": dt.datetime.now(ARGENTINA).isoformat(timespec="seconds"),
            "importancia": tema["importancia"],
            "fuentes": [{"medio": f["medio"], "titulo": f["titulo"], "link": f["link"]} for f in tema["fuentes"]],
        }
        if not nota["slug"]:
            continue
        try:
            nota["observaciones"] = verificar(cliente, modelo, nota, tema)
        except Exception as error:
            nota["observaciones"] = [{"dato": "verificación", "problema": f"no se pudo verificar: {str(error)[:80]}"}]
        if graves(nota["observaciones"]):  # un intento de corregir y volver a verificar
            try:
                nota = corregir(cliente, modelo, nota, graves(nota["observaciones"]), tema)
                nota["observaciones"] = verificar(cliente, modelo, nota, tema)
                print(f"     corrección: quedan {len(graves(nota['observaciones']))} datos sin respaldo")
            except Exception as error:
                print(f"     no se pudo corregir: {str(error)[:80]}")
        nota["copias"] = copias_textuales(nota, tema)
        for _ in range(2):  # hasta dos intentos de reescritura
            if not nota["copias"]:
                break
            try:
                nota["cuerpo"] = reescribir(cliente, modelo, nota, nota["copias"])
            except Exception as error:
                print(f"     no se pudo reescribir: {str(error)[:80]}")
                break
            nota["copias"] = copias_textuales(nota, tema)
            print(f"     reescritura: quedan {len(nota['copias'])} frases copiadas")
        nota["imagen"] = buscar_imagen(borrador.get("imagen"), nota["seccion"])

        # Cada control se puede activar o apagar por separado en config.py.
        retener = bool(
            (graves(nota["observaciones"]) and config.RETENER_DATOS_SIN_RESPALDO)
            or (nota["copias"] and config.RETENER_FRASES_COPIADAS)
        )
        if retener:
            guardar(nota, CARPETA_RETENIDAS)
            retenidas += 1
            print(f"     retenida: {nota['titulo']} [{len(graves(nota['observaciones']))} datos, {len(nota['copias'])} copias]")
            for o in graves(nota["observaciones"]):
                print(f"       dato sin respaldo: {o.get('dato')} ({o.get('problema', '')})")
        else:
            # El detalle de la revisión se informa acá, en el registro de la corrida, y no se guarda
            # en el archivo de la nota publicada.
            pendientes = nota.pop("observaciones") + nota.pop("copias")
            guardar(nota, CARPETA_NOTAS)
            publicadas += 1
            print(f"     publicada: {nota['titulo']} [{'con foto' if nota['imagen'] else 'sin foto'}]")
            for item in pendientes:
                if "fragmento" in item:
                    print(f"       frase parecida a {item['medio']}: {item['fragmento']}")
                else:
                    print(f"       dato a revisar: {item.get('dato')} ({item.get('problema', '')})")

    # Se conservan los últimos 6000 artículos usados para que el archivo no crezca sin límite.
    ARCHIVO_VISTOS.write_text(json.dumps(historial[-6000:], ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"\nListo: {publicadas} notas publicadas, {retenidas} retenidas.")


if __name__ == "__main__":
    main()
