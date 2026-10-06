(function () {
  var BASE = (window.LB && window.LB.base) || '';

  // Fecha y hora de Buenos Aires
  var reloj = document.getElementById('reloj');
  if (reloj) {
    var hora = function () {
      try {
        var ahora = new Date();
        var zona = 'America/Argentina/Buenos_Aires';
        var dia = new Intl.DateTimeFormat('es-AR', { weekday: 'long', day: 'numeric', month: 'long', timeZone: zona }).format(ahora);
        var hm = new Intl.DateTimeFormat('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: zona }).format(ahora);
        reloj.textContent = dia.charAt(0).toUpperCase() + dia.slice(1) + ', ' + hm + ' h';
      } catch (e) {
        reloj.textContent = '';
      }
    };
    hora();
    setInterval(hora, 30000);
  }

  // Buscador desplegable
  var abrir = document.getElementById('abrir-buscador');
  var buscador = document.getElementById('buscador');
  if (abrir && buscador) {
    abrir.addEventListener('click', function () {
      var abierto = buscador.hidden;
      buscador.hidden = !abierto;
      abrir.setAttribute('aria-expanded', String(abierto));
      if (abierto) {
        var campo = buscador.querySelector('input[type="search"]');
        if (campo) { campo.focus(); }
      }
    });
  }

  // Newsletter: todavía no está activo y no se guarda ningún dato
  var formNews = document.getElementById('form-newsletter');
  if (formNews) {
    formNews.addEventListener('submit', function (e) {
      e.preventDefault();
      document.getElementById('aviso-newsletter').hidden = false;
      formNews.reset();
    });
  }

  // ---------- Índice de notas: lo usan el filtro, "cargar más" y el buscador ----------
  var indice = null;
  function traerIndice() {
    if (indice) { return Promise.resolve(indice); }
    return fetch(BASE + '/indice.json')
      .then(function (r) { if (!r.ok) { throw new Error('indice'); } return r.json(); })
      .then(function (datos) { indice = datos; return datos; });
  }
  function crear(etiqueta, attrs, hijos) {
    var e = document.createElement(etiqueta);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'texto') { e.textContent = attrs[k]; } else { e.setAttribute(k, attrs[k]); }
    });
    (hijos || []).forEach(function (h) { if (h) { e.appendChild(h); } });
    return e;
  }
  function tarjeta(n, nivel) {
    var img = n.i ? crear('img', { src: n.i, alt: '', loading: 'lazy' }) : null;
    if (img) { img.addEventListener('error', function () { img.remove(); }); }
    return crear('article', { class: 'tarjeta' }, [
      crear('a', { class: 'foto', href: n.u, tabindex: '-1', 'aria-hidden': 'true' }, [img]),
      crear('div', {}, [
        crear('a', { class: 'etiqueta', href: n.su, texto: n.s }),
        crear(nivel || 'h3', {}, [crear('a', { href: n.u, texto: n.t })]),
        crear('time', { class: 'fecha', datetime: n.d, texto: n.f })
      ])
    ]);
  }

  // Portada: filtro por sección y carga de más notas sin recargar la página.
  var grilla = document.getElementById('grilla');
  var filtros = document.getElementById('filtros');
  if (grilla && filtros && window.fetch) {
    var botonMas = document.getElementById('cargar-mas');
    var cajaMas = botonMas ? botonMas.parentNode : null;
    var tanda = parseInt(grilla.getAttribute('data-tanda'), 10) || 9;
    var excluir = (grilla.getAttribute('data-excluir') || '').split(',');
    var estado = { seccion: '', visibles: tanda };

    var pintar = function () {
      return traerIndice().then(function (datos) {
        var lista = datos.filter(function (n) {
          return excluir.indexOf(n.g) === -1 && (!estado.seccion || n.s === estado.seccion);
        });
        grilla.textContent = '';
        lista.slice(0, estado.visibles).forEach(function (n) { grilla.appendChild(tarjeta(n)); });
        if (!lista.length) {
          grilla.appendChild(crear('p', { class: 'vacio', texto: 'Todavía no hay notas en esta sección.' }));
        }
        if (cajaMas) { cajaMas.hidden = lista.length <= estado.visibles; }
      });
    };

    filtros.addEventListener('click', function (e) {
      var enlace = e.target.closest ? e.target.closest('a[data-seccion]') : null;
      if (!enlace) { return; }
      e.preventDefault();
      var destino = enlace.href;
      estado.seccion = enlace.getAttribute('data-seccion');
      estado.visibles = tanda;
      Array.prototype.forEach.call(filtros.querySelectorAll('a'), function (a) {
        a.setAttribute('aria-current', String(a === enlace));
      });
      pintar().catch(function () { window.location.href = destino; });
    });

    if (botonMas) {
      botonMas.addEventListener('click', function (e) {
        e.preventDefault();
        estado.visibles += tanda;
        pintar().catch(function () { if (cajaMas) { cajaMas.hidden = true; } });
      });
    }
  }

  // Página de búsqueda
  var resultados = document.getElementById('resultados');
  if (resultados && window.fetch) {
    var normalizar = function (s) {
      return String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    };
    var consulta = new URLSearchParams(window.location.search).get('q') || '';
    var titulo = document.getElementById('titulo-busqueda');
    Array.prototype.forEach.call(document.querySelectorAll('.listado input[name="q"]'), function (c) { c.value = consulta; });
    var palabras = normalizar(consulta).split(/\s+/).filter(function (p) { return p.length > 1; });

    if (palabras.length) {
      titulo.textContent = 'Resultados para «' + consulta + '»';
      traerIndice().then(function (datos) {
        var hallados = datos.filter(function (n) {
          var texto = normalizar(n.t + ' ' + n.b);
          return palabras.every(function (p) { return texto.indexOf(p) !== -1; });
        }).slice(0, 60);
        hallados.forEach(function (n) { resultados.appendChild(tarjeta(n, 'h2')); });
        if (!hallados.length) {
          resultados.appendChild(crear('p', { class: 'sin-resultados', texto: 'No encontramos notas con esas palabras. Probá con otras.' }));
        }
      }).catch(function () {
        resultados.appendChild(crear('p', { class: 'sin-resultados', texto: 'No se pudo cargar el buscador. Probá de nuevo en un rato.' }));
      });
    }
  }
})();
