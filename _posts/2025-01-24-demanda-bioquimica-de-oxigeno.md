---
layout: post
title: "Demanda Bioquímica de Oxígeno"
date: 2025-01-24
category: Agua
excerpt: "La DBO5 no cuantifica la masa orgánica total de un efluente, sino la dinámica con la que los microorganismos consumen oxígeno. Comprender este indicador como una simulación biológica es clave para evitar fallos catastróficos en ingeniería ambiental."
image: /assets/imagenes/demanda-bioquimica-de-oxigeno/esquema-digestion-dqo.jpg
permalink: /agua/2025/01/24/demanda-bioquimica-de-oxigeno.html
---

## El pulso de oxígeno en los ecosistemas acuáticos

En los ríos, lagos y estuarios del planeta, la salud del ecosistema depende de un delicado equilibrio gaseoso: la concentración de oxígeno disuelto. Cuando las actividades humanas descargan efluentes domésticos, agropecuarios e industriales en los cuerpos receptores, se introduce una masa diversa de materia orgánica. Este aporte desencadena una demanda masiva de oxígeno por parte de la biota acuática, provocando episodios severos de deoxigenación que amenazan la vida piscícola y alteran la dinámica biogeoquímica del recurso hídrico (Escobar, 2003; Kiely, 1999).

Para prevenir el colapso ecológico, la ingeniería enfrenta el desafío de medir cuánta contaminación orgánica contiene una muestra de agua. Sin embargo, cuantificar cada molécula de origen vegetal, animal o sintético resulta técnicamente inviable debido a la inmensa complejidad metabólica de la matriz líquida. Por esta razón, la disciplina adoptó una estrategia analítica indirecta: en lugar de medir la masa exacta de contaminantes orgánicos, se mide el volumen de oxígeno necesario para destruirlos o estabilizarlos (Giner et al., 2019; Tinoco et al., 2003).

De este enfoque surgen dos parámetros fundamentales: la **Demanda Bioquímica de Oxígeno (DBO)** y la **Demanda Química de Oxígeno (DQO)**. Aunque a menudo se citan juntas en expedientes normativos y diseños de plantas de tratamiento, interpretar estas métricas como números intercambiables constituye un grave error diagnóstico. La DBO y la DQO obedecen a principios operativos intrínsecamente distintos —una es la respiración de un ecosistema microbiano en el tiempo; la otra es una combustión química instantánea—. Comprender las fronteras conceptuales de cada una, para luego cruzar sus magnitudes, es la única vía rigurosa para evaluar la tratabilidad y el impacto ambiental de un vertimiento (Tinoco et al., 2003; Vargas Franco, 2007).


## El festín microbiano: la naturaleza biológica de la DBO

Para comprender la Demanda Bioquímica de Oxígeno sin perderse en la jerga de laboratorio, conviene visualizar un escenario cotidiano. Imagina que viertes una cantidad de alimento en un estanque cerrado donde habita una comunidad de bacterias. La DBO representa, sencillamente, la cantidad de oxígeno que esas bacterias necesitan "respirar" mientras devoran y digieren el alimento disponible. Si el agua contiene azúcares sencillos o materia fácilmente digerible, la actividad microbiana se intensificará y el consumo de oxígeno será elevado; si el agua está limpia, los microorganismos apenas consumirán oxígeno (Kiely, 1999; Madigan et al., 2015).

Desde el punto de vista formal, la DBO cuantifica el oxígeno disuelto consumido por microorganismos aerobios durante la estabilización bioquímica de la materia orgánica biodegradable a una temperatura y tiempo estandarizados (Giner et al., 2019). Para homologar los ensayos a nivel internacional, la metodología estándar estipula la incubación de la muestra en botellas herméticas de 300 mL mantenidas a 20 °C durante un período exacto de 5 días, parámetro denominado **\\(\text{DBO}_5\\)** (Giner et al., 2019; Kiely, 1999).

Sin embargo, los microorganismos no consumen toda la materia orgánica de manera instantánea ni uniforme. La descomposición bioquímica sigue una cinética de reacción de primer orden, donde la velocidad de degradación en cualquier instante es directamente proporcional a la concentración de materia orgánica remanente en la muestra (Metcalf et al., 1995). Matemáticamente, este fenómeno se expresa mediante la ecuación diferencial:

