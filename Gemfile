# Solo para levantar el sitio en local con `bundle exec jekyll serve`.
# GitHub Pages no lee este archivo: construye el sitio con su propia versión
# fijada del bundle `github-pages`.
source "https://rubygems.org"

# github-pages trae Jekyll y TODOS los plugins permitidos (jekyll-feed,
# jekyll-sitemap y jekyll-seo-tag incluidos) en las mismas versiones exactas
# que corren en producción. No hay que declarar esos plugins por separado: si
# se declaran, bundler puede resolverlos a otra versión y el sitio local deja
# de ser igual al publicado, que es justo lo que este Gemfile evita.
# La lista de plugins activos se edita en `plugins:` dentro de _config.yml.
gem "github-pages", "~> 232", group: :jekyll_plugins

# Servidor local: Ruby 3.x ya no lo trae de fábrica y Jekyll lo necesita.
gem "webrick", "~> 1.8"
