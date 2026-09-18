/*
  Índice flotante -- construye la lista de <h2> del artículo dentro de
  <nav class="toc"> y resalta el que está en pantalla (scroll-spy) con
  IntersectionObserver. JS vanilla, sin librerías externas.
*/
(function () {
  var articulo = document.querySelector('.post-body');
  var toc = document.querySelector('.toc');
  if (!articulo || !toc) return;

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
