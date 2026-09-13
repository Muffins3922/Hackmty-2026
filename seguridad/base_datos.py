# =============================================================================
#  ARCHIVO 8 de 11:  seguridad/base_datos.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Construye la base de datos y guarda dentro los datos de los clientes.
#
#  ¿QUÉ ES UNA "BASE DE DATOS"?
#  Es un archivo que guarda información en TABLAS, como un Excel pero mucho
#  más estricto. Cada tabla tiene columnas fijas (nombre, correo, saldo) y
#  filas (una por cada cliente).
#
#  ¿POR QUÉ CAMBIAMOS DE UN ARCHIVO .py A UNA BASE DE DATOS?
#  Antes los clientes vivían en datos/clientes.py como diccionarios de Python.
#  Eso funciona para una demo, pero tiene un problema grave de seguridad:
#  TODO el programa podía leer TODOS los datos de TODAS las personas.
#  No había forma de decir "María solo puede ver lo de María".
#
#  Con una base de datos SÍ podemos ponerle esa regla, y se llama RLS.
#
#  ¿QUÉ ES "RLS"?
#  Son las siglas de Row Level Security, en español "seguridad a nivel de
#  fila". Significa: la regla de quién puede ver qué NO está en el programa,
#  está DENTRO de la base de datos.
#
#  La diferencia importa muchísimo:
#     SIN RLS → el programa pide "dame todos los pagos" y la base los da
#               todos. Si el programador se le olvida filtrar, se filtran
#               los datos de todos los clientes. Es el error #1 en fugas
#               de datos bancarios.
#     CON RLS → el programa pide "dame todos los pagos" y la base responde
#               SOLO con los de María, porque María es quien está conectada.
#               Aunque el programador se equivoque, los datos no salen.
#
#  ¿QUÉ ES "SQLite"?
#  Es la base de datos más simple que existe. Toda la base es UN SOLO ARCHIVO
#  (el nuestro se llama banco.db). No hay que instalar nada, ya viene incluida
#  con Python. Por eso la elegimos: funciona en cualquier computadora.
#
#  ¿QUÉ ES "SQL"?
#  Es el idioma con el que se le habla a una base de datos. Se pronuncia
#  "ese-cu-ele" o "síquel". Tiene como 6 palabras importantes:
#     CREATE TABLE → crea una tabla nueva
#     INSERT       → mete una fila
#     SELECT       → lee filas
#     UPDATE       → cambia filas
#     DELETE       → borra filas
#     WHERE        → "solo las filas que cumplan esto"
# =============================================================================


# =============================================================================
#  IMPORTACIONES: las herramientas que necesita este archivo
# =============================================================================

# -----------------------------------------------------------------------------
# sqlite3 es la librería que trae Python para hablar con bases de datos SQLite.
# No se instala, ya viene incluida. Es la que abre el archivo banco.db y
# ejecuta las instrucciones en SQL.
# -----------------------------------------------------------------------------
import sqlite3

# -----------------------------------------------------------------------------
# "os" son las siglas de Operating System (sistema operativo). Sirve para
# trabajar con rutas de archivos y carpetas sin importar si estás en Windows,
# Mac o Linux.
# -----------------------------------------------------------------------------
import os

# -----------------------------------------------------------------------------
# De nuestro propio archivo de datos traemos el diccionario con los 3 clientes
# de ejemplo. Los vamos a copiar UNA VEZ a la base de datos.
#
# Después de esta copia, datos/clientes.py ya no se usa para nada más.
# Queda como el "archivo semilla": de ahí salieron los datos iniciales.
# -----------------------------------------------------------------------------
from datos.clientes import TODOS_LOS_CLIENTES

# -----------------------------------------------------------------------------
# De nuestro guardia de seguridad traemos la función que revuelve contraseñas.
# La explicación completa de qué hace está en seguridad/guardia.py línea 95.
#
# Resumen: convierte "123" en algo como "a4f8e9c2..." de donde es imposible
# regresar al "123" original.
# -----------------------------------------------------------------------------
from seguridad.guardia import revolver_contrasena, generar_sal


# =============================================================================
#  DÓNDE VIVE EL ARCHIVO DE LA BASE DE DATOS
# =============================================================================

