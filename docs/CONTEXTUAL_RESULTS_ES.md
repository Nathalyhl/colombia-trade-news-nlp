# Resultados ejecutados de la adaptación NLP

Se procesaron **410 artículos reales**, con predicciones independientes para el titular y el cuerpo. La ejecución quedó completa; las marcas originales de inicio y finalización en UTC se conservan en contextual_manifest.json.

| Concepto | Resultado observado |
| --- | ---: |
| Artículos elegibles procesados | 410 |
| Fragmentos de cuerpos procesados | 3883 |
| Tokens de contenido de los cuerpos, después del preprocesamiento original | 463240 |
| Meses con predicciones sobre artículos | 78 / 80 |
| Artículos con coincidencias en el diccionario para la comparación restringida | 321 |
| Etiquetas humanas de referencia suministradas | 0 |

Los tokens son unidades del tokenizador del modelo y no equivalen al denominador de palabras procesadas del método léxico. Los fragmentos pertenecen a los artículos originales: no son noticias nuevas ni observaciones independientes de prensa.

## Clases automáticas observadas

| Clase | Cuerpos completos | Titulares |
| --- | ---: | ---: |
| Negativa | 40 | 59 |
| Neutra | 317 | 298 |
| Positiva | 53 | 53 |

Estos conteos describen las predicciones del modelo. No son etiquetas verificadas ni porcentajes de precisión. La mayoría de predicciones neutras debe revisarse frente a juicios humanos y a la diferencia entre tono subjetivo y dirección de un acontecimiento exportador.

## Caso real: reactivación de exportaciones de carbón a Israel

Titular de DW: “Colombia reactivará exportaciones de carbón a Israel”, registro b30d353a15880d52e0b3. El cuerpo contiene antecedentes de suspensión y conflicto. El diccionario encuentra P=0 y N=1, por la forma suspensión, y da −1. La nueva clasificación es la clase con mayor probabilidad entre tres alternativas:

| Entrada al modelo | P(negativa) | P(neutra) | P(positiva) | Clase | P(positiva) − P(negativa) |
| --- | ---: | ---: | ---: | --- | ---: |
| Titular | 0.100934 | 0.655333 | 0.243733 | NEU | 0.142799 |
| Cuerpo completo | 0.325052 | 0.536534 | 0.138414 | NEU | -0.186638 |

Ambas entradas reciben la clase neutra. El signo del puntaje continuo cambia entre titular y cuerpo, pero la clase neutra sigue siendo la más probable. Esto no prueba que el modelo tenga razón ni que reactivar exportaciones sea económicamente neutro; revela una diferencia de medición que se puede revisar sobre un caso concreto. El modelo no fue obligado mediante una regla a clasificar reactivará como positivo.

## Reproducibilidad y límites

El modelo fijado es pysentimiento/robertuito-sentiment-analysis, revisión a2cc0f67ebd705c55191e25a05ba23d885fcc09b. Los hashes de pesos, tokenizador, preprocesamiento y corpus vinculan los resultados a sus entradas. El cálculo de clases y agregados se comprueba sin descargar pesos; repetir la inferencia requiere el modelo y el archivo local de artículos.

La ejecución no produce una validación de dominio ni un índice predictivo demostrado. Se conserva el problema de cobertura histórica, se mantienen sin completar los meses sin textos y no se inventan datos de exportaciones. Los créditos y el alcance de la adaptación están explicados en CONTEXTUAL_REPLICATION_ES.md.
