# =============================================================================
#  ARCHIVO 6 de 7:  servidor.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Es el mesero del restaurante.
#
#  ANALOGÍA COMPLETA DEL PROYECTO:
#     - datos/clientes.py    → la despensa (los ingredientes)
#     - logica/calculos.py   → el prep cook (pica y prepara)
#     - logica/score.py      → el chef (arma el platillo principal)
#     - logica/prediccion.py → el chef de postres
#     - ia/explicador.py     → quien escribe la descripción del menú
#     - servidor.py          → EL MESERO: recibe el pedido de la mesa,
#                              va a la cocina, y regresa con el plato
#     - web/index.html       → el comedor donde se sienta el cliente
#
#  El mesero no cocina. Solo recibe pedidos y entrega resultados.
#
#  ¿QUÉ ES UNA "API"?
#  Son las siglas de "Application Programming Interface". Suena horrible.
#  En la práctica es solo esto: una lista de direcciones a las que la
#  página web le puede pedir cosas.
#
#  Como el menú de un restaurante: cada platillo tiene un nombre, tú lo
#  pides por ese nombre, y te llega. No necesitas saber cómo se cocina.
#
#  NUESTRO MENÚ TIENE 5 PLATILLOS:
#     GET  /                      → la página web
#     POST /api/login             → "¿este correo y clave son válidos?"
#     GET  /api/clientes          → la lista de clientes de ejemplo
#     GET  /api/analisis/{id}     → el análisis completo de una persona
#     POST /api/simular-compra    → "¿qué pasa si compro esto?"
#
#  ¿QUÉ SIGNIFICAN "GET" Y "POST"?
#     GET  = "dame información" (como abrir una página)
#     POST = "aquí te mando datos, haz algo con ellos" (como llenar un
#            formulario y darle enviar)
# =============================================================================


# =============================================================================
#  IMPORTACIONES: las herramientas que necesita este archivo
# =============================================================================

# -----------------------------------------------------------------------------
# FastAPI es la librería que convierte Python en un servidor web.
# Se instala con:  pip install fastapi uvicorn
#
#   - FastAPI      → la clase principal, la aplicación en sí
#   - HTTPException → sirve para responder errores educados
#                     (ej: "404: no encontré ese cliente")
# -----------------------------------------------------------------------------
from fastapi import FastAPI, HTTPException, Header

# -----------------------------------------------------------------------------
# Tipos de respuesta que podemos mandar de vuelta:
#   - FileResponse → mandar un archivo completo (nuestro index.html)
# -----------------------------------------------------------------------------
from fastapi.responses import FileResponse

# -----------------------------------------------------------------------------
# CORS: son las siglas de "Cross-Origin Resource Sharing".
#
# ¿QUÉ PROBLEMA RESUELVE?
# Por seguridad, los navegadores prohíben que una página web le pida datos
# a un servidor que está en otra dirección. Es una protección contra
# páginas maliciosas.
#
# Pero en desarrollo eso estorba: tú abres el HTML desde tu computadora y
# el servidor está en localhost:8000, y el navegador los ve como "distintos"
# y bloquea todo.
#
# Este middleware le dice al navegador "tranquilo, yo autorizo estas
# peticiones". Sin esta línea, la página se vería pero saldría vacía.
# -----------------------------------------------------------------------------
from fastapi.middleware.cors import CORSMiddleware

# -----------------------------------------------------------------------------
# "BaseModel" de Pydantic sirve para describir qué forma deben tener los
# datos que llegan. Lo usamos más abajo para el endpoint de simular compra.
# -----------------------------------------------------------------------------
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# "os" para trabajar con rutas de archivos del sistema.
# -----------------------------------------------------------------------------
import os

# -----------------------------------------------------------------------------
# Y ahora traemos NUESTROS propios archivos, los que escribimos nosotros.
# Fíjate que el nombre después de "from" es la carpeta, y después del
# "import" es la función.
# -----------------------------------------------------------------------------
from logica.calculos import analizar_cliente
from logica.score import calcular_score
from logica.prediccion import predecir_21_dias, simular_compra
from ia.explicador import explicar_con_ia