# -----------------------------------------------------------------------------
# Armamos la ruta completa hasta el archivo banco.db.
#
# Desglose de la línea, de adentro hacia afuera:
#   __file__              → la ruta de ESTE archivo (base_datos.py)
#   os.path.abspath(...)  → la convierte en ruta completa desde la raíz del disco
#   os.path.dirname(...)  → se queda solo con la carpeta que lo contiene
#                           (o sea: .../proyecto/seguridad)
#   os.path.dirname(...)  → otra vez, para subir un nivel más
#                           (o sea: .../proyecto)
#   os.path.join(a, b)    → pega las dos partes con la diagonal correcta
#                           (\ en Windows, / en Mac y Linux)
#
# ¿Por qué no escribimos "banco.db" y ya? Porque esa ruta depende de desde
# qué carpeta ejecutes el programa. Si lo corres desde otro lado, no lo
# encuentra. Con esta línea siempre lo encuentra.
# -----------------------------------------------------------------------------
CARPETA_DEL_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BASE_DATOS = os.path.join(CARPETA_DEL_PROYECTO, "banco.db")


# =============================================================================
#  EL PLANO DE LAS TABLAS
#
#  Aquí describimos, en SQL, qué tablas va a tener la base de datos y qué
#  columnas tiene cada una. Es como dibujar el plano antes de construir.
#
#  ¿QUÉ SIGNIFICAN LAS PALABRAS QUE APARECEN?
#
#     TEXT          → la columna guarda letras (nombres, correos, fechas)
#     REAL          → la columna guarda números con decimales (dinero)
#     INTEGER       → la columna guarda números enteros (cantidades, 0 y 1)
#     PRIMARY KEY   → "llave primaria": la columna que identifica de forma
#                     única a cada fila. No se puede repetir. Como el CURP
#                     de una persona o el número de cuenta.
#     UNIQUE        → "único": esta columna no se puede repetir entre filas.
#                     Dos clientes no pueden tener el mismo correo.
#     NOT NULL      → "no vacío": esta columna es obligatoria, no se puede
#                     dejar en blanco.
#     REFERENCES    → "apunta a": conecta esta tabla con otra. Le dice a la
#                     base de datos "esta columna guarda el id de un usuario
#                     que DEBE existir en la tabla usuarios". Si intentas
#                     meter un pago de un usuario que no existe, la base lo
#                     rechaza. A esto se le llama "llave foránea".
#     AUTOINCREMENT → la base pone el número sola: 1, 2, 3, 4...
#                     No tenemos que llevar la cuenta nosotros.
# =============================================================================

