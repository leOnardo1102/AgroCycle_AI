# 🌱 AgroCycle

## Idioma / Language

La app está en **español** y en **inglés**. El selector **Español | English** está arriba en la barra lateral.
Para abrirla directamente en inglés (por ejemplo, para los jueces de NASA) usa la dirección con `?lang=en`,
por ejemplo `https://<tu-app>.streamlit.app/?lang=en`.

- La traducción vive en `ui/i18n.py` (mecanismo) y `ui/traducciones_en.py` (diccionario).
- Para encontrar textos sin traducir: `AGROCYCLE_I18N_LOG=1 streamlit run app.py` y revisa `logs/i18n_faltantes.txt`.
- El PDF y el mensaje de WhatsApp para el agricultor se mantienen en español.


Herramienta de apoyo a la toma de decisiones para la **rotación de cultivos** de pequeños productores de **Chimborazo, Ecuador**. Integra datos de observación de la Tierra de la **NASA** con el historial de la parcela, las características del terreno y las prioridades del agricultor.

**Evento:** NASA Space Apps Challenge · **Institución:** UNACH · **Especificación:** `Proyecto.md` (ERS v0.1)

**Usuario principal:** el **técnico agropecuario de territorio** (MAG, GAD provincial, cooperativas, ONG). Gestiona su cartera de agricultores, genera el plan de cada parcela y se lo **entrega al agricultor** por WhatsApp, correo, hoja impresa o PDF, siempre en lenguaje sencillo.

---

## ▶️ Cómo ejecutarlo

Requisitos: **Python 3.10+** e internet (para el mapa y los datos de la NASA).

**Windows:** doble clic en `iniciar.bat`.