\\[ \frac{dL_t}{dt} = -k_e L_t \\]

Donde:
- **\\(L_t\\)**: concentración de materia orgánica biodegradable remanente en el tiempo \\(t\\), expresada en \\(\text{mg/L}\\) de oxígeno equivalente.
- **\\(k_e\\)**: constante cinética de degradación bioquímica en base neperiana (\\(\text{días}^{-1}\\)).
- **\\(t\\)**: tiempo transcurrido desde el inicio de la incubación (días).

Al integrar esta ecuación diferencial entre el instante inicial \\(t = 0\\) (donde la materia orgánica biodegradable total o DBO última es \\(L_0\\)) y un tiempo \\(t\\), se obtiene la concentración de materia orgánica que aún no ha sido degradada:

\\[ L_t = L_0 e^{-k_e t} \\]

Consecuentemente, la cantidad de oxígeno consumida o DBO ejercida hasta el instante \\(t\\), representada por \\(y_t\\), equivale a la diferencia entre la carga inicial y la remanente (Giner et al., 2019; Metcalf et al., 1995):

\\[ y_t = L_0 - L_t = L_0 (1 - e^{-k_e t}) \\]

En la práctica analítica, es habitual convertir la constante cinética de base neperiana (\\(k_e\\)) a base decimal (\\(K_{10}\\)) utilizando el factor de conversión logarítmico \\(\ln(10) \approx 2.303\\):

\\[ K_{10} = \frac{k_e}{2.303} \\]

A continuación se desarrolla la demostración numérica sustituida de la \\(\text{DBO}_5\\) para un efluente doméstico típico con una DBO última \\(L_0 = 300\ \text{mg/L}\\) y una constante cinética de degradación \\(k_e = 0.23\ \text{días}^{-1}\\) a 20 °C:

Paso 1: Conversión de la constante cinética a base decimal:<br>

\\(K_{10} = \frac{0.23\ \text{días}^{-1}}{2.303}\\)<br>
\\(K_{10} \approx 0.10\ \text{días}^{-1}\\)<br>

Paso 2: Evaluación de la fracción exponencial degradada a los 5 días:<br>

\\(e^{-k_e \cdot t} = e^{-0.23 \cdot 5} = e^{-1.15} \approx 0.3166\\)<br>

Paso 3: Cálculo de la DBO ejercida a los 5 días (\\(y_5\\)):<br>

\\(y_5 = 300\ \text{mg/L} \cdot (1 - 0.3166)\\)<br>
\\(y_5 = 300\ \text{mg/L} \cdot 0.6834\\)<br>
\\(y_5 = 205.02\ \text{mg/L}\\)

*Nota técnica:* La sustitución numérica evidencia que a los 5 días de incubación a 20 °C se satisface aproximadamente entre el 65% y el 70% de la demanda bioquímica total carbonácea (\\(L_0\\)). El 30% restante requiere un período de incubación extendido de hasta 20 o 20 días para alcanzar la estabilización completa (Giner et al., 2019).


<figure class="post-figure">
<img src="/assets/imagenes/demanda-bioquimica-de-oxigeno/cinetica-dbo-fases.jpg" alt="Curva cinética de consumo de oxígeno separada en fase carbonácea y nitrogenada" loading="lazy" decoding="async" width="658" height="368">
<figcaption>Figura 1. Separación analítica y temporal del consumo de oxígeno en la DBO carbonácea y la demanda nitrogenada a lo largo de 25 días. Fuente: Giner et al. (2019).</figcaption>
</figure>

Un aspecto biológico crucial radica en la bifurcación temporal de las poblaciones microbianas. Durante los primeros 5 días, el consumo de oxígeno es ejercido casi exclusivamente por bacterias heterótrofas que oxidan compuestos de carbono (fase carbonácea). A partir del quinto u octavo día, cuando la materia carbonada disminuye, proliferan las bacterias nitrificantes autótrofas (*Nitrosomonas* y *Nitrobacter*), las cuales consumen oxígeno para transformar el amonio en nitrito y nitrato (fase nitrogenada) (Giner et al., 2019). Por esta razón, el ensayo estandarizado a 5 días evita la interferencia de la demanda nitrogenada, aislando la fracción carbonácea fácilmente biodegradable.


