# =============================================================================
#  ARCHIVO 1 de 11:  datos/clientes.py
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Guarda la información de 3 personas de ejemplo (clientes del banco).
#  Es como una libreta donde anotamos: cuánto dinero tiene cada uno,
#  cuánto le pagaron sus clientes, y qué gastos fijos tiene cada mes.
#
#  ¿POR QUÉ EXISTE?
#  Para que la aplicación funcione aunque no tengamos internet ni la API
#  del banco. Estos datos tienen EXACTAMENTE la misma forma que los que
#  devuelve la API real de Capital One (llamada "Nessie"), así que el
#  resto del programa no nota la diferencia.
#
#  ---------------------------------------------------------------------------
#  ⚠️ LEE ESTO ANTES DE MODIFICAR ALGO AQUÍ
#
#  Este archivo YA NO es de donde el programa lee los datos mientras corre.
#  Ahora es la SEMILLA: se lee UNA SOLA VEZ, la primera vez que arrancas el
#  proyecto, para copiar estos datos a la base de datos (banco.db).
#
#  ¿Por qué cambió? Porque un diccionario de Python no puede tener reglas de
#  quién ve qué. Con estos datos en memoria, cualquier parte del programa
#  podía leer la información de las tres personas. Al pasarlos a una base de
#  datos les pudimos poner RLS, que es la regla de "cada quien ve lo suyo".
#  Está explicado en seguridad/guardia.py.
#
#  ENTONCES, SI CAMBIAS UN NÚMERO DE AQUÍ:
#     1. Borra el archivo banco.db de la carpeta del proyecto
#     2. Vuelve a arrancar el servidor (python servidor.py)
#     3. La base se reconstruye sola con tus cambios
#
#  Si solo cambias el número y arrancas, no verás nada distinto: el programa
#  seguirá leyendo de la base vieja, que ya tenía el número anterior.
#  ---------------------------------------------------------------------------
# =============================================================================


# -----------------------------------------------------------------------------
# LÍNEA 1: Traemos herramientas de fecha que ya vienen incluidas en Python.
#
# ¿Qué es "from ... import ..."?  Es como decir "de esta caja de herramientas,
# sácame solo estas dos". No instalas nada, ya vienen con Python.
#
#   - "date"      = sirve para representar un día del calendario (ej: 2026-09-13)
#   - "timedelta" = sirve para SUMAR o RESTAR días a una fecha
#                   (ej: hoy - 30 días = hace un mes)
# -----------------------------------------------------------------------------
from datetime import date, timedelta


# -----------------------------------------------------------------------------
# LÍNEA 2: Guardamos la fecha de HOY en una variable.
#
# "date.today()" es una función de la librería datetime que pregunta al
# sistema operativo qué día es hoy y devuelve algo como: 2026-09-13
#
# Usamos una variable llamada HOY (en MAYÚSCULAS) porque en Python la
# costumbre es escribir en mayúsculas las cosas que NO van a cambiar
# durante el programa. A eso se le llama "constante".
# -----------------------------------------------------------------------------
HOY = date.today()


# -----------------------------------------------------------------------------
# LÍNEA 3: Creamos nuestra propia función auxiliar (ayudante).
#
# ¿Qué es una "función"?  Es una receta con nombre. La escribes una vez y la
# usas muchas veces. Esta se llama "hace_dias".
#
# ¿Qué hace?  Le das un número (por ejemplo 30) y te devuelve la fecha de
# hace 30 días, escrita como texto: "2026-08-14".
#
# ¿Por qué la necesitamos?  Porque queremos que los datos de ejemplo SIEMPRE
# sean recientes. Si escribiéramos fechas fijas como "2025-01-15", en unos
# meses la demo mostraría datos viejos y las gráficas saldrían vacías.
#
# Desglose de la línea de adentro:
#   HOY - timedelta(days=n)  →  resta n días a la fecha de hoy
#   .isoformat()             →  convierte la fecha a texto "AAAA-MM-DD"
#                               (isoformat es una función que ya trae el
#                                objeto fecha de Python)
# -----------------------------------------------------------------------------
def hace_dias(n):
    return (HOY - timedelta(days=n)).isoformat()


