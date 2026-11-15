"""English translations of the AgroCycle interface.

Keys are the exact Spanish text shown in the app. In keys and values, write « # » in place of every number
(and « #º » for Spanish ordinals such as 1ro / 2do): the translator puts the real figures back, in English format.
PALABRAS holds single words or names that may appear inside sentences (months, crops, levels).
PLANTILLAS holds regular expressions for sentences that embed variable words (months, crops, problems).
Anything missing is shown in Spanish; run the app with AGROCYCLE_I18N_LOG=1 to list missing texts in logs/.
"""
import re

# ------------------------------------------------------------------ words and names
MESES = {
    "enero": "January", "febrero": "February", "marzo": "March", "abril": "April", "mayo": "May", "junio": "June",
    "julio": "July", "agosto": "August", "septiembre": "September", "octubre": "October", "noviembre": "November",
    "diciembre": "December",
}
MESES_CORTOS = {"Ene": "Jan", "Feb": "Feb", "Mar": "Mar", "Abr": "Apr", "May": "May", "Jun": "Jun", "Jul": "Jul",
                "Ago": "Aug", "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dic": "Dec"}

CULTIVOS = {
    "Papa": "Potato", "Haba (verde)": "Faba bean (green)", "Haba": "Faba bean", "Fréjol (seco)": "Common bean (dry)",
    "Fréjol": "Common bean", "Maíz suave (choclo)": "Soft corn (fresh ears)", "Maíz suave": "Soft corn",
    "Cebolla blanca (de rama)": "Bunching onion", "Cebolla blanca": "Bunching onion", "Quinua": "Quinoa",
    "Chocho (lupino)": "Andean lupin (chocho)", "Chocho": "Andean lupin", "Cebada": "Barley", "Trigo": "Wheat",
    "Arveja (tierna)": "Pea (green)", "Arveja": "Pea", "Zanahoria": "Carrot", "Melloco": "Melloco (ulluco)",
    "Oca": "Oca", "Avena + vicia (abono verde)": "Oat + vetch (green manure)", "Avena + vicia": "Oat + vetch",
    "Ajo": "Garlic", "Brócoli": "Broccoli", "Avena forrajera": "Forage oat", "Pasto ryegrass + trébol": "Ryegrass + clover pasture",
    # usos del plan anual
    "Arveja tierna": "Green pea", "Avena + vicia (abono verde de corte temprano)": "Oat + vetch (early-cut green manure)",
    "Avena forrajera (corte)": "Forage oat (cut)", "Cebada forrajera": "Forage barley", "Cebada para forraje verde": "Barley for green forage",
    "Cebolla blanca (primer corte)": "Bunching onion (first cut)", "Fréjol tierno (vainita)": "Green bean (snap)",
    "Haba tierna": "Green faba bean", "Haba tierna en vaina": "Green faba bean in pod",
    "Maíz suave para choclo (variedad precoz)": "Soft corn for fresh ears (early variety)",
    "Papa de variedad precoz": "Early potato variety", "Quinua de variedad precoz": "Early quinoa variety",
    "Siembra de pasto ryegrass + trébol (queda establecido)": "Ryegrass + clover sowing (stays established)",
    "siembra de pasto ryegrass + trébol (queda establecido)": "ryegrass + clover sowing (stays established)",
}
FAMILIAS = {
    "Abono verde": "Green manure", "Aliáceas": "Alliaceae", "Amarantáceas": "Amaranthaceae", "Apiáceas": "Apiaceae",
    "Baseláceas": "Basellaceae", "Brasicáceas": "Brassicaceae", "Gramíneas": "Grasses (Poaceae)", "Leguminosas": "Legumes",
    "Oxalidáceas": "Oxalidaceae", "Pradera": "Pasture", "Solanáceas": "Solanaceae", "Asteráceas": "Asteraceae",
}
PROBLEMAS = {
    "falta agua en el verano": "water runs short in the dry season",
    "la tierra ya no produce como antes": "the land no longer yields as before",
    "la lluvia se lleva la tierra": "rain washes the soil away",
    "caen heladas": "frosts occur", "salió con gusano blanco": "white grub appeared",
    "se encharca cuando llueve": "it waterlogs when it rains",
    "Falta agua en el verano": "Water runs short in the dry season",
    "La tierra ya no produce como antes": "The land no longer yields as before",
    "La lluvia se lleva la tierra (erosión)": "Rain washes the soil away (erosion)",
    "Caen heladas": "Frosts occur", "Gusano blanco / plagas en la papa": "White grub / potato pests",
    "Se encharca cuando llueve": "It waterlogs when it rains",
}
PALABRAS = {
    **MESES, **{k.capitalize(): v for k, v in MESES.items()}, **MESES_CORTOS, **CULTIVOS,
    **{k.lower(): v.lower() for k, v in CULTIVOS.items()}, **FAMILIAS, **PROBLEMAS,
    "alta": "high", "media": "medium", "baja": "low", "alto": "high", "medio": "medium", "bajo": "low",
    "moderado": "moderate", "normal": "normal", "Alta": "High", "Media": "Medium", "Baja": "Low",
    "franco": "loam", "francoarenoso": "sandy loam", "Franco": "Loam", "Franco-arenoso": "Sandy loam",
    "Franco-arcilloso": "Clay loam", "Arenoso": "Sandy", "Arcilloso": "Clayey", "Pedregoso": "Stony",
    "verano": "dry season", "lluvias": "rainy season", "mixta": "mixed", "agricultor": "farmer",
    "Uso del agua de lluvia": "Use of rainwater", "Conservación del suelo": "Soil conservation",
    "Adaptación al clima": "Climate adaptation", "Sanidad": "Plant health",
}

