# =============================================================================
#  prueba_seguridad.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Demuestra que la seguridad funciona de verdad, no solo que está escrita.
#
#  ¿POR QUÉ ES IMPORTANTE TENERLO?
#  Porque escribir medidas de seguridad sin probarlas es peor que no
#  escribirlas: te da una falsa sensación de que estás protegido. Muchas
#  fugas de datos reales pasaron en sistemas que SÍ tenían las reglas
#  escritas, pero mal conectadas, y nadie lo había verificado.
#
#  Este archivo NO necesita que el servidor esté corriendo. Habla directo
#  con la base de datos. Para probar también la parte de internet (los
#  códigos 401 y 403), está la sección 5 al final, que sí lo necesita.
#
#  CÓMO CORRERLO:
#      python prueba_seguridad.py
# =============================================================================

# -----------------------------------------------------------------------------
# Traemos las funciones que vamos a poner a prueba.
# -----------------------------------------------------------------------------
from seguridad.base_datos import construir_la_base
from seguridad.guardia import (
    conectar_como,
    intentar_entrar,
    revisar_pulsera,
    quitar_pulsera,
    revolver_contrasena,
    generar_sal,
)
from seguridad.consultas import traer_ficha_completa, traer_lista_de_clientes


# -----------------------------------------------------------------------------
# Dos contadores para llevar la cuenta de cómo nos fue.
#
# Están fuera de las funciones para que todas puedan sumarles. En Python,
# para modificar una variable de afuera desde adentro de una función, hay
# que escribir "global" primero (lo verás en la función de abajo).
# -----------------------------------------------------------------------------
pasaron = 0
fallaron = 0


def revisar(descripcion, salio_bien):
    """
    Anota el resultado de una prueba y lo imprime.

    PARÁMETROS:
       descripcion → qué estábamos probando, en español
       salio_bien  → True si el resultado fue el esperado
    """
    global pasaron, fallaron

    if salio_bien:
        pasaron += 1
        print(f"  OK     {descripcion}")
    else:
        fallaron += 1
        print(f"  FALLÓ  {descripcion}")


# =============================================================================
#  PREPARATIVOS
# =============================================================================

print()
print("=" * 70)
print("  PRUEBAS DE SEGURIDAD — Consola de Liquidez")
print("=" * 70)

# Nos aseguramos de que la base exista antes de probar nada.
construir_la_base()


# =============================================================================
#  BLOQUE 1 — LAS CONTRASEÑAS
# =============================================================================

print()
print("1) Las contraseñas se guardan de forma irreversible")

# -----------------------------------------------------------------------------
# PRUEBA 1.1: la misma contraseña con la misma sal SIEMPRE da lo mismo.
#
# Si esto fallara, nadie podría entrar nunca: al comparar, el resultado
# nunca coincidiría con el guardado.
# -----------------------------------------------------------------------------
sal = generar_sal()
primera_vez = revolver_contrasena("miClave123", sal)
segunda_vez = revolver_contrasena("miClave123", sal)
revisar("la misma clave con la misma sal da el mismo resultado",
        primera_vez == segunda_vez)

# -----------------------------------------------------------------------------
# PRUEBA 1.2: la misma contraseña con DISTINTA sal da resultados distintos.
#
# Esto es lo que rompe las tablas arcoíris. Si dos personas tienen la clave
# "123", en la base se ven completamente diferentes.
# -----------------------------------------------------------------------------
otra_sal = generar_sal()
con_otra_sal = revolver_contrasena("miClave123", otra_sal)
revisar("la misma clave con distinta sal da resultados distintos",
        primera_vez != con_otra_sal)

# -----------------------------------------------------------------------------
# PRUEBA 1.3: la contraseña original NO aparece en el resultado.
#
# Parece obvio, pero un hash mal implementado (por ejemplo, uno que solo
# invierta el texto) dejaría rastros. Revisamos que no esté adentro.
# -----------------------------------------------------------------------------
revisar("la clave original no aparece dentro del resultado",
        "miClave123" not in primera_vez)

# -----------------------------------------------------------------------------
# PRUEBA 1.4: en la base de datos NO hay ninguna contraseña en texto plano.
#
# Esta es la prueba que un juez pediría: "ábreme la tabla de usuarios".
# -----------------------------------------------------------------------------
conexion = conectar_como("admin", "admin")
filas = conexion.execute("SELECT contrasena_revuelta FROM usuarios").fetchall()
conexion.close()

