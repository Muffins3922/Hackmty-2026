# =============================================================================
#  ARCHIVO 10 de 11:  seguridad/consultas.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Es el único lugar del programa que lee datos de clientes de la base.
#
#  ¿POR QUÉ TODO PASA POR AQUÍ?
#  Porque así hay UN SOLO camino hacia los datos, y ese camino está vigilado.
#  Si mañana hay que cambiar una regla de seguridad, se cambia aquí y ya.
#  Si los accesos estuvieran regados por todo el programa, habría que revisar
#  archivo por archivo y seguro se nos escaparía uno.
#
#  A esto se le llama "cuello de botella de seguridad", y es a propósito:
#  una sola puerta es más fácil de cuidar que veinte.
#
#  LA REGLA DE ORO DE ESTE ARCHIVO:
#  Ninguna función de aquí toca las tablas reales (pagos_recibidos, cuentas).
#  Todas leen de las VISTAS (mis_pagos, mi_cuenta), que ya traen el filtro
#  del RLS metido por dentro. Explicado en guardia.py línea 380.
# =============================================================================


# -----------------------------------------------------------------------------
# Del guardia traemos las dos funciones que necesitamos:
#   conectar_como        → abre la base disfrazada de una persona
#   apuntar_en_bitacora  → deja rastro de lo que se pidió
# -----------------------------------------------------------------------------
from seguridad.guardia import conectar_como, apuntar_en_bitacora


# =============================================================================
#  FUNCIÓN 1:  traer_ficha_completa
#
#  Arma la ficha de un cliente con todos sus datos, igual que el diccionario
#  que antes vivía en datos/clientes.py.
#
#  ¿POR QUÉ DEVOLVEMOS EL MISMO FORMATO DE ANTES?
#  Para no tener que tocar logica/calculos.py, logica/score.py ni
#  logica/prediccion.py. Ellos siguen recibiendo exactamente lo que esperaban
#  y ni se enteran de que ahora viene de una base de datos.
#
#  Eso se llama "mantener el contrato": si la forma de los datos no cambia,
#  lo de adentro se puede reescribir sin romper nada.
#
#  PARÁMETROS:
#     quien_pide  → el id de quien está conectado, ej: "maria"
#     rol         → "cliente" o "admin"
#     de_quien    → de quién quiere los datos, ej: "carlos"
#
#  DEVUELVE:
#     La ficha completa, o None si no tiene permiso / no existe.
# =============================================================================
def traer_ficha_completa(quien_pide, rol, de_quien):

    # -------------------------------------------------------------------------
    # Abrimos la base DISFRAZADOS de quien está pidiendo.
    #
    # Esta línea es la que activa el RLS. A partir de aquí, esta conexión
    # solo puede ver lo que le toca a "quien_pide".
    # -------------------------------------------------------------------------
    conexion = conectar_como(quien_pide, rol)

    try:
        # ---------------------------------------------------------------------
        # PASO 1: traer los datos básicos de la persona.
        #
        # Fíjate que leemos de "mis_datos", que es la VISTA, no de la tabla
        # "usuarios".
        #
        # EL MOMENTO CLAVE: si María pide los datos de Carlos, este SELECT
        # devuelve None. No porque lo revisemos nosotros, sino porque la vista
        # literalmente no contiene la fila de Carlos cuando María es la
        # conectada. Los datos de Carlos no existen para esta conexión.
        # ---------------------------------------------------------------------
        persona = conexion.execute(
            "SELECT * FROM mis_datos WHERE id = ?", (de_quien,)
        ).fetchone()

        # ---------------------------------------------------------------------
        # Si no hay nada, o intentó ver a alguien más, o ese alguien no existe.
        #
        # Anotamos el intento en la bitácora marcado como NO permitido,
        # y devolvemos None.
        # ---------------------------------------------------------------------
        if persona is None:
            apuntar_en_bitacora(
                conexion, quien_pide, "ver_ficha",
                f"intentó ver los datos de: {de_quien}", False
            )
            conexion.commit()
            return None

        # ---------------------------------------------------------------------
        # PASO 2: traer el dinero de la cuenta. Otra vez, de la vista.
        # ---------------------------------------------------------------------
        cuenta = conexion.execute(
            "SELECT * FROM mi_cuenta WHERE id_usuario = ?", (de_quien,)
        ).fetchone()

        # Si no tiene cuenta (como el admin), no hay ficha que armar.
        if cuenta is None:
            conexion.commit()
            return None

        # ---------------------------------------------------------------------
        # PASO 3: traer todos sus pagos recibidos.
        #
        # ORDER BY fecha → ordenados del más viejo al más nuevo. Importa
        # porque logica/calculos.py mide los huecos entre pagos, y si vienen
        # desordenados los huecos salen negativos y todo se rompe.
        #
        # .fetchall() trae TODAS las filas (a diferencia de .fetchone()).
        # ---------------------------------------------------------------------
        pagos = conexion.execute(
            "SELECT fecha, monto, cliente FROM mis_pagos WHERE id_usuario = ? ORDER BY fecha",
            (de_quien,)
        ).fetchall()

        # ---------------------------------------------------------------------
        # PASO 4: traer sus gastos fijos.
        #
        # ORDER BY se_paga_en → del que toca más pronto al que toca más tarde.
        # ---------------------------------------------------------------------
        gastos = conexion.execute(
            "SELECT concepto, monto, se_paga_en FROM mis_gastos WHERE id_usuario = ? ORDER BY se_paga_en",
            (de_quien,)
        ).fetchall()

        # ---------------------------------------------------------------------
        # PASO 5: anotar en la bitácora que SÍ se permitió, y armar la ficha.
        # ---------------------------------------------------------------------
        apuntar_en_bitacora(
            conexion, quien_pide, "ver_ficha",
            f"vio los datos de: {de_quien}", True
        )
        conexion.commit()

        # ---------------------------------------------------------------------
        # Armamos el diccionario con la MISMA forma que tenía en clientes.py.
        #
        # El "[dict(p) for p in pagos]" convierte cada fila de SQLite a un
        # diccionario normal de Python. Sin eso, el resto del programa
        # recibiría objetos sqlite3.Row que no sabe manejar.
        # ---------------------------------------------------------------------
        return {
            "id": persona["id"],
            "nombre": persona["nombre"],
            "profesion": persona["profesion"],
            "correo": persona["correo"],
            "dinero_en_el_banco": cuenta["dinero_en_el_banco"],
            "gasto_diario_promedio": cuenta["gasto_diario_promedio"],
            "veces_sin_dinero": cuenta["veces_sin_dinero"],
            "pagos_recibidos": [dict(p) for p in pagos],
            "gastos_fijos": [dict(g) for g in gastos],
        }

    finally:
        # ---------------------------------------------------------------------
        # ¿QUÉ ES "finally"?
        # Es un bloque que se ejecuta SIEMPRE, pase lo que pase: si todo salió
        # bien, si hubo un error, o si se hizo return a medio camino.
        #
        # Lo usamos para cerrar la conexión. Si no cerráramos, cada petición
        # dejaría una conexión abierta y en unas horas el servidor se queda
        # sin poder abrir más. A eso se le llama "fuga de recursos".
        # ---------------------------------------------------------------------
        conexion.close()