## La combustión química severa: la naturaleza de la DQO

A diferencia del proceso biológico de la DBO, la **Demanda Química de Oxígeno (DQO)** no depende de la supervivencia ni del metabolismo de microorganismos. La DQO mide la cantidad total de oxígeno requerida para oxidar químicamente la materia orgánica presente en una muestra de agua mediante la acción de un agente oxidante fuerte bajo condiciones severas de acidez y temperatura (Vargas Franco, 2007).

Si la DBO es un festín microbiano de 5 días, la DQO equivale a una incineración química instantánea. En el procedimiento analítico estándar, la muestra se somete a una digestión por reflujo abierto o cerrado en presencia de dicromato de potasio (\\(\text{K}_2\text{Cr}_2\text{O}_7\\)) o permanganato de potasio (\\(\text{KMnO}_4\\)) en medio concentrado de ácido sulfúrico (\\(\text{H}_2\text{SO}_4\\)) a ebullición durante un tiempo controlado (Garay Tinoco et al., 2003). Bajo este tratamiento térmico y químico agresivo, prácticamente la totalidad de los compuestos orgánicos —tanto los biodegradables como los recalcitrantes o sintéticos— sufren una descomposición forzada hacia dióxido de carbono (\\(\text{CO}_2\\)) y agua (\\(\text{H}_2\text{O}\\)) (Garay Tinoco et al., 2003; Vargas Franco, 2007).

El siguiente diagrama de flujo ilustra la bifurcación metodológica y cinético-analítica entre la medición biológica y la destrucción química de la materia orgánica:

El siguiente diagrama de flujo ilustra la bifurcación metodológica y cinético-analítica entre la medición biológica y la destrucción química de la materia orgánica:

<div class="mermaid">
graph TD
    Muestra["Muestra de Agua Residual"] --> DBO_Branch["Ensayo Biológico: DBO"]
    Muestra --> DQO_Branch["Digestión Química: DQO"]

    subgraph R_DBO ["Vía Bioquímica<br>(5 días / 20 °C)"]
        DBO_Branch --> Het["Bacterias Heterótrofas (DBC)"]
        Het --> Fase1["Fase 1: Oxidación Carbonácea<br>(Días 0 a 5)"]
        Fase1 --> Nit["Bacterias Nitrificantes (DBN)"]
        Nit --> Fase2["Fase 2: Oxidación Nitrogenada<br>(Días 5 a 20)"]
    end

    subgraph R_DQO ["Vía Química Severa<br>(2 horas / Reflujo)"]
        DQO_Branch --> Oxidante["Oxidante Fuerte:<br>Dicromato / Permanganato + H2SO4"]
        Oxidante --> Digestion["Digestión Térmica a Ebullición<br>(10 - 120 min)"]
        Digestion --> Reacciones["Oxidación Total:<br>Biodegradable + Recalcitrante"]
    end

    Fase1 --> ResDBO["Lectura: DBO5<br>(Biodegradable)"]
    Fase2 --> FinDBO[Fin Ciclo Biológico]
    Reacciones --> ResDQO["Titulación / Fotometría:<br>DQO Total"]
</div>

<!-- Script necesario para que GitHub Pages dibuje el gráfico -->
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: true });
</script>

## El cruce conceptual: diagnóstico de tratabilidad y biodegradabilidad

Una vez comprendidos los fundamentos operacionales de la DBO y la DQO, el siguiente paso metodológico consiste en cruzar ambas variables. Evaluar la calidad de un efluente observando la DBO o la DQO de manera aislada equivale a leer únicamente la mitad de una sentencia analítica. Es en la brecha diferencial entre la oxidación bioquímica y la oxidación química donde la ingeniería ambiental encuentra el verdadero diagnóstico de tratabilidad de una muestra líquida (Tinoco et al., 2003; Vargas Franco, 2007).

