/*
  Mejoras de lectura de un artículo, sin librerías externas. Tres cosas:

  0. Botón "Volver arriba" y cierre del panel "Secciones" del celular (Escape
     o toque afuera) -- en todas las páginas del sitio.
  1. Índice flotante -- construye la lista de <h2> dentro de <nav class="toc">
     y resalta el que está en pantalla (scroll-spy) con IntersectionObserver.
  2. Tablas con scroll -- envuelve cada <table> en un contenedor desplazable
     para que una tabla ancha se pueda leer en celular. Se hace acá y no en el
     Markdown para que quien escribe el artículo solo tenga que pegar la tabla
     Markdown normal, sin acordarse de ningún <div>.

  Las dos últimas solo corren si la página tiene .post-body (un artículo);
  la primera corre siempre, por eso va en su propio bloque más arriba.
*/

/* ---- Botón "Volver arriba" ----
   Aparece recién después de bajar una pantalla, así que no ocupa lugar ni
   distrae mientras se lee desde arriba. Se crea desde acá y no en el layout
   a propósito: sin JavaScript un botón de este tipo no haría nada, y es
   preferible que directamente no exista a que esté y no responda. */
(function () {
  var UMBRAL = 400; // px de scroll antes de mostrarlo

  var boton = document.createElement('button');
  boton.type = 'button';
  boton.className = 'ir-arriba';
  boton.setAttribute('aria-label', 'Volver arriba');
  boton.title = 'Volver arriba';
  boton.innerHTML =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"' +
    ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
    '<path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>';
  document.body.appendChild(boton);

  function mostrar(si) {
    boton.classList.toggle('visible', si);
  }

  // Un "centinela" invisible de UMBRAL px de alto, pegado al principio de la
  // página: mientras se lo vea en pantalla estamos arriba de todo; cuando
  // sale de vista, es que se bajó lo suficiente y el botón aparece. Se hace
  // con IntersectionObserver (igual que el índice flotante) en vez de
  // escuchar el scroll: el navegador avisa solo cuando el estado cambia, sin
  // ejecutar código en cada uno de los cientos de eventos que dispara el dedo.
  var centinela = document.createElement('div');
  centinela.className = 'ir-arriba-centinela';
  centinela.setAttribute('aria-hidden', 'true');
  centinela.style.height = UMBRAL + 'px';
  document.body.insertBefore(centinela, document.body.firstChild);

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      mostrar(!entries[entries.length - 1].isIntersecting);
    }).observe(centinela);
  } else {
    // Navegador viejo: se cae al listener de scroll de toda la vida.
    window.addEventListener('scroll', function () {
      mostrar((window.pageYOffset || document.documentElement.scrollTop || 0) > UMBRAL);
    }, { passive: true });
  }

  boton.addEventListener('click', function () {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (window.scrollTo) {
      try {
        window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
      } catch (e) {
        window.scrollTo(0, 0); // navegadores viejos: sin opciones
      }
    }
    // Sin esto el foco del teclado se queda abajo, donde estaba el botón,
    // y el siguiente Tab sigue navegando desde el pie de la página.
    // Va al nombre del sitio: está arriba de todo y se ve en cualquier ancho.
    // Antes apuntaba al primer enlace del encabezado ("Inicio" del menú),
    // pero en celular ese menú ahora está oculto detrás de "Secciones" y el
    // foco caía en un elemento invisible. Desde el nombre del sitio, el
    // siguiente Tab llega al menú (o a "Secciones") y al buscador.
    var destino = document.querySelector('.site-header h1') || document.querySelector('h1');
    if (destino) {
      if (!destino.hasAttribute('tabindex')) destino.setAttribute('tabindex', '-1');
      destino.focus({ preventScroll: true });
    }
  });
})();

/* ---- Panel "Secciones" (menú del celular) ----
   Es un <details>: abre y cierra solo, sin este script. Esto nada más le
   suma lo que se espera de un panel desplegable -- que se cierre con Escape
   (devolviendo el foco al botón) y al tocar fuera de él. */
(function () {
  var panel = document.querySelector('.nav-movil');
  if (!panel) return;

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel.open) {
      panel.open = false;
      panel.querySelector('summary').focus();
    }
  });
  document.addEventListener('click', function (e) {
    if (panel.open && !panel.contains(e.target)) panel.open = false;
  });
})();

