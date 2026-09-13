# =============================================================================
#  ARCHIVO 9 de 11:  seguridad/guardia.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Es el guardia de seguridad del banco. Hace cuatro trabajos:
#
#     1. REVOLVER CONTRASEÑAS  → guardarlas de forma que ni nosotros las
#                                podamos leer
#     2. REPARTIR PULSERAS     → darle un pase temporal a quien entre bien
#     3. APLICAR EL RLS        → que cada quien vea SOLO lo suyo
#     4. ANOTAR EN LA BITÁCORA → dejar rastro de todo lo que pasa
#
#  ESTE ES EL ARCHIVO MÁS IMPORTANTE DEL PROYECTO PARA LOS JUECES.
#  Todo lo demás calcula números. Este decide quién puede verlos.
# =============================================================================


# =============================================================================
#  IMPORTACIONES
# =============================================================================

# -----------------------------------------------------------------------------
# hashlib trae las funciones de "revoltura" (hash). Viene incluida en Python.
# La usamos para convertir contraseñas en algo irreversible.
# -----------------------------------------------------------------------------
import hashlib

# -----------------------------------------------------------------------------
# secrets genera números y textos aleatorios SEGUROS.
#
# ¿Por qué no usar "random", que es el de siempre?
# Porque random es predecible: si alguien averigua desde qué número empezó,
# puede adivinar todos los siguientes. Sirve para juegos, no para seguridad.
# secrets usa el generador de aleatoriedad del sistema operativo, que sí es
# impredecible. Para contraseñas y tokens SIEMPRE se usa secrets.
# -----------------------------------------------------------------------------
import secrets

# -----------------------------------------------------------------------------
# datetime maneja fechas y horas. La usamos para saber cuándo se vence
# una sesión y para poner la hora en la bitácora.
#   - datetime  → un momento exacto (13 de septiembre de 2026, 14:32:07)
#   - timedelta → una cantidad de tiempo (30 minutos, 5 días)
# -----------------------------------------------------------------------------
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# sqlite3 para hablar con la base de datos.
# -----------------------------------------------------------------------------
import sqlite3

# -----------------------------------------------------------------------------
# os para armar la ruta del archivo de la base de datos.
# -----------------------------------------------------------------------------
import os


# =============================================================================
#  AJUSTES QUE PUEDES CAMBIAR
# =============================================================================

# -----------------------------------------------------------------------------
# Cuántos minutos dura la pulsera antes de vencerse.
#
# Es un balance: muy corto y molestas al usuario pidiéndole la clave todo el
# tiempo; muy largo y si alguien le roba la pulsera tiene horas para usarla.
# Los bancos reales usan entre 5 y 15 minutos. 30 está bien para una demo.
# -----------------------------------------------------------------------------
MINUTOS_QUE_DURA_LA_SESION = 30

# -----------------------------------------------------------------------------
# Cuántas veces puede fallar la contraseña antes de que bloqueemos la cuenta.
#
# Esto detiene el ataque de "fuerza bruta": un programa que prueba miles de
# contraseñas por segundo hasta atinarle. Con 5 intentos y 15 minutos de
# castigo, probar un millón de claves tardaría unos 5 años.
# -----------------------------------------------------------------------------
INTENTOS_ANTES_DE_BLOQUEAR = 5
MINUTOS_DE_BLOQUEO = 15

# -----------------------------------------------------------------------------
# Cuántas vueltas le damos a la licuadora al revolver la contraseña.
#
# Cada vuelta tarda un poquito. 200,000 vueltas tardan como 0.1 segundos,
# que al usuario ni se le nota al entrar. Pero al que quiere adivinar
# contraseñas le multiplica el trabajo por 200,000. Es el mismo truco de
# ponerle una cerradura lenta a la puerta: al dueño no le estorba, al
# ladrón sí.
# -----------------------------------------------------------------------------
VUELTAS_DE_LICUADORA = 200_000

# -----------------------------------------------------------------------------
# La ruta al archivo de la base de datos. Misma lógica que en base_datos.py.
# -----------------------------------------------------------------------------
CARPETA_DEL_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BASE_DATOS = os.path.join(CARPETA_DEL_PROYECTO, "banco.db")


# =============================================================================
#  PARTE 1 — LAS CONTRASEÑAS
# =============================================================================