Por definición estricta, para cualquier muestra hídrica se cumple invariablemente la relación \\(\text{DQO} \ge \text{DBO}\\). Esta disparidad radica en que el oxidante químico (dicromato o permanganato de potasio) destruye estructuras orgánicas complejas, celulosa, lignina y compuestos sintéticos que la maquinaria enzimática de las bacterias no puede descomponer en el lapso del ensayo biológico (Garay Tinoco et al., 2003; Vargas Franco, 2007). Cuanto mayor sea la distancia numérica entre la DQO y la DBO, mayor será la fracción de materia orgánica recalcitrante o inerte presente en el medio (Vargas Franco, 2007).

Para cuantificar esta propiedad, se utiliza el **cociente de biodegradabilidad**, definido como la relación \\(\text{DBO}_5/\text{DQO}\\). La interpretación de este índice establece tres escenarios operacionales fundamentales para el diseño de sistemas de depuración (Metcalf et al., 1995; Tinoco et al., 2003):

- **\\(\text{DBO}_5/\text{DQO} \ge 0.6\\) (Efluente altamente biodegradable):** Predomina la materia orgánica soluble y fácilmente asimilable (característica de vertimientos domésticos, de la industria azucarera o cervecera). El efluente es idóneo para ser tratado mediante reactores biológicos convencionales, como lodos activados, filtros biológicos o humedales artificiales (Escobar, 2003; Giner et al., 2019).
- **\\(0.2 < \text{DBO}_5/\text{DQO} < 0.5\\) (Biodegradabilidad moderada):** Existe un equilibrio entre compuestos degradables y material de lenta descomposición (frecuente en efluentes industriales mixtos). Requiere tiempos de retención hidráulica prolongados o la aclimatación específica de las poblaciones microbianas (Metcalf et al., 1995; Velasquez y Calderon, 2018).
- **\\(\text{DBO}_5/\text{DQO} \le 0.2\\) (Efluente recalcitrante o inhibido):** La materia orgánica es predominantemente inerte a la acción microbiana, o bien existen sustancias tóxicas que inactivan la biota del ensayo. En este escenario, los tratamientos biológicos resultan ineficaces, siendo obligatorio recurrir a Fisicoquímica avanzada o Procesos de Oxidación Avanzada (POA) (Tinoco et al., 2003).

Existe una patología analítica crítica que ilustra la necesidad imperiosa de cruzar ambos parámetros: el **envenenamiento biológico de la muestra**. Si un efluente industrial contiene metales pesados, cianuro, fenoles o plaguicidas, estos compuestos destruyen la población microbiana dentro de la botella de incubación. Como consecuencia, el consumo de oxígeno biológico será nulo (\\(\text{DBO}_5 \approx 0\ \text{mg/L}\\)). Un analista desprevenido podría interpretar falsamente que el efluente está "libre de contaminación". Sin embargo, al ejecutar la DQO en paralelo, el reactivo químico digerirá la carga orgánica total, revelando valores de cientos o miles de miligramos por litro. Esta disparidad extrema (\\(\text{DBO}_5 \approx 0\\) frente a una \\(\text{DQO}\\) elevada) no indica agua limpia, sino **toxicidad aguda** que impide la medición biológica (Tinoco et al., 2003).

### La demanda teórica de oxígeno en sistemas anaerobios

El cruce conceptual entre masa orgánica y consumo de oxígeno se manifiesta también en las transformaciones anaerobias. Cuando la materia orgánica se degrada en ausencia de oxígeno (como en digestores de lodos o reactores UASB), la demanda de oxígeno no desaparece: se transfiere energéticamente al gas metano (\\(\text{CH}_4\\)) generado (Metcalf et al., 1995; Selena-Mesías et al., 2013).

A continuación se desarrolla la demostración estequiométrica sustituida paso a paso para la conversión teórica de glucosa (\\(\text{C}\_6\text{H}\_{12}\text{O}\_6\\)) a metano y su posterior demanda equivalente de oxígeno en fase aerobia:

Paso 1: Estequiometría de la fermentación metanogénica de la glucosa:
<br>
\\[ \text{C}\_6\text{H}\_{12}\text{O}\_6 \rightarrow 3\text{CO}\_2 + 3\text{CH}\_4 \\]<br>
Masa molar de glucosa (\\(\text{C}\_6\text{H}\_{12}\text{O}\_6\\)) = \\(6 \cdot 12 + 12 \cdot 1 + 6 \cdot 16 = 180\ \text{g/mol}\\)<br>
Masa de metano producido (\\(3\text{CH}\_4\\)) = \\(3 \cdot (12 + 4 \cdot 1) = 48\ \text{g}\\)<br>