# -----------------------------------------------------------------------------
# LÍNEA 4: Otra función ayudante, pero al revés: mira hacia el FUTURO.
#
# Le das un número (por ejemplo 5) y te devuelve la fecha de dentro de
# 5 días, como texto. La usamos para decir "tu renta se paga en 5 días".
# -----------------------------------------------------------------------------
def en_dias(n):
    return (HOY + timedelta(days=n)).isoformat()


# =============================================================================
#  AQUÍ EMPIEZAN LOS DATOS DE LOS CLIENTES
#
#  ¿Qué es un "diccionario" en Python?
#  Es una lista de parejas "etiqueta: valor", escrita entre llaves { }.
#  Funciona como una ficha de datos:
#
#      { "nombre": "María", "edad": 28 }
#
#  Para leer un dato le pides su etiqueta:  ficha["nombre"]  →  "María"
#
#  ¿Qué es una "lista"?
#  Es una fila de cosas, escrita entre corchetes [ ].
#  Ejemplo:  [10, 20, 30]  o  [{...}, {...}]  (una lista de diccionarios)
# =============================================================================


# =============================================================================
# ---------------------------- CLIENTE NÚMERO 1 -------------------------------
#
#  MARÍA — Diseñadora gráfica independiente (freelance)
#
#  PERFIL EN UNA FRASE: gana bien, pero sus pagos llegan cuando quieren,
#  y gasta casi todo lo que gana. Riesgo MEDIO.
#
#  Ella es nuestro caso "normal": el típico freelancer al que un banco
#  tradicional le diría que no, aunque en realidad sí puede pagar.
# =============================================================================
MARIA = {

    # -------------------------------------------------------------------------
    # Identificador único del cliente dentro del sistema.
    # Es como su número de cuenta. Nunca se repite entre clientes.
    # La interfaz web manda este texto al servidor para pedir "dame los
    # datos de este cliente".
    # -------------------------------------------------------------------------
    "id": "maria",

    # Nombre para mostrar en pantalla. Solo es decorativo.
    "nombre": "María Fernanda",

    # A qué se dedica. Solo es decorativo, se muestra en la tarjeta.
    "profesion": "Diseñadora gráfica",

    # -------------------------------------------------------------------------
    # DATOS PARA INICIAR SESIÓN (login)
    #
    # ¿QUÉ ES UN "LOGIN"?
    # Es la puerta de entrada. El usuario escribe quién es (correo) y demuestra
    # que es él (contraseña). Si los dos coinciden con lo que tenemos guardado,
    # lo dejamos pasar a ver su cuenta.
    #
    # ⚠️ ADVERTENCIA IMPORTANTE PARA LOS JUECES:
    # En un banco REAL las contraseñas NUNCA se guardan así, escritas tal cual.
    # Se guarda una versión revuelta e irreversible llamada "hash" (imagina
    # licuar una fruta: puedes hacer el jugo, pero no puedes regresar la fruta).
    # Aquí las dejamos visibles A PROPÓSITO, porque esto es una DEMO y queremos
    # que cualquiera pueda entrar sin pedir claves.
    #
    # "correo"     = el usuario. Acepta escribir solo "maria" o el correo largo.
    # "contrasena" = la clave. Sin la ñ porque Python se lleva mejor sin acentos
    #                ni eñes en los nombres de variables.
    # -------------------------------------------------------------------------
    "correo": "maria@capitalone.mx",
    "contrasena": "123",

    # -------------------------------------------------------------------------
    # DINERO QUE TIENE EN EL BANCO AHORITA MISMO, en pesos.
    #
    # En la API real de Capital One este número viene del campo "balance"
    # cuando pides:  GET /accounts/{id}
    #
    # ESTE NÚMERO ES CLAVE: es el punto de partida de toda la predicción.
    # Se usa en:  logica/prediccion.py  (para saber desde dónde empieza
    # la línea de la gráfica) y en logica/calculos.py (para los días de
    # colchón).
    # -------------------------------------------------------------------------
    "dinero_en_el_banco": 18400,

    # -------------------------------------------------------------------------
    # PAGOS QUE RECIBIÓ EN LOS ÚLTIMOS 90 DÍAS (3 meses).
    #
    # Cada elemento de la lista es un pago que le hizo un cliente suyo.
    # En la API real esto viene de:  GET /accounts/{id}/deposits
    #
    # Cada pago tiene 3 datos:
    #   "fecha"   = cuándo entró el dinero (texto "AAAA-MM-DD")
    #   "monto"   = cuánto dinero entró, en pesos
    #   "cliente" = quién se lo pagó (para saber si depende de uno solo)
    #
    # FÍJATE EN LOS HUECOS ENTRE FECHAS: a veces pasan 11 días entre pagos
    # y a veces 23. Eso es exactamente lo que hace "volátil" a un freelancer
    # y lo que un score bancario tradicional no sabe leer.
    # -------------------------------------------------------------------------
    "pagos_recibidos": [
        {"fecha": hace_dias(88), "monto": 14500, "cliente": "Agencia Norte"},
        {"fecha": hace_dias(74), "monto":  6200, "cliente": "Tienda Luna"},
        {"fecha": hace_dias(61), "monto": 15800, "cliente": "Agencia Norte"},
        {"fecha": hace_dias(52), "monto":  4300, "cliente": "Café Mendoza"},
        {"fecha": hace_dias(38), "monto":  9100, "cliente": "Tienda Luna"},
        {"fecha": hace_dias(29), "monto": 16200, "cliente": "Agencia Norte"},
        {"fecha": hace_dias(17), "monto":  5400, "cliente": "Café Mendoza"},
        {"fecha": hace_dias( 6), "monto": 11800, "cliente": "Tienda Luna"},
    ],

    # -------------------------------------------------------------------------
    # GASTOS FIJOS: los pagos que SIEMPRE tiene que hacer cada mes.
    #
    # En la API real vienen de:  GET /accounts/{id}/bills
    # (el campo "payment_amount" es el monto y "upcoming_payment_date"
    #  es cuándo toca pagar)
    #
    # Cada gasto fijo tiene 3 datos:
    #   "concepto"    = de qué es el pago (para mostrarlo en pantalla)
    #   "monto"       = cuánto cuesta, en pesos
    #   "se_paga_en"  = dentro de cuántos días toca pagarlo
    #
    # "se_paga_en" es un NÚMERO DE DÍAS, no una fecha. Lo guardamos así
    # porque la predicción de 21 días necesita saber "¿en qué día del
    # calendario futuro cae este gasto?" y comparar números es más simple
    # que comparar fechas.
    # -------------------------------------------------------------------------
    "gastos_fijos": [
        {"concepto": "Renta del departamento", "monto": 6800, "se_paga_en": 14},
        {"concepto": "Seguro de gastos médicos", "monto": 1450, "se_paga_en": 9},
        {"concepto": "Luz (CFE)", "monto": 890, "se_paga_en": 3},
        {"concepto": "Internet", "monto": 650, "se_paga_en": 6},
    ],

    # -------------------------------------------------------------------------
    # GASTO VARIABLE PROMEDIO DE CADA DÍA, en pesos.
    #
    # Es el dinero que se va sin que lo planees: comida, gasolina, el café,
    # la farmacia. No es un pago fijo, pero pasa todos los días.
    #
    # ¿De dónde salió el número 420?
    # En la API real se calcula así: pides GET /accounts/{id}/purchases,
    # sumas TODAS las compras de los últimos 90 días, y divides entre 90.
    # Aquí lo dejamos ya calculado para que el ejemplo sea fácil de leer.
    #
    # Se usa en logica/calculos.py para los días de colchón y en
    # logica/prediccion.py para restar dinero cada día de la gráfica.
    # -------------------------------------------------------------------------
    "gasto_diario_promedio": 420,

    # -------------------------------------------------------------------------
    # VECES QUE SE QUEDÓ SIN DINERO en los últimos 90 días.
    #
    # "Quedarse sin dinero" = intentar pagar algo cuando la cuenta estaba
    # en ceros o en negativo. El banco lo llama "sobregiro".
    #
    # Es un número entero (0, 1, 2...). Entre más alto, peor.
    # Se usa en logica/score.py como una de las 6 notas del score.
    # -------------------------------------------------------------------------
    "veces_sin_dinero": 1,
}