# -----------------------------------------------------------------------------
# LA CAPA DE SEGURIDAD (lo nuevo).
#
# Fíjate que YA NO importamos nada de datos/clientes.py. Ese archivo quedó
# como la semilla: de ahí salieron los datos que ahora viven en la base.
# Todo el acceso a datos pasa ahora por estas funciones vigiladas.
#
#   intentar_entrar        → revisa correo y contraseña, reparte la pulsera
#   revisar_pulsera        → dice de quién es un token, o None si no sirve
#   quitar_pulsera         → cerrar sesión
#   leer_bitacora          → el diario de seguridad (solo para el admin)
#   traer_ficha_completa   → los datos de UNA persona, con RLS aplicado
#   traer_lista_de_clientes→ la lista completa, solo si eres admin
#   construir_la_base      → crea banco.db la primera vez que arrancas
# -----------------------------------------------------------------------------
from seguridad.guardia import (
    intentar_entrar,
    revisar_pulsera,
    quitar_pulsera,
    leer_bitacora,
)
from seguridad.consultas import traer_ficha_completa, traer_lista_de_clientes
from seguridad.base_datos import construir_la_base


# =============================================================================
#  CREAR LA APLICACIÓN
# =============================================================================

# -----------------------------------------------------------------------------
# Esta línea crea el servidor. La variable "app" es la aplicación completa.
#
# El "title" y la "description" aparecen en la documentación automática
# que FastAPI genera solita en http://localhost:8000/docs
#
# ESE /docs ES UN REGALO PARA LA PRESENTACIÓN: puedes abrirlo frente a los
# jueces y probar la API en vivo sin escribir una sola línea de código.
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Consola de Liquidez",
    description="Score de crédito y predicción de flujo para trabajadores independientes",
    version="1.0",
)

# -----------------------------------------------------------------------------
# Activamos el permiso CORS que explicamos arriba.
#
#   allow_origins=["*"]  → el asterisco significa "desde cualquier lado".
#                          Está bien para un hackathon o desarrollo local.
#                          En un banco real aquí irían solo las direcciones
#                          autorizadas, nunca un asterisco.
#   allow_methods=["*"]  → permite GET, POST, y todos los demás.
#   allow_headers=["*"]  → permite cualquier encabezado.
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
#  PLATILLO 1:  GET /
#  Entrega la página web
# =============================================================================

# -----------------------------------------------------------------------------
# ¿QUÉ ES ESA LÍNEA QUE EMPIEZA CON @?
# Se llama "decorador". Es una etiqueta que le pegas a una función para
# decirle a FastAPI "cuando alguien entre a esta dirección, corre esta
# función".
#
# @app.get("/") significa: cuando alguien abra la raíz del sitio
# (http://localhost:8000/), ejecuta la función que está justo abajo.
# -----------------------------------------------------------------------------
@app.get("/")
def mostrar_pagina():

    # -------------------------------------------------------------------------
    # Armamos la ruta hasta el archivo index.html.
    #
    # ¿Por qué no escribimos "web/index.html" y ya?
    # Porque esa ruta depende de desde dónde ejecutes el programa. Si lo
    # corres desde otra carpeta, no lo encuentra.
    #
    # Desglose de la línea:
    #   __file__                 → la ruta de ESTE archivo (servidor.py)
    #   os.path.abspath(...)     → la vuelve una ruta completa desde la raíz
    #   os.path.dirname(...)     → se queda con la carpeta que lo contiene
    #   os.path.join(a, b, c)    → pega pedazos de ruta usando el separador
    #                              correcto según el sistema (\ en Windows,
    #                              / en Mac y Linux). Por eso nunca escribas
    #                              las diagonales a mano.
    # -------------------------------------------------------------------------
    carpeta_de_este_archivo = os.path.dirname(os.path.abspath(__file__))
    ruta_del_html = os.path.join(carpeta_de_este_archivo, "web", "index.html")

    # -------------------------------------------------------------------------
    # Y lo mandamos como respuesta. El navegador lo recibe y lo dibuja.
    # -------------------------------------------------------------------------
    return FileResponse(ruta_del_html)