Paso 2: Estequiometría de la combustión/oxidación del metano producido:
<br>
\\[ 3\text{CH}\_4 + 6\text{O}\_2 \rightarrow 3\text{CO}\_2 + 6\text{H}\_2\text{O} \\]<br>
Masa de oxígeno requerida (\\(6\text{O}\_2\\)) = \\(6 \cdot (2 \cdot 16) = 192\ \text{g}\\)<br>

Paso 3: Relación de conversión de biogás a demanda de oxígeno equivalente:
<br>
\\[ \text{Relación} = \frac{192\ \text{g O}\_2}{180\ \text{g glucosa}} \approx 1.067\ \text{g O}\_2 / \text{g glucosa} \\]

*Nota técnica:* La sustitución numérica demuestra que por cada \\(180\ \text{g}\\) de glucosa digerida anaeróbicamente se generan \\(48\ \text{g}\\) de metano, los cuales retienen un potencial de consumo de oxígeno equivalente de \\(192\ \text{g}\\) de \\(\text{O}\_2\\). Esto confirma que el metano generado en reactores anaeróbicos representa masa de DBO/DQO removida de la fase líquida y transferida a la fase gaseosa como recurso energético (Metcalf et al., 1995; Selena-Mesías et al., 2013).


## Evaluación de campo y contraste con los Estándares de Calidad Ambiental (ECA-Agua)

Para llevar estas herramientas analíticas al terreno práctico, es necesario examinar datos de monitoreo real en cuerpos hídricos y contrastarlos frente a los marcos regulatorios. En el contexto peruano, el Decreto Supremo N.° 004-2017-MINAM establece los Estándares de Calidad Ambiental (ECA) para Agua, fijando límites máximos de DBO5 y DQO según la categoría y uso asignado al cuerpo receptor (Ministerio del Ambiente, 2017).

La siguiente tabla organiza los datos de monitoreo en diez estaciones de control (CA-1 a CA-6 y MuAs-7 a MuAs-10) reportados en la literatura del dosier, evaluando de forma integrada la DBO5, la DQO y el cociente de biodegradabilidad frente a los umbrales de la Categoría 1 A1 (Agua potable con tratamiento desinfectante) y Categoría 3 D1/D2 (Riego de vegetales y bebida de animales) (Geología y Desarrollo Ambiental S.A.C., 2019; Ministerio del Ambiente, 2017):

| Estación de Monitoreo | \\(\text{DBO}_5\\) (mg/L) | \\(\text{DQO}\\) (mg/L) | Cociente \\(\text{DBO}_5/\text{DQO}\\) | Cumplimiento ECA 1 A1 (\\(\text{DBO}_5 \le 3\\) / \\(\text{DQO} \le 10\\)) | Cumplimiento ECA 3 D1/D2 (\\(\text{DBO}_5 \le 15\\) / \\(\text{DQO} \le 40\\)) | Diagnóstico de Tratabilidad y Matriz |
| :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **CA-1** | 0.60 | 26.50 | 0.023 | Alerta (DQO supera límite) | Conforme | Inerte / Recalcitrante alto |
| **CA-2** | 0.60 | 13.10 | 0.046 | Alerta (DQO supera límite) | Conforme | Recalcitrante / Lenta degradación |
| **CA-3** | 0.60 | 14.90 | 0.040 | Alerta (DQO supera límite) | Conforme | Recalcitrante / Lenta degradación |
| **CA-4** | 0.60 | 25.30 | 0.024 | Alerta (DQO supera límite) | Conforme | Inerte / Recalcitrante alto |
| **CA-5** | 0.60 | 17.80 | 0.034 | Alerta (DQO supera límite) | Conforme | Recalcitrante / Lenta degradación |
| **CA-6** | 0.60 | 38.20 | 0.016 | Alerta (DQO supera límite crítico) | Conforme (próximo al techo de 40) | Altamente recalcitrante / Riesgo de descarga |
| **MuAs-7** | 2.60 | 8.20 | 0.317 | Conforme en ambos parámetros | Conforme | Biodegradabilidad moderada |
| **MuAs-8** | 2.60 | 4.50 | 0.578 | Conforme en ambos parámetros | Conforme | Biodegradabilidad alta |
| **MuAs-9** | 2.60 | 4.50 | 0.578 | Conforme en ambos parámetros | Conforme | Biodegradabilidad alta |
| **MuAs-10** | 2.60 | 4.50 | 0.578 | Conforme en ambos parámetros | Conforme | Biodegradabilidad alta |

