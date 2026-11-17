# Contraste económico ejecutado

## Pregunta y resultado

¿Añade el tono de las noticias información al historial exportador, después de controlar la cantidad y composición de fuentes? En doce meses de prueba el error baja ligeramente al añadir tono, pero los diagnósticos impiden interpretar esa diferencia como evidencia suficiente de un predictor válido. Se conservan los resultados adversos.

## Auditoría del archivo recibido

El libro `Totales de control Exportaciones.xlsx`, recibido dentro del ZIP de la investigadora, contiene **309 meses consecutivos: enero de 2001–septiembre de 2026**, sin duplicados ni meses interiores vacíos. Sus 26 hojas tienen FOB US$, PESO NETO KGM y REGISTROS. Los totales anuales almacenados coinciden con las sumas mensuales dentro de 0,01 de sus unidades. La hoja de 2026 tiene nueve meses; el título «ENERO DICIEMBRE» no convierte los meses vacíos en observaciones. No contiene destinos ni fechas históricas de publicación/revisión. No se exportan nombres personales de las propiedades del documento.

`exports_monthly_supplied.csv` conserva las observaciones y sus referencias exactas a hoja/celdas y SHA-256; `exports_source_audit.json` registra fórmulas de totales, sumas y diferencias. El libro original no se modifica ni se redistribuye. La procedencia editorial y todas las versiones históricas del conjunto no han sido autenticadas independientemente.