# =============================================================================
#  PLATILLO NUEVO:  POST /api/login
#  La puerta de entrada. Revisa correo y contraseña.
# =============================================================================

# -----------------------------------------------------------------------------
# Igual que con la compra, describimos qué datos van a llegar.
# La página web va a mandar un paquete con esta forma exacta:
#
#     { "correo": "maria", "contrasena": "123" }
#
# Los dos son "str" (texto). Si alguien manda un número o le falta un campo,
# FastAPI lo rechaza solo, antes de que llegue a nuestro código.
# -----------------------------------------------------------------------------
class DatosDelLogin(BaseModel):
    correo: str
    contrasena: str


# =============================================================================
#  EL TORNIQUETE
#
#  Estas dos funciones se llaman al principio de CASI TODOS los endpoints.
#  Son el punto donde se revisa la pulsera antes de dejar pasar a alguien.
# =============================================================================

# -----------------------------------------------------------------------------
#  FUNCIÓN:  sacar_token
#
#  Saca el token del encabezado de la petición.
#
#  ¿QUÉ ES UN "ENCABEZADO" (header)?
#  Cada petición de internet lleva dos partes: el contenido (lo que pides) y
#  los encabezados (datos sobre la petición: qué navegador eres, qué idioma
#  hablas, quién eres). El token va en un encabezado llamado "Authorization".
#
#  ¿POR QUÉ EN UN ENCABEZADO Y NO EN LA DIRECCIÓN?
#  Porque las direcciones se guardan en el historial del navegador, en los
#  registros del servidor, y se ven completas en el marcador cuando compartes
#  un enlace. Un token en la dirección acabaría escrito en cinco lugares
#  distintos. Los encabezados no se guardan en ninguno de esos.
#
#  El formato estándar es:   Authorization: Bearer abc123...
#  "Bearer" significa "portador": quien traiga esto, es quien dice ser.
# -----------------------------------------------------------------------------
def sacar_token(encabezado_authorization):

    # Si no mandaron nada, no hay token.
    if not encabezado_authorization:
        return None

    # -------------------------------------------------------------------------
    # .replace("Bearer ", "") quita la palabra "Bearer " del principio y deja
    # solo el token. Si no venía, no pasa nada, devuelve el texto igual.
    # .strip() quita espacios sobrantes.
    # -------------------------------------------------------------------------
    return encabezado_authorization.replace("Bearer ", "").strip()


# -----------------------------------------------------------------------------
#  FUNCIÓN:  quien_esta_pidiendo
#
#  Recibe el encabezado, revisa la pulsera, y devuelve quién es.
#  Si la pulsera no sirve, corta la petición ahí mismo con un error 401.
#
#  ¿POR QUÉ CORTA AQUÍ Y NO DEVUELVE None?
#  Porque así es IMPOSIBLE que a un programador se le olvide revisar el
#  resultado. Si devolviera None, alguien podría escribir:
#
#      usuario = quien_esta_pidiendo(auth)   # devuelve None
#      datos = traer_ficha(usuario["id"])    # ...y truena o peor, pasa
#
#  Con "raise" la ejecución se detiene en seco y nunca llega a la siguiente
#  línea. El error es imposible de ignorar. A este patrón se le llama
#  "fallar en seguro" (fail closed): ante la duda, se cierra, no se abre.
# -----------------------------------------------------------------------------
def quien_esta_pidiendo(encabezado_authorization):

    token = sacar_token(encabezado_authorization)
    usuario = revisar_pulsera(token)

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Tu sesión venció o no has iniciado sesión",
        )

    return usuario