<figure class="post-figure">
<img src="/assets/imagenes/demanda-bioquimica-de-oxigeno/dbo-dbo-estaciones-eca.jpg" alt="Gráfico de barras comparativo de DQO por estaciones frente a los límites de ECA Agua" loading="lazy" decoding="async" width="892" height="412">
<figcaption>Figura 2. Concentraciones de DBO5 medidas en estaciones de monitoreo superficial frente a los umbrales normativos ECA-Agua Categorías 1 y 3. Fuente: Geología y Desarrollo Ambiental S.A.C. (2019).</figcaption>
</figure>

<figure class="post-figure">
<img src="/assets/imagenes/demanda-bioquimica-de-oxigeno/dqo-dbo-estaciones-eca.jpg" alt="Gráfico de barras comparativo de DQO por estaciones frente a los límites de ECA Agua" loading="lazy" decoding="async" width="892" height="422">
<figcaption>Figura 3. Concentraciones de DQO medidas en estaciones de monitoreo superficial frente a los umbrales normativos ECA-Agua Categorías 1 y 3. Fuente: Geología y Desarrollo Ambiental S.A.C. (2019).</figcaption>
</figure>

El análisis de la matriz de datos revela un comportamiento hidroquímico revelador. Si la autoridad ambiental evaluara las estaciones CA-1 a CA-6 utilizando únicamente la \\(\text{DBO}_5\\) (con un valor constante y bajo de \\(0.60\ \text{mg/L}\\)), concluiría apresuradamente que el cuerpo hídrico cumple de forma holgada los Estándares de Calidad Ambiental para potabilización directa (ECA 1 A1) (Geología y Desarrollo Ambiental S.A.C., 2019). 

Sin embargo, al observar la DQO en el mismo bloque de estaciones (que oscila entre \\(13.10\ \text{mg/L}\\) y \\(38.20\ \text{mg/L}\\)), se evidencia que todas superan el límite de \\(10\ \text{mg/L}\\) estipulado para la Categoría 1 A1, alcanzando en CA-6 un valor crítico de \\(38.20\ \text{mg/L}\\), rozando el umbral de contaminación agrícola (ECA 3) (Geología y Desarrollo Ambiental S.A.C., 2019; Ministerio del Ambiente, 2017). Los cocientes de biodegradabilidad extremadamente bajos en la serie CA (\\(\text{DBO}_5/\text{DQO} < 0.05\\)) demuestran la presencia de aportes orgánicos no biodegradables o sustancias químicas resistentes, cuya identificación habría sido totalmente omitida sin el análisis pareado de la DQO (Tinoco et al., 2003; Vargas Franco, 2007).

Por el contrario, el grupo de estaciones MuAs-7 a MuAs-10 muestra una dinámica opuesta: valores moderados de \\(\text{DBO}_5\\) (\\(2.60\ \text{mg/L}\\)) combinados con niveles muy bajos de DQO (\\(4.50\ \text{mg/L}\\) a \\(8.20\ \text{mg/L}\\)). El cociente \\(\text{DBO}_5/\text{DQO}\\) cercano a \\(0.58\\) confirma que la carga orgánica en estos puntos es de origen biológico natural o doméstico fácilmente degradable, garantizando el cumplimiento integral de los estándares de potabilización (Geología y Desarrollo Ambiental S.A.C., 2019; Kiely, 1999).


## La ilusión de la estandarización: una reflexión sobre la mensurabilidad ambiental