# ------------------------------------------------------------------ exact sentences
EXACTAS = {
    # --- shell, menu, sidebar
    "Idioma": "Language", "Vista": "View", "Agricultor": "Farmer", "Técnica": "Technical", "Menú": "Menu",
    "Rotación de cultivos · Chimborazo": "Crop rotation · Chimborazo", "Guía rápida": "Quick guide",
    "Técnico responsable": "Responsible technician", "Agricultor en atención": "Farmer being assisted",
    "Mi perfil de técnico": "My technician profile", "Cartera de agricultores": "Farmer portfolio",
    "Parcelas del agricultor": "Farmer's plots", "Registrar parcela": "Register plot", "Catálogo y reglas": "Catalog & rules",
    "Acerca y limitaciones": "About & limitations", "Inicio": "Home",
    "La vista técnica muestra los datos satelitales, puntajes y reglas usadas.":
        "The technical view shows the satellite data, scores and rules used.",
    "Sus datos salen en el encabezado y la firma de la hoja, el PDF y los mensajes.":
        "Their details appear in the header and signature of the sheet, the PDF and the messages.",
    "Datos: NASA POWER, SRTM, GPM, SMAP, MODIS/Landsat y SoilGrids.": "Data: NASA POWER, SRTM, GPM, SMAP, MODIS/Landsat and SoilGrids.",
    "Orientativo; no reemplaza al técnico agrícola.": "Guidance only; it does not replace the agricultural technician.",
    "Técnica de extensión agrícola": "Agricultural extension technician",
    "Técnica de extensión agrícola, MAG Chimborazo": "Agricultural extension technician, MAG Chimborazo",
    "Técnica de extensión agrícola · MAG Chimborazo": "Agricultural extension technician · MAG Chimborazo",
    "Ing.": "Eng.",

    # --- quick guide
    "Guía rápida — AgroCycle": "Quick guide — AgroCycle", "Pruébala en # pasos": "Try it in # steps",
    "**AgroCycle** ayuda a planificar la rotación de cultivos en Chimborazo combinando datos satelitales y agroclimáticos (**NASA POWER, SRTM, GPM, SMAP, MODIS/Landsat** y **SoilGrids**) con el historial de cada parcela.":
        "**AgroCycle** helps plan crop rotation in Chimborazo by combining satellite and agro-climatic data (**NASA POWER, SRTM, GPM, SMAP, MODIS/Landsat** and **SoilGrids**) with each plot's history.",
    "**#. Elige la vista**": "**#. Choose the view**", "**#. Abre una parcela**": "**#. Open a plot**", "**#. Genera el plan**": "**#. Generate the plan**",
    "En el panel izquierdo: **Agricultor** (lenguaje sencillo) o **Técnica** (indicadores agronómicos y datos satelitales).":
        "In the left panel: **Farmer** (plain language) or **Technical** (agronomic indicators and satellite data).",
    "En **Parcelas del agricultor** pulsa **Abrir parcela** en un terreno *Lista para planificar*, o registra uno nuevo en el mapa con **Nueva parcela**.":
        "In **Farmer's plots** press **Open plot** on a field marked *Ready to plan*, or register a new one on the map with **New plot**.",
    "En la pestaña **Plan de cultivo** pulsa **Generar mi plan de cultivo**.": "In the **Crop plan** tab press **Generate my crop plan**.",
    "Luego mira **Comparar** y **¿Qué pasa si…?**": "Then look at **Compare** and **What if…?**",
    "Qué encontrarás en cada parcela": "What you will find in each plot",
    "**Diagnóstico:** lluvia, heladas, agua, terreno y cobertura del suelo.": "**Diagnosis:** rain, frost, water, terrain and soil cover.",
    "**Plan de cultivo:** tres rotaciones para # meses comparadas con lo que se siembra hoy.": "**Crop plan:** three rotations for # months compared with what is planted today.",
    "**Comparar:** puntajes de suelo, agua, clima y sanidad frente al manejo actual.": "**Compare:** soil, water, climate and plant-health scores against current practice.",
    "**¿Qué pasa si…?:** cómo cambia el plan con un año seco, lluvioso, más calor o heladas.": "**What if…?:** how the plan changes in a dry or wet year, with more heat or frost.",
    "**Entrega:** envía el plan por WhatsApp o descárgalo en PDF.": "**Delivery:** send the plan by WhatsApp or download it as a PDF.",
    "Las recomendaciones son orientativas y complementan el criterio del técnico agrícola en campo.":
        "Recommendations are guidance and complement the agricultural technician's judgment in the field.",
    "Entendido, empezar": "Got it, let's start",

    # --- home / plots
    "Agricultor": "Farmer", "Parcelas de {nombre}": "Plots of {nombre}", "Mis parcelas": "My plots",
    "Terrenos registrados del agricultor": "Farmer's registered fields", "Parcelas": "Plots", "registradas": "registered",
    "Superficie total": "Total area", "≈ # cuadras": "≈ # cuadras", "Con plan de rotación": "With rotation plan",
    "todas planificadas": "all planned", "# por planificar": "# still to plan", "Con riego": "With irrigation",
    "# solo con lluvia": "# rain-fed only", "Mapa de las parcelas": "Plot map", "Terrenos": "Fields", "Nueva parcela": "New plot",
    "Lista para planificar": "Ready to plan", "Falta el historial": "History missing",
    "Haz clic en una parcela para ver su ficha": "Click a plot to see its details",
    "Superficie": "Area", "Agua": "Water", "Cultivo previo": "Previous crop", "Sin registrar": "Not recorded",
    "Permanente": "Permanent", "Por turnos": "By turns", "Solo lluvia": "Rain-fed only",
    "Tiene historial: ya puedes generar las alternativas de rotación.": "History recorded: you can now generate the rotation options.",
    "Registra qué se sembró antes para obtener un plan confiable.": "Record what was planted before to get a reliable plan.",
    "Plan del #/#/#:": "Plan of #/#/#:", "Abrir parcela": "Open plot", "Editar": "Edit",
    "Aún no hay parcelas registradas": "No plots registered yet",
    "Registrar la primera parcela": "Register the first plot",

    # --- portfolio, profile
    "Técnico": "Technician", "Agricultores": "Farmers", "en tu cartera": "in your portfolio", "Superficie": "Area",
    "acompañada": "supported", "Con plan entregado": "Plan delivered", "agricultores": "farmers",
    "Comunidad": "Community", "Celular": "Mobile", "Último plan": "Latest plan", "Sin plan": "No plan",
    "Entregado #/#/#": "Delivered #/#/#", "Sin datos de contacto": "No contact details", "Ver sus parcelas": "See their plots",
    "Editar sus datos": "Edit their details",
    "Agricultores que acompañas. Sus datos de contacto se usan para enviarles el plan por WhatsApp o correo.":
        "Farmers you support. Their contact details are used to send them the plan by WhatsApp or email.",
    "Registrar agricultor": "Register farmer", "Editar agricultor": "Edit farmer", "Nombres y apellidos *": "Full name *",
    "Cédula": "ID number", "Celular (WhatsApp)": "Mobile (WhatsApp)", "Correo electrónico": "Email",
    "Comunidad / parroquia": "Community / parish", "Cantón / parroquia": "Canton / parish", "Guardar": "Save", "Cancelar": "Cancel",
    "Perfil del técnico": "Technician profile",
    "Tus datos aparecen en el encabezado y la firma de los planes, PDF y mensajes":
        "Your details appear in the header and signature of the plans, PDFs and messages",
    "Nombre completo *": "Full name *", "Cargo": "Position", "Institución": "Institution",
    "MAG Chimborazo / GAD Provincial / Cooperativa": "MAG Chimborazo / Provincial Government / Cooperative",
    "Técnicos registrados": "Registered technicians", "Equipo técnico registrado": "Registered technical team",
    "en el equipo": "on the team", "Técnico activo": "Active technician", "zona de atención": "service area",
    "Registrar otro técnico": "Register another technician", "Editar mis datos (Ing.": "Edit my details (Eng.",
    "Vista previa de tu firma en la hoja impresa y PDF": "Preview of your signature on the printed sheet and PDF",
    "Firma: **Ing.": "Signature: **Eng.", "Eliminar este registro": "Delete this record",

    # --- registration and map
    "Registrar parcela": "Register plot", "Editar parcela": "Edit plot",
    "Marca el terreno en el mapa satelital y completa sus datos": "Mark the field on the satellite map and complete its details",
    "Ubicar terreno": "Locate field", "Datos de suelo y agua": "Soil and water data", "Generar plan anual": "Generate annual plan",
    "#. ¿Dónde está tu terreno?": "#. Where is your field?", "¿Dónde está tu terreno?": "Where is your field?",
    "Marcar el centro": "Mark the center", "Un toque en el mapa ubica tu terreno": "One tap on the map locates your field",
    "Dibujar el contorno": "Draw the outline", "Toca cada esquina y se calcula el área": "Tap each corner and the area is calculated",
    "**Marcar el centro**  \nUn toque en el mapa ubica tu terreno": "**Mark the center**  \nOne tap on the map locates your field",
    "**Dibujar el contorno**  \nToca cada esquina y se calcula el área": "**Draw the outline**  \nTap each corner and the area is calculated",
    "Ir a un cantón…": "Go to a canton…", "Ir a un cantón": "Go to a canton",
    "Deshacer esquina": "Undo corner", "Cerrar contorno": "Close outline", "Borrar dibujo": "Clear drawing",
    "Acercar a mi terreno": "Zoom to my field", "Añadir esquina aquí": "Add corner here", "Usar centro del mapa": "Use map center",
    "Terminar contorno": "Finish outline",
    "Toca la **primera esquina** de tu terreno en el mapa.": "Tap the **first corner** of your field on the map.",
    "Llevas **# esquina(s)**. Toca la siguiente (necesitas al menos #).": "**# corner(s)** so far. Tap the next one (you need at least #).",
    "Toca el mapa para marcar el centro de tu terreno.": "Tap the map to mark the center of your field.",
    "Punto: -#, -# · aún sin contorno (opcional)": "Point: -#, -# · no outline yet (optional)",
    "¿Cómo marco mi terreno? (# formas fáciles)": "How do I mark my field? (# easy ways)", "¿Cómo marco mi terreno?": "How do I mark my field?",
    "**Ubica tu zona**: elige tu cantón, usa el buscador del mapa o toca el botón GPS.": "**Find your area**: choose your canton, use the map search or tap the GPS button.",
    "**Acércate** con la rueda del ratón o **Acercar a mi terreno** hasta ver con claridad los linderos.": "**Zoom in** with the mouse wheel or **Zoom to my field** until the boundaries are clear.",
    "Toca cada esquina del terreno en el mapa: **desde la #º esquina el contorno se cierra solo** y calcula las hectáreas al instante.":
        "Tap each corner of the field on the map: **from the #º corner the outline closes by itself** and the hectares are calculated instantly.",
    "Toca las esquinas de tu terreno directamente en el mapa satelital (con # o más se forma el contorno).": "Tap the corners of your field directly on the satellite map (# or more form the outline).",
    "También puedes usar las herramientas de polígono o rectángulo en la esquina izquierda del mapa.": "You can also use the polygon or rectangle tools in the left corner of the map.",
    "Toca cada esquina; con # o más se cierra solo": "Tap each corner; with # or more it closes by itself",
    "Un toque en el mapa ubica el centro": "One tap on the map locates the center",
    "Dibujar el contorno de este terreno": "Draw the outline of this field", "**Dibujar el contorno**": "**Draw the outline**",
    "**Marcar solo un punto**": "**Mark a single point**",
    "#. Datos de suelo y agua": "#. Soil and water data", "Nombre de la parcela": "Plot name", "Tamaño aproximado (hectáreas)": "Approximate size (hectares)",
    "Si dibujaste el contorno, se calcula solo.": "If you drew the outline, it is calculated automatically.",
    "# cuadra ≈ # ha.": "# cuadra ≈ # ha.", "¿Tienes agua de riego?": "Do you have irrigation water?",
    "Tengo riego siempre": "I always have irrigation", "Riego a veces / por turnos": "Irrigation sometimes / by turns",
    "Solo lluvia (sin riego)": "Rain only (no irrigation)", "¿Cómo es tu tierra?": "What is your soil like?",
    "Negra y suave (fácil de trabajar)": "Dark and soft (easy to work)", "Suelta / arenosa (se desmorona)": "Loose / sandy (crumbles)",
    "Pesada / barrosa (se pega en las botas)": "Heavy / muddy (sticks to boots)", "No sé / aún no": "I don't know / not yet",
    "¿Cómo es tu terreno?": "What is your field like?", "Plano": "Flat", "Un poco inclinado": "Slightly sloped", "Inclinado": "Sloped",
    "Muy inclinado": "Very steep", "Se seca rápido después de llover": "Dries quickly after rain", "Se empoza el agua cuando llueve": "Water pools when it rains",
    "¿Qué problemas has visto en tu terreno?": "What problems have you seen in your field?", "Elige uno o varios (opcional)": "Choose one or more (optional)",
    "Observaciones (opcional)": "Notes (optional)", "(opcional)": "(optional)",
    "**Suelo (opcional).** Deja vacío lo que no conozcas: se estimará con SoilGrids.": "**Soil (optional).** Leave blank what you don't know: it will be estimated with SoilGrids.",
    "Textura": "Texture", "Materia orgánica (%)": "Organic matter (%)", "Pendiente (%) · vacío = usar NASA SRTM": "Slope (%) · blank = use NASA SRTM",
    "Si no sabes, la calculamos con el relieve de la NASA.": "If you don't know, we calculate it from NASA terrain data.",
    "Guardar y continuar al plan anual": "Save and continue to the annual plan", "Parcela guardada": "Plot saved",
    "Drenaje": "Drainage",

    # --- plot page: header and tabs
    "Parcela": "Plot", "Diagnóstico": "Diagnosis", "Historial": "History", "Plan de cultivo": "Crop plan", "Comparar": "Compare",
    "¿Qué pasa si…?": "What if…?", "Planes guardados": "Saved plans", "Datos técnicos": "Technical data",
    "Así está tu terreno": "This is your field", "Lluvias": "Rainfall", "Temperatura": "Temperature", "Terreno": "Terrain",
    "Cobertura de la tierra": "Ground cover", "Tu tierra": "Your soil", "Ubicación de la parcela": "Plot location",
    "Altitud y pendiente": "Altitude and slope", "Lluvia anual": "Annual rainfall", "Cobertura en verano": "Dry-season cover",
    "Suelo descubierto": "Bare soil", "Suelo descubierto en verano": "Bare soil in the dry season", "Cubierto": "Covered",
    "Volver a consultar los datos de la NASA": "Query NASA data again", "Actualizar datos satelitales de la parcela": "Refresh the plot's satellite data",
    "Consultando datos satelitales NASA y propiedades de suelo...": "Querying NASA satellite data and soil properties...",
    "Información del clima y relieve de tu terreno actualizada con datos satelitales.": "Climate and terrain information for your field updated with satellite data.",
    "Clima fresco (# °C en promedio).": "Cool climate (# °C on average).", "Llueve unos # mm al año.": "About # mm of rain a year.",
    "Terreno plano.": "Flat terrain.", "Altura de # m.": "Altitude # m.", "Pendiente suave (# %).": "Gentle slope (# %).",
    "Riesgo de erosión: alto.": "Erosion risk: high.", "Tu tierra es negra y suave.": "Your soil is dark and soft.",
    "Tu tierra es suelta.": "Your soil is loose.", "Tiene buena materia orgánica.": "It has good organic matter.",
    "Tiene buena cantidad de abono natural (tierra negra).": "It has a good amount of natural fertilizer (dark soil).",
    "Solo cuentas con la lluvia: la fecha de siembra es clave.": "You depend only on rain: the sowing date is key.",
    "Tienes riego por turnos: conviene sembrar con las lluvias y usar el riego como apoyo.": "You have irrigation by turns: sow with the rains and use irrigation as support.",
    "La humedad de la tierra está normal para la época.": "Soil moisture is normal for the season.",
    "Estado actual de humedad de la tierra:": "Current soil moisture:",
    "Último cultivo: 🥔 Papa.": "Last crop: 🥔 Potato.", "Registraste # siembra(s) en esta parcela.": "You recorded # planting(s) on this plot.",
    "Suelo franco, pH # (adecuado para la mayoría de cultivos).": "Loam soil, pH # (suitable for most crops).",
    "Suelo franco-arenoso, pH # (adecuado para la mayoría de cultivos).": "Sandy loam soil, pH # (suitable for most crops).",
    "Cobertura de la tierra: Suelo descubierto en verano (julio, agosto y septiembre), conviene sembrar cultivo de cobertura para que el viento y la lluvia no se lleven la tierra.":
        "Ground cover: bare soil in the dry season (July, August and September); a cover crop is advised so wind and rain do not carry the soil away.",
    "Inclinación del terreno (# %): pendiente suave que permite alternar cultivos sin desgastar tanto la tierra.": "Field slope (# %): a gentle slope that allows rotating crops without wearing the soil down much.",
    "Lluvia medida desde el satélite: unos # mm al año.": "Rainfall measured by satellite: about # mm a year.",
    "que alcanzan para cubrir # de cada # partes del agua que piden estos cultivos.": "enough to cover # out of # parts of the water these crops need.",
    "La lluvia cubre el # % del agua que necesitan los cultivos.": "Rain covers # % of the water the crops need.",
    "Aprovecha bien la lluvia: cubre # de cada # partes del agua que necesitan tus cultivos.": "Makes good use of rain: it covers # out of # parts of the water your crops need.",
    "Humedad de la tierra por satélite: humedad en nivel normal (# %): buena condición para arrancar la siembra.": "Soil moisture by satellite: normal level (# %): a good condition to start sowing.",
    "Para que el plan sea más exacto: Anota lo que sembraste antes en este terreno.": "To make the plan more accurate: note what you planted before on this field.",
    "Para que el plan sea más exacto: Un análisis de tu tierra en laboratorio haría el plan más exacto.": "To make the plan more accurate: a laboratory soil test would make the plan more precise.",
    "Un análisis de tu tierra en laboratorio haría el plan más exacto.": "A laboratory soil test would make the plan more precise.",
    "Un pluviómetro en la finca mejoraría el cálculo.": "A rain gauge on the farm would improve the calculation.",
    "Altitud": "Altitude", "Pendiente": "Slope", "Fuentes:": "Sources:",
    "Problemas:": "Problems:",

    # --- history tab
    "¿Qué has sembrado en esta parcela?": "What have you planted on this plot?",
    "Registra al menos los últimos # o # cultivos, del más antiguo al más reciente.": "Record at least the last # or # crops, from oldest to most recent.",
    "Agregar un cultivo anterior": "Add a previous crop", "Cultivo": "Crop", "Mes de siembra": "Sowing month", "Año de siembra": "Sowing year",
    "Mes de cosecha": "Harvest month", "Año de cosecha": "Harvest year", "Agregar": "Add", "Registrar cultivo": "Record crop",
    "Aún no registras cultivos anteriores.": "You have not recorded previous crops yet.", "Agrégalos para mejorar la recomendación.": "Add them to improve the recommendation.",
    "Todavía no hay cultivos registrados.": "No crops recorded yet.", "No hay historial de cultivos de la parcela.": "There is no crop history for this plot.",
    "Siembra:": "Sowing:", "Cosecha:": "Harvest:", "→ Cosecha:": "→ Harvest:", "Siembra": "Sowing", "Cosecha": "Harvest",
    "Registrar un cultivo nuevo": "Record a new crop", "Ej.: papa, maíz suave, quinua": "E.g.: potato, soft corn, quinoa",

    # --- plan tab
    "¿Qué es lo más importante para ti?": "What matters most to you?", "**¿Qué es lo más importante para ti?**": "**What matters most to you?**",
    "Cuidar mi tierra": "Take care of my soil", "No arriesgar mi cosecha": "Don't risk my harvest", "Ahorrar agua": "Save water",
    "**Tipo de plan**": "**Plan type**", "Tipo de plan": "Plan type",
    "Plan de # meses (# etapas)": "#-month plan (# stages)", "(rápido y sencillo)": "(quick and simple)",
    "Rotación larga (# o # cultivos, # a # años)": "Long rotation (# or # crops, # to # years)",
    "**¿Cuándo empiezas a sembrar?** (inicio de lluvias)": "**When do you start sowing?** (start of the rains)",
    "**¿Qué cultivos puedes sembrar?**": "**Which crops can you sow?**", "Cultivos que puede sembrar": "Crops you can sow",
    "Solo para la rotación larga": "Only for the long rotation", "Automático": "Automatic",
    "Elige tus opciones y presiona **Generar mi plan de cultivo**.": "Choose your options and press **Generate my crop plan**.",
    "Generar mi plan de cultivo": "Generate my crop plan", "Probando todas las combinaciones de cultivos…": "Trying every crop combination…",
    "Recalculando…": "Recalculating…",
    "Opción A · # meses · de noviembre # a octubre #": "Option A · # months · November # to October #",
    "Tu tierra": "Your soil", "Mejora": "Improves", "La lluvia alcanza casi todo": "Rain covers almost everything",
    "Heladas y sequía": "Frost and drought", "Riesgo bajo": "Low risk", "Riesgo medio": "Medium risk", "Riesgo alto": "High risk",
    "Seguridad del cálculo": "Confidence of the calculation", "Información suficiente": "Enough information",
    "Si repites papa todo el año vs.": "If you repeat potato all year vs.", "este plan recomendado": "this recommended plan",
    "Plan superior al manejo actual": "Plan better than current practice",
    "+# % salud de tu tierra y ahorro estimado de $# en abono frente a repetir papa todo el año.": "+# % soil health and an estimated $# saved on fertilizer versus repeating potato all year.",
    "Qué sembrar mes a mes (plan de # meses)": "What to sow month by month (#-month plan)",
    "Etapa # · Lluvias (mes # a #)": "Stage # · Rainy season (months # to #)", "Etapa # · Lluvias": "Stage # · Rainy season",
    "Etapa # · Salida de lluvias (mes # a #)": "Stage # · End of rains (months # to #)", "Etapa # · Salida de lluvias": "Stage # · End of rains",
    "Etapa # · Verano (mes # a #)": "Stage # · Dry season (months # to #)", "Etapa # · Verano": "Stage # · Dry season",
    "# meses · cultivo principal": "# months · main crop", "# meses · ciclo corto / recuperador de tierra": "# months · short cycle / soil restorer",
    "# meses · cultivo resistente o cobertura forrajera": "# months · hardy crop or forage cover",
    "Cosecha esperada": "Expected harvest", "unos # quintales": "about # quintals", "# quintales": "# quintals",
    "unas # toneladas de forraje": "about # tonnes of forage", "Abono: unos # sacos de urea de # kg.": "Fertilizer: about # bags of # kg urea.",
    "# sacos de urea": "# bags of urea", "Casi no necesita urea.": "Hardly needs any urea.",
    "Casi no necesita urea: haba dejó abono natural en la tierra.": "Hardly needs urea: the faba bean left natural fertilizer in the soil.",
    "Por qué te conviene": "Why it suits you", "Por qué y ventajas": "Why and benefits", "Cuidados del clima": "Weather care",
    "Consejo:": "Tip:", "Atención:": "Attention:", "Alerta:": "Alert:",
    "Cada siembra es de un tipo distinto de planta: la tierra no se cansa tanto.": "Each planting is a different kind of plant: the soil does not tire as much.",
    "Cambiar de cultivo corta las plagas: el gusano blanco y la lancha de la papa no encuentran comida.": "Changing crops breaks pest cycles: potato white grub and late blight find nothing to feed on.",
    "El pasto con trébol deja descansar la tierra y además da comida para tus animales.": "Pasture with clover lets the soil rest and also feeds your animals.",
    "Después de cosechar, pica las matas y déjalas en el terreno: son abono.": "After harvesting, chop the plants and leave them on the field: they are fertilizer.",
    "Siembra con las primeras lluvias.": "Sow with the first rains.", "Cuidado con heladas en julio.": "Watch out for frost in July.",
    "Riega sobre todo en septiembre.": "Irrigate mainly in September.", "Priorizar riego en septiembre": "Prioritize irrigation in September",
    "En septiembre suele faltar agua: asegura tus turnos de riego para esos meses.": "Water often runs short in September: secure your irrigation turns for those months.",
    "Aguanta bien la falta de lluvia; deshierba en el primer mes.": "Copes well with little rain; weed in the first month.",
    "Córtala antes de que espigue para que tus animales coman mejor; aguanta las heladas.": "Cut it before it heads so your animals eat better; it tolerates frost.",
    "Deja descansar la tierra con pasto y trébol: tus animales comen y la tierra se recupera.": "Let the soil rest with grass and clover: your animals eat and the soil recovers.",
    "Cuidado con heladas en julio, sobre todo en madrugadas despejadas: aporca bien las matas y, si la tarde está despejada y fría, riega antes de que anochezca.":
        "Watch out for frost in July, especially on clear early mornings: hill the plants well and, if the evening is clear and cold, irrigate before nightfall.",
    "Puede helar casi todo el año, sobre todo en madrugadas despejadas: aporca bien las matas y, si la tarde está despejada y fría, riega antes de que anochezca.":
        "It can freeze almost all year, especially on clear early mornings: hill the plants well and, if the evening is clear and cold, irrigate before nightfall.",
    "El plan anual es ajustado: usar quinua de variedad precoz y sembrar apenas termine la etapa anterior.": "The annual plan is tight: use an early quinoa variety and sow as soon as the previous stage ends.",
    "Cultivos con buena cobertura: bajo riesgo de erosión.": "Crops with good cover: low erosion risk.",
    "# familias botánicas distintas: menos plagas compartidas.": "# different botanical families: fewer shared pests.",
    "Con esto evitamos repetir plagas (RN-#).": "This avoids repeating pests (RN-#).",
    "Fertilización N: requerimiento mínimo de urea": "N fertilization: minimal urea requirement",
    "N residual: haba aporta nitrógeno (~# kg/ha); casi no requiere urea": "Residual N: faba bean supplies nitrogen (~# kg/ha); hardly needs urea",
    "Incorporar al suelo los residuos de la leguminosa después de la cosecha.": "Incorporate the legume residues into the soil after harvest.",
    "Disponer de unos # m³ de agua de riego en toda la rotación.": "Have about # m³ of irrigation water for the whole rotation.",
    "conviene cultivo de cobertura": "a cover crop is advisable",
    "Destaca en conservación del suelo (#/#).": "Stands out in soil conservation (#/#).",
    "Destaca en sanidad (plagas y enfermedades) (#/#).": "Stands out in plant health (pests and diseases) (#/#).",
    "Se editan en data/reglas_agronomicas.json.": "They are edited in data/reglas_agronomicas.json.",
    "Guardar estas alternativas en el historial de planes": "Save these options to the plan history",
    "Descargar este plan (CSV)": "Download this plan (CSV)", "Entregar el plan al agricultor": "Deliver the plan to the farmer",
    "Enviar por WhatsApp": "Send by WhatsApp", "Enviar por correo": "Send by email", "Descargar PDF": "Download PDF",
    "Imprimir hoja": "Print sheet", "Ver y copiar el mensaje (por si WhatsApp no se abre)": "View and copy the message (in case WhatsApp does not open)",
    "Plan guardado en el historial": "Plan saved to history",
    "Alternativas": "Options", "Recomendada": "Recommended", "Opción": "Option", "Opción A": "Option A", "Opción B": "Option B", "Opción C": "Option C",
    "Testigo (repetir papa)": "Baseline (repeat potato)", "Testigo (Sin rotación)": "Baseline (no rotation)",
    "Escenario Testigo (Sin rotación: repetir papa)": "Baseline scenario (no rotation: repeat potato)",
    "monocultivo continuo de papa.": "continuous potato monoculture.",
    "Nivel de confianza: Media — información faltante o estimada": "Confidence level: Medium — missing or estimated information",
    "Confianza media": "Medium confidence", "Confianza alta": "High confidence", "Confianza baja": "Low confidence", "Confianza": "Confidence",
    "Limitaciones y Qué Validar en Campo": "Limitations and What to Check in the Field",
    "Plagas bajo tierra: el satélite no detecta gusano blanco ni enfermedades en la raíz; revisa el terreno al arar.":
        "Below-ground pests: the satellite cannot detect white grub or root diseases; check the field when ploughing.",
    "Partes duras o encharcadas: camina el lote para ver si hay zonas compactadas o donde se empoza el agua.":
        "Hard or waterlogged patches: walk the plot to find compacted areas or places where water pools.",
    "Turnos de agua y suelo real: confirma tus turnos reales con la junta de riego y verifica la tierra junto al técnico.":
        "Real water turns and soil: confirm your actual turns with the irrigation board and check the soil with the technician.",
    "Calendario técnico de rotación, paso a paso": "Technical rotation calendar, step by step",
    "Trazabilidad: datos y reglas usadas (RNF-#)": "Traceability: data and rules used (RNF-#)",
    "Pesos usados: Suelo #, Agua #, Clima #, Sanidad #": "Weights used: Soil #, Water #, Climate #, Plant health #",
    "Secuencias válidas evaluadas: **#** · descartadas por restricciones: **#**": "Valid sequences evaluated: **#** · discarded by constraints: **#**",
    "Restricciones esenciales verificadas (todas cumplidas): R# No repetir cultivo, R# Descanso de la papa, R# Aliáceas no seguidas, R# Crucíferas no seguidas, R# Altitud adecuada, R# Incluir una leguminosa, R# Encharcamiento":
        "Essential constraints checked (all met): R# Do not repeat crop, R# Potato rest period, R# No consecutive Alliaceae, R# No consecutive crucifers, R# Suitable altitude, R# Include a legume, R# Waterlogging",
    "**Clima usado por el motor** (temperatura corregida por altitud y lluvia según el modo elegido)": "**Climate used by the engine** (temperature corrected for altitude, rainfall according to the chosen mode)",
    "Clima usado por el motor": "Climate used by the engine",
    "**Valores exactos de NASA POWER** (celda a # m, sin corregir) · fuente: NASA POWER": "**Exact NASA POWER values** (cell at # m, uncorrected) · source: NASA POWER",
    "La lluvia de NASA POWER (# mm) difiere #% de la referencia local (# mm): se usó un promedio de ambas.": "NASA POWER rainfall (# mm) differs #% from the local reference (# mm): an average of both was used.",
    "Suelo +# % (+# pts) · Sanidad +# pts · Puntaje global +# pts · Ahorro # kg N/ha ($# en la parcela) vs. monocultivo continuo de papa.":
        "Soil +# % (+# pts) · Plant health +# pts · Overall score +# pts · Saves # kg N/ha ($# on the plot) vs. continuous potato monoculture.",
    "Se dio más peso a «Adaptación al clima» porque indicaste que caen heladas.": "More weight was given to «Climate adaptation» because you reported frosts.",
    "Se dio más peso a «Conservación del suelo» porque indicaste que hay erosión.": "More weight was given to «Soil conservation» because you reported erosion.",
    "Se dio más peso a «Conservación del suelo» porque indicaste que la tierra ya no produce como antes.": "More weight was given to «Soil conservation» because you reported the land no longer yields as before.",
    "Se dio más peso a «Uso del agua de lluvia» porque indicaste que falta agua en verano.": "More weight was given to «Use of rainwater» because you reported water shortages in the dry season.",
    "Lluvias intensas moderadas: mantener rastrojo picado o cobertura viva y evitar labores profundas en meses pico.":
        "Moderate heavy rainfall: keep chopped stubble or living cover and avoid deep tillage in peak months.",
    "Opción A · # años · Puntaje #/#": "Option A · # years · Score #/#",
    "Mejora +#% suelo": "Soil +#% better",

    # --- compare tab
    "Compara las opciones frente al manejo sin rotación": "Compare the options against no rotation",
    "Primero genera un plan en la pestaña «Plan de cultivo».": "First generate a plan in the «Crop plan» tab.",
    "Comparación vs.": "Comparison vs.", "Cultivos": "Crops", "Suelo": "Soil", "Clima": "Climate", "Sanidad": "Plant health",
    "Diversidad (familias)": "Diversity (families)", "Riego (m³)": "Irrigation (m³)", "Puntaje": "Score",
    "Línea base": "Baseline", "Testigo suelo:": "Baseline soil:", "Testigo agua:": "Baseline water:", "Testigo sanidad:": "Baseline plant health:",
    "Los puntajes (#-#) son indicadores comparativos del modelo frente al escenario testigo, no mediciones directas de fertilidad (sección #).":
        "Scores (#-#) are the model's comparative indicators against the baseline scenario, not direct fertility measurements (section #).",

    # --- what-if tab
    "¿Qué pasaría si…?": "What would happen if…?", "Escenario": "Scenario", "Año seco (-# % lluvia)": "Dry year (-# % rain)",
    "Año lluvioso (+# % lluvia)": "Wet year (+# % rain)", "Más calor (+# °C)": "Warmer (+# °C)", "Heladas fuertes (-# °C mín.)": "Hard frosts (-# °C min.)",
    "Precio de papa -# %": "Potato price -# %",
    "*# % menos lluvia en todos los meses (similar a un año de La Niña fuerte en la sierra).*": "*# % less rain every month (similar to a strong La Niña year in the highlands).*",
    "Tomar en cuenta la humedad actual de la tierra al inicio": "Take current soil moisture into account at the start",
    "Simular escenario": "Simulate scenario", "Simular": "Simulate",
    "Resultado con **Año seco (-# % lluvia)** (hipotético)": "Result with **Dry year (-# % rain)** (hypothetical)",
    "Puntaje normal": "Normal score", "Puntaje con escenario": "Score with scenario", "Cambio": "Change",
    "Con este escenario, la opción que mejor resiste es la **Opción A**.": "In this scenario, the most resilient option is **Option A**.",
    "Escenario hipotético: no es un pronóstico meteorológico ni de mercado (RN-#).": "Hypothetical scenario: not a weather or market forecast (RN-#).",
    "Detalle técnico de simulación": "Technical simulation detail",
    "Lectura satelital conectada al simulador (NASA SMAP + GPM):": "Satellite reading fed to the simulator (NASA SMAP + GPM):",
    "Humedad superficial SMAP en rango normal (# %, anomalía +# %): simular «Año seco» para estrés en verano.": "SMAP surface moisture in normal range (# %, anomaly +# %): simulate «Dry year» for dry-season stress.",
    "Incorporar anomalía de humedad superficial NASA SMAP al inicio de la simulación": "Include the NASA SMAP surface-moisture anomaly at the start of the simulation",

    # --- saved plans
    "Aún no guardas planes para esta parcela.": "No plans saved for this plot yet.",

    # --- technical data tab
    "Datos de observación de la Tierra (NASA + SoilGrids)": "Earth observation data (NASA + SoilGrids)",
    "Fuente satelital": "Satellite source", "Variables": "Variables", "Resolución": "Resolution", "Validación": "Validation",
    "Calibrada a la referencia local": "Calibrated to the local reference", "Promedio NASA + local": "NASA + local average",
    "Armonización al polígono": "Harmonization to the polygon", "Incertidumbre espacial": "Spatial uncertainty",
    "Curva estacional": "Seasonal curve", "NDVI mensual": "Monthly NDVI", "NDVI promedio": "Average NDVI", "Umbral suelo desnudo (#)": "Bare-soil threshold (#)",
    "Vegetación y suelo desnudo (NDVI)": "Vegetation and bare soil (NDVI)",
    "Serie estacional NDVI (MODIS / Landsat / Sentinel-#) y suelo desnudo": "Seasonal NDVI series (MODIS / Landsat / Sentinel-#) and bare soil",
    "Lluvias intensas (NASA GPM IMERG) y humedad superficial (NASA SMAP)": "Heavy rainfall (NASA GPM IMERG) and surface moisture (NASA SMAP)",
    "Mapa con capas NASA (usa el selector de capas para activar NDVI MODIS)": "Map with NASA layers (use the layer selector to turn on MODIS NDVI)",
    "Fusión de Datos Satelitales y Escalas": "Satellite Data and Scale Fusion",
    "Armonización multiescala al polígono de la parcela:": "Multi-scale harmonization to the plot polygon:",
    "Mes": "Month", "Lluvia mm": "Rain mm", "Lluvia (mm)": "Rain (mm)", "Lluvia usada mm": "Rain used mm", "Lluvia NASA cruda": "Raw NASA rain",
    "Lluvia efectiva": "Effective rain", "Lluvia a usar": "Rain to use", "Lluvia usada / GPM": "Rain used / GPM",
    "Demanda mm": "Demand mm", "Demanda del cultivo (mm)": "Crop demand (mm)", "Déficit mm": "Deficit mm", "Riego mm": "Irrigation mm",
    "Riego necesario (mm)": "Irrigation needed (mm)", "T mín °C": "Min T °C", "T media °C": "Mean T °C", "Riesgo helada": "Frost risk",
    "Días intensos / mes": "Heavy-rain days / month", "GPM días lluvia intensa/mes": "GPM heavy-rain days/month",
    "SMAP humedad superficial (%)": "SMAP surface moisture (%)", "NDVI / SMAP actual": "Current NDVI / SMAP",
    "Pendiente y erosión": "Slope and erosion", "Riesgo bajo (LS #)": "Low risk (LS #)", "Riesgo moderado (LS #)": "Moderate risk (LS #)",
    "Pendiente # % (bajo)": "Slope # % (low)", "Pendiente # % (moderado)": "Slope # % (moderate)",
    "Riesgo de erosión en ladera: bajo (LS #).": "Hillside erosion risk: low (LS #).", "Riesgo de erosión en ladera: moderado (LS #).": "Hillside erosion risk: moderate (LS #).",
    "Altitud (SRTM # m)": "Altitude (SRTM # m)", "Inicio (mes)": "Start (month)",
    "Cada sensor observa la Tierra a una escala espacial distinta.": "Each sensor observes the Earth at a different spatial scale.",
    "Nota agronómica": "Agronomic note", "Respaldo Satelital NASA": "NASA Satellite Backing", "Información": "Information",

    # --- catalog
    "Catálogo de cultivos y reglas": "Crop and rule catalog", "Vista técnica": "Technical view",
    "Base de conocimiento agronómico usada por el motor de recomendaciones": "Agronomic knowledge base used by the recommendation engine",
    "Familia": "Family", "Ciclo (meses)": "Cycle (months)", "Altitud mín.": "Min. altitude", "Altitud máx.": "Max. altitude",
    "Tolerancia a helada": "Frost tolerance", "Tolerancia a sequía": "Drought tolerance", "Necesidad de agua": "Water need",
    "N que necesita (kg/ha)": "N required (kg/ha)", "N que deja (kg/ha)": "N supplied (kg/ha)", "Rendimiento t/ha": "Yield t/ha",
    "Precio $/kg": "Price $/kg", "Costo sin N $/ha": "Cost without N $/ha", "Descripción": "Description", "Kc promedio": "Average Kc",
    "Rendimiento": "Yield", "pH mín.": "pH min.", "pH máx.": "pH max.", "Laboreo": "Tillage", "Residuos": "Residues", "Icono": "Icon",
    "Nombre": "Name", "Estado": "Status", "Regla": "Rule", "Acción": "Action", "Fuente": "Source", "Uso en AgroCycle": "Use in AgroCycle",
    "Edita rendimiento, precio y costo con datos del mercado local.": "Edit yield, price and cost with local market data.",
    "Guardar cambios de precios y rendimientos": "Save price and yield changes",
    "Restricciones agronómicas esenciales (se aplican antes de puntuar)": "Essential agronomic constraints (applied before scoring)",
    "Exigir una leguminosa (R#)": "Require a legume (R#)", "Prioridades (pesos de # a #)": "Priorities (weights from # to #)",
    "**Prioridades (pesos de # a #)**": "**Priorities (weights from # to #)**", "Ciclos en la rotación": "Cycles in the rotation",
    "Condiciones de manejo": "Management conditions", "Limitaciones agronómicas": "Agronomic limitations",
    "Valores referenciales que deben validar los integrantes de agroindustria y ambiental (RN-#).": "Reference values to be validated by the agro-industry and environmental team members (RN-#).",
    "Los parámetros de los cultivos son referenciales y aún no los validan los especialistas del equipo (RN-#).": "Crop parameters are reference values not yet validated by the team's specialists (RN-#).",
    "referencial - pendiente de validación por agroindustria": "reference value - pending agro-industry validation",
    "Otra": "Other", "Ref.": "Ref.",

    # --- about
    "Acerca de AgroCycle": "About AgroCycle",
    "Cómo funciona, fusión multiescala de observación de la Tierra y limitaciones": "How it works, multi-scale Earth-observation fusion and limitations",
    "Herramienta de apoyo a la toma de decisiones para la rotación de cultivos de pequeños productores de Chimborazo, desarrollada para el NASA Space Apps Challenge.":
        "Decision-support tool for crop rotation by smallholder farmers in Chimborazo, built for the NASA Space Apps Challenge.",
    "¿Cómo decide el motor agronómico?": "How does the agronomic engine decide?",
    "Reúne el **historial** de la parcela, lo que indicó el agricultor y las **capas ambientales NASA + SoilGrids**.": "It gathers the plot **history**, what the farmer reported and the **NASA + SoilGrids environmental layers**.",
    "Evalúa todas las secuencias posibles de # etapas anuales o #–# ciclos multianuales y filtra las que incumplen **restricciones esenciales** (como repetir papa antes de # ciclos).":
        "It evaluates every possible sequence of # annual stages or #–# multi-year cycles and filters out those that break **essential constraints** (such as repeating potato within # cycles).",
    "Simula mes a mes el **agua** (lluvia, evapotranspiración, riego y humedad superficial SMAP), el **nitrógeno**, las **heladas**, la **erosión en ladera/lavado** y el **pH**.":
        "It simulates month by month the **water** (rain, evapotranspiration, irrigation and SMAP surface moisture), **nitrogen**, **frost**, **hillside erosion/leaching** and **pH**.",
    "Compara cada plan recomendado contra el **escenario testigo sin rotación** (repetir el mismo cultivo todo el año) y presenta hasta # opciones diferenciadas.":
        "It compares each recommended plan against the **no-rotation baseline** (repeating the same crop all year) and presents up to # distinct options.",
    "Fuentes de observación de la Tierra integradas": "Integrated Earth-observation sources",
    "Integrado (API + respaldo Chimborazo)": "Integrated (API + Chimborazo backup)", "Integrado (OpenTopoData)": "Integrated (OpenTopoData)",
    "Integrado (climatología + capa GIBS)": "Integrated (climatology + GIBS layer)", "Integrado (climatología calibrada)": "Integrated (calibrated climatology)",
    "Integrado (climatología + simulador)": "Integrated (climatology + simulator)", "Integrado (API complementaria)": "Integrated (complementary API)",
    "AgroCycle armoniza estas resoluciones al polígono de la parcela combinando muestreo topográfico fino (# m), corrección térmica por gradiente andino (-# °C/# m), calibración cantonal de lluvia y validación obligatoria en campo.":
        "AgroCycle harmonizes these resolutions to the plot polygon by combining fine topographic sampling (# m), Andean lapse-rate temperature correction (-# °C/# m), canton-level rainfall calibration and mandatory field validation.",
    "Limitaciones y rol irremplazable del técnico": "Limitations and the irreplaceable role of the technician",
    "Es una herramienta **de apoyo**: no reemplaza a un técnico agrícola ni un análisis de suelo de laboratorio.": "It is a **support** tool: it does not replace an agricultural technician or a laboratory soil test.",
    "Los datos satelitales tienen incertidumbre espacial según su resolución (# m en SRTM hasta ~# km en NASA POWER) y no detectan plagas subterráneas (gusano blanco, nematodos), compactación puntual ni turnos reales de agua.":
        "Satellite data carry spatial uncertainty depending on resolution (# m for SRTM up to ~# km for NASA POWER) and cannot detect underground pests (white grub, nematodes), local compaction or actual water turns.",
    "Los parámetros de cultivos, precios y costos son **referenciales** y están pendientes de validación local (RN-#).": "Crop parameters, prices and costs are **reference values** pending local validation (RN-#).",
    "Los escenarios del simulador son **hipotéticos**, no pronósticos meteorológicos ni de mercado.": "Simulator scenarios are **hypothetical**, not weather or market forecasts.",
    "Los resultados son estimaciones orientativas, no garantías de rendimiento ni de precio (RNF-#).": "Results are indicative estimates, not guarantees of yield or price (RNF-#).",
    "Privacidad": "Privacy",
    "Las coordenadas se envían únicamente a NASA POWER, OpenTopoData (SRTM) y SoilGrids para obtener las capas ambientales.": "Coordinates are sent only to NASA POWER, OpenTopoData (SRTM) and SoilGrids to obtain the environmental layers.",
    "Los datos de las parcelas se guardan en la base de datos local SQLite de la aplicación y solo se usan para generar recomendaciones.": "Plot data are stored in the app's local SQLite database and are used only to generate recommendations.",
    "Plagas y patógenos subterráneos: los sensores satelitales no detectan gusano blanco, nematodos ni pudriciones en raíz; inspeccionar al preparar el lote.":
        "Underground pests and pathogens: satellite sensors cannot detect white grub, nematodes or root rot; inspect when preparing the plot.",
    "Compactación y micro-drenaje: las escalas de #–# m no captan sectores puntuales compactados ni pozas locales dentro de la parcela.":
        "Compaction and micro-drainage: #–# m scales do not capture compacted spots or local puddles within the plot.",
    "Disponibilidad real de riego y laboratorio: validar turnos efectivos de agua con la junta y contrastar pH/MO estimados con análisis de suelo local.":
        "Actual irrigation availability and lab tests: validate effective water turns with the board and check estimated pH/OM against local soil analysis.",
    "las resoluciones satelitales varían entre # m (relieve SRTM) y ~# km (climatología NASA POWER).": "satellite resolutions range from # m (SRTM terrain) to ~# km (NASA POWER climatology).",
    "AgroCycle integra cada fuente reduciendo la escala térmica por gradiente andino (-# °C/# m), calibrando lluvia con estaciones cantonales y evaluando la incertidumbre espacial.":
        "AgroCycle integrates each source by downscaling temperature with the Andean lapse rate (-# °C/# m), calibrating rainfall with canton stations and assessing spatial uncertainty.",
    "Uso en AgroCycle": "Use in AgroCycle",

    # --- misc
    "AgroCycle": "AgroCycle", "¿Qué sembrar después de tu cosecha?": "What to sow after your harvest?",
    "Riesgo de heladas en julio": "Frost risk in July", "Caen heladas": "Frosts occur",
    "Lluvias": "Rainfall", "Heladas": "Frost", "heladas": "frost", "Agua": "Water", "Terreno": "Terrain", "Cobertura del suelo": "Soil cover",
    "Riesgo climático bajo": "Low climate risk", "Riesgo climático medio": "Medium climate risk", "Suelo en mejora": "Soil improving",
}