@app.post("/api/login")
def endpoint_login(datos: DatosDelLogin):

    # -------------------------------------------------------------------------
    # Le preguntamos al guardia (seguridad/guardia.py) si estos datos sirven.
    #
    # Fíjate que el servidor NO compara contraseñas él mismo, ni las ve nunca.
    # Solo pregunta y recibe un sí o un no. Toda la lógica de revolver y
    # comparar vive en un solo archivo, que es el que hay que auditar.
    # -------------------------------------------------------------------------
    sesion = intentar_entrar(datos.correo, datos.contrasena)

    # -------------------------------------------------------------------------
    # Si el guardia devolvió None, los datos no sirven.
    #
    # El código 401 significa "no autorizado" en el idioma de internet. Es el
    # código correcto para "tus datos de acceso están mal" (el 404 sería
    # "no existe" y el 403 sería "sé quién eres pero no te dejo").
    #
    # ⚠️ DETALLE DE SEGURIDAD REAL:
    # El mensaje dice "correo o contraseña incorrectos", sin decir CUÁL de
    # los dos falló, y es EL MISMO mensaje si la cuenta está bloqueada.
    #
    # Si dijéramos "esa contraseña está mal", le confirmaríamos a un atacante
    # que ese correo SÍ existe en el banco. Y si dijéramos "cuenta bloqueada",
    # le confirmaríamos lo mismo. A eso se le llama "enumeración de usuarios":
    # armar la lista de clientes del banco solo probando correos. Los bancos
    # de verdad dan un mensaje vago aquí, siempre, a propósito.
    # -------------------------------------------------------------------------
    if sesion is None:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    # -------------------------------------------------------------------------
    # Si sí pasó, le devolvemos la pulsera (el token) y lo mínimo para saludarlo.
    #
    # NO devolvemos la contraseña, ni la sal, ni sus movimientos. Regla de oro:
    # una respuesta nunca debe traer más datos de los que hacen falta.
    #
    # El "rol" sí va, porque la página necesita saber qué panel mostrar.
    # Pero ojo: la página lo usa solo para DIBUJAR. El permiso de verdad lo
    # revisa el servidor en cada petición. Si alguien edita el rol en su
    # navegador para poner "admin", vería el panel vacío y cada petición le
    # respondería 403. Nunca confíes en lo que dice el navegador.
    # -------------------------------------------------------------------------
    return {
        "entro": True,
        "token": sesion["token"],
        "id": sesion["id"],
        "nombre": sesion["nombre"],
        "profesion": sesion["profesion"],
        "rol": sesion["rol"],
    }


# =============================================================================
#  PLATILLO 2:  POST /api/salir
#  Cerrar sesión: destruye la pulsera
# =============================================================================

# -----------------------------------------------------------------------------
# ¿POR QUÉ HACE FALTA UN ENDPOINT PARA SALIR?
#
# Uno pensaría que basta con que la página olvide el token. Pero si el token
# sigue siendo válido en el servidor, alguien que lo haya copiado (de un café
# internet, de un historial, de la memoria del navegador) puede seguirlo
# usando los 30 minutos que le quedan.
#
# Al borrarlo de la tabla sesiones, deja de funcionar en ese instante.
# -----------------------------------------------------------------------------
@app.post("/api/salir")
def endpoint_salir(authorization: str = Header(default="")):
    token = sacar_token(authorization)
    if token:
        quitar_pulsera(token)
    return {"salio": True}


# =============================================================================
#  PLATILLO 3:  GET /api/analisis/{id_del_cliente}
#  EL PLATILLO PRINCIPAL: hace todo el análisis de una persona
# =============================================================================