PLANO_DE_LAS_TABLAS = """

-- ---------------------------------------------------------------------------
-- TABLA 1: usuarios
-- Quién puede entrar al sistema y con qué permisos.
--
-- Ojo: aquí NO hay una columna "contrasena". Hay "contrasena_revuelta".
-- Ese es el punto entero de la seguridad y lo explicamos en guardia.py.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id                   TEXT PRIMARY KEY,   -- "maria", "carlos", "ana", "admin"
    nombre               TEXT NOT NULL,      -- "María Fernanda"
    profesion            TEXT,               -- "Diseñadora gráfica"
    correo               TEXT UNIQUE NOT NULL, -- "maria@capitalone.mx"
    contrasena_revuelta  TEXT NOT NULL,      -- el resultado de revolver "123"
    sal                  TEXT NOT NULL,      -- el ingrediente secreto de cada uno
    rol                  TEXT NOT NULL,      -- "cliente" o "admin"
    intentos_fallidos    INTEGER DEFAULT 0,  -- cuántas veces falló la clave
    bloqueado_hasta      TEXT                -- fecha y hora del desbloqueo
);

-- ---------------------------------------------------------------------------
-- TABLA 2: cuentas
-- El dinero de cada cliente. Una fila por cliente.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cuentas (
    id_usuario            TEXT PRIMARY KEY REFERENCES usuarios(id),
    dinero_en_el_banco    REAL NOT NULL,     -- cuánto tiene ahorita
    gasto_diario_promedio REAL NOT NULL,     -- cuánto se le va al día
    veces_sin_dinero      INTEGER DEFAULT 0  -- cuántas veces quedó en ceros
);

-- ---------------------------------------------------------------------------
-- TABLA 3: pagos_recibidos
-- Cada pago que recibió cada cliente. Muchas filas por cliente.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagos_recibidos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario  TEXT NOT NULL REFERENCES usuarios(id),
    fecha       TEXT NOT NULL,   -- "2026-06-17"
    monto       REAL NOT NULL,   -- 14500
    cliente     TEXT             -- "Agencia Norte" (quién le pagó)
);

-- ---------------------------------------------------------------------------
-- TABLA 4: gastos_fijos
-- Los pagos que cada cliente tiene que hacer cada mes.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gastos_fijos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario  TEXT NOT NULL REFERENCES usuarios(id),
    concepto    TEXT NOT NULL,      -- "Renta del departamento"
    monto       REAL NOT NULL,      -- 6800
    se_paga_en  INTEGER NOT NULL    -- dentro de cuántos días toca pagarlo
);

-- ---------------------------------------------------------------------------
-- TABLA 5: sesiones
-- Quién está conectado en este momento.
--
-- ¿QUÉ ES UNA "SESIÓN"?
-- Cuando entras a tu banco, no escribes tu contraseña en cada clic. La
-- escribes UNA vez y el banco te da una pulsera invisible. Esa pulsera es
-- el "token". Cada vez que pides algo, muestras la pulsera en vez de la
-- contraseña. Si pierdes la pulsera, el ladrón no tiene tu contraseña,
-- y además la pulsera se vence sola a los 30 minutos.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sesiones (
    token       TEXT PRIMARY KEY,  -- el número secreto de la pulsera
    id_usuario  TEXT NOT NULL REFERENCES usuarios(id),
    rol         TEXT NOT NULL,     -- copiado del usuario, para no consultarlo
    creada_en   TEXT NOT NULL,     -- cuándo entró
    expira_en   TEXT NOT NULL      -- cuándo se vence la pulsera
);

-- ---------------------------------------------------------------------------
-- TABLA 6: bitacora
-- El diario de todo lo que pasa. Quién pidió qué y si se le permitió.
--
-- ¿PARA QUÉ SIRVE?
-- Si mañana se filtran datos, esta tabla dice exactamente quién los pidió,
-- cuándo, y desde dónde. En un banco real esto es obligatorio por ley.
-- Se le llama "auditoría" (revisar el rastro de lo que pasó).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bitacora (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    momento     TEXT NOT NULL,     -- "2026-09-13 14:32:07"
    id_usuario  TEXT,              -- quién lo pidió (puede ser desconocido)
    accion      TEXT NOT NULL,     -- "login", "ver_analisis", "ver_clientes"
    detalle     TEXT,              -- de quién intentó ver los datos
    permitido   INTEGER NOT NULL   -- 1 = sí se le dejó, 0 = se le negó
);

"""


# =============================================================================
#  FUNCIÓN 1:  abrir_conexion
#  Abre el archivo de la base de datos para poder trabajar con él.
# =============================================================================

def abrir_conexion():

    # -------------------------------------------------------------------------
    # sqlite3.connect abre el archivo. Si el archivo no existe, lo crea vacío.
    #
    # La variable "conexion" es como tener el Excel abierto en la pantalla:
    # mientras la tengas, puedes leer y escribir. Al final hay que cerrarla.
    # -------------------------------------------------------------------------
    conexion = sqlite3.connect(RUTA_BASE_DATOS)

    # -------------------------------------------------------------------------
    # Por defecto SQLite devuelve las filas como tuplas: ("maria", "María", 28)
    # y para leerlas tendrías que acordarte que el nombre está en la posición 1.
    # Eso se presta a errores.
    #
    # Con esta línea las devuelve como diccionarios: fila["nombre"]
    # Mucho más claro de leer y más difícil de equivocarse.
    # -------------------------------------------------------------------------
    conexion.row_factory = sqlite3.Row

    # -------------------------------------------------------------------------
    # Esta línea activa las llaves foráneas (el REFERENCES del plano de arriba).
    #
    # Ojo con esto: SQLite las trae APAGADAS por defecto, por compatibilidad
    # con programas viejos. Si no pones esta línea, la base acepta pagos de
    # usuarios que no existen y nadie te avisa. Es una trampa clásica.
    #
    # PRAGMA es una instrucción especial de SQLite para cambiar su configuración.
    # -------------------------------------------------------------------------
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion


# =============================================================================
#  FUNCIÓN 2:  construir_la_base
#  Crea las tablas y mete los datos de los 3 clientes + 1 administrador.
# =============================================================================

def construir_la_base(borrar_lo_anterior=False):

    # -------------------------------------------------------------------------
    # Si nos piden empezar de cero, borramos el archivo viejo.
    #
    # os.path.exists pregunta "¿existe este archivo?" y devuelve True o False.
    # os.remove lo borra.
    # -------------------------------------------------------------------------
    if borrar_lo_anterior and os.path.exists(RUTA_BASE_DATOS):
        os.remove(RUTA_BASE_DATOS)

    conexion = abrir_conexion()

    # -------------------------------------------------------------------------
    # executescript ejecuta VARIAS instrucciones SQL de un jalón, separadas
    # por punto y coma. Lo usamos para crear las 6 tablas de una vez.
    #
    # (execute, sin "script", solo acepta UNA instrucción a la vez)
    # -------------------------------------------------------------------------
    conexion.executescript(PLANO_DE_LAS_TABLAS)

    # -------------------------------------------------------------------------
    # Revisamos si ya hay usuarios guardados, para no meterlos dos veces.
    #
    # Desglose de la consulta SQL:
    #   SELECT COUNT(*)   → "cuéntame cuántas filas hay"
    #   FROM usuarios     → "en la tabla usuarios"
    #
    # .fetchone() trae la primera (y aquí única) fila del resultado.
    # El [0] toma la primera columna de esa fila, que es el número.
    # -------------------------------------------------------------------------
    cuantos_hay = conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

    # Si ya hay usuarios, no hacemos nada más. La base ya estaba lista.
    if cuantos_hay > 0:
        conexion.close()
        return False

    # -------------------------------------------------------------------------
    # AQUÍ EMPIEZA LA COPIA DE LOS DATOS
    #
    # Recorremos los 3 clientes de datos/clientes.py y los metemos a la base.
    #
    # ".values()" de un diccionario devuelve solo los valores, sin las
    # etiquetas. Como TODOS_LOS_CLIENTES es {"maria": {...}, "carlos": {...}},
    # .values() nos da directamente las fichas de cada uno.
    # -------------------------------------------------------------------------
    for ficha in TODOS_LOS_CLIENTES.values():

        # ---------------------------------------------------------------------
        # PASO 1: preparar la contraseña para guardarla de forma segura.
        #
        # generar_sal() inventa un texto aleatorio distinto para cada persona.
        # revolver_contrasena() mezcla la contraseña con esa sal y devuelve
        # algo irreversible. Los dos están explicados en guardia.py.
        # ---------------------------------------------------------------------
        sal = generar_sal()
        revuelta = revolver_contrasena(ficha["contrasena"], sal)

        # ---------------------------------------------------------------------
        # PASO 2: meter la fila en la tabla usuarios.
        #
        # ¿QUÉ SON LOS SIGNOS DE INTERROGACIÓN?
        # Son huecos. Le decimos a SQLite "aquí va un valor, pero te lo doy
        # aparte, en la lista de después". SQLite mete los valores por su
        # cuenta, tratándolos SIEMPRE como texto, nunca como instrucciones.
        #
        # ¿POR QUÉ NO PEGAR EL TEXTO DIRECTAMENTE?
        # Porque existe un ataque que se llama "inyección SQL". Si armáramos
        # la consulta pegando texto, alguien podría escribir como nombre:
        #
        #     Juan'); DROP TABLE usuarios; --
        #
        # y la base leería eso como DOS instrucciones: meter a Juan, y luego
        # BORRAR LA TABLA COMPLETA. Con los signos de interrogación eso es
        # imposible: SQLite guardaría ese texto tal cual, como un nombre raro.
        #
        # Regla de oro: NUNCA armes consultas SQL pegando texto. Siempre ?
        # ---------------------------------------------------------------------
        conexion.execute(
            """INSERT INTO usuarios
               (id, nombre, profesion, correo, contrasena_revuelta, sal, rol)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ficha["id"], ficha["nombre"], ficha["profesion"],
             ficha["correo"], revuelta, sal, "cliente")
        )

        # ---------------------------------------------------------------------
        # PASO 3: meter el dinero de esa persona en la tabla cuentas.
        # ---------------------------------------------------------------------
        conexion.execute(
            """INSERT INTO cuentas
               (id_usuario, dinero_en_el_banco, gasto_diario_promedio, veces_sin_dinero)
               VALUES (?, ?, ?, ?)""",
            (ficha["id"], ficha["dinero_en_el_banco"],
             ficha["gasto_diario_promedio"], ficha["veces_sin_dinero"])
        )

        # ---------------------------------------------------------------------
        # PASO 4: meter TODOS sus pagos recibidos, uno por uno.
        #
        # ficha["pagos_recibidos"] es una lista de diccionarios. El "for"
        # recorre la lista y mete una fila por cada pago.
        # ---------------------------------------------------------------------
        for pago in ficha["pagos_recibidos"]:
            conexion.execute(
                """INSERT INTO pagos_recibidos (id_usuario, fecha, monto, cliente)
                   VALUES (?, ?, ?, ?)""",
                (ficha["id"], pago["fecha"], pago["monto"], pago["cliente"])
            )

        # ---------------------------------------------------------------------
        # PASO 5: meter todos sus gastos fijos.
        # ---------------------------------------------------------------------
        for gasto in ficha["gastos_fijos"]:
            conexion.execute(
                """INSERT INTO gastos_fijos (id_usuario, concepto, monto, se_paga_en)
                   VALUES (?, ?, ?, ?)""",
                (ficha["id"], gasto["concepto"], gasto["monto"], gasto["se_paga_en"])
            )

    # -------------------------------------------------------------------------
    # AHORA CREAMOS AL ADMINISTRADOR
    #
    # El administrador es el empleado del banco. No tiene cuenta ni dinero,
    # solo el permiso de ver la lista de clientes. Por eso solo va en la
    # tabla usuarios y NO en la tabla cuentas.
    #
    # Fíjate que su rol dice "admin" en vez de "cliente". Esa sola palabra
    # es la que le abre el otro panel.
    # -------------------------------------------------------------------------
    sal_admin = generar_sal()
    conexion.execute(
        """INSERT INTO usuarios
           (id, nombre, profesion, correo, contrasena_revuelta, sal, rol)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("admin", "Laura Méndez", "Analista de riesgo",
         "admin@capitalone.mx", revolver_contrasena("admin123", sal_admin),
         sal_admin, "admin")
    )

    # -------------------------------------------------------------------------
    # commit() confirma los cambios y los graba en el archivo.
    #
    # ¿POR QUÉ HAY QUE CONFIRMARLOS?
    # Porque hasta este momento todos los INSERT viven solo en la memoria.
    # Si el programa se cierra antes del commit, no se guardó nada.
    #
    # Esto es a propósito y se llama "transacción": o se guardan TODOS los
    # cambios, o no se guarda NINGUNO. Nunca a medias. Imagina una
    # transferencia: sería terrible que se reste de una cuenta y se apague
    # la luz antes de sumarlo a la otra.
    # -------------------------------------------------------------------------
    conexion.commit()
    conexion.close()

    return True


# =============================================================================
#  SI ALGUIEN EJECUTA ESTE ARCHIVO DIRECTAMENTE, CONSTRUYE LA BASE
#
#  La línea de abajo significa: "si me están corriendo a mí directamente
#  (python seguridad/base_datos.py), haz esto. Si solo me están importando
#  desde otro archivo, no hagas nada."
# =============================================================================

if __name__ == "__main__":
    print("Construyendo la base de datos...")
    se_creo = construir_la_base(borrar_lo_anterior=True)
    print(f"Listo. Archivo creado en: {RUTA_BASE_DATOS}")