# any() devuelve True si ALGUNA de las cosas de la lista es verdadera.
# Aquí preguntamos: ¿alguna fila tiene guardado literalmente "123"?
hay_clave_visible = any(f[0] == "123" or f[0] == "admin123" for f in filas)
revisar("ninguna contraseña está guardada en texto plano",
        not hay_clave_visible)


# =============================================================================
#  BLOQUE 2 — EL LOGIN
# =============================================================================

print()
print("2) La puerta de entrada deja pasar a quien debe")

revisar("maria entra con su clave correcta",
        intentar_entrar("maria", "123") is not None)

revisar("maria NO entra con una clave equivocada",
        intentar_entrar("maria", "clave_inventada") is None)

revisar("un usuario que no existe no entra",
        intentar_entrar("fulanito", "123") is None)

revisar("también se puede entrar con el correo completo",
        intentar_entrar("maria@capitalone.mx", "123") is not None)

revisar("el admin entra con su propia clave",
        intentar_entrar("admin", "admin123") is not None)

# -----------------------------------------------------------------------------
# PRUEBA: el login devuelve el rol correcto.
#
# Es lo que decide qué panel ve cada quien. Si esto se equivocara, un
# cliente acabaría en el panel del banco.
# -----------------------------------------------------------------------------
sesion_maria = intentar_entrar("maria", "123")
sesion_admin = intentar_entrar("admin", "admin123")

revisar("maria recibe el rol 'cliente'", sesion_maria["rol"] == "cliente")
revisar("admin recibe el rol 'admin'", sesion_admin["rol"] == "admin")


# =============================================================================
#  BLOQUE 3 — LAS SESIONES (los tokens)
# =============================================================================

print()
print("3) Las pulseras de sesión funcionan como deben")

token_de_maria = sesion_maria["token"]

# -----------------------------------------------------------------------------
# PRUEBA: el token es largo. Un token corto se podría adivinar probando.
# len() cuenta cuántos caracteres tiene un texto.
# -----------------------------------------------------------------------------
revisar("el token tiene al menos 32 caracteres",
        len(token_de_maria) >= 32)

# -----------------------------------------------------------------------------
# PRUEBA: dos sesiones distintas nunca comparten el mismo token.
# Si se repitieran, dos personas podrían acabar viendo la misma cuenta.
# -----------------------------------------------------------------------------
otra_sesion = intentar_entrar("maria", "123")
revisar("dos sesiones distintas tienen tokens distintos",
        otra_sesion["token"] != token_de_maria)

revisar("un token válido dice a quién pertenece",
        revisar_pulsera(token_de_maria)["id"] == "maria")

revisar("un token inventado no vale nada",
        revisar_pulsera("token_falso_123") is None)

revisar("sin token no hay identidad",
        revisar_pulsera(None) is None)

# -----------------------------------------------------------------------------
# PRUEBA: al cerrar sesión, el token deja de servir INMEDIATAMENTE.
#
# Esta es la razón de que exista el endpoint /api/salir. Si solo borráramos
# el token del navegador, el de acá seguiría vivo 30 minutos.
# -----------------------------------------------------------------------------
quitar_pulsera(token_de_maria)
revisar("al cerrar sesión el token deja de servir al instante",
        revisar_pulsera(token_de_maria) is None)


# =============================================================================
#  BLOQUE 4 — EL RLS (la prueba principal)
# =============================================================================

print()
print("4) El RLS: cada quien ve solo lo suyo")

# -----------------------------------------------------------------------------
# LA PRUEBA MÁS IMPORTANTE DE TODO EL ARCHIVO.
#
# Conectados como María, pedimos TODOS los pagos de la base, sin ningún
# filtro, sin WHERE, sin nada. Es la consulta que escribiría un programador
# distraído.
#
# Si el RLS funciona, de todos modos solo salen los de María.
# -----------------------------------------------------------------------------
conexion = conectar_como("maria", "cliente")
duenos = conexion.execute("SELECT DISTINCT id_usuario FROM mis_pagos").fetchall()
conexion.close()

# Convertimos el resultado a una lista simple de textos para compararla.
lista_de_duenos = [f[0] for f in duenos]
revisar("pidiendo TODOS los pagos, maria solo obtiene los suyos",
        lista_de_duenos == ["maria"])

# -----------------------------------------------------------------------------
# Lo mismo con las cuentas: el saldo de los demás no existe para María.
# -----------------------------------------------------------------------------
conexion = conectar_como("maria", "cliente")
cuentas = conexion.execute("SELECT id_usuario FROM mi_cuenta").fetchall()
conexion.close()
revisar("maria solo puede ver una cuenta: la suya",
        len(cuentas) == 1 and cuentas[0][0] == "maria")