# -----------------------------------------------------------------------------
#  FUNCIÓN:  generar_sal
#
#  ¿QUÉ ES LA "SAL"?
#  Es un texto aleatorio que se le agrega a la contraseña ANTES de revolverla.
#  Cada usuario tiene la suya, distinta.
#
#  ¿PARA QUÉ SIRVE? Con un ejemplo se entiende:
#
#  SIN SAL: María y Carlos tienen la misma contraseña "123".
#           Al revolverla, los dos dan el MISMO resultado:
#              María  → a665a45920422f9d...
#              Carlos → a665a45920422f9d...
#           Un ladrón que robe la base ve que son iguales. Y peor: existen
#           listas públicas con el resultado ya calculado de las contraseñas
#           más comunes (se llaman "rainbow tables", tablas arcoíris). Busca
#           a665a459... en la lista y descubre que es "123". Sin esfuerzo.
#
#  CON SAL: a María le tocó la sal "x7k2m" y a Carlos "p9q4z".
#              María  → revuelve("123" + "x7k2m") → 4f8e9c2a1b...
#              Carlos → revuelve("123" + "p9q4z") → e2d7a3f5c8...
#           Resultados completamente distintos. La lista pública ya no sirve
#           de nada, porque tendrían que hacer una lista nueva para CADA sal.
#
#  La sal NO es secreta. Se guarda junto a la contraseña revuelta, a la vista.
#  Su chiste no es esconderse, es hacer que cada contraseña sea única.
# -----------------------------------------------------------------------------
def generar_sal():

    # -------------------------------------------------------------------------
    # token_hex(16) genera 16 bytes aleatorios y los escribe como texto en
    # sistema hexadecimal (números del 0 al 9 y letras de la a a la f).
    # Devuelve algo como: "3f7a9c2e8b1d4056a7e3f9c1b8d2e405"
    #
    # 16 bytes son 32 caracteres. Es más que suficiente: hay más combinaciones
    # posibles que átomos en la Vía Láctea.
    # -------------------------------------------------------------------------
    return secrets.token_hex(16)


# -----------------------------------------------------------------------------
#  FUNCIÓN:  revolver_contrasena
#
#  ¿QUÉ ES "REVOLVER" (hash)?
#  Es convertir un texto en otro texto, de forma que:
#     - el mismo texto SIEMPRE da el mismo resultado
#     - del resultado es IMPOSIBLE regresar al original
#
#  La analogía es una licuadora: metes una fruta y sale jugo. El mismo mango
#  siempre da el mismo jugo. Pero del jugo no puedes reconstruir el mango.
#
#  ¿POR QUÉ GUARDAMOS EL JUGO Y NO LA FRUTA?
#  Porque si alguien roba nuestra base de datos, se lleva puros jugos. No
#  puede entrar a ninguna cuenta, ni tampoco probar esas claves en el Gmail
#  o el banco real de la persona (la gente repite contraseñas).
#
#  ¿Y CÓMO VERIFICAMOS ENTONCES SI LA CLAVE ES CORRECTA?
#  Licuamos lo que el usuario acaba de escribir y comparamos jugo contra jugo.
#  Si los dos jugos son idénticos, la fruta era la misma.
#
#  PARÁMETROS (los datos que recibe la función):
#     contrasena → lo que el usuario escribió, ej: "123"
#     sal        → el texto aleatorio de esa persona, ej: "3f7a9c2e..."
#
#  DEVUELVE: un texto de 64 caracteres, ej: "4f8e9c2a1b7d..."
# -----------------------------------------------------------------------------
def revolver_contrasena(contrasena, sal):

    # -------------------------------------------------------------------------
    # pbkdf2_hmac es la función de revoltura. Su nombre viene de
    # "Password-Based Key Derivation Function 2". Es un estándar internacional,
    # diseñado específicamente para contraseñas.
    #
    # Recibe 4 cosas, en este orden:
    #
    #   1) "sha256"  → qué licuadora usar. SHA-256 es la más común y confiable.
    #                  El 256 son los bits del resultado.
    #
    #   2) contrasena.encode()  → la contraseña convertida a bytes.
    #                  .encode() convierte texto a bytes (los unos y ceros).
    #                  Es necesario porque las funciones de revoltura trabajan
    #                  con bytes, no con letras.
    #
    #   3) sal.encode()  → la sal, también en bytes.
    #
    #   4) VUELTAS_DE_LICUADORA  → las 200,000 vueltas de la constante de
    #                  arriba. Es lo que hace lento el ataque.
    #
    # Devuelve bytes, así que al final le ponemos .hex() para convertirlos
    # a texto legible que se pueda guardar en la base de datos.
    # -------------------------------------------------------------------------
    resultado_en_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena.encode(),
        sal.encode(),
        VUELTAS_DE_LICUADORA
    )

    return resultado_en_bytes.hex()