**A mano (Windows, PowerShell):**
```powershell
cd AgroCycle_AI
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Se abre solo en el navegador (http://localhost:8501).

**Mac / Linux:** `./iniciar.sh`

**Pruebas:**
```bash
pip install -r requirements-dev.txt
python -m pytest -q        # 45 pruebas, no necesitan internet
```

---

## 🆕 Novedades v0.4

| Novedad | Detalle |
|---|---|
| 👨‍💼 **Perfil del técnico** | Nombre, cargo, institución (MAG, GAD, cooperativa, ONG), cantón o parroquia, celular y correo. Se elige en la barra izquierda. Sus datos salen en el **encabezado y la firma** de la hoja impresa y del PDF, y **al final** de los mensajes de WhatsApp y correo. Cada plan guardado queda asociado al técnico |
| 📅 **Plan de 12 meses en 3 etapas** (opción por defecto) | **Etapa 1 · Lluvias** (meses 1 a 5): cultivo principal (papa precoz, maíz suave para choclo, quinua). **Etapa 2 · Salida de lluvias** (meses 6 a 9): ciclo corto o recuperador (arveja, haba tierna, cebada). **Etapa 3 · Verano** (meses 10 a 12): cultivo resistente o cobertura forrajera (avena forrajera, pasto con trébol). Se respetan las mismas reglas R01–R07 y una prueba verifica que el plan nunca pase de 12 meses. La rotación larga de 3 o 4 cultivos sigue disponible |
| 🗺️ **Mapa más fácil para dibujar la parcela** | Modo **«✏️ Dibujar tocando las esquinas»**: cada toque agrega una esquina y el área se ve al instante, con botones Deshacer, Cerrar contorno y Borrar. Además: herramientas ⬠/▭ en español y más grandes, buscador de comunidades 🔍, botón GPS 🎯, pantalla completa, acercamiento hasta nivel 20 y aviso si el dibujo parece demasiado grande. El mapa ya no se recarga en cada toque |

En `data/cultivos.json`, el campo `anual` indica en qué etapa puede ir cada cultivo, con qué variedad o uso, y cuánto cambian su rendimiento y su costo en el ciclo corto. **Lo debe validar agroindustria**: un año con 3 cultivos es exigente y depende de variedades precoces y de sembrar a tiempo.

## Novedades v0.3 (enfoque técnico de territorio)

| Novedad | Detalle |
|---|---|
| 👥 **Cartera de agricultores** | Nombre, cédula (con dígito verificador), comunidad, celular y correo. Al iniciar con la base vacía se cargan **3 agricultores de ejemplo** (Licto, Quimiag, Guamote) con parcela e historial |
| 🟢 **Regla de oro: lenguaje sencillo** | `modules/lenguaje_sencillo.py` traduce el plan sin siglas ni jerga, respondiendo a 4 preguntas: **qué sembrar en orden**, **por qué conviene**, **cuánto ahorra** y **qué cuidar del clima**. Hay una prueba automática que verifica que no se cuelen términos técnicos |
| 🚦 **Semáforos** | Tu tierra, agua, heladas y sequía, ganancia y seguridad del cálculo |
| 📤 **Centro de Entrega** | 📲 WhatsApp (convierte 09XXXXXXXX → 5939XXXXXXXX), 📋 copiar mensaje, ✉️ correo, 🖨️ hoja A4 para imprimir con firmas del técnico y del agricultor, 📄 PDF de 1 página (fpdf2). También funciona desde los planes guardados |
| 🧑‍🌾 **Preguntas en palabras del agricultor** | «¿Cómo es tu tierra?» (suelta, negra y suave, pesada o barrosa) y «¿Qué pasa cuando llueve fuerte?». Si se empoza el agua, se activa la regla R07 |
| 🌾 **Cultivos nuevos** | Avena forrajera y pasto ryegrass + trébol (18 en total), con un consejo práctico para cada cultivo |
| 🛰️ **Variables NASA exactas** (vista técnica) | PRECTOTCORR, T2M, T2M_MIN, T2M_MAX, ALLSKY_SFC_SW_DWN (radiación) y GWETROOT (humedad radicular), con gráfico |
| 🛟 **Respaldo NASA** | Si NASA POWER no responde (espera máxima de 8 s, en `config.py`) y la parcela no tiene datos guardados, usa una respuesta **real** de NASA POWER para Riobamba y lo avisa |
| 🌡️ **Simulador** | El escenario de calor ahora es de +1,5 °C |

> Se mantuvo la arquitectura de `Proyecto.md` (Python + Streamlit + Folium + Plotly). Del documento de recomendaciones se tomaron las funciones, pero no el cambio a FastAPI, Tailwind y Chart.js, porque implicaba rehacer una app que ya cumple los criterios del MVP.

## 🧭 Cómo se usa

1. En la barra izquierda escribe tu nombre como **Técnico responsable** y elige un **Agricultor**, o regístralo en **👥 Cartera de agricultores**.
2. **➕ Registrar parcela**: toca el terreno en el mapa satelital (o dibuja su contorno con ⬠ para calcular el área). Luego indica el riego, la pendiente y los problemas que has visto.
3. En la parcela, pestaña **📜 Historial**: registra lo que sembraste antes.
4. Pestaña **🌱 Plan de cultivo**: elige qué es lo más importante para ti y presiona **Generar**. Recibes 3 opciones con:
   - fechas de siembra y cosecha,
   - quintales esperados y ganancia para tu terreno,
   - sacos de urea,
   - alertas de helada y de riego,
   - ventajas, limitaciones, condiciones y nivel de confianza.
5. **📤 Entregar el plan**: WhatsApp, correo, hoja para imprimir o PDF.
6. **⚖️ Comparar**, **🔮 ¿Qué pasa si…?** y **🗂️ Planes guardados**.

**Dos vistas** (barra lateral):
- **👨‍🌾 Agricultor**: lenguaje sencillo, sin indicadores técnicos (sección 9.2).
- **🔬 Técnica**: pesos editables, puntajes, gráfico de agua mes a mes, tabla de factores, trazabilidad, datos NASA crudos y corregidos, mapa con NDVI de MODIS, y catálogo y reglas editables.

---

## 🛰️ Datos

| Fuente | Estado | Archivo | Uso |
|---|---|---|---|
| **NASA POWER** | ✅ | `services/nasa_power.py` | Lluvia y temperaturas mensuales. La temperatura se **corrige por altitud** (−0,58 °C/100 m) entre la celda NASA (~50 km) y la parcela |
| **NASA SRTM** | ✅ | `services/srtm.py` | Altitud y **pendiente** (5 puntos alrededor de la parcela) |
| **NASA MODIS (GIBS)** | ✅ | `vistas/comun.py` | Capas de NDVI y de color real en el mapa (vista técnica) |
| **SoilGrids** | ✅ complementario | `services/soilgrids.py` | pH, materia orgánica y textura cuando el agricultor no los conoce |
| **GPM / IMERG** | ⏳ | `services/gpm.py` | Requiere cuenta NASA Earthdata (siguiente fase) |
| **SMAP** | ⏳ | `services/smap.py` | Requiere cuenta NASA Earthdata (siguiente fase) |

Los datos se guardan en la tabla `datos_ambientales` y se reutilizan durante 30 días. Si una fuente falla, la app avisa qué faltó y sigue con estimaciones (RF-15).

> **Hallazgo con datos reales (Riobamba):** NASA POWER da ~1.400 mm de lluvia al año, frente a ~480 mm de la referencia local. Cuando la diferencia supera el 40 %, la app usa el **promedio de ambas** y baja el nivel de confianza. En la vista técnica se puede elegir otra opción.

---

## 🧠 Motor de recomendaciones (sección 13)

1. **Filtra** los cultivos por altitud (R05).
2. **Enumera** todas las secuencias de 3 o 4 cultivos (hasta ~38 000).
3. **Descarta** las que incumplen una **restricción esencial** *antes de puntuar* (13.4):

| Id | Regla |
|---|---|
| R01 | No repetir el mismo cultivo seguido (incluye el último del historial) |
| R02 | ≥ 2 ciclos sin papa entre papas, contando el historial (≥ 3 si se reporta gusano blanco) |
| R03 / R04 | No suceder aliáceas (cebolla y ajo) ni crucíferas |
| R05 | Altitud dentro del rango del cultivo (± 250 m) |
| R06 | Al menos una leguminosa o abono verde |
| R07 | Sin cultivos sensibles si el terreno se encharca |

4. **Simula** mes a mes:
   - agua: Kc × ET0 de Hargreaves, lluvia efectiva USDA-SCS, almacenamiento del suelo y riego;
   - nitrógeno: lo que dejan las leguminosas y lo que aporta la materia orgánica;
   - heladas: a partir de la T mínima;
   - altitud y pH.
5. **Puntúa** 5 criterios (suelo, agua, clima, sanidad e ingresos) con los pesos del agricultor. Los problemas reportados refuerzan algunos pesos, y eso se informa en pantalla.
6. Devuelve las **3 mejores opciones distintas entre sí**, con explicación y nivel de confianza (13.5).

Las reglas están en `data/reglas_agronomicas.json` y el catálogo de 18 cultivos en `data/cultivos.json`. **Todo debe validarse con agroindustria y ambiental (RN-10).**

---

## 📁 Estructura (sección 10.3)

```
AgroCycle_AI/
├── app.py                      # entrada Streamlit y navegación
├── config.py                   # coordenadas, tiempos de espera y respaldo NASA
├── vistas/                     # (añadido) capa de presentación: perfil, cartera, inicio, registro, mapa_parcela, parcela, catálogo, acerca
├── modules/
│   ├── parcelas.py             # RF-01, 02, 04, 05, 06
│   ├── historial.py            # RF-03 + catálogo
│   ├── datos_ambientales.py    # RF-07, 08, 15 + diagnóstico (9.2)
│   ├── motor_agronomico.py     # reglas + puntuación (13)
│   ├── recomendaciones.py      # RF-09 a 13, 16 + confianza
│   ├── simulador.py            # RF-14, CU-05
│   ├── tecnicos.py             # (v0.4) perfil del técnico responsable
│   ├── lenguaje_sencillo.py    # (v0.3) traductor sin jerga + semáforos
│   └── entrega.py              # (v0.3) WhatsApp, correo, hoja A4 y PDF
├── database/
│   ├── conexion.py             # SQLite por defecto · SQL Server con DATABASE_URL
│   ├── modelos.py              # entidades de la sección 12 (+ contacto del agricultor, drenaje)
│   └── semillas.py             # 3 agricultores de ejemplo
├── data/                       # cultivos.json, reglas_agronomicas.json, cantones.json
├── services/                   # nasa_power, srtm, soilgrids, gpm, smap
├── utils/                      # calculos.py, validaciones.py
└── tests/                      # test_parcelas, test_recomendaciones, test_datos_ambientales, test_entrega (+ respuestas reales NASA en tests/datos)
```

**Base de datos:** el documento propone SQL Server. El MVP usa **SQLite** para que funcione sin instalar nada. Para cambiar a SQL Server no hay que tocar el código:
```powershell
pip install pyodbc
$env:DATABASE_URL="mssql+pyodbc://usuario:clave@SERVIDOR/agrocycle?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
streamlit run app.py
```

**Reparto sugerido (15.1):**
- Programador 1: `services/` y `modules/datos_ambientales.py`
- Programador 2: `modules/motor_agronomico.py`, `recomendaciones.py` y `simulador.py`
- Programador 3: `app.py` y `vistas/`
- Agroindustria: `data/cultivos.json`
- Ambiental: `data/reglas_agronomicas.json`

---

## ✅ Criterios de aceptación del MVP (14.5)

| # | Criterio | Dónde |
|---|---|---|
| 1 | Registrar y consultar parcelas | ➕ Registrar parcela, 🏠 Inicio, ✏️ Editar |
| 2 | Registrar historial | Pestaña 📜 Historial |
| 3 | Al menos una fuente NASA | NASA POWER + SRTM + MODIS (GIBS) |
| 4 | No bloquearse si falla una fuente | Avisos + estimación (`test_fuente_caida_no_bloquea`) |
| 5 | Alternativas con reglas documentadas | `reglas_agronomicas.json`, R01–R07 |
| 6 | Explicaciones y limitaciones | Ventajas / Limitaciones / Qué necesitas / Confianza |
| 7 | Comparar alternativas | Pestaña ⚖️ Comparar (radar + tabla) |
| 8 | Identificar información faltante | «Nivel de confianza — información que falta» |
| 9 | Al menos un escenario hipotético | 5 escenarios en 🔮 ¿Qué pasa si…? |
| 10 | Interfaz comprensible | Vista Agricultor (validar con 5–8 agricultores, sección 17) |

---

## ⚠️ Limitaciones

Es una herramienta **de apoyo**. Los parámetros de los cultivos, los precios y los costos son referenciales. Los datos satelitales tienen resolución gruesa. Los escenarios son hipotéticos y los resultados no garantizan rendimientos (secciones 16 y 18).

**Seguridad (RNF-07):** el MVP no tiene contraseñas, porque está pensado para uso local o en una demo. Si se publica en internet, hay que agregar autenticación: la cartera guarda cédulas y teléfonos.

**Base de datos existente:** al abrir la app, `database/conexion.py` agrega sola las columnas nuevas a una base antigua. Los 3 agricultores de ejemplo solo se cargan si la base está vacía; para verlos, borra `database/agrocycle.db`.
