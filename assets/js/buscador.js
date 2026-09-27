/*
  Buscador predictivo del encabezado. Filtra los artículos mientras se
  escribe, sin recargar la página, usando Fuse.js (búsqueda aproximada:
  tolera errores de tipeo) sobre /search.json, que arma Jekyll en cada build.

  Nada se descarga hasta que alguien toca el buscador: ni Fuse.js ni el
  índice. Mismo criterio que MathJax/Mermaid, que solo se bajan en las
  páginas que los usan. Fuse.js va con la versión fijada (no "latest"),
  desde jsdelivr como los otros dos; desde la 7.x solo se publica como
  módulo ES, por eso se carga con import() y no con un <script>.

  Tildes: Fuse.js no las iguala solo, así que se buscan versiones "sin
  tildes" del texto y de la consulta ("toxicologia" encuentra
  "Toxicología"), pero se muestra siempre el texto original.

  Accesibilidad: patrón combobox de WAI-ARIA -- flechas para recorrer los
  resultados, Enter para abrir, Escape para cerrar, y un aviso con la
  cantidad de resultados para quien usa lector de pantalla.

  Sin JavaScript no se dibuja nada (ver el comentario en header.html).
*/
(function () {
  var lugar = document.querySelector('[data-buscador]');
  if (!lugar || !window.fetch || !window.Promise) return;

  var FUSE_URL = 'https://cdn.jsdelivr.net/npm/fuse.js@7.5.0/dist/fuse.basic.min.mjs';
  var INDICE_URL = '/search.json';
  var MINIMO = 2;      // letras antes de empezar a buscar
  var MAXIMO = 6;      // resultados a la vista

  var form = document.createElement('form');
  form.className = 'buscador-form';
  form.setAttribute('role', 'search');
  form.innerHTML =
    '<label class="solo-lector" for="buscador-campo">Buscar artículos</label>' +
    '<div class="buscador-caja">' +
    '<svg class="buscador-icono" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"' +
    ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
    '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
    '<input id="buscador-campo" type="search" placeholder="Buscar artículos" autocomplete="off"' +
    ' spellcheck="false" role="combobox" aria-autocomplete="list" aria-expanded="false"' +
    ' aria-controls="buscador-resultados">' +
    '</div>' +
    '<ul id="buscador-resultados" class="buscador-resultados" role="listbox" aria-label="Resultados" hidden></ul>' +
    '<p class="solo-lector" aria-live="polite" data-aviso></p>';
  lugar.appendChild(form);

  var campo = form.querySelector('input');
  var lista = form.querySelector('ul');
  var aviso = form.querySelector('[data-aviso]');
  var activo = -1;
  var resultados = [];
  var motor = null;       // promesa de Fuse ya armado con el índice
  var ultimaConsulta = '';

  function sinTildes(texto) {
    return (texto || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function cargarMotor() {
    if (motor) return motor;
    motor = Promise.all([
      import(FUSE_URL),
      fetch(INDICE_URL).then(function (r) {
        if (!r.ok) throw new Error('índice ' + r.status);
        return r.json();
      })
    ]).then(function (partes) {
      var Fuse = partes[0].default;
      var articulos = partes[1].map(function (a) {
        a._titulo = sinTildes(a.title);
        a._categoria = sinTildes(a.category);
        a._extracto = sinTildes(a.excerpt);
        return a;
      });
      return new Fuse(articulos, {
        keys: [
          { name: '_titulo', weight: 0.6 },
          { name: '_categoria', weight: 0.15 },
          { name: '_extracto', weight: 0.25 }
        ],
        threshold: 0.35,
        ignoreLocation: true,
        minMatchCharLength: 2
      });
    });
    // Si falló (sin conexión, CDN caído), se puede reintentar la próxima vez.
    motor.catch(function () { motor = null; });
    return motor;
  }

  function abrir(si) {
    lista.hidden = !si;
    campo.setAttribute('aria-expanded', si ? 'true' : 'false');
    form.classList.toggle('abierto', si);
    if (!si) marcar(-1);
  }

  function marcar(indice) {
    activo = indice;
    Array.prototype.forEach.call(lista.children, function (li, i) {
      li.setAttribute('aria-selected', i === indice ? 'true' : 'false');
    });
    if (indice >= 0 && lista.children[indice]) {
      campo.setAttribute('aria-activedescendant', lista.children[indice].id);
      lista.children[indice].scrollIntoView({ block: 'nearest' });
    } else {
      campo.removeAttribute('aria-activedescendant');
    }
  }

  function mensaje(texto) {
    lista.innerHTML = '';
    var li = document.createElement('li');
    li.className = 'buscador-vacio';
    li.setAttribute('role', 'presentation');
    li.textContent = texto;
    lista.appendChild(li);
    resultados = [];
    abrir(true);
  }

  // El DOM se arma con createElement/textContent, nunca con innerHTML de
  // texto que venga del índice: un título con "<" no puede romper nada.
  function pintar(encontrados) {
    lista.innerHTML = '';
    resultados = encontrados;
    encontrados.forEach(function (articulo, i) {
      var li = document.createElement('li');
      li.id = 'buscador-opcion-' + i;
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', 'false');

      var a = document.createElement('a');
      a.href = articulo.url;
      a.tabIndex = -1;

      var meta = document.createElement('span');
      meta.className = 'buscador-meta';
      meta.textContent = articulo.category + ' · ' + articulo.date;

      var titulo = document.createElement('span');
      titulo.className = 'buscador-titulo';
      titulo.textContent = articulo.title;

      var extracto = document.createElement('span');
      extracto.className = 'buscador-extracto';
      extracto.textContent = articulo.excerpt;

      a.appendChild(meta);
      a.appendChild(titulo);
      a.appendChild(extracto);
      li.appendChild(a);
      // mousedown y no click: el click llegaría después de que el campo
      // pierda el foco y cierre la lista.
      li.addEventListener('mousedown', function (e) { e.preventDefault(); });
      lista.appendChild(li);
    });
    abrir(true);
  }

  function buscar() {
    var consulta = campo.value.trim();
    ultimaConsulta = consulta;
    if (consulta.length < MINIMO) {
      abrir(false);
      aviso.textContent = '';
      return;
    }
    cargarMotor().then(function (fuse) {
      if (consulta !== ultimaConsulta) return; // llegó otra tecla mientras tanto
      var encontrados = fuse.search(sinTildes(consulta), { limit: MAXIMO }).map(function (r) { return r.item; });
      if (encontrados.length) {
        pintar(encontrados);
        aviso.textContent = encontrados.length === 1 ? '1 resultado' : encontrados.length + ' resultados';
      } else {
        mensaje('Sin resultados para «' + consulta + '».');
        aviso.textContent = 'Sin resultados';
      }
    }, function () {
      mensaje('No se pudo cargar el buscador. Revisa la conexión e intenta de nuevo.');
    });
  }

  campo.addEventListener('input', buscar);
  // Se empieza a bajar apenas se enfoca el campo, mientras se escribe la
  // primera letra: cuando llegan las dos letras mínimas ya suele estar listo.
  campo.addEventListener('focus', function () {
    cargarMotor();
    if (campo.value.trim().length >= MINIMO) buscar();
  });

  campo.addEventListener('keydown', function (e) {
    var hay = resultados.length;
    if (e.key === 'ArrowDown' && hay) {
      e.preventDefault();
      marcar(activo < hay - 1 ? activo + 1 : 0);
    } else if (e.key === 'ArrowUp' && hay) {
      e.preventDefault();
      marcar(activo > 0 ? activo - 1 : hay - 1);
    } else if (e.key === 'Escape') {
      if (!lista.hidden) {
        e.preventDefault();
        abrir(false);
      } else if (campo.value) {
        campo.value = '';
      }
    }
  });

  // Enter: abre el resultado marcado con las flechas, o el primero.
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var elegido = resultados[activo >= 0 ? activo : 0];
    if (elegido) window.location.href = elegido.url;
  });

  campo.addEventListener('blur', function () { abrir(false); });

  // El panel "Secciones" del celular y la lista de resultados ocupan el
  // mismo lugar debajo del encabezado: abrir uno cierra el otro.
  var secciones = document.querySelector('.nav-movil');
  if (secciones) {
    secciones.addEventListener('toggle', function () {
      if (secciones.open) abrir(false);
    });
    campo.addEventListener('focus', function () { secciones.open = false; });
  }
})();