# =============================================================================
# ---------------------------- CLIENTE NÚMERO 2 -------------------------------
#
#  CARLOS — Programador independiente
#
#  PERFIL EN UNA FRASE: tiene contratos largos y estables, ahorra, y sus
#  pagos llegan casi siempre el mismo día. Riesgo BAJO (el mejor caso).
#
#  Lo incluimos para que los jueces vean el contraste: mismo sistema,
#  datos distintos, score muy distinto. Sirve para demostrar que el modelo
#  sí distingue entre perfiles.
# =============================================================================
CARLOS = {

    "id": "carlos",
    "nombre": "Carlos Iván",
    "profesion": "Programador",

    # Sus datos para entrar. Se escribe "carlos" y "123" en la pantalla de login.
    "correo": "carlos@capitalone.mx",
    "contrasena": "123",

    # Tiene más guardado que María: casi 3 meses de gastos cubiertos.
    "dinero_en_el_banco": 52300,

    # -------------------------------------------------------------------------
    # FÍJATE EN LA DIFERENCIA CON MARÍA:
    # Los pagos de Carlos llegan cada 15 días casi exactos (60, 45, 30, 15, 2)
    # y son casi del mismo tamaño. Eso se llama tener ingresos ESTABLES,
    # y su score va a subir mucho por eso.
    # -------------------------------------------------------------------------
    "pagos_recibidos": [
        {"fecha": hace_dias(89), "monto": 28000, "cliente": "SoftCorp"},
        {"fecha": hace_dias(75), "monto": 28000, "cliente": "SoftCorp"},
        {"fecha": hace_dias(60), "monto": 30000, "cliente": "SoftCorp"},
        {"fecha": hace_dias(45), "monto": 28000, "cliente": "SoftCorp"},
        {"fecha": hace_dias(31), "monto": 12000, "cliente": "StartUp MX"},
        {"fecha": hace_dias(30), "monto": 28000, "cliente": "SoftCorp"},
        {"fecha": hace_dias(15), "monto": 30000, "cliente": "SoftCorp"},
        {"fecha": hace_dias( 2), "monto": 28000, "cliente": "SoftCorp"},
    ],

    "gastos_fijos": [
        {"concepto": "Renta del departamento", "monto": 9500, "se_paga_en": 12},
        {"concepto": "Colegiatura hija", "monto": 4200, "se_paga_en": 5},
        {"concepto": "Seguro de auto", "monto": 1800, "se_paga_en": 18},
        {"concepto": "Internet y celular", "monto": 1100, "se_paga_en": 7},
    ],

    "gasto_diario_promedio": 610,

    # Nunca se ha quedado sin dinero. Este cero le va a sumar puntos.
    "veces_sin_dinero": 0,
}


