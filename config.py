"""Ajustes de La Birome. Todo lo que quieras cambiar está acá."""

# ---------- El sitio ----------

NOMBRE = "La Birome"
DOMINIO = "labirome.com"
URL_SITIO = "https://labirome.com"
DESCRIPCION = "Noticias de Argentina y el mundo, actualizadas durante todo el día."

# Dejar vacío con dominio propio. Solo se usa si el sitio se ve desde usuario.github.io/repositorio.
RUTA_BASE = ""

# Con False el sitio les pide a los buscadores que no lo incluyan: lo ve quien tenga el enlace,
# pero no aparece en Google. Pasalo a True cuando quieras abrirlo.
INDEXABLE = False

# Leyenda al pie de cada nota y texto del pie de página.
AVISO_IA = "Nota elaborada con inteligencia artificial a partir de las fuentes citadas."
SOBRE = "Un medio digital que tiene como premisa la objetividad y el respaldo de cada dato. Las notas se elaboran con inteligencia artificial, contrastan al menos dos fuentes periodísticas y las citan al pie."

# Secciones, en el orden en que aparecen en la barra.
SECCIONES = [
    "Política", "Sociedad", "Policiales", "Deportes",
    "Internacional", "Espectáculos", "Efemérides", "Bizarras",
]

# ---------- La redacción automática ----------

# Cuántas notas genera en cada corrida. La cantidad de corridas por día se define en
# .github/workflows/publicar.yml. Con dos corridas diarias, esto da hasta cuatro notas por día.
N_NOTAS = 2

# Un tema solo se redacta si lo cubren al menos estos medios distintos.
MIN_MEDIOS = 2

MAX_FUENTES_POR_NOTA = 4
MAX_CARACTERES_POR_FUENTE = 3500
VENTANA_HORAS = 12
MAX_TITULARES_POR_MEDIO = 25

# Controles antes de publicar. Las notas retenidas quedan en la carpeta "retenidas" y no salen en el
# sitio; para publicarlas a mano, se mueven a la carpeta "notas".
#
# Datos sin respaldo: el verificador encontró una cifra, un nombre o una cita que no figura en las fuentes.
RETENER_DATOS_SIN_RESPALDO = True
# Frases copiadas: después de dos intentos de reescritura, todavía queda alguna frase muy parecida
# a la de otro medio.
RETENER_FRASES_COPIADAS = False

TEMAS_A_EVITAR = [
    "suicidios",
    "abuso sexual de menores",
    "horóscopo, quiniela y sorteos",
    "contenido patrocinado o publicitario",
    "columnas de opinión y editoriales",
]

MODELOS_PREFERIDOS = ["gpt-5-mini", "gpt-4.1-mini", "gpt-4o-mini"]

# Medios de los que se leen titulares. Si alguno deja de responder, se saltea y se avisa.
FUENTES = [
    ("Clarín", "https://www.clarin.com/rss/lo-ultimo/"),
    ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml"),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/"),
    ("Ámbito", "https://www.ambito.com/rss/pages/home.xml"),
    ("Perfil", "https://www.perfil.com/feed"),
    ("El Cronista", "https://www.cronista.com/files/rss/news.xml"),
    ("TN", "https://tn.com.ar/arc/outboundfeeds/rss/?outputType=xml"),
]