# Crop catalog texts (description and practical tip)
EXACTAS.update({
    "Eje económico de la sierra. Muy exigente en N y en laboreo; gusano blanco, nematodo y lancha obligan a dejar ≥# ciclos sin papa.":
        "Economic backbone of the highlands. Very demanding in N and tillage; white grub, nematodes and late blight require ≥# cycles without potato.",
    "Usa semilla sana, aporca a tiempo y no la vuelvas a sembrar en el mismo lote antes de # siembras.":
        "Use healthy seed, hill on time and do not replant it on the same plot within # plantings.",
    "Fija nitrógeno (deja ~# kg N/ha). Tolera heladas leves. En años lluviosos vigilar mancha de chocolate.":
        "Fixes nitrogen (leaves ~# kg N/ha). Tolerates light frost. In wet years watch for chocolate spot.",
    "Siembra con las primeras lluvias. Después de cosechar, pica las matas y déjalas en el terreno: son abono.":
        "Sow with the first rains. After harvesting, chop the plants and leave them on the field: they are fertilizer.",
    "Propio de valles (Penipe, Chambo, Guano). Muy sensible a heladas; aporta N moderado.": "Typical of valleys (Penipe, Chambo, Guano). Very frost-sensitive; supplies moderate N.",
    "Siémbralo en las partes más abrigadas del terreno: no aguanta heladas.": "Sow it in the most sheltered parts of the field: it does not tolerate frost.",
    "Ciclo largo en altura. Mucho rastrojo (materia orgánica). Rinde más después de una leguminosa.": "Long cycle at altitude. Lots of stubble (organic matter). Yields more after a legume.",
    "Después de cosechar, deja el rastrojo picado en el terreno para que la tierra se haga más negra.": "After harvesting, leave the chopped stubble on the field so the soil gets darker.",
    "Muy rentable pero necesita riego constante. Rompe ciclos de plagas de la papa; no repetir aliáceas (pudrición blanca).":
        "Very profitable but needs constant irrigation. Breaks potato pest cycles; do not repeat Alliaceae (white rot).",
    "Necesita agua seguida: riega poco pero seguido y no la siembres donde hubo ajo.": "Needs regular water: irrigate little but often, and do not sow it where garlic was.",
    "Chimborazo es el principal productor del país. Muy tolerante a sequía y a suelos pobres.": "Chimborazo is the country's main producer. Very tolerant of drought and poor soils.",
    "El gran “abonador” andino: deja hasta ~# kg N/ha y tolera suelos arenosos y ácidos.": "The great Andean “fertilizer”: leaves up to ~# kg N/ha and tolerates sandy, acidic soils.",
    "Es el mejor abonador de la tierra y crece hasta en tierra pobre y suelta.": "It is the best soil fertilizer and grows even in poor, loose soil.",
    "Rústica: aguanta heladas y sequía. Excelente cobertura contra la erosión.": "Hardy: withstands frost and drought. Excellent cover against erosion.",
    "Protege la tierra de la lluvia y el viento; aguanta heladas.": "Protects the soil from rain and wind; tolerates frost.",
    "Buena cobertura y rastrojo; cereal de rotación clásico tras la papa.": "Good cover and stubble; the classic rotation cereal after potato.",
    "Buena opción después de la papa; deja paja para cubrir la tierra.": "A good option after potato; leaves straw to cover the soil.",
    "Ciclo corto y buen precio en vaina verde; fija ~# kg N/ha.": "Short cycle and good price as green pods; fixes ~# kg N/ha.",
    "Cosecha rápida y buen precio en verde; deja abono natural en la tierra.": "Quick harvest and good price when green; leaves natural fertilizer in the soil.",
    "Rentable en Chambo y Guano; laboreo intenso: cuidado en pendientes.": "Profitable in Chambo and Guano; intensive tillage: take care on slopes.",
    "Prepara bien la tierra y no la siembres en terreno muy inclinado sin hacer curvas.": "Prepare the soil well and do not sow it on very steep ground without contour rows.",
    "Tubérculo andino de buen precio; no comparte plagas clave con la papa.": "Well-priced Andean tuber; does not share key pests with potato.",
    "Buena alternativa a la papa en zonas altas; no comparte sus plagas.": "A good alternative to potato in high areas; it does not share its pests.",
    "Rústica para zonas altas; diversifica tubérculos sin repetir solanáceas.": "Hardy for high areas; diversifies tubers without repeating Solanaceae.",
    "Aguanta el frío de las zonas altas; cambia de lugar cada siembra.": "Withstands the cold of high areas; change its location every planting.",
    "Se incorpora al suelo o se usa como forraje: aporta N y materia orgánica y corta ciclos de plagas.": "Ploughed into the soil or used as forage: supplies N and organic matter and breaks pest cycles.",
    "Puedes cortarla para tus animales o virarla con la tierra como abono verde.": "You can cut it for your animals or turn it into the soil as green manure.",
    "Alto valor; no sembrar cerca en el tiempo de la cebolla (pudrición blanca).": "High value; do not sow close in time to onion (white rot).",
    "No lo siembres donde hubo cebolla en la siembra anterior.": "Do not sow it where onion was in the previous planting.",
    "Ciclo corto, exigente en N y agua; no repetir crucíferas (hernia de la col).": "Short cycle, demanding in N and water; do not repeat crucifers (clubroot).",
    "Necesita bastante abono y agua; no repitas col ni brócoli seguido.": "Needs plenty of fertilizer and water; do not repeat cabbage or broccoli back to back.",
    "Forraje para el ganado; cubre bien el suelo y aguanta heladas.": "Forage for livestock; covers the soil well and tolerates frost.",
    "Pradera de descanso: el trébol aporta nitrógeno y el pasto protege y recupera el suelo; da forraje para leche.": "Resting pasture: clover supplies nitrogen and grass protects and restores the soil; gives forage for milk.",
})