(function () {
  var articulo = document.querySelector('.post-body');
  if (!articulo) return;

  // ---- Tablas anchas: envoltorio con scroll horizontal ----
  // tabindex + role="region" para que la zona desplazable también sea
  // alcanzable con el teclado, no solo arrastrando con el dedo o el mouse.
  Array.prototype.slice.call(articulo.querySelectorAll('table')).forEach(function (tabla) {
    var padre = tabla.parentNode;
    if (padre && padre.classList && padre.classList.contains('tabla-scroll')) {
      if (!padre.hasAttribute('tabindex')) {
        padre.setAttribute('tabindex', '0');
        padre.setAttribute('role', 'region');
        padre.setAttribute('aria-label', 'Tabla desplazable horizontalmente');
      }
      return;
    }
    var caja = document.createElement('div');
    caja.className = 'tabla-scroll';
    caja.setAttribute('tabindex', '0');
    caja.setAttribute('role', 'region');
    caja.setAttribute('aria-label', 'Tabla desplazable horizontalmente');
    padre.insertBefore(caja, tabla);
    caja.appendChild(tabla);
  });

  // ---- Infografías densas ----
  // Una imagen marcada como infografía (ver la nota en styles.css) no se
  // achica al ancho de la columna: se envuelve en una caja que se desliza de
  // costado y en un enlace al archivo original, para poder abrirla y hacer
  // zoom con el pellizco del teléfono. Mismo patrón que el envoltorio de las
  // tablas anchas de acá arriba.
  Array.prototype.slice.call(articulo.querySelectorAll('img.infografia')).forEach(function (imagen) {
    if (imagen.closest('.infografia-scroll')) return;
    var fuente = imagen.getAttribute('src');
    if (!fuente) return;

    var caja = document.createElement('div');
    caja.className = 'infografia-scroll';
    caja.setAttribute('tabindex', '0');
    caja.setAttribute('role', 'region');
    caja.setAttribute('aria-label', 'Infografía desplazable horizontalmente');

    var enlace = document.createElement('a');
    enlace.className = 'infografia-enlace';
    enlace.href = fuente;
    enlace.target = '_blank';
    enlace.rel = 'noopener';
    enlace.setAttribute('aria-label', 'Abrir la infografía en tamaño completo');

    imagen.parentNode.insertBefore(caja, imagen);
    caja.appendChild(enlace);
    enlace.appendChild(imagen);
  });

  // ---- Fórmulas anchas ----
  // El CSS ya las deja deslizarse (mjx-container[display="true"]). MathJax
  // por su cuenta ya le pone tabindex="0" a cada fórmula, así que con el
  // teclado se llega igual; lo que falta es AVISAR, a quien usa un lector de
  // pantalla, que esa en particular se puede correr de costado. Eso se marca
  // solo en las que de verdad no entran, y se revisa de nuevo al rotar el
  // teléfono, que es cuando una fórmula pasa de entrar a no entrar.
  function marcarFormulasAnchas() {
    Array.prototype.forEach.call(
      articulo.querySelectorAll('mjx-container[display="true"]'),
      function (formula) {
        var desborda = formula.scrollWidth > formula.clientWidth + 1;
        if (desborda) {
          if (!formula.hasAttribute('tabindex')) formula.setAttribute('tabindex', '0');
          formula.setAttribute('role', 'region');
          formula.setAttribute('aria-label', 'Fórmula desplazable horizontalmente');
        } else if (formula.getAttribute('role') === 'region') {
          formula.removeAttribute('role');
          formula.removeAttribute('aria-label');
        }
      }
    );
  }

  // El evento lo dispara la configuración de MathJax en _layouts/default.html
  // cuando terminó de dibujar; si por lo que sea ya había terminado antes de
  // llegar acá, la promesa de arranque sirve igual.
  document.addEventListener('formulas-listas', marcarFormulasAnchas);
  if (window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) {
    window.MathJax.startup.promise.then(marcarFormulasAnchas);
  }
  var temporizadorFormulas = null;
  window.addEventListener('resize', function () {
    clearTimeout(temporizadorFormulas);
    temporizadorFormulas = setTimeout(marcarFormulasAnchas, 200);
  });

  // ---- Índice flotante ----
  var toc = document.querySelector('.toc');
  if (!toc) return;

  var encabezados = Array.prototype.slice.call(articulo.querySelectorAll('h2'));
  if (!encabezados.length) {
    toc.remove();
    return;
  }

  var lista = document.createElement('ul');
  encabezados.forEach(function (h, i) {
    if (!h.id) h.id = 'seccion-' + (i + 1);
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent;
    li.appendChild(a);
    lista.appendChild(li);
  });
  toc.appendChild(lista);

  // ---- Índice plegable (celular) ----
  // Mismo índice, otra forma: en pantallas angostas el flotante queda al
  // final del artículo, donde ya no sirve para navegar. Este va arriba, justo
  // debajo del título y antes del cuerpo, cerrado por defecto para no empujar
  // el comienzo de la lectura. Se usa <details>, que ya trae de fábrica el
  // abrir/cerrar con teclado y el anuncio correcto en un lector de pantalla.
  var contenedorArticulo = document.querySelector('.article-layout');
  if (contenedorArticulo && contenedorArticulo.parentNode) {
    var plegable = document.createElement('details');
    plegable.className = 'toc-movil';

    var titulo = document.createElement('summary');
    titulo.innerHTML =
      '<span>En este artículo</span>' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"' +
      ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
      '<path d="M9 18l6-6-6-6"/></svg>';

    var navMovil = document.createElement('nav');
    navMovil.setAttribute('aria-label', 'Índice del artículo');
    navMovil.appendChild(lista.cloneNode(true));

    plegable.appendChild(titulo);
    plegable.appendChild(navMovil);
    contenedorArticulo.parentNode.insertBefore(plegable, contenedorArticulo);

    // Al elegir una sección se cierra solo: si quedara abierto, al volver
    // arriba el lector se encontraría con el índice desplegado tapando el
    // principio del artículo.
    navMovil.addEventListener('click', function (evento) {
      if (evento.target.closest('a')) plegable.open = false;
    });
  }

  var enlaces = Array.prototype.slice.call(lista.querySelectorAll('a'));

  function marcarActivo(id) {
    enlaces.forEach(function (a) {
      a.classList.toggle('activo', a.getAttribute('href') === '#' + id);
    });
  }

  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) marcarActivo(entry.target.id);
        });
      },
      { rootMargin: '-15% 0px -70% 0px' }
    );
    encabezados.forEach(function (h) { observer.observe(h); });
  }

  marcarActivo(encabezados[0].id);
})();