# -----------------------------------------------------------------------------
# Fíjate en las llaves { } dentro de la dirección: eso marca una parte
# VARIABLE de la ruta. Lo que el usuario escriba ahí llega como parámetro
# de la función.
#
#   /api/analisis/maria   →  id_del_cliente = "maria"
#   /api/analisis/carlos  →  id_del_cliente = "carlos"
# -----------------------------------------------------------------------------
@app.get("/api/analisis/{id_del_cliente}")
def endpoint_analisis(id_del_cliente: str, authorization: str = Header(default="")):

    # =========================================================================
    #  PASO 0 — EL TORNIQUETE (esto es lo nuevo, y es lo importante)
    #
    #  Antes de tocar un solo dato, revisamos la pulsera. Si no sirve, esta
    #  línea lanza el error 401 y la función termina aquí mismo.
    # =========================================================================
    usuario = quien_esta_pidiendo(authorization)

    # =========================================================================
    #  PASO 1 — Buscar a la persona, CON EL RLS PUESTO
    #
    #  Fíjate bien en los tres datos que le pasamos:
    #
    #     usuario["id"]   → quién está pidiendo    (ej: "maria")
    #     usuario["rol"]  → con qué permisos       (ej: "cliente")
    #     id_del_cliente  → de quién quiere datos  (ej: "carlos")
    #
    #  Los dos primeros salen de LA PULSERA, no de lo que mandó la página.
    #  Esa es toda la diferencia: el usuario puede escribir lo que quiera en
    #  la dirección, pero no puede falsificar quién es, porque eso lo dice el
    #  token que solo el servidor pudo haber creado.
    #
    #  Entonces si María escribe a mano /api/analisis/carlos en su navegador,
    #  la función recibe ("maria", "cliente", "carlos") y el RLS no le da nada.
    # =========================================================================
    cliente = traer_ficha_completa(usuario["id"], usuario["rol"], id_del_cliente)

    # -------------------------------------------------------------------------
    # Si no hay nada, puede ser por dos razones: ese cliente no existe, o
    # existe pero no es tuyo.
    #
    # ⚠️ DETALLE DE SEGURIDAD:
    # Respondemos 404 ("no encontrado") en los DOS casos, no 403 ("prohibido").
    #
    # ¿Por qué? Porque un 403 le confirmaría al atacante que ese cliente SÍ
    # existe, solo que no es suyo. Probando ids uno por uno podría armar la
    # lista completa de clientes del banco sin ver un solo dato. Con el 404
    # no distingue entre "no existe" y "no es tuyo", así que no aprende nada.
    # -------------------------------------------------------------------------
    if cliente is None:
        raise HTTPException(status_code=404, detail="No encontré ese cliente")

    # =========================================================================
    #  PASO 2 — Sacar los 9 indicadores
    #  (esto llama a logica/calculos.py)
    # =========================================================================
    analisis = analizar_cliente(cliente)

    # =========================================================================
    #  PASO 3 — Calcular el puntaje de crédito
    #  (esto llama a logica/score.py, que usa lo del paso 2)
    # =========================================================================
    resultado_score = calcular_score(analisis)

    # =========================================================================
    #  PASO 4 — Predecir los próximos 21 días
    #  (esto llama a logica/prediccion.py)
    # =========================================================================
    prediccion = predecir_21_dias(analisis)

    # =========================================================================
    #  PASO 5 — Pedirle a la IA que lo explique bonito
    #  (esto llama a ia/explicador.py, y le pasa TODO lo anterior ya
    #   calculado, para que la IA solo redacte)
    # =========================================================================
    consejo = explicar_con_ia(analisis, resultado_score, prediccion)

    # =========================================================================
    #  PASO 6 — Empaquetar todo y mandarlo de regreso
    # =========================================================================

    # -------------------------------------------------------------------------
    # IMPORTANTE: el ORDEN de estos 5 pasos no es negociable.
    #
    # El paso 3 necesita el resultado del paso 2.
    # El paso 4 necesita el resultado del paso 2.
    # El paso 5 necesita los resultados del 2, 3 y 4.
    #
    # A esto se le llama una "cadena de dependencias". Si intentaras correr
    # el paso 5 primero, no tendría con qué trabajar.
    # -------------------------------------------------------------------------
    return {
        "analisis": analisis,
        "score": resultado_score,
        "prediccion": prediccion,
        "consejo": consejo,
    }