# ------------------------------------------------------------------ sentences with variable words
def _ord(m, palabra):
    from ui.i18n import ordinal
    return f"{ordinal(m.group('n'))} {palabra(m.group('c'))}"


PLANTILLAS = [
    (r"Parcelas de (?P<n>.+)", "Plots of {n}"),
    (r"(?P<n>\d+)(?:ro|do|er|to|vo|no|mo)\s+(?P<c>[^→·]+)", _ord),
    (r"(?P<m>[a-záéíóú]+) (?P<y>\d{4})", lambda m, p: f"{p(m.group('m'))} {m.group('y')}"),
    (r"siembra (?P<f>.+)", lambda m, p: "sowing " + " ".join(p(x) for x in m.group("f").split())),
    (r"cosecha (?P<f>.+)", lambda m, p: "harvest " + " ".join(p(x) for x in m.group("f").split())),
    (r"(?:Hay )?[Rr]iesgo de heladas en (?P<m>.+?)(?P<p>\.?)", lambda m, p: f"Frost risk in {p(m.group('m'))}{m.group('p')}"),
    (r"Cuidado con heladas en (?P<m>.+?)\.", "Watch out for frost in {m}."),
    (r"Los meses con más lluvia son (?P<m>.+)\.", "The rainiest months are {m}."),
    (r"Meses críticos de suelo desnudo \(≤ (?P<u>[\d.,]+)\): (?P<m>.+)\.", "Critical bare-soil months (≤ {u}): {m}."),
    (r"Suelo desnudo crítico en (?P<m>.+) \(NDVI <= (?P<u>[\d.,]+)\): riesgo de erosión eólica e hídrica; requiere cultivo de cobertura o rastrojo\.",
     "Critical bare soil in {m} (NDVI <= {u}): wind and water erosion risk; requires a cover crop or stubble."),
    (r"(?P<c>.+?) tiene riesgo de helada en (?P<m>.*?) \(pérdida estimada (?P<x>\d+)%\)\.", "{c} is at risk of frost in {m} (estimated loss {x}%)."),
    (r"(?P<c>.+?) puede sufrir falta de agua \(pérdida estimada (?P<x>\d+)%\)\.", "{c} may suffer water shortage (estimated loss {x}%)."),
    (r"(?P<c>.+?) cubre bien la tierra y la protege de la lluvia y del viento\.", "{c} covers the soil well and protects it from rain and wind."),
    (r"(?P<c>.+?) deja abono natural en la tierra: en la siguiente siembra \((?P<d>.+)\) gastas menos en fertilizante\.",
     "{c} leaves natural fertilizer in the soil: in the next planting ({d}) you spend less on fertilizer."),
    (r"(?P<c>.+?) podría dar pérdida económica con los precios de referencia\.", "{c} could lose money at reference prices."),
    (r"Problemas: (?P<p>.+)", "Problems: {p}"),
    (r"Opción (?P<x>[ABC]): (?P<r>.+)", "Option {x}: {r}"),
    (r"Recomendada", "Recommended"),
    (r"Hay riesgo de heladas en (?P<m>.+)\.", "There is frost risk in {m}."),
]
PLANTILLAS = [(p, r) for p, r in PLANTILLAS]

