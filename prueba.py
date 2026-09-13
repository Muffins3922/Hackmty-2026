# =============================================================================
#  ARCHIVO EXTRA:  prueba.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Revisa que todo el sistema funcione bien, sin necesidad de abrir el
#  navegador. Se corre con:
#
#      python prueba.py
#
#  ¿PARA QUÉ SIRVE EN LA PRESENTACIÓN?
#  Si un juez pregunta "¿cómo sabes que tu score no cambia solo?", corres
#  esto enfrente de él y le muestras la prueba número 3.
#
#  ¿QUÉ ES UNA "PRUEBA" O "TEST"?
#  Es código que revisa otro código. Le das datos que ya sabes cómo deben
#  salir, y verifica que salgan así. Si un día alguien rompe algo sin
#  querer, esta prueba lo detecta antes que un usuario.
# =============================================================================

from datos.clientes import obtener_cliente, listar_clientes
from logica.calculos import analizar_cliente
from logica.score import calcular_score, PESOS
from logica.prediccion import predecir_21_dias, simular_compra, DIAS_A_PREDECIR


# -----------------------------------------------------------------------------
# Contadores para el reporte final.
# -----------------------------------------------------------------------------
pasadas = 0
falladas = 0


def revisar(descripcion, condicion):
    """
    Revisa una condición y la reporta.

    "global" le dice a Python que queremos modificar las variables de afuera
    de la función, no crear unas nuevas adentro.
    """
    global pasadas, falladas

    if condicion:
        print(f"  OK   {descripcion}")
        pasadas += 1
    else:
        print(f"  FALLA  {descripcion}")
        falladas += 1


print("")
print("=" * 68)
print("  PRUEBAS DE LA CONSOLA DE LIQUIDEZ")
print("=" * 68)


# =============================================================================
#  PRUEBA 1 — Los datos de ejemplo están completos
# =============================================================================
print("")
print("1) Los tres clientes existen y tienen todos sus datos")

for id_cliente in ["maria", "carlos", "ana"]:
    c = obtener_cliente(id_cliente)
    revisar(f"existe el cliente '{id_cliente}'", c is not None)
    revisar(f"'{id_cliente}' tiene pagos registrados", len(c["pagos_recibidos"]) > 0)
    revisar(f"'{id_cliente}' tiene gastos fijos", len(c["gastos_fijos"]) > 0)


# =============================================================================
#  PRUEBA 2 — Los pesos del score suman 1.00
# =============================================================================
print("")
print("2) Los pesos del score están bien repartidos")

suma_de_pesos = sum(PESOS.values())
revisar(f"los 6 pesos suman 1.00 (dio {suma_de_pesos:.4f})", abs(suma_de_pesos - 1.0) < 0.001)
revisar("hay exactamente 6 componentes", len(PESOS) == 6)


# =============================================================================
#  PRUEBA 3 — CONSISTENCIA: el score nunca cambia solo
#
#  Esta es la prueba más importante del proyecto.
# =============================================================================
print("")
print("3) El score es determinista (no cambia entre corridas)")

for id_cliente in ["maria", "carlos", "ana"]:
    cliente = obtener_cliente(id_cliente)

    # "set" en Python es un conjunto: guarda valores SIN repetir.
    # Si corremos 100 veces y todos dan lo mismo, el conjunto tendrá
    # exactamente 1 elemento. Si algo varía, tendrá 2 o más.
    resultados = set()

    for _ in range(100):
        resultados.add(calcular_score(analizar_cliente(cliente))["score"])

    revisar(
        f"'{id_cliente}': 100 corridas dieron un solo valor {resultados}",
        len(resultados) == 1
    )


# =============================================================================
#  PRUEBA 4 — El score siempre cae dentro de la escala 300-850
# =============================================================================
print("")
print("4) El score respeta los límites de la escala bancaria")

for id_cliente in ["maria", "carlos", "ana"]:
    s = calcular_score(analizar_cliente(obtener_cliente(id_cliente)))
    revisar(
        f"'{id_cliente}': score {s['score']} está entre 300 y 850",
        300 <= s["score"] <= 850
    )
    revisar(
        f"'{id_cliente}': las 6 barras del desglose están completas",
        len(s["detalle_de_notas"]) == 6
    )


# =============================================================================
#  PRUEBA 5 — El modelo SÍ distingue entre perfiles
#
#  Un modelo que le da el mismo score a todos no sirve de nada.
#  Carlos (estable, ahorrador) debe salir mejor que María (medio),
#  y María mejor que Ana (en riesgo).
# =============================================================================
print("")
print("5) El modelo separa correctamente los tres perfiles")