# =============================================================================
#  PLATILLO 4:  GET /api/admin/clientes
#  La lista de todos los clientes. SOLO para el administrador.
# =============================================================================
@app.get("/api/admin/clientes")
def endpoint_admin_clientes(authorization: str = Header(default="")):

    # Torniquete: ¿quién eres?
    usuario = quien_esta_pidiendo(authorization)

    # -------------------------------------------------------------------------
    # traer_lista_de_clientes devuelve None si quien pide no es admin.
    # La revisión del rol está adentro de esa función (seguridad/consultas.py
    # línea 150), no aquí, para que haya un solo lugar donde se decide.
    # -------------------------------------------------------------------------
    lista = traer_lista_de_clientes(usuario["id"], usuario["rol"])

    # -------------------------------------------------------------------------
    # Aquí SÍ usamos 403 ("prohibido") en vez de 404, y es a propósito.
    #
    # ¿No dijimos arriba que 403 filtra información? Sí, pero aquí no filtra
    # nada: la dirección /api/admin/clientes ya se ve en el código de la
    # página web. Que exista un panel de administrador no es un secreto.
    # El secreto son los datos, y esos no salen.
    #
    # La regla real es: el 403 se evita cuando revela si algo EXISTE. Aquí
    # solo confirma lo que ya se sabía.
    # -------------------------------------------------------------------------
    if lista is None:
        raise HTTPException(
            status_code=403,
            detail="Esta sección es solo para el personal del banco",
        )

    return {"clientes": lista}


# =============================================================================
#  PLATILLO 5:  GET /api/admin/bitacora
#  El diario de seguridad. SOLO para el administrador.
# =============================================================================
@app.get("/api/admin/bitacora")
def endpoint_admin_bitacora(authorization: str = Header(default="")):

    usuario = quien_esta_pidiendo(authorization)

    # -------------------------------------------------------------------------
    # Esta revisión sí va aquí mismo, porque leer_bitacora() no tiene RLS:
    # la bitácora no es de nadie en particular, es del banco.
    #
    # Por eso el candado tiene que estar antes de llamarla.
    # -------------------------------------------------------------------------
    if usuario["rol"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Esta sección es solo para el personal del banco",
        )

    return {"bitacora": leer_bitacora(50)}


# =============================================================================
#  PLATILLO 6:  POST /api/simular-compra
#  "¿Qué pasa si compro esto?"
# =============================================================================

# -----------------------------------------------------------------------------
# Para las peticiones POST hay que describir qué datos van a llegar.
# Esta clase es esa descripción.
#
# ¿Qué es "class ... (BaseModel)"?
# Estamos creando un molde de datos. Le decimos a FastAPI: "los datos que
# lleguen aquí deben tener un texto llamado id_del_cliente y un número
# llamado monto".
#
# LO BUENO: FastAPI revisa esto SOLO. Si alguien manda un monto como texto
# ("cien pesos" en vez de 100), FastAPI lo rechaza automáticamente con un
# mensaje claro, antes de que llegue a nuestro código. Nos ahorra escribir
# un montón de validaciones a mano.
#
# Los ":" indican el TIPO de dato:
#   str   = texto
#   float = número con decimales
# -----------------------------------------------------------------------------
class DatosDeLaCompra(BaseModel):
    id_del_cliente: str
    monto: float


