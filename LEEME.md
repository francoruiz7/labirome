# La Birome

Medio de noticias experimental que se actualiza solo. Varias veces por día, un programa lee los titulares de los principales medios, detecta los temas del momento, redacta notas propias citando las fuentes, las revisa, les busca una foto con licencia libre y publica el sitio.

Todo corre en GitHub, sin servidor ni hosting pago: GitHub Actions ejecuta el programa y GitHub Pages aloja el sitio.

## Cómo funciona

1. `generar.py` lee los titulares, agrupa los que hablan del mismo hecho y elige los temas cubiertos por al menos dos medios.
2. Redacta cada nota con un modelo de lenguaje, usando solo los hechos de las fuentes y atribuyéndolos.
3. La revisa de dos maneras: un verificador busca cifras, nombres y citas sin respaldo, y un control detecta frases copiadas.
4. Le busca una foto de archivo: primero la del artículo de Wikipedia del protagonista (Wikimedia Commons) y, si no hay, una de banco en Pexels. Siempre con el crédito al pie.
5. Guarda cada nota como un archivo en la carpeta `notas`. Las que tienen observaciones van a `retenidas` y no se publican.
6. `construir.py` arma el sitio completo a partir de la carpeta `notas`.

## Tareas habituales

- **Borrar una nota:** abrí su archivo en la carpeta `notas`, tocá el tacho de basura y confirmá. El sitio se actualiza solo en un par de minutos.
- **Corregir una nota:** abrí el archivo, tocá el lápiz, editá el texto y guardá.
- **Publicar una nota retenida:** mové el archivo de `retenidas` a `notas`. En cada archivo, los campos `observaciones` y `copias` dicen por qué quedó retenida.
- **Generar notas ahora:** pestaña Actions, "Publicar La Birome", botón "Run workflow".
- **Pausar el medio:** pestaña Actions, "Publicar La Birome", menú de los tres puntos, "Disable workflow".

## Qué se puede ajustar

- `guia_estilo.md`: la voz del medio.
- `config.py`: cantidad de notas por corrida, medios que se leen, secciones, temas a evitar, y si el sitio aparece o no en buscadores (`INDEXABLE`).
- `.github/workflows/publicar.yml`: los horarios en que corre.

## Puesta en marcha

1. Crear un repositorio público y subir estos archivos.
2. En Settings > Secrets and variables > Actions, cargar el secreto `OPENAI_API_KEY`. Opcional: `PEXELS_API_KEY`, que se obtiene gratis en pexels.com/api.
3. En Settings > Pages, elegir "GitHub Actions" como origen y cargar el dominio propio.
4. En el registrador del dominio, apuntar el dominio a GitHub Pages.
5. En la pestaña Actions, ejecutar "Publicar La Birome".

## Probarlo en una compu

    pip install -r requirements.txt
    python generar.py      (necesita un archivo .env, ver .env.ejemplo)
    python construir.py
    cd sitio && python -m http.server

y abrir http://localhost:8000