assert all(isinstance(p, str) for p, _ in PLANTILLAS)
_ = re  # el módulo re se usa al compilar en ui/i18n.py


# ------------------------------------------------------------------ technical view (variable figures)
EXACTAS.update({
    "Plan:": "Plan:", "Correo": "Email", "mm/mes": "mm/month", "# mm/año": "# mm/year", "f agua": "f water", "f helada": "f frost",
    "f altitud": "f altitude", "f rotación": "f rotation", "N residual": "Residual N", "N a aplicar": "N to apply",
    "Mes # del plan": "Month # of the plan", "actual #": "current #", "# m críticos": "# critical months",
    "Ahorro de agua y dinero": "Water and money savings", "¿Qué pasa cuando llueve fuerte?": "What happens in heavy rain?",
    "Ej.: arveja, haba tierna, cebada": "E.g.: pea, green faba bean, barley", "Ej.: avena forrajera, pasto con trébol": "E.g.: forage oat, grass with clover",
    "Ej. Riobamba, Licto": "E.g. Riobamba, Licto", "Ej. Terreno de abajo": "E.g. Lower field", "Ej. Licto, Quimiag, Guamote": "E.g. Licto, Quimiag, Guamote",
    "Fertilización N: ~": "N fertilization: ~", "lavado moderado": "moderate leaching", "lavado moderado.": "moderate leaching.",
    "GPM: # d intensos": "GPM: # heavy-rain days", "GPM IMERG: # días/año de lluvia intensa": "GPM IMERG: # heavy-rain days/year",
    "GPM IMERG: ~# días/año de lluvia intensa (riesgo de lavado moderado).": "GPM IMERG: ~# heavy-rain days/year (moderate leaching risk).",
    "GPM IMERG: # días/año de lluvia intensa · lavado moderado.": "GPM IMERG: # heavy-rain days/year · moderate leaching.",
    "GPM IMERG (~# km): intensidad máx. # mm/día, índice erosividad R ≈ #.": "GPM IMERG (~# km): max. intensity # mm/day, erosivity index R ≈ #.",
    "GPM IMERG (~# km): intensidad máx.": "GPM IMERG (~# km): max. intensity", "# mm/día, índice erosividad R ≈ #.": "# mm/day, erosivity index R ≈ #.",
    "Humedad superficial SMAP: # % (anomalía +# %, estado normal).": "SMAP surface moisture: # % (anomaly +# %, normal status).",
    "NDVI promedio # (actual #; rango estacional #–#).": "Average NDVI # (current #; seasonal range #–#).",
    "El suelo se estimó con SoilGrids (resolución de # m): un análisis de laboratorio sería más exacto.": "Soil was estimated with SoilGrids (# m resolution): a laboratory test would be more accurate.",
    "Descarta los cultivos que no se dan a la altura SRTM de la parcela (regla R#).": "Discards crops that do not grow at the plot's SRTM altitude (rule R#).",
    "Clima: NASA POWER (celda a # m; temperatura corregida +# °C; lluvia modo «mixta»)": "Climate: NASA POWER (cell at # m; temperature corrected +# °C; rainfall mode «mixed»)",
    "Secuencias válidas evaluadas: **#**": "Valid sequences evaluated: **#**", "descartadas por restricciones: **#**": "discarded by constraints: **#**",
    "Altitud: # m (NASA SRTM)": "Altitude: # m (NASA SRTM)",
    "NASA SMAP (#–# km): humedad superficial actual de # % (anomalía hídrica +# %, estado normal), calibrando la reserva de agua inicial y los meses críticos.":
        "NASA SMAP (#–# km): current surface moisture # % (water anomaly +# %, normal status), calibrating the initial water reserve and critical months.",
    "Ahorrar agua": "Save water",
})