# =============================================================================
#  FUNCIÓN 2:  traer_lista_de_clientes
#
#  Devuelve la lista de todos los clientes, para el panel de administrador.
#
#  ¡OJO CON ESTA FUNCIÓN! Es la que más cuidado necesita, porque es la única
#  que devuelve datos de MUCHAS personas a la vez.
#
#  Por eso tiene DOS candados:
#     Candado 1 → revisamos el rol aquí mismo, en Python
#     Candado 2 → el RLS de la base, que de todos modos filtraría
#
#  ¿POR QUÉ DOS CANDADOS SI CON UNO BASTA?
#  Se llama "defensa en profundidad". La idea es que ninguna sola falla
#  sea suficiente para que se filtren datos. Si alguien borra el candado
#  de Python por error, el de la base sigue ahí. Es el mismo motivo por el
#  que un banco tiene bóveda Y guardia Y cámaras.
# =============================================================================
def traer_lista_de_clientes(quien_pide, rol):

    conexion = conectar_como(quien_pide, rol)

    try:
        # ---------------------------------------------------------------------
        # CANDADO 1: si no es administrador, se va con las manos vacías.
        #
        # El "!=" significa "es diferente de".
        # ---------------------------------------------------------------------
        if rol != "admin":
            apuntar_en_bitacora(
                conexion, quien_pide, "ver_lista_clientes",
                "un cliente intentó ver la lista completa", False
            )
            conexion.commit()
            return None

        # ---------------------------------------------------------------------
        # CANDADO 2: aunque ya pasó el candado de arriba, seguimos leyendo de
        # las vistas y no de las tablas. Si alguien se equivocara y llamara
        # esta función con rol "cliente", la vista solo le daría su propia fila.
        #
        # ¿QUÉ ES UN "JOIN"?
        # Es pegar dos tablas por una columna que tienen en común, para armar
        # filas más completas. Aquí pegamos:
        #     mis_datos  (que tiene: id, nombre, profesion, correo)
        #     mi_cuenta  (que tiene: id_usuario, dinero_en_el_banco, ...)
        # usando la condición "donde el id de una sea igual al id_usuario
        # de la otra".
        #
        # El resultado es una fila por cliente con las columnas de ambas.
        #
        # Las letras "u" y "c" después del nombre de cada vista son apodos
        # (alias). Sirven para escribir u.nombre en vez de mis_datos.nombre.
        #
        # WHERE u.rol = 'cliente' → el administrador no se lista a sí mismo.
        # ---------------------------------------------------------------------
        filas = conexion.execute("""
            SELECT u.id, u.nombre, u.profesion, u.correo,
                   c.dinero_en_el_banco, c.veces_sin_dinero
            FROM mis_datos u
            JOIN mi_cuenta c ON u.id = c.id_usuario
            WHERE u.rol = 'cliente'
            ORDER BY u.nombre
        """).fetchall()

        apuntar_en_bitacora(
            conexion, quien_pide, "ver_lista_clientes",
            f"listó {len(filas)} clientes", True
        )
        conexion.commit()

        return [dict(f) for f in filas]

    finally:
        conexion.close()
