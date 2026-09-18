/*
  Mejoras de lectura de un artículo, sin librerías externas. Dos cosas, las
  dos sobre .post-body:

  1. Índice flotante -- construye la lista de <h2> dentro de <nav class="toc">
     y resalta el que está en pantalla (scroll-spy) con IntersectionObserver.
  2. Tablas con scroll -- envuelve cada <table> en un contenedor desplazable
     para que una tabla ancha se pueda leer en celular. Se hace acá y no en el
     Markdown para que quien escribe el artículo solo tenga que pegar la tabla
     Markdown normal, sin acordarse de ningún <div>.
*/
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