PLANTILLAS += [
    (r"Fuentes: (?P<r>.+)", lambda m, p: "Sources: " + m.group("r")),
    (r"(?P<n>[^–]+) – Técnica de extensión agrícola(?P<r>.*)", lambda m, p: f"{m.group('n')} – Agricultural extension technician{m.group('r')}"),
    (r"ph: (?P<v>\*\*[\d.,]+\*\*) \((?P<s>[^)]+)\)", lambda m, p: f"pH: {m.group('v')} ({p(m.group('s'))})"),
    (r"materia_organica: (?P<v>\*\*[\d.,]+\*\*) \((?P<s>[^)]+)\)", lambda m, p: f"organic matter: {m.group('v')} ({p(m.group('s'))})"),
    (r"textura: \*\*(?P<v>[^*]+)\*\* \((?P<s>[^)]+)\)", lambda m, p: f"texture: **{p(m.group('v'))}** ({p(m.group('s'))})"),
    (r"pendiente: (?P<v>\*\*[\d.,]+\*\*) \((?P<s>[^)]+)\)", lambda m, p: f"slope: {m.group('v')} ({p(m.group('s'))})"),
    (r"Suelo: ph = (?P<ph>[\d.,]+) \((?P<a>[^)]+)\), materia_organica = (?P<mo>[\d.,]+) \((?P<b>[^)]+)\), textura = (?P<t>[^ ]+) \((?P<c>[^)]+)\), pendiente = (?P<pe>[\d.,]+) \((?P<d>[^)]+)\)",
     lambda m, p: (f"Soil: pH = {m.group('ph')} ({p(m.group('a'))}), organic matter = {m.group('mo')} ({p(m.group('b'))}), "
                   f"texture = {p(m.group('t'))} ({p(m.group('c'))}), slope = {m.group('pe')} ({p(m.group('d'))})")),
    (r"NASA SRTM \((?P<r>\d+) m\): altitud de (?P<a>[\d.,]+) m \(NASA SRTM\) y pendiente de (?P<s>[\d.,]+) % \(riesgo de erosión en ladera (?P<n>\w+)(?:\. LS (?P<ls>[\d.,]+))?\)?\.?",
     lambda m, p: (f"NASA SRTM ({m.group('r')} m): altitude {m.group('a').replace('.', ',')} m (NASA SRTM) and slope {m.group('s')} % "
                   f"(hillside erosion risk {p(m.group('n'))}" + (f", LS {m.group('ls')}" if m.group('ls') else "") + ").")),
    (r"GPM IMERG \(~(?P<r>\d+) km\) \+ NASA POWER: (?P<mm>[\d.,]+) mm/año y ~(?P<d>\d+) días/año de lluvia intensa \(pico en (?P<m>.+?)\. lavado (?P<l>\w+)\); la lluvia cubre (?P<c>\d+) % de la demanda hídrica del plan\.",
     lambda m, p: (f"GPM IMERG (~{m.group('r')} km) + NASA POWER: {m.group('mm')} mm/year and ~{m.group('d')} heavy-rain days/year "
                   f"(peak in {', '.join(p(x) for x in m.group('m').split('. '))}; {p(m.group('l'))} leaching); rainfall covers {m.group('c')} % of the plan's water demand.")),
    (r"MODIS/Landsat/Sentinel-2 NDVI \((?P<r>[^)]+)\): promedio anual (?P<a>[\d.,]+) \(actual (?P<c>[\d.,]+)\); suelo desnudo detectado en (?P<m>.+) \(riesgo (?P<n>\w+)\), lo que justifica incluir cobertura vegetal\.",
     lambda m, p: (f"MODIS/Landsat/Sentinel-2 NDVI ({m.group('r')}): annual mean {m.group('a')} (current {m.group('c')}); bare soil detected in "
                   f"{p(m.group('m'))} ({p(m.group('n'))} risk), which justifies including vegetation cover.")),
    (r"SMAP (?P<v>[\d.,]+) % \((?P<a>[+-][\d.,]+) %\)", lambda m, p: f"SMAP {m.group('v')} % ({m.group('a')} %)"),
    (r"(?P<n>.+) · Cel\. (?P<t>\d+)", lambda m, p: f"{m.group('n')} · Mob. {m.group('t')}"),
    (r"Cel\. (?P<t>\d+)", lambda m, p: f"Mob. {m.group('t')}"),
]
EXACTAS.update({"PRECTOTCORR (mm/mes)": "PRECTOTCORR (mm/month)", "Normal": "Normal"})