# =============================================================================
# ---------------------------- CLIENTE NÚMERO 3 -------------------------------
#
#  ANA — Fotógrafa de eventos
#
#  PERFIL EN UNA FRASE: gana poco, gasta casi todo, depende de un solo
#  cliente y ya se quedó sin dinero varias veces. Riesgo ALTO.
#
#  Lo incluimos para demostrar que el sistema SÍ detecta el peligro y no
#  recomienda prestarle mucho. Un modelo que aprueba a todos no sirve.
# =============================================================================
ANA = {

    "id": "ana",
    "nombre": "Ana Sofía",
    "profesion": "Fotógrafa de eventos",

    # Sus datos para entrar. Se escribe "ana" y "123" en la pantalla de login.
    "correo": "ana@capitalone.mx",
    "contrasena": "123",

    # Muy poco guardado: le alcanza para menos de 2 semanas.
    "dinero_en_el_banco": 4100,

    # -------------------------------------------------------------------------
    # FÍJATE EN DOS PROBLEMAS AQUÍ:
    #
    # 1) HUECOS ENORMES: entre el pago de hace 71 días y el de hace 34 días
    #    pasaron 37 días sin que entrara un solo peso.
    #
    # 2) UN SOLO CLIENTE MANDA: "Bodas Elite" le paga la mayor parte.
    #    Si ese cliente la deja, Ana se queda sin casi nada de ingreso.
    #    A eso se le llama estar CONCENTRADA en un cliente, y es peligroso.
    # -------------------------------------------------------------------------
    "pagos_recibidos": [
        {"fecha": hace_dias(85), "monto": 12000, "cliente": "Bodas Elite"},
        {"fecha": hace_dias(71), "monto":  3200, "cliente": "Particular"},
        {"fecha": hace_dias(34), "monto": 14000, "cliente": "Bodas Elite"},
        {"fecha": hace_dias(22), "monto":  2800, "cliente": "Particular"},
        {"fecha": hace_dias( 9), "monto":  9500, "cliente": "Bodas Elite"},
    ],

    "gastos_fijos": [
        {"concepto": "Renta de estudio", "monto": 5200, "se_paga_en": 4},
        {"concepto": "Pago de cámara a meses", "monto": 2300, "se_paga_en": 11},
        {"concepto": "Internet", "monto": 600, "se_paga_en": 8},
    ],

    "gasto_diario_promedio": 380,

    # Tres sobregiros en 90 días. Esto le va a bajar mucho el score.
    "veces_sin_dinero": 3,
}