Como contraste puntual, las cifras de enero de 2023, 2024 y 2025 redondeadas a millones con una decimal coinciden con 3.733,2; 3.621,1 y 3.776,8 en el [boletín DANE de enero de 2025, publicado el 4 de marzo de 2025](https://www.dane.gov.co/files/operaciones/EXPORTACIONES/bol-EXPORTACIONES-ene2025.pdf). Esto comprueba tres puntos a la precisión del boletín, no certifica los 309 meses. El mismo boletín explica las fechas de declaración, la excepción de petróleo/derivados y las revisiones provisionales. No se confunden con fechas de publicación de noticias.

En el libro, enero–septiembre de 2026 suma US$42.302 mil millones FOB, frente a US$37.339 mil millones en los mismos nueve meses de 2025: variación acumulada de 13.29%. El peso neto acumulado cambia 3.88%. Esta divergencia ilustra por qué valor nominal y peso agregado son medidas diferentes; no identifica por sí misma precios ni cantidades reales ajustadas por composición. Los registros cuentan registros, no empresas.

## Diseño y disponibilidad

Noticias del marco directo de Valora/La República, marzo de 2020–octubre de 2026. Se predice el crecimiento interanual logarítmico del FOB del mes t al cierre de t−1, con tono, incertidumbre y controles de cobertura de t−1. Los cuatro errores siguen ARMA(1,1), fijado antes de abrir errores de prueba. Estimación expansiva; medias y escalas solo de entrenamiento; mínimo 36 crecimientos disponibles. Primer entrenamiento desde abril de 2020, 64 observaciones disponibles; último, 75. Prueba: octubre de 2025–septiembre de 2026, doce orígenes comunes, sin fallos de convergencia en el escenario principal.

La disponibilidad principal se **supone** al cierre del segundo mes posterior al período, con sensibilidades de uno y tres meses. Los valores actuales del libro sustituyen a versiones históricas desconocidas. Las fechas desconocidas permanecen vacías en la fuente; se generan únicamente en memoria dentro del escenario declarado. La opción estricta sin ese supuesto no produce pronósticos. Los textos web y el checkpoint lingüístico tampoco tienen disponibilidad histórica acreditada. El ejercicio es retrospectivo; no es una evaluación en tiempo real.

## Errores y diagnósticos

Unidades: puntos de variación interanual logarítmica ×100; no porcentajes de acierto.

| Especificación | Meses | MAE | RMSE | Sesgo predicción−observación |
| --- | ---: | ---: | ---: | ---: |
| baseline_arma | 12 | 7.535 | 9.194 | -4.618 |
| baseline_coverage | 12 | 7.020 | 8.741 | -4.610 |
| plus_tone | 12 | 6.951 | 8.593 | -4.586 |
| plus_tone_uncertainty | 12 | 7.032 | 8.964 | -4.693 |
| growth_persistence | 12 | 8.144 | 9.517 | -2.179 |
| seasonal_naive_fob | 12 | 9.587 | 11.354 | -9.108 |

En las cuatro especificaciones estimadas, **Ljung–Box rechaza ausencia de autocorrelación al 5% en los doce ajustes**. Los p-valores ADF de los entrenamientos van de 0.222 a 0.316: no se rechaza raíz unitaria con esa prueba/especificación. La transformación anual no garantiza estacionariedad. No rechazar tampoco prueba que exista una raíz unitaria. Los intervalos gaussianos del modelo son condicionales a supuestos cuestionados por los diagnósticos; no se presentan como intervalos calibrados.

Los comparadores `growth_persistence` y `seasonal_naive_fob` se añadieron **después** de ver estos fallos. No se ajustan parámetros ni se usan cifras futuras: el primero repite el último crecimiento disponible; el segundo supone el mismo FOB que doce meses antes, crecimiento cero. Esta enmienda está declarada en el protocolo; no es confirmación independiente. No se buscaron órdenes que ganaran en los doce meses de prueba.

## Sensibilidades

| Escenario | Meses comunes | RMSE base con cobertura | RMSE al añadir tono |
| --- | ---: | ---: | ---: |
| main_assumed_lag_2 | 12 | 8.741 | 8.593 |
| assumed_lag_1 | 12 | 8.202 | 8.013 |
| assumed_lag_3 | 12 | 9.039 | 8.881 |
| exclude_reporting | 12 | 8.91 | 8.738 |
| valora_only | 12 | 7.598 | 6.907 |
| larepublica_only | 0 | Sin estimar | Sin estimar |

La República sola no alcanza 36 crecimientos disponibles en el tramo continuo posterior al vacío de diciembre de 2024; se conservan doce omisiones justificadas, sin inventar resultados. Los marcos por fuente pueden cambiar el inicio de entrenamiento, por lo que sus errores no son experimentos idénticos ni permiten escoger retrospectivamente el medio ganador. La exclusión de propuestas de informe/mixto deja roles sin resolver y depende de reglas aún no validadas.

Las correlaciones de tono_t con crecimiento_t+h para h=−3,…,+3 se publican con sus tamaños en el JSON, sin seleccionar el desfase más favorable ni inferir causalidad. Referencias exportadoras anteriores y noticias posteriores pueden estar relacionadas por difusión de estadísticas: correlación no demuestra anticipación.

## Conclusión defendible y siguiente evaluación

Existe una implementación reproducible y un contraste real sobre el archivo recibido; la utilidad predictiva no queda establecida. La conclusión académica actual es **evidencia exploratoria, sensible al diseño y con diagnósticos adversos**, no un indicador validado. Hace falta completar las referencias humanas, autenticar definición/versiones del insumo numérico y revisar tendencia, estacionalidad y especificación con validación temporal adicional. Las decisiones posteriores a estos resultados deben documentarse y evaluarse con otros orígenes; los doce meses ya usados no son un nuevo conjunto de prueba.

La motivación de comparar con/sin noticias procede de la sección 6 de [BE1340](https://doi.org/10.32468/be.1340). Su modelo de factores dinámicos y sus resultados sobre actividad económica no se reproducen aquí. [Statsmodels](https://www.statsmodels.org/stable/examples/notebooks/generated/statespace_forecasting.html) aporta la implementación de los pronósticos recursivos; la pregunta, el corpus y esta evaluación exportadora son la adaptación del proyecto.
