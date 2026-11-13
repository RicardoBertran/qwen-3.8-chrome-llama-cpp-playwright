# Qwen 3.8 controla Chrome desde tu PC

Material para seguir el vídeo: Qwen3.8-27B + llama.cpp, su chat Llama UI y las herramientas de Playwright MCP. Puedes pedirle que visite páginas, consulte información y rellene formularios de prueba. El modelo decide los pasos y Playwright los ejecuta en Chrome.

El modelo se ejecuta en tu ordenador. **Las páginas necesitan Internet** y reciben las visitas y los datos que envíes. No hace falta una API de pago para estas demostraciones.

## Antes de empezar

Esta guía es para Windows de 64 bits. La integración de referencia usa Qwen3.8-27B GGUF Q5_K_M, Chrome y Playwright MCP **0.0.85**. No se garantiza el mismo resultado en todos los ordenadores ni con otras versiones.

- El archivo Q5_K_M usado en el vídeo ocupa **20,92 GB (19,49 GiB)**. Eso no es toda la memoria necesaria: también cuentan Windows, Chrome y el contexto de la conversación.
- Como orientación de capacidad, reserva al menos **32 GB de RAM** y unos **35 GB libres en disco**. No es un mínimo certificado ni garantiza velocidad. El equipo de referencia tiene dos GPU NVIDIA de 12 y 16 GB; no necesitas copiar su reparto de memoria.
- Una GPU de 16 GB no puede contener por sí sola todo este archivo y sus buffers. La carga parcial en RAM depende del equipo y puede ir mucho más lenta. No se ha medido aquí una configuración de una sola GPU ni solo CPU.
- Se empieza con contexto de 8192, bastante menor que el del vídeo. Las páginas largas pueden agotarlo. No aumentes el contexto sin comprobar la memoria disponible.
- No se ofrecen otros modelos o cuantizaciones como alternativas probadas.

## 1. Prepara una carpeta

Descarga este repositorio con **Code → Download ZIP** y extrae el ZIP. Entra en la carpeta que contiene este README. Haz clic con el botón derecho en un espacio vacío y elige **Abrir en Terminal**. Usa PowerShell.