# =============================================================================
#  ÍNDICE DE TODOS LOS CLIENTES
#
#  Este diccionario junta a los 3 clientes en un solo lugar, usando su "id"
#  como etiqueta. Así el servidor puede buscar a cualquiera rápido:
#
#      TODOS_LOS_CLIENTES["maria"]   →  la ficha completa de María
#
#  Es como el índice de un libro: en vez de leer todas las páginas buscando
#  a María, vas directo a su letra.
# =============================================================================
TODOS_LOS_CLIENTES = {
    "maria": MARIA,
    "carlos": CARLOS,
    "ana": ANA,
}


# -----------------------------------------------------------------------------
# FUNCIÓN PÚBLICA: la única que usan los demás archivos.
#
# Le pasas un id ("maria") y te devuelve su ficha completa.
#
# ¿Qué es ".get(...)"?
# Es una función que ya traen los diccionarios de Python. Funciona como los
# corchetes [ ] pero es más segura: si le pides un id que no existe, en vez
# de tronar el programa te devuelve lo que le pongas como segunda opción
# (aquí: None, que en Python significa "nada").
#
# Así, si alguien pide el cliente "pedro" (que no existe), el servidor puede
# responder amablemente "no encontré ese cliente" en vez de crashear.
# -----------------------------------------------------------------------------
def obtener_cliente(id_del_cliente):
    return TODOS_LOS_CLIENTES.get(id_del_cliente, None)


# -----------------------------------------------------------------------------
# FUNCIÓN PÚBLICA: devuelve la lista de clientes para llenar el menú
# desplegable de la página web.
#
# Solo devuelve el id, el nombre y la profesión (no el dinero ni los pagos),
# porque el menú no necesita esos datos y así viaja menos información por
# internet.
#
# ¿Qué es "[... for ... in ...]"?
# Se llama "comprensión de lista". Es una forma corta de escribir un ciclo.
# En español se lee: "arma una lista nueva con esto, por cada cliente que
# haya en la lista de valores".
#
# La versión larga del mismo código sería:
#     lista = []
#     for c in TODOS_LOS_CLIENTES.values():
#         lista.append({"id": c["id"], ...})
#     return lista
# -----------------------------------------------------------------------------
def listar_clientes():
    return [
        {
            "id": c["id"],
            "nombre": c["nombre"],
            "profesion": c["profesion"],
            "correo": c["correo"],
            "saldo": c["dinero_en_el_banco"],
            "riesgo": c.get("riesgo", "medio")
        }
        for c in TODOS_LOS_CLIENTES.values()
    ]