score_carlos = calcular_score(analizar_cliente(obtener_cliente("carlos")))["score"]
score_maria = calcular_score(analizar_cliente(obtener_cliente("maria")))["score"]
score_ana = calcular_score(analizar_cliente(obtener_cliente("ana")))["score"]

revisar(f"Carlos ({score_carlos}) sale mejor que María ({score_maria})", score_carlos > score_maria)
revisar(f"María ({score_maria}) sale mejor que Ana ({score_ana})", score_maria > score_ana)
revisar(f"Ana ({score_ana}) queda por debajo de 560 (En riesgo)", score_ana < 560)


# =============================================================================
#  PRUEBA 6 — La predicción devuelve exactamente 21 días
# =============================================================================
print("")
print("6) La predicción de 21 días está bien formada")

for id_cliente in ["maria", "carlos", "ana"]:
    p = predecir_21_dias(analizar_cliente(obtener_cliente(id_cliente)))

    revisar(f"'{id_cliente}': devuelve {DIAS_A_PREDECIR} días", len(p["dias"]) == DIAS_A_PREDECIR)

    # Revisamos que los días vayan numerados del 1 al 21 en orden.
    numeros = [d["dia"] for d in p["dias"]]
    revisar(f"'{id_cliente}': los días van del 1 al 21 en orden",
            numeros == list(range(1, DIAS_A_PREDECIR + 1)))

    # Revisamos que cada día tenga su nivel de riesgo asignado.
    niveles_validos = all(d["nivel"] in ("bien", "cuidado", "peligro") for d in p["dias"])
    revisar(f"'{id_cliente}': todos los días tienen nivel de riesgo válido", niveles_validos)


# =============================================================================
#  PRUEBA 7 — Ana debe disparar la alerta de quedarse sin dinero
# =============================================================================
print("")
print("7) La alerta de riesgo se dispara cuando debe")

p_ana = predecir_21_dias(analizar_cliente(obtener_cliente("ana")))
revisar("Ana (perfil de riesgo) sí dispara la alerta", p_ana["se_queda_sin_dinero"] is True)

p_carlos = predecir_21_dias(analizar_cliente(obtener_cliente("carlos")))
revisar("Carlos (perfil sano) NO dispara la alerta", p_carlos["se_queda_sin_dinero"] is False)


# =============================================================================
#  PRUEBA 8 — El simulador de compras reacciona al monto
#
#  Una compra chica debe salir verde y una enorme debe salir roja.
#  Si ambas salieran igual, el simulador no estaría sirviendo de nada.
# =============================================================================
print("")
print("8) El simulador de compras responde al tamaño de la compra")

analisis_maria = analizar_cliente(obtener_cliente("maria"))

compra_chica = simular_compra(analisis_maria, 1500)
compra_enorme = simular_compra(analisis_maria, 30000)

revisar(f"compra de $1,500 sale en verde (dio '{compra_chica['semaforo']}')",
        compra_chica["semaforo"] == "verde")
revisar(f"compra de $30,000 sale en rojo (dio '{compra_enorme['semaforo']}')",
        compra_enorme["semaforo"] == "rojo")

# La compra grande debe costar más días de colchón que la chica.
revisar("la compra grande cuesta más días de colchón que la chica",
        compra_enorme["dias_de_colchon_que_cuesta"] > compra_chica["dias_de_colchon_que_cuesta"])

# La simulación debe devolver las dos proyecciones para poder comparar.
revisar("la simulación devuelve el 'antes' y el 'después'",
        "antes" in compra_chica and "despues" in compra_chica)


# =============================================================================
#  PRUEBA 9 — La línea de crédito nunca es negativa ni absurda
# =============================================================================
print("")
print("9) La línea de crédito recomendada tiene sentido")

for id_cliente in ["maria", "carlos", "ana"]:
    s = calcular_score(analizar_cliente(obtener_cliente(id_cliente)))
    a = analizar_cliente(obtener_cliente(id_cliente))

    revisar(f"'{id_cliente}': la línea (${s['linea_recomendada']:,}) no es negativa",
            s["linea_recomendada"] >= 0)

# A quien está en riesgo no se le debe ofrecer crédito.
s_ana = calcular_score(analizar_cliente(obtener_cliente("ana")))
revisar("a Ana (en riesgo) no se le ofrece crédito", s_ana["linea_recomendada"] == 0)


# =============================================================================
#  REPORTE FINAL
# =============================================================================
print("")
print("=" * 68)

if falladas == 0:
    print(f"  TODO BIEN — {pasadas} pruebas pasaron, 0 fallaron")
else:
    print(f"  ATENCIÓN — {pasadas} pasaron, {falladas} FALLARON")

print("=" * 68)
print("")