# -----------------------------------------------------------------------------
#  FUNCIÓN:  contrasenas_son_iguales
#
#  Compara dos contraseñas ya revueltas y dice si son la misma.
#
#  ¿POR QUÉ NO USAR SIMPLEMENTE ==  ?
#  Por un ataque muy elegante que se llama "ataque de tiempo" (timing attack).
#
#  Cuando Python compara dos textos con ==, va letra por letra y se DETIENE
#  en la primera que no coincide. O sea:
#     comparar "abc..." con "xyz..."  → falla en la letra 1, tarda 1 nanosegundo
#     comparar "abc..." con "abd..."  → falla en la letra 3, tarda 3 nanosegundos
#
#  Un atacante paciente puede medir esos nanosegundos y adivinar la contraseña
#  LETRA POR LETRA: prueba todas las primeras letras, ve cuál tardó un poquito
#  más, y ya sabe la primera. Repite. Suena a película pero es real y funciona.
#
#  compare_digest siempre tarda EXACTAMENTE lo mismo, coincida o no. No hay
#  nada que medir.
# -----------------------------------------------------------------------------
def contrasenas_son_iguales(revuelta_guardada, revuelta_nueva):
    return secrets.compare_digest(revuelta_guardada, revuelta_nueva)


# =============================================================================
#  PARTE 2 — LAS SESIONES (las pulseras)
# =============================================================================