El desarrollo de la \\(\text{DBO}_5\\) como estándar global esconde un capítulo curioso de la historia de la ciencia y la tecnología. A finales del siglo XIX, la *Royal Commission on Sewage Disposal* del Reino Unido buscaba un parámetro para regular los vertimientos en los ríos británicos. Tras observar que el tiempo promedio de tránsito de las aguas continentales desde sus fuentes hasta desembocar en el mar era de aproximadamente 5 días, y que la temperatura media de los cauces ingleses en verano rondaba los 20 °C, la comisión adoptó la convención de incubar la muestra durante 5 días a 20 °C (Kiely, 1999; Metcalf et al., 1995).

Este dato histórico pone de manifiesto una paradoja de la ingeniería moderna: una decisión regulatoria tomada en función de la geografía e hidrología de las Islas Británicas del siglo XIX se convirtió en una métrica rígida universal utilizada hoy en ríos tropicales, desiertos y cuencas altoandinas.


<figure class="post-figure">
<img src="/assets/imagenes/demanda-bioquimica-de-oxigeno/esquema-digestion-dqo.jpg" alt="Diagrama de flujo del procedimiento analítico de digestión por reflujo para DQO" loading="lazy" decoding="async" width="730" height="466">
<figcaption>Figura 4. Diagrama de flujo estandarizado para la digestión por reflujo, adición de reactivos oxidantes y valoración volumétrica. Fuente: Garay Tinoco et al. (2003).</figcaption>
</figure>

En las ciencias ambientales opera con frecuencia un fenómeno conceptual conocido como **reduccionismo analítico**: la suposición de que un sistema ecológico complejo, dinámico y no lineal puede resumirse por completo en un número producido en un frasco de vidrio (Madigan et al., 2015; Tinoco et al., 2003). Cuando la gestión ambiental se vuelve obsesiva hacia el indicador (cumplir la cifra de \\(30\ \text{mg/L}\\) en el tubo de salida), corre el riesgo de caer en la *Ley de Campbell*: cuando un indicador cuantitativo se convierte en el único objetivo de las decisiones políticas o de ingeniería, se corrompen los procesos que se pretende monitorear. Una planta de tratamiento puede diseñar un sistema que precipite químicamente los sólidos para reducir la DBO del efluente, transfiriendo la carga contaminante hacia un volumen masivo de lodos peligrosos que terminarán contaminando el suelo (Giner et al., 2019).

Medir el agua no es simplemente leer un instrumento; es interpretar la interacción entre la química sintética, el metabolismo microbiano y la capacidad de resiliencia del ecosistema. Reconocer los límites metodológicos de la DBO y la DQO es el primer paso para transitar de una ingeniería reactiva de cumplimiento de papel a una biotecnología ambiental de diagnóstico real (Garay Tinoco et al., 2003; Madigan et al., 2015).


## Cierre y síntesis integradora

La Demanda Bioquímica de Oxígeno y la Demanda Química de Oxígeno no deben concebirse como parámetros aislados en una matriz de calidad hídrica. La DBO evalúa la respuesta respiratoria del ecosistema microbiano ante sustancias degradables en un intervalo cinético; la DQO cuantifica la masa de materia oxidable mediante una agresión química severa.

Sostener una postura rigurosa en ingeniería ambiental exige abandonar la práctica errónea de utilizar la DBO como sustituto automático de la carga orgánica total. La evaluación integral de un efluente y la protección efectiva de los cuerpos receptores requieren interpretar de forma conjunta la cinética de degradación, la velocidad analítica y el cociente de biodegradabilidad \\(\text{DBO}_5/\text{DQO}\\). Solo a través de este diagnóstico pareado es posible diseñar plantas de tratamiento eficientes, detectar la presencia de sustancias tóxicas y garantizar la sostenibilidad del recurso hídrico ante la presión antropogénica.

---

## Referencias

