# Protocolo de investigación: noticias y exportaciones colombianas de bienes

Este protocolo distingue un programa que funciona, una medición de texto válida y una señal con utilidad económica. Son tres resultados diferentes. Se fija para esta revisión antes de recibir los datos numéricos de la investigadora; no constituye una inscripción en un registro externo ni una validación ya realizada.

## Preguntas y contribución

1. ¿Con qué cobertura y errores puede construirse un corpus de noticias sobre exportaciones colombianas de bienes?
2. ¿Cómo se comportan un diccionario económico publicado y un modelo contextual en español frente a juicios humanos independientes sobre el tono del texto?
3. ¿Añaden las mediciones de noticias información para pronosticar exportaciones, más allá de sus valores históricos ya disponibles?

El aporte del proyecto es la adquisición documentada, la adaptación al dominio exportador, la evaluación de errores y la comparación temporal reproducible. No consiste en entrenar desde cero RoBERTuito ni en atribuirnos resultados de otros autores. La tercera pregunta puede dar un resultado negativo; no se modificará el período o el modelo para obtener una mejora deseada.

## Referencias y diferencias

[Dávila y Chasi, Banco Central del Ecuador](https://doi.org/10.47550/RCE/35.2.1) describen extracción mediante sitemaps de once medios, comparación entre métodos, un puntaje de probabilidades y evaluación humana. Se retoman la adquisición directa y la evaluación independiente. Los pesos y el preprocesamiento reutilizados proceden de [PySentimiento](https://github.com/pysentimiento/pysentimiento); no se obtuvieron los scripts completos del estudio ni una revisión exacta de su modelo. La fragmentación completa de artículos y la frecuencia mensual son decisiones de esta adaptación.

[Mora-Quiñones, Orozco-Gallo y Mora-Pérez, BE1340](https://doi.org/10.32468/be.1340) construyen sentimiento e incertidumbre léxicos y comparan modelos de actividad económica con y sin esas señales. La sección 6 combina factores dinámicos y ARMAX; la nota 10 aclara que emplean ARMAX porque las variables ya se hicieron estacionarias. Su objetivo es comprobar utilidad adicional en pronósticos, no solo dibujar noticias. Aquí se conservan el diccionario y las ecuaciones como mediciones separadas. La futura comparación sobre exportaciones será una adaptación más pequeña, sin afirmar que reproduce sus factores dinámicos, su corpus o sus resultados sobre ISE y PIB.

## Corpus y elección del período

La ventana de búsqueda inicial es marzo de 2020–octubre de 2026. Se recorren archivos declarados por los editores, se conservan los fallos y se verifican las fechas en cada artículo. La fecha lastmod del sitemap nunca sustituye datePublished. Los titulares o fragmentos de buscadores tampoco sustituyen el cuerpo.

La versión previa dependía de Google News para prensa histórica: 483 enlaces de 2020–2024 quedaron sin resolver y la búsqueda de 2025 no se intentó por esa vía. Analdex completaba un corpus institucional diferente. Esa limitación del recolector no prueba ausencia de noticias. La nueva recuperación directa conserva una trazabilidad separada.

Se computa por mes la cantidad de artículos elegibles de prensa, dominios, composición de fuentes y publicaciones institucionales. El panel principal usa la adquisición directa de Valora Analitik y La República durante toda la ventana; otros medios y Analdex son complementarios. La propuesta principal es la secuencia más larga de meses consecutivos con al menos tres artículos de prensa, una fuente cada mes y dos dominios en al menos 95% de los meses; en empate, la primera. Se conserva como sensibilidad la mayor ventana estricta de dos fuentes por mes, con mínimos de uno, tres y cinco artículos. Son umbrales operativos explícitos, no garantías de representatividad, calidad semántica o potencia estadística.

La decisión de permitir hasta 5% de meses con una sola fuente se fijó después de observar exclusivamente la cobertura: existen noticias en los 80 meses y dos fuentes en 78, con noviembre de 2020 y diciembre de 2024 como excepciones. Exigir dos fuentes en todos los meses cortaba el intervalo en 2024 aunque seguían existiendo noticias. Esta enmienda precede a la inspección de los valores del Excel recibido y a cualquier ajuste económico. No se trata un mes de una fuente como ausencia de noticias ni se interpola la fuente faltante. Los recuentos y proporciones de fuente se incorporarán como controles de cobertura y la ventana estricta seguirá visible.

No se recorta el período para mejorar el resultado del modelo. Si ningún intervalo suficientemente largo tiene apoyo de varias fuentes, se declara insuficiencia para la evaluación temporal. Un período corto todavía puede servir para evaluar clasificación de texto, pero no justifica ajustar modelos complejos de exportaciones.

Los dominios no equivalen necesariamente a grupos empresariales independientes. Las búsquedas por términos en URL omiten artículos relevantes con otros títulos; la deduplicación exacta no elimina toda sindicación ni todas las notas sobre un mismo acontecimiento. El corpus es un marco de búsqueda documentado, no un censo de noticias colombianas.

## Analdex, informes y disponibilidad de información

Analdex se identifica como fuente institucional. Sus publicaciones quedan separadas del corpus principal de prensa y disponibles para análisis de sensibilidad. No se decide el tipo de documento solo por quién lo publica: otros medios también repiten datos oficiales y Analdex también publica comentarios y expectativas.

Las reglas proponen cuatro categorías: informe estadístico, acontecimiento o expectativa, mixto y sin resolver. Para confirmar el tipo de documento se revisa el cuerpo, la fuente de las cifras y el período referido. Una regla que detecta «crecieron» o «DANE» no demuestra novedad informativa ni valor predictivo.

Ejemplo: una noticia de junio que informa las exportaciones de abril no puede utilizarse para anunciar que predijo esa misma cifra de abril. Puede describir información pasada o contribuir a un pronóstico posterior, pero debe compararse con un modelo que ya tenga acceso a esas cifras históricas. La revisión anotará el período estadístico, la comparación interanual/mensual/acumulada y, cuando pueda establecerse, la fecha del acontecimiento.

## Evaluación de texto independiente

Se preparará una muestra fijada de 200 textos recuperados y deduplicados, estratificada por año y dominio, que incluya propuestas de exclusión y revisión. Se excluyen los casos diagnósticos utilizados para diseñar reglas. La selección no consulta predicciones. Su alcance es el marco de noticias recuperadas; no estima la cobertura de toda la prensa.

Dos hojas iguales permiten que dos personas revisen independientemente antes de abrir las predicciones. Una tercera hoja registra la adjudicación humana posterior. Los campos no se rellenan automáticamente. Los pesos por estrato se conservan; un resumen sin ponderación describe este conjunto de evaluación, no toda la prensa, y la falta de respuestas puede introducir sesgos.

Las personas anotarán por separado: pertenencia al tema, tipo de documento, tono general, dirección del acontecimiento exportador y períodos de referencia. La dirección puede ser expansión, contracción, reanudación, restricción, sin cambio, mixta, incierta o no aplicable. No se usa «reanudar» como una regla para corregir a posteriori el sentimiento general.

La evaluación calculará exactitud, precisión y recall de pertinencia; matriz de confusión, métricas por clase y F1 macro del tono; cobertura y abstenciones del diccionario; acuerdo entre revisores; y Brier/ECE del modelo contextual cuando existan referencias humanas. Se documentarán tamaños por clase, faltantes y limitaciones de calibración. La probabilidad máxima nunca se interpreta como porcentaje comprobado de acierto. Las pruebas de software usan casos sintéticos identificados y no generan etiquetas para esta evaluación.

## Evaluación económica con los datos de la investigadora

El insumo principal será el total nacional mensual de exportaciones de bienes en dólares FOB, con mes de referencia, fuente, fecha de publicación y versión de las cifras. Los países y pesos físicos se conservarán como análisis posterior. El valor FOB es nominal: aumentos de precio y cambios de composición pueden aumentar el valor sin aumentar el volumen real. Sumar kilogramos de bienes distintos no crea automáticamente un índice de volumen.

El diseño compara cuatro especificaciones con error ARMA(1,1): historia numérica; historia más controles de cobertura (log(1+número de artículos) y proporción de Valora); esos controles más tono; y controles, tono e incertidumbre. Los controles se incorporan antes de ejecutar los ajustes económicos, por los cambios observados en composición de fuentes. Se usa la clase SARIMAX de [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html). El contraste principal del tono es contra la base con cobertura. Es un experimento acotado sobre exportaciones; no una réplica exacta del ARMAX con factores del Banco. La especificación se fija antes de observar los errores de prueba.

El objetivo será la variación interanual logarítmica del FOB: 100 × [log(FOB_t) − log(FOB_t−12)]. Se examinará estacionariedad y diagnóstico residual; transformar no garantiza que todos los supuestos se cumplan. En cada origen se estima con una ventana expansiva, mínimo 36 observaciones de crecimiento disponibles, y se reservan inicialmente doce meses de prueba. Esos mínimos son decisiones operativas, no una promesa de potencia suficiente.

La predicción del mes t se formula al cierre de t−1 y usa noticias como máximo de t−1. Las cifras numéricas cuya publicación o versión sea posterior al origen se ocultan antes de calcular crecimiento. Los valores faltantes no se convierten en ceros. Las transformaciones de regresores se estiman solo con la ventana de entrenamiento. Se comparan errores sobre los mismos orígenes exitosos y se conserva cada fallo de ajuste.

Se reportarán MAE, RMSE, sesgo, intervalos y diagnósticos de convergencia, autocorrelación residual y estacionariedad. Se examinarán sensibilidad a fuentes constantes y a la exclusión de candidatos a informe estadístico. Esta última sigue siendo una separación provisional hasta que existan etiquetas humanas. Una diferencia de errores con pocos meses no basta para afirmar superioridad estadística; la conclusión debe reconocer el tamaño y dependencia de la muestra.

Sin fechas de publicación no se reportará una simulación como si respetara la disponibilidad real. Si únicamente se dispone de cifras revisadas, una opción explícita permitirá una comparación retrospectiva, identificada como tal. La recuperación retrospectiva de páginas web tampoco demuestra que exactamente ese texto estuviera disponible en la fecha histórica: no se prometerá un ejercicio en tiempo real.

El archivo recibido contiene 309 meses, enero de 2001–septiembre de 2026, sin fechas de publicación ni versiones históricas. Antes de ejecutar los modelos se fija un escenario retrospectivo principal: disponibilidad supuesta al cierre del segundo mes posterior al período de referencia, y sensibilidades de uno y tres meses. Son supuestos de simulación, no fechas observadas ni reconstruidas. El CSV original conserva vacías las fechas desconocidas; la opción estricta sigue bloqueada. Se usan los valores actuales del libro, no versiones históricas. Tampoco se ha acreditado la disponibilidad del checkpoint del modelo lingüístico en cada origen histórico. Por ello no se interpretarán los errores como desempeño en tiempo real.

Antes de ajustar se fijan también correlaciones descriptivas entre tono del mes t y crecimiento FOB del mes t+h para h de −3 a +3, sin escoger el desfase que más favorezca al índice. Se repetirá la comparación excluyendo propuestas automáticas de informe estadístico o texto mixto, y manteniendo por separado cada uno de los dos medios. Estas separaciones no sustituyen la clasificación humana del tipo de documento. Los diagnósticos y los fallos se conservarán aunque no favorezcan al modelo.

Enmienda posterior al primer ajuste: los residuos de las cuatro especificaciones muestran autocorrelación y el ADF no rechaza raíz unitaria en sus entrenamientos. Se mantienen esos resultados, sin buscar otros órdenes sobre los doce meses de prueba. Se añaden dos comparadores diagnósticos sin ajuste: persistir el último crecimiento disponible y mantener el mismo FOB del año anterior (crecimiento cero). Esta adición responde a los diagnósticos observados; no estaba fijada antes del primer ajuste, no se presenta como confirmación independiente y no se elige un ganador por el menor error. Una revisión de la especificación requerirá otra separación temporal o nuevos datos de prueba.

## Qué constituye un resultado académico defendible

Un resultado debe poder rastrearse hasta su texto o dato, tener una definición estable y una evaluación apropiada. La coincidencia de una curva con una narración conocida no valida el clasificador. Una correlación positiva no demuestra causalidad ni utilidad incremental. Un modelo que no mejora al comparador puede ser un resultado válido si el experimento está bien documentado.

La entrega distinguirá siempre: implementación verificada, resultados descriptivos ejecutados, evaluación humana pendiente o realizada y evaluación económica pendiente o realizada. No se completarán etapas con resultados inventados para presentar el proyecto como terminado.