# -----------------------------------------------------------------------------
#  FUNCIÓN:  intentar_entrar
#
#  Es la puerta del banco. Recibe correo y contraseña, y decide si abre.
#
#  DEVUELVE:
#     Si todo bien  → un diccionario con el token y los datos de la persona
#     Si algo falla → None (que en Python significa "nada")
# -----------------------------------------------------------------------------
def intentar_entrar(correo_escrito, contrasena_escrita):

    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row

    # -------------------------------------------------------------------------
    # Limpiamos lo que escribió el usuario:
    #   .strip()  → quita espacios de los extremos (se pegan al copiar y pegar)
    #   .lower()  → lo pasa todo a minúsculas ("MARIA" y "maria" son lo mismo)
    # -------------------------------------------------------------------------
    correo_limpio = correo_escrito.strip().lower()

    # -------------------------------------------------------------------------
    # Buscamos al usuario. Aceptamos que escriba solo "maria" o el correo
    # completo "maria@capitalone.mx". El "OR" del SQL significa "o".
    #
    # Otra vez: signos de interrogación, nunca texto pegado.
    # -------------------------------------------------------------------------
    fila = conexion.execute(
        "SELECT * FROM usuarios WHERE id = ? OR correo = ?",
        (correo_limpio, correo_limpio)
    ).fetchone()

    # -------------------------------------------------------------------------
    # CASO 1: no existe ese usuario.
    #
    # Fíjate que anotamos el intento fallido en la bitácora, pero al usuario
    # le vamos a responder con un mensaje vago. Ahorita explicamos por qué.
    # -------------------------------------------------------------------------
    if fila is None:
        apuntar_en_bitacora(conexion, None, "login", f"usuario inexistente: {correo_limpio}", False)
        conexion.commit()
        conexion.close()
        return None

    # -------------------------------------------------------------------------
    # CASO 2: la cuenta está bloqueada por intentos fallidos.
    #
    # datetime.now() da la fecha y hora de este momento.
    # .isoformat() la convierte a texto "2026-09-13T14:32:07"
    #
    # Comparamos textos de fecha directamente. Funciona porque el formato
    # ISO está ordenado de lo más grande a lo más chico (año, mes, día),
    # así que comparar los textos da el mismo resultado que comparar fechas.
    # -------------------------------------------------------------------------
    ahora = datetime.now().isoformat()
    if fila["bloqueado_hasta"] and fila["bloqueado_hasta"] > ahora:
        apuntar_en_bitacora(conexion, fila["id"], "login", "cuenta bloqueada", False)
        conexion.commit()
        conexion.close()
        return None

    # -------------------------------------------------------------------------
    # CASO 3: existe el usuario. Ahora sí revisamos la contraseña.
    #
    # Licuamos lo que acaba de escribir, usando LA SAL DE ESTA PERSONA
    # (la que guardamos cuando se creó su cuenta), y comparamos jugos.
    # -------------------------------------------------------------------------
    revuelta_de_lo_escrito = revolver_contrasena(contrasena_escrita, fila["sal"])

    if not contrasenas_son_iguales(fila["contrasena_revuelta"], revuelta_de_lo_escrito):

        # ---------------------------------------------------------------------
        # Contraseña incorrecta: le sumamos uno al contador de fallos.
        #
        # UPDATE cambia filas que ya existen.
        # "intentos_fallidos + 1" toma el valor actual y le suma uno.
        # ---------------------------------------------------------------------
        nuevos_intentos = fila["intentos_fallidos"] + 1

        # ---------------------------------------------------------------------
        # Si ya llegó al límite, calculamos hasta cuándo queda bloqueado.
        #
        # datetime.now() + timedelta(minutes=15) es "dentro de 15 minutos".
        # ---------------------------------------------------------------------
        if nuevos_intentos >= INTENTOS_ANTES_DE_BLOQUEAR:
            hasta_cuando = (datetime.now() + timedelta(minutes=MINUTOS_DE_BLOQUEO)).isoformat()
            conexion.execute(
                "UPDATE usuarios SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE id = ?",
                (nuevos_intentos, hasta_cuando, fila["id"])
            )
        else:
            conexion.execute(
                "UPDATE usuarios SET intentos_fallidos = ? WHERE id = ?",
                (nuevos_intentos, fila["id"])
            )

        apuntar_en_bitacora(conexion, fila["id"], "login", "contraseña incorrecta", False)
        conexion.commit()
        conexion.close()
        return None

    # -------------------------------------------------------------------------
    # CASO 4: ¡TODO CORRECTO! Le damos su pulsera.
    #
    # Primero borramos el contador de intentos fallidos, porque ya demostró
    # que sí es él.
    # -------------------------------------------------------------------------
    conexion.execute(
        "UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id = ?",
        (fila["id"],)
    )

    # -------------------------------------------------------------------------
    # Generamos el token: 32 bytes aleatorios = 64 caracteres.
    #
    # ¿Por qué tan largo? Para que sea imposible adivinarlo. Con 64 caracteres
    # hexadecimales hay 16^64 combinaciones. Si una computadora probara mil
    # millones por segundo, tardaría más que la edad del universo.
    # -------------------------------------------------------------------------
    token = secrets.token_hex(32)

    # Calculamos cuándo se vence la pulsera.
    creada = datetime.now()
    expira = creada + timedelta(minutes=MINUTOS_QUE_DURA_LA_SESION)

    conexion.execute(
        "INSERT INTO sesiones (token, id_usuario, rol, creada_en, expira_en) VALUES (?, ?, ?, ?, ?)",
        (token, fila["id"], fila["rol"], creada.isoformat(), expira.isoformat())
    )

    apuntar_en_bitacora(conexion, fila["id"], "login", "entró correctamente", True)
    conexion.commit()

    # Guardamos los datos antes de cerrar, porque después de close() ya no
    # se puede leer nada de la conexión.
    respuesta = {
        "token": token,
        "id": fila["id"],
        "nombre": fila["nombre"],
        "profesion": fila["profesion"],
        "rol": fila["rol"],
    }
    conexion.close()
    return respuesta


# -----------------------------------------------------------------------------
#  FUNCIÓN:  revisar_pulsera
#
#  Recibe un token y dice de quién es, o None si no sirve.
#
#  Esta función se llama en CADA petición al servidor. Es el torniquete.
# -----------------------------------------------------------------------------
def revisar_pulsera(token):

    # Si no mandaron token, ni siquiera vale la pena abrir la base.
    if not token:
        return None

    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row

    fila = conexion.execute(
        "SELECT * FROM sesiones WHERE token = ?", (token,)
    ).fetchone()

    conexion.close()

    # El token no existe: o es inventado, o ya se cerró sesión.
    if fila is None:
        return None

    # -------------------------------------------------------------------------
    # El token existe pero ya se venció.
    #
    # Comparamos la fecha de vencimiento contra ahorita.
    # -------------------------------------------------------------------------
    if fila["expira_en"] < datetime.now().isoformat():
        return None

    return {"id": fila["id_usuario"], "rol": fila["rol"]}


# -----------------------------------------------------------------------------
#  FUNCIÓN:  quitar_pulsera
#  Cerrar sesión: borramos el token de la tabla y deja de funcionar al instante.
# -----------------------------------------------------------------------------
def quitar_pulsera(token):
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.execute("DELETE FROM sesiones WHERE token = ?", (token,))
    conexion.commit()
    conexion.close()