# -----------------------------------------------------------------------------
# Ahora el intento directo: María pide la ficha de Carlos por su nombre.
# -----------------------------------------------------------------------------
revisar("maria NO puede traer la ficha de carlos",
        traer_ficha_completa("maria", "cliente", "carlos") is None)

revisar("maria NO puede traer la ficha de ana",
        traer_ficha_completa("maria", "cliente", "ana") is None)

revisar("maria SÍ puede traer su propia ficha",
        traer_ficha_completa("maria", "cliente", "maria") is not None)

# -----------------------------------------------------------------------------
# El analista sí puede. Es la excepción escrita a propósito, en un solo lugar.
# -----------------------------------------------------------------------------
conexion = conectar_como("admin", "admin")
duenos_admin = conexion.execute("SELECT DISTINCT id_usuario FROM mis_pagos").fetchall()
conexion.close()

# sorted() ordena la lista alfabéticamente, para que la comparación no
# dependa del orden en que la base devolvió las filas.
revisar("el admin SÍ ve los datos de los tres clientes",
        sorted(f[0] for f in duenos_admin) == ["ana", "carlos", "maria"])

revisar("el admin puede abrir la ficha de cualquiera",
        traer_ficha_completa("admin", "admin", "carlos") is not None)

# -----------------------------------------------------------------------------
# La lista completa de clientes es solo para el analista.
# -----------------------------------------------------------------------------
revisar("un cliente NO puede pedir la lista completa",
        traer_lista_de_clientes("maria", "cliente") is None)

lista = traer_lista_de_clientes("admin", "admin")
revisar("el admin SÍ obtiene la lista, con los 3 clientes",
        lista is not None and len(lista) == 3)

# -----------------------------------------------------------------------------
# PRUEBA SUTIL PERO IMPORTANTE: el admin no se lista a sí mismo.
#
# La política dice "solo las filas cuyo rol sea cliente". Sirve para que
# alguien que robe una cuenta de analista no obtenga el directorio de
# empleados del banco.
# -----------------------------------------------------------------------------
ids_en_la_lista = [c["id"] for c in lista]
revisar("el admin no aparece en su propia lista de clientes",
        "admin" not in ids_en_la_lista)

# -----------------------------------------------------------------------------
# PRUEBA: las vistas no exponen contraseñas.
#
# Aunque alguien lograra leer mis_datos, no se lleva nada útil para entrar.
# -----------------------------------------------------------------------------
conexion = conectar_como("admin", "admin")
columnas = [d[0] for d in conexion.execute("SELECT * FROM mis_datos LIMIT 1").description]
conexion.close()
revisar("la vista de usuarios no expone la contraseña ni la sal",
        "contrasena_revuelta" not in columnas and "sal" not in columnas)


# =============================================================================
#  BLOQUE 5 — LA BITÁCORA
# =============================================================================

print()
print("5) La bitácora deja rastro de todo")

from seguridad.guardia import leer_bitacora

# Hacemos un intento que debe quedar registrado como bloqueado.
traer_ficha_completa("maria", "cliente", "carlos")

diario = leer_bitacora(20)

# -----------------------------------------------------------------------------
# Buscamos si el intento quedó anotado. La expresión de abajo se lee:
# "¿existe alguna línea del diario que sea de maria, sobre ver_ficha,
#  y que esté marcada como no permitida?"
# -----------------------------------------------------------------------------
quedo_registrado = any(
    linea["id_usuario"] == "maria"
    and linea["accion"] == "ver_ficha"
    and linea["permitido"] == 0
    for linea in diario
)
revisar("el intento bloqueado de maria quedó en la bitácora", quedo_registrado)

# Y también los accesos que SÍ se permitieron.
traer_ficha_completa("maria", "cliente", "maria")
diario = leer_bitacora(20)
hay_permitidos = any(linea["permitido"] == 1 for linea in diario)
revisar("los accesos permitidos también se registran", hay_permitidos)


# =============================================================================
#  RESULTADO FINAL
# =============================================================================

print()
print("=" * 70)
if fallaron == 0:
    print(f"  TODO BIEN — {pasaron} pruebas de seguridad pasaron, 0 fallaron")
else:
    print(f"  ATENCIÓN — {pasaron} pasaron, {fallaron} FALLARON")
print("=" * 70)
print()
print("  Para probar también los códigos HTTP (401, 403, 404), arranca el")
print("  servidor con 'python servidor.py' y revisa la sección 8 del")
print("  MAPA_DE_FLUJO.md, que trae los comandos curl listos para copiar.")
print()