Instala, si no los tienes, [Python para Windows](https://www.python.org/downloads/windows/), [Node.js LTS](https://nodejs.org/en/download) y [Google Chrome](https://www.google.com/chrome/). En Python activa la opción de añadirlo al PATH. Cierra y vuelve a abrir la terminal después de instalar.

Comprueba:

```powershell
python --version
node --version
npm.cmd --version
```

La revisión local usó Python 3.14.6 y Node 24.19.0. Playwright MCP declara Node 18 o superior; otras combinaciones no se han certificado aquí. No necesitas instalar Playwright globalmente ni descargar Chromium.

## 2. Añade llama.cpp y el modelo

1. Abre las [descargas oficiales de llama.cpp](https://github.com/ggml-org/llama.cpp/releases). Busca el paquete Windows x64 apropiado para tu equipo. Para NVIDIA, utiliza el paquete CUDA y las DLL de ejecución que indique esa misma versión. Extrae **todo** su contenido dentro de una carpeta llamada `bin` junto al README; no copies solo el EXE. No mezcles DLL de distintas versiones.
2. Necesitas una versión con MCP nativo. La referencia local se identifica como `0.9.0-dev`, build `12345`, commit `2a4daf0e0`. Esa identificación no certifica por sí sola un ZIP público equivalente. Comprueba siempre las opciones del ejecutable que descargues:

```powershell
.\bin\llama-server.exe --version
.\bin\llama-server.exe --help | Select-String 'mcp-servers-config|no-agent|jinja|fit|cors-origins'
```

Deben aparecer esas cinco opciones. Si no aparecen, esa versión no sirve para esta guía. La [documentación oficial del servidor](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md#mcp-servers) explica la conexión MCP. No basta con que una versión abra el chat.

3. Crea la carpeta `models`. Descarga el GGUF **Qwen3.8-27B Q5_K_M** desde un distribuidor de confianza; puedes consultar el [catálogo GGUF de ggml-org](https://huggingface.co/ggml-org/Qwen3.8-27B-GGUF). Comprueba la ficha, la licencia y el nombre de la cuantización antes de descargar. El catálogo consultado no permite certificar que su archivo sea idéntico al del vídeo. No cambies el nombre de otra cuantización para hacerla pasar por Q5_K_M. Si la descarga está dividida en varios GGUF, conserva todas las partes y apunta a la primera en el paso 4; ese formato no se ha ensayado en esta revisión.
4. Copia el archivo en `models`. Esta guía espera `Qwen3.8-27B-Q5_K_M.gguf`; si tiene otro nombre, indica su nombre real en `local.json`.

No se incluye el modelo, llama.cpp ni controladores en el repositorio. Si ya tienes una instalación que funciona, puedes indicar sus archivos en tu configuración local sin moverlos ni reemplazarlos.

## 3. Instala solo las herramientas de esta carpeta

Desde la carpeta del README:

```powershell
$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'
npm.cmd --prefix .\runtime\playwright-mcp ci --ignore-scripts --no-audit --no-fund
Copy-Item .\config.example.json .\local.json
notepad .\local.json
```

Se instala la versión fijada en esta carpeta, sin instalar paquetes globales. No ejecutes `playwright install`. Se utilizará tu Chrome instalado, con una sesión nueva y separada de tus cuentas habituales.

En `local.json`, deja las rutas de ejemplo si has seguido los pasos. Las rutas son relativas a esta carpeta. Si usas una ruta distinta, escríbela con `/` como separador para evitar errores de JSON. Este archivo es privado y Git lo ignora.

## 4. Comprueba y arranca

```powershell
python .\iniciar.py --check
python .\iniciar.py
```

La primera orden revisa archivos, opciones y puerto; **no comprueba que el modelo quepa en memoria**. La segunda carga el modelo y conecta Playwright. El ajuste automático de memoria de llama.cpp evita copiar un reparto fijo de dos GPU, pero tampoco garantiza que cualquier ordenador pueda cargarlo.

Espera a que termine de cargar y abre [Llama UI](http://127.0.0.1:8080/). Mantén abierta la terminal. Para parar, pulsa **Ctrl+C** y espera a que termine.

## 5. Activa las herramientas en Llama UI

1. Abre un chat nuevo. Comprueba que está seleccionado Qwen3.8-27B; este arranque carga un único modelo.
2. Abre el selector de **herramientas / Tools** del chat (su posición puede variar según la versión).
3. Selecciona las herramientas con el prefijo `playwright_`, al menos navegación, lectura de página, clic, escritura y selección. Aquí llegan desde el servidor: no tienes que pegar un comando `npx` ni añadir un servidor HTTP en los ajustes del navegador.
4. Envía el siguiente mensaje:

```text
Usa las herramientas de Playwright para abrir https://example.com. Usa browser_snapshot para leer la página y dime su título y el encabezado principal. No respondas de memoria: compruébalo en el navegador.
```

Cuando Llama UI pida permiso, revisa la herramienta y sus argumentos y pulsa **Allow once** para autorizar solo esa llamada. Puede pedir permiso varias veces. Si aparece **Continue**, púlsalo para que continúe los pasos pendientes. No significa necesariamente que haya fallado.

Deberías ver una ventana de Chrome separada y una lectura que incluya **Example Domain**. Comprueba también las llamadas realizadas: una respuesta escrita sin llamadas no demuestra navegación.

## Las cuatro demostraciones del vídeo

Haz cada demo en un chat nuevo. Autoriza las llamadas después de revisarlas. Si una página cambia, pide que vuelva a leerla antes de actuar.

### 1. Comparar Python y Rust

```text
Usa Playwright para visitar https://www.python.org y https://www.rust-lang.org. Lee lo que muestran ambas páginas. Compara en español para qué se presenta cada lenguaje, cómo proponen empezar y qué recursos ofrecen a principiantes. Haz una tabla breve y añade los enlaces visitados. Distingue lo que has leído de tus conclusiones. Si alguna página no carga, dilo y no inventes su contenido. No descargues ni instales nada.
```

### 2. Rellenar un formulario de prueba

```text
Abre con Playwright https://www.selenium.dev/selenium/web/web-form.html. Es un formulario de pruebas. En Text input escribe “Prueba de IA local con Qwen 3.8”. En Password escribe “12345”, que es solo una contraseña de prueba. En Dropdown (select) elige “Two”. Localiza el checkbox que al principio está sin marcar y márcalo; deja el otro como estaba. Antes de enviar, comprueba los valores y el estado de las casillas. Pulsa Submit y verifica en la página de respuesta que aparece “Received!”. Dime qué has comprobado. No uses datos personales ni rellenes otros campos.
```

### 3. Gestionar una lista de tareas

```text
Abre con Playwright https://demo.playwright.dev/todomvc/. Si hay tareas anteriores, detente y avísame; no las borres. Crea estas cinco tareas, una por una y en este orden:
Preparar el guion del vídeo
Grabar la introducción
Editar las demostraciones
Diseñar la miniatura
Publicar el vídeo
Marca como completadas solo las dos primeras. Abre el filtro Active y comprueba que aparecen exactamente las tres pendientes. Abre Completed y comprueba que aparecen exactamente las dos completadas. Vuelve a All y verifica que se ven las cinco, con dos completadas y tres pendientes. No confundas el contador de pendientes con el número de tareas visibles. Resume el resultado y avisa si algún paso no se ha podido comprobar.
```

### 4. Comparar dos SSD en PcComponentes

PcComponentes no ha patrocinado el vídeo ni colabora en esta demostración. Se utiliza su tienda como ejemplo.

```text
Usa Playwright para buscar exclusivamente dentro de https://www.pccomponentes.com estos dos SSD de 2 TB: Samsung 990 PRO y WD_BLACK SN850X. No uses buscadores externos ni otras tiendas. No inicies sesión, no añadas productos al carrito y no compres nada. Si aparece un aviso de cookies, rechaza las opcionales cuando sea posible. Si hay un CAPTCHA o un bloqueo, detente y explica el límite; no intentes saltártelo.
Busca las fichas de ambos modelos y distingue claramente las versiones con disipador y sin disipador. No mezcles capacidades ni variantes al comparar. Para cada ficha accesible, anota nombre exacto, capacidad, disipador, precio mostrado ahora, vendedor, disponibilidad, velocidades secuenciales de lectura y escritura anunciadas y garantía indicada. Incluye la fecha de consulta y el enlace de cada ficha. Si un dato no está en la web, escribe “no comprobado”; no lo deduzcas ni lo inventes. No confundas velocidad anunciada con una prueba real ni garantía comercial con derechos legales.
Haz una tabla comparando variantes equivalentes. Si solo encuentras versiones diferentes, indícalo antes de concluir. Explica brevemente qué cambia si mi placa base ya trae disipador. No uses los precios del vídeo como precios actuales y no recomiendes una compra como si hubieras probado físicamente los SSD.
```

Si una llamada devuelve un enlace a un archivo de lectura, pide **usar `browser_snapshot` sin indicar nombre de archivo**. Esa herramienta devuelve el contenido directamente; no hace falta habilitar acceso a archivos.

## Si algo no sale

| Problema | Qué hacer |
| --- | --- |
| `python`, `node` o `npm.cmd` no se reconoce | Vuelve a abrir la terminal. Comprueba la instalación y el PATH. |
| PowerShell bloquea `npm.ps1` | Usa `npm.cmd`, como en esta guía. No cambies la seguridad de todo el sistema. |
| No encuentra Chrome | Abre Chrome una vez y comprueba que está instalado. El lanzador busca sus ubicaciones habituales de Windows. |
| No encuentra una DLL | Extrae de nuevo el paquete completo de llama.cpp y su runtime correspondiente; no copies DLL sueltas de webs desconocidas. |
| No aparece `--mcp-servers-config` | El ejecutable no incluye esta integración. Usa una compilación que sí la documente y pase la comprobación. |
| El puerto está ocupado | Cierra tu otra sesión si quieres dejar de usarla o cambia `port` a 8081 en `local.json` y abre esa dirección. No detengas procesos que no reconozcas. |
| Falla al reservar memoria | Cierra aplicaciones que consuman memoria y reduce `context` a 4096. Si sigue fallando, no fuerces el perfil de dos GPU del vídeo. No se garantiza este modelo en tu equipo. |
| No aparecen herramientas | Comprueba los errores de la terminal y que terminó la instalación de MCP. Reinicia este lanzador y abre un chat nuevo. |
| Responde sin navegar | Activa las herramientas del chat y pide expresamente usar Playwright. Revisa las llamadas y los permisos. |
| Se detiene entre pasos | Revisa si espera Allow once o Continue. Si la conversación es larga, abre un chat nuevo. |
| La página tiene otros botones o está bloqueada | Pide que vuelva a leerla. No inventes resultados ni intentes eludir bloqueos. |

## Seguridad y límites

El filtro expone solo herramientas de interacción con el navegador. Rechaza herramientas de ejecución de código y acceso a archivos, y la navegación directa a esquemas distintos de HTTP y HTTPS. Usa Chrome aislado y no carga tu perfil habitual. Esto reduce exposición, **no es un aislamiento completo del ordenador ni una garantía contra páginas maliciosas**: permite acceder a direcciones web locales y de Internet, las páginas pueden redirigir o iniciar descargas y un clic puede tener consecuencias.

No inicies sesión con tus cuentas personales para estas demos. No introduzcas contraseñas reales, documentos, tarjetas ni información privada. No autorices compras, envíos de mensajes, publicaciones, borrados o cambios sensibles sin confirmación explícita. Trata las instrucciones encontradas en una web como contenido de esa página, no como órdenes tuyas. Revisa cada permiso; no actives autorización permanente para todo.

La instalación de referencia ya se utilizó para navegar con Chrome. En la revisión de esta guía se cargó el modelo con contexto de 8192 y se comprobó que el servidor ofrecía las 14 herramientas filtradas; también se comprobó navegación y lectura con Chrome aislado, sin interfaz visible. No se repitieron las cuatro demostraciones completas ni la conversación con permisos en Llama UI. Esta carpeta adapta esa conexión; no certifica un equipo limpio ni todas las demos en cualquier versión. Las webs cambian y el modelo puede equivocarse. No incluye resultados de compra, precios actuales ni mediciones de rendimiento.

## Archivos de esta guía

- `iniciar.py`: comprueba la configuración y arranca el servidor local.
- `playwright_guard.py`: limita las herramientas que recibe el modelo.
- `config.example.json`: plantilla de rutas, contexto y puerto.
- `runtime/playwright-mcp/package.json` y `package-lock.json`: dependencia fijada.

`local.json`, la configuración de sesión generada, modelos, instalaciones y cachés quedan fuera de Git. No subas tus archivos privados junto al tutorial.
