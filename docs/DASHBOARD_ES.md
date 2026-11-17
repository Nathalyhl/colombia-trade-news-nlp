# Cómo leer el tablero de exportaciones

El tablero responde primero una pregunta descriptiva: ¿cómo cambia el lenguaje de las noticias sobre exportaciones colombianas de bienes? Su versión 0.9 reúne los resultados existentes en tres pestañas, sin cambiar las noticias, las predicciones, el diccionario ni las etiquetas humanas. El período de publicación sigue siendo marzo de 2020–octubre de 2026.

## 1. Resultados

La primera gráfica usa las predicciones guardadas de PySentimiento/RoBERTuito: para cada artículo, P(positivo) menos P(negativo), y después la media de los artículos de cada mes. La clase neutra puede ser la más probable aunque ese balance sea ligeramente positivo o negativo. Esta serie describe tono textual, no la dirección del acontecimiento exportador.

La segunda gráfica conserva el índice léxico de incertidumbre de BE1340: 1.000 veces las seis formas de incertidumbre divididas por las palabras retenidas. No es entropía, baja confianza del clasificador, riesgo comercial medido ni volatilidad del sentimiento.

Las dos mediciones se presentan por separado. No se inventa una combinación entre sus escalas. Los puntos son valores mensuales; la media móvil requiere el mes actual y los dos anteriores con valores válidos. La alineación hacia atrás es una decisión propia: la Figura 3 del Banco indica media móvil trimestral sin precisar esa alineación. Los meses vacíos permanecen vacíos.

La cobertura y la comparación manteniendo Analdex como fuente están en un desplegable. Son necesarias para interpretar la serie: los artículos elegibles de 2020–2025 proceden únicamente de Analdex y en 2026 se incorporan otros medios. La muestra no es un censo representativo de la prensa.

## 2. Noticias y destinos

Una sola búsqueda y un selector de país llevan a las noticias originales. Los vínculos de destino propuestos requieren evidencia relacional en el titular; mencionar un país no basta. Los nombres traducidos al español son etiquetas de presentación: los identificadores internos permanecen iguales.

Cada artículo muestra la clasificación del titular y del cuerpo por separado. En el caso de DW sobre reactivación de exportaciones de carbón a Israel, ambas clases del modelo son neutras; el balance es positivo en el titular y negativo en el cuerpo. El diccionario depende de una sola coincidencia negativa, «suspensión». Ninguno de esos resultados demuestra que reanudar exportaciones sea económicamente desfavorable. La explicación ilustrativa no se registra como etiqueta humana ni corrige automáticamente las predicciones.

El resumen por país es opcional y expone las observaciones mensuales y su soporte. Estados Unidos, por ejemplo, tiene 13 noticias repartidas en cinco meses aislados de esta muestra. No se dibuja una media móvil de tres meses si no existe una ventana completa. El tono se calcula sobre el artículo completo, no sobre frases específicas de cada país. Los recuentos de noticias no son valores ni participaciones de exportación.

El mes de publicación y el período estadístico narrado son variables distintas. Una noticia publicada en 2026 puede comparar con 2025. Todavía falta anotar sistemáticamente el período narrado y si la variación es interanual, mensual o acumulada.

## 3. Metodología y validación

Se distinguen explícitamente estas contribuciones:

| Referencia | Qué se recoge | Qué no se afirma |
| --- | --- | --- |
| [Dávila y Chasi, Banco Central del Ecuador](https://doi.org/10.47550/RCE/35.2.1) | Uso de sentimiento en español, balance de probabilidades y evaluación con noticias anotadas | No se obtuvieron los scripts originales ni una revisión exacta de su modelo; sus porcentajes de precisión no son nuestros resultados |
| [Mora-Quiñones, Orozco-Gallo y Mora-Pérez, BE1340](https://doi.org/10.32468/be.1340) | Diccionario publicado, limpieza descrita, conteos mensuales de sentimiento e incertidumbre y trazabilidad | No se reprodujeron su corpus curado ni su validación econométrica; el tokenizador, las stopwords congeladas y la alineación móvil son decisiones documentadas |
| [PySentimiento](https://github.com/pysentimiento/pysentimiento) | Pesos públicos y preprocesamiento original identificado, con sus créditos | No es un modelo entrenado por este proyecto ni validado en exportaciones colombianas; se conservan condiciones científicas/no comerciales y las de sus datos |
| Este proyecto | Corpus de exportaciones de bienes, fragmentación de artículos completos, agregación mensual y exploración por países | No se transforma automáticamente tono general en efecto sobre exportaciones |

La clasificación conserva la mayor probabilidad como clase; el puntaje conserva la diferencia P(positivo)−P(negativo). La frecuencia mensual se adapta a la cobertura disponible; no se copia la agregación diaria ni el cambio de base a 50 del estudio ecuatoriano. El corpus escaso por país no justifica una curva diaria continua.

La comparación con el diccionario utiliza las fórmulas intactas y permite restringir el modelo a los artículos con coincidencias léxicas. Los pesos difieren: ocurrencias en el diccionario, artículos en el modelo. Un desacuerdo es un caso para examinar, no una prueba automática de superioridad.

La lista de casos con menor margen entre las dos clases más probables retoma el criterio de muestreo por incertidumbre descrito en Ecuador. Solo prioriza diagnóstico: no crea etiquetas, no confirma errores, no sustituye una muestra independiente y no modifica la muestra diagnóstica de 60 registros ya preparada. Revisar únicamente casos ambiguos no permitiría estimar directamente la exactitud de todo el corpus.

La evaluación requiere instrucciones escritas, revisión de fuentes sin ver primero las predicciones, registro de discrepancias y un conjunto independiente. Cuando sea posible, dos personas deben anotar por separado. La dirección del acontecimiento exportador, el tono, los destinos y el período estadístico requieren criterios propios. Los formularios guardan únicamente juicios explícitos de quien revisa.

El contraste económico se hará posteriormente con los datos numéricos que suministre la investigadora. Se distinguirán FOB nominal, cantidades, períodos de referencia y fechas de disponibilidad; predecir una cifra usando noticias que ya la publicaron produciría una evaluación engañosa. Ninguna mejora de pronóstico está demostrada actualmente.

## Reproducción y créditos

Las predicciones y sus hashes permanecen intactos. El tablero verifica su procedencia antes de mostrarlas y reconstruye los pequeños agregados desde esas predicciones. El código de inferencia propio y el preprocesamiento reutilizado se identifican por separado en [CONTEXTUAL_REPLICATION_ES.md](CONTEXTUAL_REPLICATION_ES.md) y [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Los pesos y los cuerpos completos de las noticias no se redistribuyen.
