# Inferencia contextual ejecutada

Se verificaron predicciones de titular y cuerpo para **1423 artículos elegibles del archivo completo**, incluidos los complementarios. El marco principal usa **1011**, marzo de 2020–octubre de 2026. El archivo completo suma 9233 fragmentos y 1073438 tokens de contenido del cuerpo; el marco principal, 5365 fragmentos y 612219 tokens. No son etiquetas humanas ni medidas de precisión.

Cada predicción se asocia a hashes exactos de cuerpo y titular, método, checkpoint y preprocesamiento. Los textos reextraídos de Valora/La República eliminan promociones y bloques de personalización; las inferencias con hashes antiguos no se adoptan para esos cuerpos. `contextual_manifest.json` documenta la adopción de resultados ya calculados y compatibles: no inventa una duración de inferencia única ni confunde versiones de caché con artículos únicos.

El modelo fijo y el adaptador se describen en [la explicación metodológica](CONTEXTUAL_REPLICATION_ES.md). La media mensual por artículo y la incertidumbre léxica son instrumentos separados. Las tablas completas se reproducen desde probabilidades guardadas, sin descargar pesos. La evaluación humana independiente de 200 registros sigue en blanco; el contraste con FOB se informa aparte en [resultados económicos](ECONOMIC_RESULTS_ES.md).

El caso DW «Colombia reactivará exportaciones de carbón a Israel» sigue siendo diagnóstico complementario: clase NEU en titular y cuerpo, balances con signos diferentes, y una coincidencia negativa del diccionario (`suspensión`). Reanudación del acontecimiento, tono general y antecedentes históricos son objetivos diferentes. El caso no se incorpora como referencia humana ni se cambian conjugaciones para obtener un signo deseado.