EXACTAS.update({"#º": "#º", "# ha": "# ha", "# m": "# m", "# mm": "# mm", "≈ # cuadras": "≈ # cuadras",
                "Etapa # · Lluvias": "Stage # · Rainy season", "Etapa # · Lluvias (mes # a #)": "Stage # · Rainy season (months # to #)"})
EXACTAS.update({"Pasto ryegrass + trébol (siembra de pasto ryegrass + trébol (queda establecido))":
                "Ryegrass + clover pasture (ryegrass + clover sowing (stays established))"})
EXACTAS.update({"Testigo (Sin rotación)": "Baseline (no rotation)", "Línea base": "Baseline", "Media": "Medium", "Alta": "High", "Baja": "Low"})

# ------------------------------------------------------------------ data-source and rule tables
EXACTAS.update({
    "Lluvia, temperatura media/mín./máx., radiación solar y humedad radicular, corregidas por altitud.": "Rainfall, mean/min./max. temperature, solar radiation and root-zone moisture, corrected for altitude.",
    "Altitud, pendiente (%) y nivel de riesgo de erosión en ladera (factor LS).": "Altitude, slope (%) and hillside erosion risk level (LS factor).",
    "Curva estacional NDVI (#–#), detección de meses críticos de suelo desnudo y alerta de erosión.": "Seasonal NDVI curve (#–#), detection of critical bare-soil months and erosion alert.",
    "Frecuencia de lluvias intensas e intensidad máxima para estimar riesgo de lavado de suelo.": "Frequency of heavy rain and maximum intensity to estimate soil leaching risk.",
    "Humedad superficial del suelo y anomalía hídrica conectadas al simulador de escenarios.": "Surface soil moisture and water anomaly fed to the scenario simulator.",
    "Estimación de pH, materia orgánica y textura USDA cuando no hay análisis de laboratorio.": "Estimates pH, organic matter and USDA texture when there is no laboratory analysis.",
    "Altitud (m) y pendiente (%)": "Altitude (m) and slope (%)", "pH, materia orgánica, arena, arcilla y textura USDA": "pH, organic matter, sand, clay and USDA texture",
    "Índice NDVI mensual (#–#) y suelo desnudo": "Monthly NDVI index (#–#) and bare soil",
    "Frecuencia de lluvias intensas e intensidad máxima (mm/día)": "Heavy-rain frequency and maximum intensity (mm/day)",
    "Humedad superficial, radicular y anomalía hídrica (%)": "Surface and root-zone moisture and water anomaly (%)",
    "Muestreo en cruz de # puntos (paso # m) en torno al centroide del lote.": "Cross-shaped sampling of # points (# m step) around the plot centroid.",
    "Media ponderada #–# cm en el punto; sustituida por datos del agricultor o laboratorio.": "Weighted mean #–# cm at the point; replaced by farmer or laboratory data.",
    "Serie estacional calibrada para Chimborazo y modulada por altitud y lluvia local.": "Seasonal series calibrated for Chimborazo and modulated by altitude and local rainfall.",
    "Cruce con la pendiente SRTM (# m) para estimar lavado e índice de erosividad.": "Combined with SRTM slope (# m) to estimate leaching and the erosivity index.",
    "Ajuste inicial del balance hídrico mensual y conexión con escenarios del simulador.": "Initial adjustment of the monthly water balance and link to simulator scenarios.",
    "Downscaling térmico (-# °C/# m vía SRTM) y calibración con pluviometría cantonal.": "Temperature downscaling (-# °C/# m via SRTM) and calibration with canton rain gauges.",
    "Baja en laderas amplias; moderada en terrazas menores a # m.": "Low on broad slopes; moderate on terraces smaller than # m.",
    "Media-Alta (variabilidad intraparcela requiere muestreo en campo).": "Medium-High (within-plot variability requires field sampling).",
    "Baja-Media (Landsat/Sentinel #–# m cubren parcelas ≥ # ha; MODIS # m mezcla bordes).": "Low-Medium (Landsat/Sentinel #–# m cover plots ≥ # ha; MODIS # m mixes edges).",
    "Media (tormentas convectivas andinas pueden variar dentro de la celda de # km).": "Medium (Andean convective storms can vary within the # km cell).",
    "Alta a escala de lote (se contrasta con riego y drenaje reportados en parcela).": "High at plot scale (checked against irrigation and drainage reported for the plot).",
    "Alta en lluvia orográfica de montaña; reducida mediante calibración cantonal.": "High for orographic mountain rainfall; reduced through canton calibration.",
    "No repetir cultivo": "Do not repeat crop", "Descanso de la papa": "Potato rest period", "Aliáceas no seguidas": "No consecutive Alliaceae",
    "Crucíferas no seguidas": "No consecutive crucifers", "Altitud adecuada": "Suitable altitude", "Incluir una leguminosa": "Include a legume",
    "Encharcamiento": "Waterlogging", "pendiente": "slope",
    "El mismo cultivo no se siembra en dos ciclos seguidos (incluye el último cultivo del historial).": "The same crop is not sown in two consecutive cycles (including the last crop in the history).",
    "Entre dos siembras de solanáceas (papa) debe haber al menos # ciclos de otras familias, contando el historial.": "Between two Solanaceae (potato) plantings there must be at least # cycles of other families, counting the history.",
    "Corta el ciclo del gusano blanco (Premnotrypes vorax), nematodo del quiste y lancha.": "Breaks the cycle of white grub (Premnotrypes vorax), cyst nematode and late blight.",
    "Cebolla y ajo no se suceden (pudrición blanca, Sclerotium cepivorum).": "Onion and garlic do not follow each other (white rot, Sclerotium cepivorum).",
    "Brócoli y otras crucíferas no se suceden (hernia de la col).": "Broccoli and other crucifers do not follow each other (clubroot).",
    "No se recomienda un cultivo a más de # m fuera de su rango de altitud.": "No crop is recommended more than # m outside its altitude range.",
    "Cada rotación incluye al menos una leguminosa o abono verde que aporte nitrógeno (configurable).": "Each rotation includes at least one legume or green manure that supplies nitrogen (configurable).",
    "Si el agricultor reporta encharcamiento, no se recomiendan cultivos sensibles (papa, chocho, quinua).": "If the farmer reports waterlogging, sensitive crops (potato, lupin, quinoa) are not recommended.",
})
EXACTAS.update({
    "Eliminar": "Delete", "Eliminar terreno": "Delete plot", "Terreno eliminado": "Plot deleted",
    "Cancelar": "Cancel", "Sí, eliminar": "Yes, delete",
    "Se borrarán también sus # registros de historial y # planes guardados. Esta acción no se puede deshacer.":
        "Its # history records and # saved plans will also be deleted. This cannot be undone.",
})
PLANTILLAS.append((r"¿Seguro que quieres eliminar \*\*(?P<n>.+)\*\* \((?P<a>[\d.,]+) ha\)\?",
                   lambda m, p: f"Are you sure you want to delete **{m.group('n')}** ({m.group('a').replace('.', '').replace(',', '.')} ha)?"))
