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
MAIL_PRENSA = "prensa@labirome.com"
AVISO_IA = "Nota elaborada con inteligencia artificial a partir de las fuentes citadas."
SOBRE = "Un medio digital que tiene como premisa la objetividad y el respaldo de cada dato. Las notas se elaboran con inteligencia artificial, contrastan al menos dos fuentes periodísticas y las citan al pie."

# Secciones, en el orden en que aparecen en la barra.
SECCIONES = [
    "Política", "Sociedad", "Policiales", "Deportes",
    "Internacional", "Espectáculos", "Efemérides", "Bizarras",
]

# ---------- La redacción automática ----------

# Cuántas notas genera en cada corrida. La cantidad de corridas por día se define en
# .github/workflows/publicar.yml. Con tres corridas diarias, esto da hasta doce notas por día.
# Las notas de cada corrida se reparten entre secciones, empezando por las que menos publicaron.
N_NOTAS = 4

# Cada cuántos días sale una efeméride ("un día como hoy"), armada a partir de Wikipedia. 0 la apaga.
EFEMERIDE_CADA_DIAS = 7

# Cada cuántos días sale una historia insólita atemporal, buscada en internet por el modelo y escrita
# solo si al menos dos de las páginas halladas se pueden leer. Si ese día los medios ya traen una
# noticia insólita, se usa esa. 0 la apaga.
BIZARRA_CADA_DIAS = 3

# Un tema solo se redacta si lo cubren al menos estos medios distintos.
MIN_MEDIOS = 2

MAX_FUENTES_POR_NOTA = 4
MAX_CARACTERES_POR_FUENTE = 3500
VENTANA_HORAS = 12
MAX_TITULARES_POR_MEDIO = 25
MAX_TITULARES_POR_SECCION = 12

# Controles antes de publicar. Las notas retenidas quedan en la carpeta "retenidas" y no salen en el
# sitio; para publicarlas a mano, se mueven a la carpeta "notas".
#
# Datos sin respaldo: el verificador encontró una cifra, un nombre o una cita que no figura en las fuentes.
RETENER_DATOS_SIN_RESPALDO = True
# Frases copiadas: después de dos intentos de reescritura, todavía queda alguna frase muy parecida
# a la de otro medio.
RETENER_FRASES_COPIADAS = False

# Temas de reserva: si una nota se descarta o queda retenida, la corrida sigue con el tema siguiente
# hasta completar N_NOTAS. Este número es cuántos temas extra puede probar como máximo.
TEMAS_DE_RESERVA = 4

# Si ninguna foto encontrada corresponde al titular: True usa una foto de archivo de la sección,
# False publica la nota sin foto.
FOTO_DE_SECCION_SI_NO_HAY = True

# Para cambiarle la foto a notas ya publicadas: poné acá un pedazo del nombre de su archivo en la carpeta
# "notas" (por ejemplo "rem-el-mercado"). Se rehace una sola vez, en la corrida siguiente.
REHACER_FOTOS = ["rem-el-mercado", "rem-del-bcra", "el-gobierno-adjudico", "el-smn-declaro"]
# Subí este número cada vez que cambies la lista de arriba, para que se vuelvan a rehacer.
TANDA_FOTOS = 2

# Foto de último recurso cuando no aparece ninguna para el tema: búsqueda en Wikimedia Commons por sección.
FOTOS_POR_SECCION = {
    "Política": ["Casa Rosada", "Congreso de la Nación Argentina"],
    "Sociedad": ["Buenos Aires skyline", "Avenida 9 de Julio"],
    "Policiales": ["Policía Federal Argentina", "Palacio de Justicia Buenos Aires"],
    "Deportes": ["football stadium Argentina", "Estadio Monumental"],
    "Internacional": ["United Nations headquarters", "world flags"],
    "Espectáculos": ["Teatro Colón", "theatre stage lights"],
    "Efemérides": ["Cabildo de Buenos Aires", "Obelisco de Buenos Aires"],
    "Bizarras": ["Obelisco de Buenos Aires", "Buenos Aires skyline"],
}

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

    # Feeds por sección, para que haya material fuera de política. El tercer dato es una pista para
    # clasificar. Si alguno deja de responder, la corrida lo saltea y lo avisa en el registro.
    ("Clarín", "https://www.clarin.com/rss/deportes/", "Deportes"),
    ("Clarín", "https://www.clarin.com/rss/espectaculos/", "Espectáculos"),
    ("Clarín", "https://www.clarin.com/rss/policiales/", "Policiales"),
    ("Clarín", "https://www.clarin.com/rss/mundo/", "Internacional"),
    ("Clarín", "https://www.clarin.com/rss/sociedad/", "Sociedad"),
    ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/deportes/?outputType=xml", "Deportes"),
    ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/espectaculos/?outputType=xml", "Espectáculos"),
    ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/seguridad/?outputType=xml", "Policiales"),
    ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/el-mundo/?outputType=xml", "Internacional"),
    ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/sociedad/?outputType=xml", "Sociedad"),
    ("TN", "https://tn.com.ar/arc/outboundfeeds/rss/category/deportes/?outputType=xml", "Deportes"),
    ("TN", "https://tn.com.ar/arc/outboundfeeds/rss/category/show/?outputType=xml", "Espectáculos"),
    ("TN", "https://tn.com.ar/arc/outboundfeeds/rss/category/policiales/?outputType=xml", "Policiales"),
    ("TN", "https://tn.com.ar/arc/outboundfeeds/rss/category/internacional/?outputType=xml", "Internacional"),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/deportes/", "Deportes"),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/teleshow/", "Espectáculos"),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/sociedad/policiales/", "Policiales"),
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/category/america/", "Internacional"),
    ("Perfil", "https://www.perfil.com/feed/deportes", "Deportes"),
    ("Perfil", "https://www.perfil.com/feed/espectaculos", "Espectáculos"),
    ("Perfil", "https://www.perfil.com/feed/policia", "Policiales"),
    ("Perfil", "https://www.perfil.com/feed/internacional", "Internacional"),
    ("Ámbito", "https://www.ambito.com/rss/pages/deportes.xml", "Deportes"),
    ("Ámbito", "https://www.ambito.com/rss/pages/espectaculos.xml", "Espectáculos"),
    ("Ámbito", "https://www.ambito.com/rss/pages/mundo.xml", "Internacional"),
]