# =============================================================================
#  FUNCIÓN PÚBLICA NUEVA:  verificar_login
#
#  ¿QUÉ HACE?
#  Es el guardia de la puerta. Le llegan dos cosas: lo que el usuario escribió
#  en la caja de "correo" y lo que escribió en la caja de "contraseña".
#
#  Devuelve dos cosas posibles:
#     - La ficha completa del cliente  → "pásale, sí eres tú"
#     - None (que significa "nada")    → "no te conozco, no pasas"
#
#  ¿POR QUÉ DEVUELVE None Y NO UN MENSAJE DE ERROR?
#  Porque esta función solo debe RESPONDER una pregunta (¿es válido?), no
#  decidir qué mostrarle al usuario. De eso se encarga el servidor. A esto se
#  le llama "separar responsabilidades": cada archivo hace una sola cosa.
# =============================================================================
def verificar_login(correo_escrito, contrasena_escrita):

    # -------------------------------------------------------------------------
    # PASO 1 — Limpiar lo que escribió el usuario.
    #
    # La gente escribe con espacios de más y a veces con mayúsculas. Si no
    # limpiamos, "  Maria  " no sería igual a "maria" y no lo dejaríamos entrar
    # aunque sí sea él. Esto pasa MUCHÍSIMO en formularios reales.
    #
    #   .strip()  → quita los espacios de los lados ("  hola  " → "hola")
    #   .lower()  → pasa todo a minúsculas ("MARIA" → "maria")
    #
    # A la contraseña solo le quitamos espacios, pero NO le bajamos las
    # mayúsculas: en una contraseña, "Perro" y "perro" deben ser distintas.
    # -------------------------------------------------------------------------
    correo_limpio = correo_escrito.strip().lower()
    contrasena_limpia = contrasena_escrita.strip()

    # -------------------------------------------------------------------------
    # PASO 2 — Buscar entre los 3 clientes a ver si alguno coincide.
    #
    # ".values()" recorre las FICHAS de los clientes (no sus etiquetas).
    # -------------------------------------------------------------------------
    for cliente in TODOS_LOS_CLIENTES.values():

        # ---------------------------------------------------------------------
        # Aceptamos DOS formas de escribir el usuario, para que la demo sea
        # cómoda enfrente de los jueces:
        #
        #    "maria"                  → solo el id, rápido de teclear
        #    "maria@capitalone.mx"    → el correo completo, más realista
        #
        # "or" en Python significa "o". La condición es verdadera si se cumple
        # cualquiera de las dos.
        # ---------------------------------------------------------------------
        el_usuario_coincide = (
            correo_limpio == cliente["id"]
            or correo_limpio == cliente["correo"]
        )

        # La contraseña sí tiene que ser exacta, sin alternativas.
        la_contrasena_coincide = (contrasena_limpia == cliente["contrasena"])

        # ---------------------------------------------------------------------
        # "and" significa "y": las DOS condiciones tienen que ser verdaderas.
        # Si solo le atinas al correo pero no a la clave, no entras.
        # ---------------------------------------------------------------------
        if el_usuario_coincide and la_contrasena_coincide:
            return cliente

    # -------------------------------------------------------------------------
    # PASO 3 — Si el ciclo terminó sin encontrar a nadie, no existe.
    #
    # Fíjate que este "return None" está FUERA del ciclo (menos indentado).
    # Solo se ejecuta cuando ya se revisaron los 3 clientes y ninguno coincidió.
    # -------------------------------------------------------------------------
    return None
