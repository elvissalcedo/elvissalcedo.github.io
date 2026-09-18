---
layout: post
title: "[Ejemplo] Calidad del agua en cuencas urbanas: qué mide realmente un ICA"
date: 2026-09-17
category: Agua
excerpt: "Página de ejemplo -- prueba real de que las fórmulas LaTeX de NotebookLM (con el backslash duplicado en los delimitadores) sobreviven el parser de kramdown. No es contenido real todavía."
permalink: /articulo-ejemplo.html
hidden: true
sitemap: false
draft: true
---
Un Índice de Calidad del Agua (ICA) resume, en un solo número, el estado de varios parámetros fisicoquímicos y biológicos de un cuerpo de agua. Es útil para comunicar, pero es fácil malinterpretarlo si no se entiende qué hay detrás del número.

<div class="callout">
<p><strong>Nota:</strong> este es contenido de ejemplo, escrito como Markdown plano -- igual al que entrega NotebookLM -- para probar la migración a Jekyll/kramdown. No reemplaza al artículo real.</p>
</div>

## Qué parámetros entran en el cálculo

La mayoría de los ICA combinan oxígeno disuelto, pH, demanda bioquímica de oxígeno, temperatura, turbidez, sólidos totales, nitratos y fosfatos, entre otros -- cada uno con un peso distinto según la metodología que se use.

## Cómo se combina todo en un solo número

Cada parámetro se normaliza a una escala común (por ejemplo 0-100) y luego se agregan con un promedio ponderado o geométrico. Cada subíndice \\(q_i\\) depende de su propia curva de calidad, no de una escala lineal simple -- por eso dos ríos con el "mismo" ICA pueden tener problemas muy distintos.

## Prueba técnica: figura con pie de foto

Esta figura no ilustra nada del ICA -- es solo para validar que el formato estándar `<figure class="post-figure">`/`<figcaption>` (mismo bloque que va a pegar Elvis en cada imagen real de cada artículo) se ve bien corriendo por el pipeline real de Jekyll/kramdown, no solo en un mockup.

<figure class="post-figure">
<img src="/assets/og-cover.jpg" alt="Imagen de prueba, sin relación con el contenido del artículo">
<figcaption>Figura 1. Imagen de prueba para validar el formato figure/figcaption. Fuente: banco de pruebas interno.</figcaption>
</figure>

## Prueba técnica: fórmula en bloque y notación suelta

Esta sección no es parte del artículo de ICA -- es el mismo caso de prueba de siempre (aceleración de frenado de una partícula por arrastre del aire), reutilizado acá tal como lo entregaría NotebookLM: Markdown plano con LaTeX real, sin HTML.

\\[ a = \frac{1.5 \cdot C_d \cdot \rho_{aire} \cdot V^2}{2 \cdot D_D \cdot \rho_D} \\]

**Donde:**

- **\\(a\\)**: aceleración de frenado de la partícula (m/s²).
- **\\(C_d\\)**: coeficiente de arrastre adimensional, tomado como 0.7.
- **\\(\rho_{aire}\\)**: densidad del aire (kg/m³).
- **\\(V\\)**: velocidad relativa de la partícula (m/s).
- **\\(D_D\\)**: diámetro de la partícula (m).
- **\\(\rho_D\\)**: densidad de la partícula (kg/m³).

El número de Reynolds, \\( Re = \dfrac{\rho \, v \, D}{\mu} \\), determina si un flujo es laminar o turbulento -- y cada subíndice como \\( q_i \\) o \\( PM_{10} \\) debe verse como texto matemático real. Si este párrafo se ve mal en el sitio publicado (paréntesis sueltos en vez de fórmulas), es que el backslash duplicado se perdió en algún paso de la migración.