- Asociación Argentina de Ingeniería Sanitaria y Ciencias del Ambiente (AIDIS Argentina). (2013). *Ingeniería Sanitaria y Ambiental*. Buenos Aires: AIDIS Argentina.
- Autoridad Nacional del Agua (ANA). (2016). *Protocolo Nacional para el Monitoreo de la Calidad de los Recursos Hídricos Superficiales (Resolución Jefatural Nº 010-2016-ANA)*. San Isidro: Autoridad Nacional del Agua.
- Autoridad Nacional del Agua (ANA). (2018). *Metodología para la determinación del índice de calidad de agua ICA-PE, aplicado a los cuerpos de agua continentales superficiales*. Autoridad Nacional del Agua.
- Escobar, J. (2003). *La contaminación de los ríos y sus efectos en las áreas costeras y el mar*. Naciones Unidas.
- Garay Tinoco, J., Ramírez T., G., y Betancourt P., J. M. (2003). *Manual de técnicas analíticas para la determinación de parámetros fisicoquímicos y contaminantes marinos (Aguas, sedimentos y organismos)*. Instituto de Investigaciones Marinas y Costeras (INVEMAR).
- Geología y Desarrollo Ambiental S.A.C. (2019). *Segunda modificatoria de la declaración de impacto ambiental del proyecto de exploración minera Palcawanka - Categoría I: capítulo III - línea base*. Lima: Consorcio Minero Palcawanka S.A.C.
- Giner, G. F. de, Torres Parra, M., Buroz, E., y Lairet, R. (Eds.). (2019). *Fundamentos de ingeniería ambiental*. Academia Nacional de la Ingeniería y el Hábitat (ANIH).
- Kiely, G. (1999). *Ingeniería Ambiental: Fundamentos, entornos, tecnologías y sistemas de gestión* (Vol. 1). McGraw-Hill.
- Loose, D. (2015). *Diagnóstico de las plantas de tratamiento de aguas residuales en el ámbito de operación de las Entidades Prestadoras de Servicios de Saneamiento*. SUNASS / GIZ.
- Madigan, M. T., Martinko, J. M., Bender, K. S., Buckley, D. H., y Stahl, D. A. (2015). *Brock. Biología de los microorganismos* (14.ª ed.). Pearson Educación.
- Metcalf & Eddy, Inc. (1995). *Ingeniería de aguas residuales: tratamiento, vertido y reutilización* (G. Tchobanoglous y F. L. Burton, Revs.; 3.ª ed., Vol. 1). McGraw-Hill / Interamericana de España, S. A.
- Ministerio del Ambiente. (2017). *Decreto Supremo N.° 004-2017-MINAM: Aprueban Estándares de Calidad Ambiental (ECA) para Agua y establecen Disposiciones Complementarias*. Lima: MINAM.
- Selena-Mesías, D., Solís-Salas, N., y Peñafiel-Ayala, R. (2013). Análisis de los sistemas anaeróbicos para la purificación lixiviados de rellenos sanitarios y la generación de energía renovable: reactores UASB, sistemas anammox y bioceldas. *Investigación y Desarrollo*, 15(1), 148–165.
- Vargas Franco, V. (2007). *Estadística descriptiva para ingeniería ambiental con SPSS*. Editora Viviana Vargas Franco.
- Velasquez, W. A. H., y Calderon, A. Z. R. (2018). *Implementación de biofiltro como agente depurador de aguas residuales del conjunto Aranjuez II, en el municipio de Villavicencio Meta* [Tesis de maestría, Universidad Cooperativa de Colombia].

---

## Preguntas / Vacíos del conocimiento

- ¿De qué manera la presencia creciente de contaminantes emergentes (microplásticos, fármacos y disruptores endocrinos) altera la constante cinética de degradación \\(k_e\\) en ensayos de DBO de efluentes urbanos, y qué sesgos introduce en el diseño cinético de bioreactores?
- Si la convención de incubación a 5 días y 20 °C fue formulada para la hidrología templada europea, ¿cuál es el margen de error diagnóstico al aplicar este mismo estándar en ecosistemas tropicales o de alta montaña sin ajustar térmicamente el modelo cinético?
- ¿Podrían los biosensores enzimáticos y las técnicas de espectroscopía de fluorescencia reemplazar a corto plazo la prueba tradicional de la DQO con dicromato de potasio, eliminando la generación de residuos tóxicos de cromo y mercurio en los laboratorios ambientales?
- En efluentes industriales con alta salinidad o presencia de halógenos, ¿hasta qué punto las interferencias por cloruros distorsionan la lectura de la DQO y de qué manera podrían escalarse bioprocesos extremófilos como oportunidad de tratamiento aplicado?