@app.post("/api/simular-compra")
def endpoint_simular_compra(datos: DatosDeLaCompra, authorization: str = Header(default="")):

    # Torniquete, igual que en los otros.
    usuario = quien_esta_pidiendo(authorization)

    # -------------------------------------------------------------------------
    # Buscamos al cliente con el RLS puesto.
    #
    # Aquí hay una trampa clásica que vale la pena señalar: el id viene dentro
    # del paquete que mandó la PÁGINA, y la página está en la computadora del
    # usuario, donde él puede cambiar lo que quiera con la consola del
    # navegador. Si confiáramos en ese id, cualquiera podría simular compras
    # sobre la cuenta de otro y deducir su saldo por el resultado.
    #
    # Como el RLS usa el id de la PULSERA y no el del paquete, mandar el id
    # de otro simplemente no devuelve nada.
    # -------------------------------------------------------------------------
    cliente = traer_ficha_completa(usuario["id"], usuario["rol"], datos.id_del_cliente)

    if cliente is None:
        raise HTTPException(status_code=404, detail="No encontré ese cliente")

    # -------------------------------------------------------------------------
    # Revisamos que el monto tenga sentido. Nadie puede comprar algo que
    # cuesta menos de cero pesos.
    #
    # El código 400 significa "petición mal hecha, es culpa de quien pidió".
    # -------------------------------------------------------------------------
    if datos.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a cero")

    # -------------------------------------------------------------------------
    # Sacamos los indicadores y corremos la simulación.
    # -------------------------------------------------------------------------
    analisis = analizar_cliente(cliente)
    resultado = simular_compra(analisis, datos.monto)

    return resultado


# =============================================================================
#  ARRANQUE DEL SERVIDOR
# =============================================================================

# -----------------------------------------------------------------------------
# ¿QUÉ ES ESTE "if" TAN RARO?
#
#   if __name__ == "__main__":
#
# "__name__" es una variable secreta que Python le pone a cada archivo.
# Vale "__main__" solo cuando ejecutas ESE archivo directamente.
# Si otro archivo lo importa, vale el nombre del archivo.
#
# Traducción: "si me están ejecutando a mí directamente, arranca el
# servidor; si solo me están importando, no hagas nada".
#
# Es la forma estándar en Python de poner código que solo debe correr al
# ejecutar el archivo.
#
# PARA ARRANCARLO, en la terminal:
#     python servidor.py
#
# Y luego abres en el navegador:  http://localhost:8000
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # -------------------------------------------------------------------------
    # "uvicorn" es el programa que realmente atiende las conexiones de
    # internet. FastAPI define QUÉ responder; uvicorn se encarga de
    # escuchar el puerto y hablar el idioma de la red.
    #
    # Se instala con:  pip install uvicorn
    # -------------------------------------------------------------------------
    import uvicorn

    # -------------------------------------------------------------------------
    # ANTES DE ARRANCAR, NOS ASEGURAMOS DE QUE LA BASE DE DATOS EXISTA.
    #
    # construir_la_base() revisa si ya hay usuarios guardados:
    #   - Si la base está vacía o no existe, la crea y copia los 3 clientes.
    #   - Si ya tenía datos, no hace nada y devuelve False.
    #
    # Por eso es seguro llamarla en cada arranque: no duplica nada ni borra
    # lo que ya había. A una operación que puedes repetir sin que cambie el
    # resultado se le llama "idempotente".
    # -------------------------------------------------------------------------
    se_creo_ahora = construir_la_base()

    # -------------------------------------------------------------------------
    # Los ajustes del arranque:
    #
    #   app        → nuestra aplicación de allá arriba
    #   host       → "127.0.0.1" significa "solo esta computadora".
    #                Es lo seguro para desarrollo. Si pusieras "0.0.0.0",
    #                cualquiera en tu red wifi podría entrar.
    #   port       → 8000 es el puerto. Un puerto es como el número de
    #                departamento en un edificio: la computadora es el
    #                edificio, y cada programa que escucha internet ocupa
    #                un departamento distinto.
    #   reload     → True hace que el servidor se reinicie solo cada vez
    #                que guardas un cambio en el código. Comodísimo mientras
    #                programas. En producción SIEMPRE va en False.
    # -------------------------------------------------------------------------
    print("")
    if se_creo_ahora:
        print("  Base de datos creada por primera vez (banco.db)")
        print("")
    print("  Servidor listo. Abre esta dirección en tu navegador:")
    print("  http://localhost:8000")
    print("")
    print("  CUENTAS DE PRUEBA")
    print("    Cliente:        maria / 123   (también carlos y ana)")
    print("    Administrador:  admin / admin123")
    print("")
    print("  (para apagarlo, presiona Ctrl + C)")
    print("")

    uvicorn.run(app, host="127.0.0.1", port=8000)