# =============================================================================
#  PARTE 3 — EL RLS (la parte más importante del archivo)
# =============================================================================

# -----------------------------------------------------------------------------
#  FUNCIÓN:  conectar_como
#
#  ESTA ES LA FUNCIÓN CLAVE DE TODO EL SISTEMA DE SEGURIDAD.
#
#  Abre la base de datos "disfrazada" de una persona específica. A partir de
#  ese momento, esa conexión FÍSICAMENTE NO PUEDE ver los datos de nadie más.
#
#  ¿CÓMO LO LOGRA? Con dos trucos de SQLite:
#
#  TRUCO 1 — LA TABLA TEMPORAL
#  "CREATE TEMP TABLE" crea una tabla que solo existe en ESTA conexión y se
#  borra sola al cerrarla. Es como un gafete que solo tú puedes ver.
#  Ahí adentro escribimos quién eres.
#
#  TRUCO 2 — LAS VISTAS
#  ¿Qué es una "vista" (VIEW)? Es una tabla falsa, hecha de una consulta.
#  No guarda datos propios: cada vez que la lees, ejecuta su consulta por
#  debajo. Es como una ventana con un filtro pegado.
#
#  Entonces creamos vistas que dicen:
#     "muéstrame los pagos DONDE el dueño sea el del gafete"
#
#  Y el resto del programa (calculos.py, score.py, prediccion.py) SOLO habla
#  con las vistas. Nunca toca las tablas reales.
#
#  ¿POR QUÉ ESTO ES MEJOR QUE FILTRAR EN PYTHON?
#  Porque si el filtro está en Python, se puede olvidar. Un programador
#  distraído escribe "SELECT * FROM pagos_recibidos" sin WHERE y se lleva
#  los datos de los 3 millones de clientes. Ha pasado, y sale en las noticias.
#
#  Con las vistas, ESE MISMO ERROR es inofensivo: aunque escriba
#  "SELECT * FROM mis_pagos" sin ningún WHERE, la vista ya trae el filtro
#  metido por dentro. La seguridad no depende de que nadie se equivoque.
#
#  PARÁMETROS:
#     id_usuario → de quién es el gafete, ej: "maria"
#     rol        → "cliente" (solo lo suyo) o "admin" (puede ver todo)
# -----------------------------------------------------------------------------
def conectar_como(id_usuario, rol):

    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")

    # -------------------------------------------------------------------------
    # PASO 1: creamos el gafete de esta conexión.
    #
    # La palabra TEMP (de "temporary", temporal) es lo que hace que esta tabla
    # sea privada de esta conexión. Otra persona conectándose al mismo tiempo
    # tiene su propia tabla sesion_actual con su propio nombre adentro, y
    # ninguna de las dos ve la de la otra.
    # -------------------------------------------------------------------------
    conexion.execute("CREATE TEMP TABLE sesion_actual (id_usuario TEXT, rol TEXT)")
    conexion.execute("INSERT INTO sesion_actual VALUES (?, ?)", (id_usuario, rol))

    # -------------------------------------------------------------------------
    # PASO 2: creamos las vistas con el filtro de seguridad metido adentro.
    #
    # Leamos la primera con calma, porque las otras tres son iguales:
    #
    #     CREATE TEMP VIEW mis_pagos AS       ← crea una ventana llamada mis_pagos
    #     SELECT * FROM pagos_recibidos       ← que mira a la tabla real
    #     WHERE                               ← pero solo deja pasar las filas donde:
    #       id_usuario = (SELECT id_usuario FROM sesion_actual)
    #                                         ← el dueño de la fila es el del gafete
    #       OR (SELECT rol FROM sesion_actual) = 'admin'
    #                                         ← O el del gafete es administrador
    #
    # Ese "OR ... = 'admin'" es la única puerta trasera, y es a propósito:
    # el analista del banco sí necesita ver a todos los clientes para evaluar
    # riesgo. Pero fíjate que está escrita UNA sola vez, aquí, y se puede
    # auditar. No está regada por todo el programa.
    # -------------------------------------------------------------------------
    conexion.execute("""
        CREATE TEMP VIEW mis_pagos AS
        SELECT * FROM pagos_recibidos
        WHERE id_usuario = (SELECT id_usuario FROM sesion_actual)
           OR (SELECT rol FROM sesion_actual) = 'admin'
    """)

    conexion.execute("""
        CREATE TEMP VIEW mis_gastos AS
        SELECT * FROM gastos_fijos
        WHERE id_usuario = (SELECT id_usuario FROM sesion_actual)
           OR (SELECT rol FROM sesion_actual) = 'admin'
    """)

    conexion.execute("""
        CREATE TEMP VIEW mi_cuenta AS
        SELECT * FROM cuentas
        WHERE id_usuario = (SELECT id_usuario FROM sesion_actual)
           OR (SELECT rol FROM sesion_actual) = 'admin'
    """)

    # -------------------------------------------------------------------------
    # La vista de usuarios tiene algo especial: fíjate que NO incluimos las
    # columnas contrasena_revuelta ni sal.
    #
    # Esto es otra capa de seguridad y se llama "mínimo privilegio": ni
    # siquiera exponemos los datos que nadie necesita ver. Aunque alguien
    # lograra leer esta vista, no se lleva las contraseñas.
    # -------------------------------------------------------------------------
    conexion.execute("""
        CREATE TEMP VIEW mis_datos AS
        SELECT id, nombre, profesion, correo, rol FROM usuarios
        WHERE id = (SELECT id_usuario FROM sesion_actual)
           OR (SELECT rol FROM sesion_actual) = 'admin'
    """)

    return conexion


