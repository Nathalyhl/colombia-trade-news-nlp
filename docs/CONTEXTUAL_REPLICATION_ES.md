# Adaptación de código público a noticias de exportaciones colombianas

## Referencia elegida y alcance

Se seleccionó el modelo de sentimiento en español de [PySentimiento](https://github.com/pysentimiento/pysentimiento), desarrollado por Juan Manuel Pérez y colaboradores, con el checkpoint público [RoBERTuito para análisis de sentimiento](https://huggingface.co/pysentimiento/robertuito-sentiment-analysis). El código y los modelos originales mantienen sus créditos y restricciones de uso científico y no comercial.

Existe una aplicación cercana a nuestro problema: Dávila y Chasi, *Índice de sentimiento económico*, publicada por el [Banco Central del Ecuador](https://doi.org/10.47550/RCE/35.2.1), utiliza PySentimiento en noticias económicas en español. Esa publicación motiva la comparación; sus resultados de validación no son resultados de este proyecto. En la página consultada no se encontró un repositorio de sus scripts ni una revisión exacta del modelo que permita reproducir íntegramente su experimento.

También se revisó [FiGASR](https://github.com/lucabarbaglia/FiGASR), que identifica sentimiento asociado a aspectos económicos, pero su implementación publicada está orientada al inglés. Cambiar únicamente sus palabras clave no la convertiría en un método validado para español. Por ello se eligió un modelo que ya procesa español para esta primera adaptación.

No se encontró código original del estudio BE1340 en el registro oficial consultado. La medición por diccionario que ya implementamos sigue siendo una reproducción de las reglas publicadas, con decisiones operativas documentadas. La nueva comparación con RoBERTuito es un método adicional y diferente.

## Qué se reutiliza y qué se adapta

Se reutilizan los pesos del modelo publicado y el preprocesamiento original de PySentimiento. El repositorio incluye una copia identificada de ese preprocesamiento y su aviso de licencia. El clasificador se ejecuta localmente: los artículos no se envían a un servicio de inferencia. Los pesos no se redistribuyen dentro del repositorio.

El código original establece un máximo de 128 tokens por entrada. Pasarle un artículo largo directamente puede dejar fuera su parte final. Nuestra adaptación divide el texto completo, después del preprocesamiento original, en fragmentos consecutivos y sin superposición que caben en ese límite. Cada fragmento incluye los tokens especiales requeridos por el modelo. Se verifican la longitud máxima y la conservación de todos los tokens de contenido.

Para cada fragmento se obtienen probabilidades de las clases negativa, neutra y positiva. Se combinan mediante un promedio ponderado por el número de tokens de contenido de cada fragmento. Esta combinación es una decisión propia de adaptación a artículos largos; no se atribuye a los autores del modelo ni se presenta como el procedimiento exacto del estudio ecuatoriano.

Los titulares se procesan por separado. Comparar un titular con un artículo completo responde a preguntas diferentes: una noticia puede anunciar una reactivación y, en el cuerpo, describir antecedentes de suspensión y conflicto. El tablero conserva esa distinción.

## Cómo se calcula la nueva serie

Para cada artículo se obtiene:

`puntaje = probabilidad_positiva − probabilidad_negativa`

La etiqueta corresponde a la clase con mayor probabilidad. Una etiqueta neutra puede coexistir con un puntaje ligeramente distinto de cero: la clase neutra puede ser la más probable sin que las probabilidades positiva y negativa sean idénticas. La probabilidad máxima no es una medida comprobada de precisión ni de certeza.

La nueva serie mensual es el promedio de los puntajes de los artículos del mes. Se muestra también una comparación restringida a artículos con coincidencias en el diccionario, para examinar la influencia de su cobertura. Los meses sin artículos permanecen sin estimación. No se añaden noticias, no se interpolan meses y no se normaliza con información futura para obtener una curva visualmente deseada.

Este cálculo no equivale a la fórmula del Banco de la República, que agrupa ocurrencias de palabras positivas y negativas antes de dividir. Ambas series se identifican por su método. El índice de incertidumbre económica del Banco conserva su propia definición; no se sustituye por la entropía o la confianza del clasificador.

## Qué permite mostrar al profesor

La muestra permite inspeccionar una adaptación reproducible de un modelo publicado, compararla con un método léxico, comprobar cómo se manejan artículos largos y rastrear cada predicción hasta su texto, fecha y versión de modelo. El código de adquisición, la selección del corpus y la adaptación a exportaciones son trabajo del proyecto; el modelo preentrenado y el preprocesamiento reutilizado conservan sus autores originales.

Los resultados de ambos métodos son predicciones o medidas automáticas. Un desacuerdo entre ellos no demuestra cuál es correcto. Para evaluar precisión se necesitan juicios independientes sobre nuestras noticias. Tampoco se presume que el nuevo modelo identifique la dirección de las exportaciones: fue entrenado con mensajes de Twitter en español, no específicamente con noticias de exportaciones colombianas.

Los informes que repiten cifras oficiales, la dependencia histórica de Analdex y la escasa cobertura por destino siguen siendo asuntos de selección y validación de datos. Cambiar el clasificador no resuelve esos problemas por sí solo. El contraste con cifras numéricas se realizará cuando la investigadora suministre los datos, respetando períodos de referencia y fechas de disponibilidad.

## Reproducción y validación pendientes

Las probabilidades guardadas, sus agregados mensuales y sus vínculos con el corpus pueden comprobarse sin instalar el modelo. Repetir la inferencia requiere el entorno opcional, los pesos públicos de la revisión fijada y el archivo local de artículos. Las versiones, hashes y fechas de la ejecución quedan registrados.

El siguiente paso empírico es revisar la muestra de 60 artículos sin mirar previamente las predicciones, registrar discrepancias y establecer después un conjunto de evaluación independiente. Se deben comparar precisión por clase, abstenciones del diccionario y errores por tipo de documento. No se atribuirán al proyecto porcentajes de precisión publicados por otros autores ni se presentarán coincidencias entre modelos como validación humana.