# =============================================================================
#  PARTE 4 — LA BITÁCORA (el diario de seguridad)
# =============================================================================

# -----------------------------------------------------------------------------
#  FUNCIÓN:  apuntar_en_bitacora
#
#  Escribe una línea en el diario. Se llama en cada acción importante.
#
#  ¿POR QUÉ GUARDAMOS TAMBIÉN LOS INTENTOS QUE SÍ SE PERMITIERON?
#  Porque la bitácora sirve para investigar DESPUÉS. Si mañana descubren que
#  se filtraron datos, lo que necesitas saber es quién los vio, no solo quién
#  lo intentó y falló.
#
#  PARÁMETROS:
#     conexion   → la conexión abierta a la base (para no abrir otra)
#     id_usuario → quién hizo la acción (puede ser None si no sabemos)
#     accion     → qué hizo, ej: "login", "ver_analisis"
#     detalle    → información extra, ej: "intentó ver los datos de carlos"
#     permitido  → True si se le dejó, False si se le negó
# -----------------------------------------------------------------------------
def apuntar_en_bitacora(conexion, id_usuario, accion, detalle, permitido):

    # -------------------------------------------------------------------------
    # strftime convierte la fecha a texto con el formato que le pidas.
    #   %Y = año con 4 dígitos    %H = hora
    #   %m = mes con 2 dígitos    %M = minutos
    #   %d = día con 2 dígitos    %S = segundos
    # -------------------------------------------------------------------------
    momento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    # SQLite no tiene tipo "booleano" (verdadero/falso). Guardamos 1 o 0.
    # El "if permitido else" es una forma corta de escribir un if de una línea:
    # "dame 1 si permitido es verdadero, si no dame 0".
    # -------------------------------------------------------------------------
    conexion.execute(
        "INSERT INTO bitacora (momento, id_usuario, accion, detalle, permitido) VALUES (?, ?, ?, ?, ?)",
        (momento, id_usuario, accion, detalle, 1 if permitido else 0)
    )


# -----------------------------------------------------------------------------
#  FUNCIÓN:  leer_bitacora
#  Trae las últimas líneas del diario. Solo la usa el panel de administrador.
# -----------------------------------------------------------------------------
def leer_bitacora(cuantas=50):

    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row

    # -------------------------------------------------------------------------
    # ORDER BY id DESC → ordena de mayor a menor. Como el id va subiendo
    #                    de uno en uno, el más grande es el más reciente.
    #                    DESC viene de "descending" (descendente).
    # LIMIT ?          → "solo tráeme estas primeras". Evita traer un millón
    #                    de filas y tumbar el servidor.
    # -------------------------------------------------------------------------
    filas = conexion.execute(
        "SELECT * FROM bitacora ORDER BY id DESC LIMIT ?", (cuantas,)
    ).fetchall()

    conexion.close()

    # -------------------------------------------------------------------------
    # Convertimos las filas de SQLite a diccionarios normales de Python,
    # porque FastAPI no sabe convertir objetos sqlite3.Row a JSON.
    #
    # Esto de abajo se llama "comprensión de lista": es una forma corta de
    # escribir un for que construye una lista nueva. Se lee así:
    #     "dame dict(f) por cada f que haya en filas"
    # -------------------------------------------------------------------------
    return [dict(f) for f in filas]
