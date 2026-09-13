# =============================================================================
#  ARCHIVO 2 de 7:  logica/calculos.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Toma la ficha cruda de un cliente (puros números sueltos) y la convierte
#  en 9 indicadores que SÍ dicen algo sobre su salud financiera.
#
#  ANALOGÍA: la ficha del cliente es como los resultados crudos de un
#  análisis de sangre (números sueltos). Este archivo es el doctor que los
#  lee y dice "tienes el colesterol alto y la presión bien".
#
#  ¿QUIÉN USA ESTE ARCHIVO?
#    - logica/score.py      → usa estos indicadores para calcular el puntaje
#    - logica/prediccion.py → usa el gasto diario y el próximo ingreso
#    - servidor.py          → se los manda a la página web para mostrarlos
#
#  REGLA IMPORTANTE: aquí NO hay inteligencia artificial ni nada aleatorio.
#  Son puras divisiones y sumas. Por eso el resultado SIEMPRE es idéntico
#  con los mismos datos de entrada. Eso se llama ser DETERMINISTA.
# =============================================================================


# -----------------------------------------------------------------------------
# LÍNEA 1: Traemos la caja de herramientas de estadística de Python.
#
# "statistics" ya viene incluida en Python, no hay que instalarla.
# De ella usaremos 2 funciones:
#
#   - statistics.mean(lista)   → calcula el PROMEDIO de una lista de números
#                                 (sumar todo y dividir entre cuántos hay)
#
#   - statistics.pstdev(lista) → calcula la DESVIACIÓN ESTÁNDAR.
#                                 Ese nombre suena feo pero significa algo
#                                 simple: "¿qué tanto se alejan los números
#                                 de su propio promedio?".
#                                 Si todos los pagos son de $100, se alejan
#                                 cero → desviación 0.
#                                 Si un pago es $10 y otro $500, se alejan
#                                 mucho → desviación grande.
#                                 La "p" del nombre significa "poblacional"
#                                 (usamos todos los datos que tenemos, no
#                                  una muestra).
# -----------------------------------------------------------------------------
import statistics


# =============================================================================
#  FUNCIÓN PRINCIPAL DEL ARCHIVO
#
#  Recibe: la ficha completa de un cliente (el diccionario de clientes.py)
#  Devuelve: un diccionario nuevo con los 9 indicadores ya calculados
# =============================================================================
def analizar_cliente(cliente):

    # =========================================================================
    #  PASO 1 — ¿CUÁNTO GANA AL MES?
    # =========================================================================

    # -------------------------------------------------------------------------
    # Sacamos solo los MONTOS de los pagos, sin las fechas ni los nombres.
    #
    # Antes teníamos:  [{"fecha": "...", "monto": 14500, "cliente": "..."}, ...]
    # Ahora queremos:  [14500, 6200, 15800, ...]
    #
    # ¿Por qué? Porque para sacar promedios solo necesitamos los números.
    #
    # "[p["monto"] for p in cliente["pagos_recibidos"]]" se lee así:
    #   "por cada pago (p) que haya en la lista de pagos_recibidos,
    #    dame nada más su campo monto"
    # -------------------------------------------------------------------------
    montos_de_los_pagos = [p["monto"] for p in cliente["pagos_recibidos"]]

    # -------------------------------------------------------------------------
    # Sumamos TODO lo que ganó en los últimos 90 días.
    #
    # "sum(...)" es una función de Python que suma todos los números de una
    # lista. Es la versión corta de "agarra el primero, súmale el segundo,
    # súmale el tercero...".
    # -------------------------------------------------------------------------
    total_ganado_en_90_dias = sum(montos_de_los_pagos)

    # -------------------------------------------------------------------------
    # FÓRMULA: ingreso mensual promedio
    #
    #      ingreso_al_mes = total_ganado_en_90_dias / 3
    #
    # ¿Por qué entre 3?  Porque 90 días son 3 meses. Si ganaste $90,000 en
    # tres meses, tu promedio mensual es $30,000.
    #
    # Variables que usa:
    #   - total_ganado_en_90_dias → se calculó 6 líneas arriba
    #   - el número 3             → es fijo, son los meses que analizamos
    #
    # OJO: es un PROMEDIO, no lo que gana cada mes exacto. Un freelancer
    # puede ganar $50,000 un mes y $10,000 el siguiente. Por eso más abajo
    # también medimos qué tan disparejo es (la volatilidad).
    # -------------------------------------------------------------------------
    ingreso_al_mes = total_ganado_en_90_dias / 3


    # =========================================================================
    #  PASO 2 — ¿CUÁNTO GASTA AL MES?
    # =========================================================================

    # -------------------------------------------------------------------------
    # Sumamos todos sus gastos fijos del mes (renta + luz + internet + ...).
    #
    # Igual que antes: primero sacamos solo los montos con la comprensión de
    # lista, luego los sumamos con sum().
    #
    # A esto también se le llama "obligaciones": son los pagos que NO puede
    # evitar. Si no paga la renta, lo sacan del depa.
    # -------------------------------------------------------------------------
    gastos_fijos_al_mes = sum(g["monto"] for g in cliente["gastos_fijos"])

    # -------------------------------------------------------------------------
    # Convertimos los gastos fijos del MES a lo que cuestan por DÍA.
    #
    #      gasto_fijo_por_dia = gastos_fijos_al_mes / 30
    #
    # ¿Por qué entre 30? Porque un mes tiene ~30 días. Si tu renta es $6,000
    # al mes, es como si te costara $200 cada día que vives ahí.
    #
    # Lo necesitamos por día porque la predicción avanza día por día.
    # -------------------------------------------------------------------------
    gasto_fijo_por_dia = gastos_fijos_al_mes / 30

    # -------------------------------------------------------------------------
    # Sumamos los dos tipos de gasto para saber cuánto se le va CADA DÍA.
    #
    #      gasto_total_por_dia = gasto_fijo_por_dia + gasto_variable_por_dia
    #
    # Variables que usa:
    #   - gasto_fijo_por_dia          → se calculó en la línea de arriba
    #   - cliente["gasto_diario_promedio"] → viene directo de datos/clientes.py
    #                                        (es la comida, gasolina, etc.)
    #
    # ESTE NÚMERO ES MUY IMPORTANTE: es el que "muerde" el saldo todos los
    # días en la gráfica de predicción.
    # -------------------------------------------------------------------------
    gasto_total_por_dia = gasto_fijo_por_dia + cliente["gasto_diario_promedio"]

    # -------------------------------------------------------------------------
    # Y el gasto total del mes = lo que se le va por día × 30 días.
    # Lo usamos para comparar contra el ingreso mensual.
    # -------------------------------------------------------------------------
    gasto_total_al_mes = gasto_total_por_dia * 30


    # =========================================================================
    #  PASO 3 — DÍAS DE COLCHÓN  (el indicador más importante de todos)
    # =========================================================================

    # -------------------------------------------------------------------------
    # ¿QUÉ ES EL "COLCHÓN"?
    # Es cuántos días puede vivir esta persona si HOY se le acabaran todos
    # los clientes y no entrara ni un peso más.
    #
    # Se llama colchón porque amortigua la caída, como el colchón de un
    # acróbata. En inglés le dicen "buffer" o "runway" (pista de aterrizaje).
    #
    # FÓRMULA:
    #      dias_de_colchon = dinero_en_el_banco / gasto_total_por_dia
    #
    # EJEMPLO CON NÚMEROS REALES (María):
    #      18,400 pesos  /  762 pesos al día  =  24.1 días
    #      → "María aguanta 24 días sin cobrar nada"
    #
    # Variables que usa:
    #   - cliente["dinero_en_el_banco"] → viene de datos/clientes.py
    #   - gasto_total_por_dia           → se calculó en el PASO 2
    #
    # ¿POR QUÉ EL "if"?
    # Si el gasto diario fuera 0, la división explotaría (dividir entre cero
    # no existe en matemáticas y Python tira un error). El "if" revisa antes:
    # si hay gasto, divide; si no hay gasto, devuelve 999 (que significa
    # "aguanta para siempre").
    #
    # "round(numero, 1)" es una función de Python que redondea. El 1 significa
    # "déjame 1 decimal". Así mostramos 24.1 en vez de 24.146981627296588.
    # -------------------------------------------------------------------------
    if gasto_total_por_dia > 0:
        dias_de_colchon = round(cliente["dinero_en_el_banco"] / gasto_total_por_dia, 1)
    else:
        dias_de_colchon = 999


    # =========================================================================
    #  PASO 4 — VOLATILIDAD DEL INGRESO  (qué tan disparejos son sus pagos)
    # =========================================================================

    # -------------------------------------------------------------------------
    # ¿QUÉ ES "VOLATILIDAD"?
    # Es qué tan brincones son sus ingresos. Un sueldo fijo de oficina tiene
    # volatilidad casi cero (siempre lo mismo). Un freelancer que un mes cobra
    # $30,000 y otro $5,000 tiene volatilidad altísima.
    #
    # Para un banco, la volatilidad alta = riesgo, porque no sabe si el mes
    # que toca pagar el préstamo va a ser un mes bueno o uno malo.
    #
    # LA MEDIMOS CON EL "COEFICIENTE DE VARIACIÓN" (en inglés: CV).
    # Suena horrible, pero es solo esta división:
    #
    #      volatilidad = desviacion_estandar / promedio
    #
    # ¿POR QUÉ DIVIDIR ENTRE EL PROMEDIO?
    # Porque si no, no podríamos comparar personas. Una desviación de $2,000
    # es enorme para alguien que gana $3,000, pero es nada para alguien que
    # gana $200,000. Al dividir entre el promedio, el resultado queda en
    # "porcentaje de qué tanto varía respecto a lo normal para esa persona".
    #
    # CÓMO LEER EL RESULTADO:
    #      0.0  = todos los pagos son idénticos (imposible en la vida real)
    #      0.3  = varía poco, muy estable  (Carlos anda por aquí)
    #      0.5  = varía bastante           (María anda por aquí)
    #      1.0+ = caótico, muy riesgoso    (Ana anda por aquí)
    # -------------------------------------------------------------------------

    # Primero revisamos que haya al menos 2 pagos.
    # ¿Por qué? Porque con un solo pago no se puede medir variación: no hay
    # con qué compararlo. "len(...)" es una función de Python que cuenta
    # cuántos elementos tiene una lista.
    if len(montos_de_los_pagos) >= 2:

        # El promedio de sus pagos (la "raya de en medio").
        promedio_de_pagos = statistics.mean(montos_de_los_pagos)

        # Qué tanto se alejan los pagos de esa raya de en medio.
        que_tanto_varian = statistics.pstdev(montos_de_los_pagos)

        # La división que convierte todo a una escala comparable.
        volatilidad = round(que_tanto_varian / promedio_de_pagos, 2)
    else:
        # Sin datos suficientes asumimos el peor caso (1.0 = caótico),
        # porque es más seguro para el banco pecar de precavido.
        volatilidad = 1.0


    # =========================================================================
    #  PASO 5 — CONCENTRACIÓN DE CLIENTES  (¿depende de una sola persona?)
    # =========================================================================

    # -------------------------------------------------------------------------
    # ¿POR QUÉ IMPORTA?
    # Si toda tu lana viene de UN solo cliente y ese cliente te deja, te
    # quedas en cero de un día para otro. Si tienes 5 clientes y uno te deja,
    # pierdes 20% pero sobrevives.
    #
    # CÓMO LO MEDIMOS:
    # Contamos cuánto le pagó cada cliente, sacamos qué porcentaje del total
    # representa cada uno, y nos quedamos con el porcentaje del MÁS GRANDE.
    #
    #      concentracion = lo_que_paga_el_cliente_mas_grande / total_ganado
    #
    # CÓMO LEER EL RESULTADO:
    #      0.20 = ningún cliente pesa más del 20%. Muy sano, bien repartido.
    #      0.50 = la mitad de tu dinero viene de uno. Cuidado.
    #      1.00 = TODO viene de un solo cliente. Peligro máximo.
    # -------------------------------------------------------------------------

    # Creamos un diccionario vacío para ir sumando lo de cada cliente.
    # Va a quedar así:  {"Agencia Norte": 46500, "Tienda Luna": 27100, ...}
    pagado_por_cada_cliente = {}

    # Recorremos pago por pago.
    # "for p in lista" significa "haz esto una vez por cada elemento de la
    # lista, y mientras tanto llámalo p".
    for p in cliente["pagos_recibidos"]:

        # Sacamos el nombre de quién pagó.
        nombre = p["cliente"]

        # Le sumamos este pago a lo que ya llevaba ese cliente.
        #
        # ".get(nombre, 0)" busca a ese cliente en el diccionario. Si es la
        # primera vez que aparece, todavía no existe, así que devuelve 0
        # (el valor por defecto) en vez de tronar. Luego le sumamos el monto.
        pagado_por_cada_cliente[nombre] = pagado_por_cada_cliente.get(nombre, 0) + p["monto"]

    # Ahora buscamos cuál cliente pagó más.
    #
    # "max(...)" es una función de Python que devuelve el número más grande
    # de una lista. ".values()" saca solo los montos del diccionario, sin
    # los nombres.
    #
    # El "if ... else 0" al final protege el caso de que no haya ningún pago.
    pago_del_cliente_mas_grande = max(pagado_por_cada_cliente.values()) if pagado_por_cada_cliente else 0

    # La división final. El "if" protege contra dividir entre cero otra vez.
    if total_ganado_en_90_dias > 0:
        concentracion = round(pago_del_cliente_mas_grande / total_ganado_en_90_dias, 2)
    else:
        concentracion = 1.0

    # También guardamos cuántos clientes distintos tiene, para mostrarlo
    # en pantalla. "len(diccionario)" cuenta cuántas etiquetas tiene.
    cuantos_clientes_tiene = len(pagado_por_cada_cliente)


    # =========================================================================
    #  PASO 6 — COBERTURA DE OBLIGACIONES  (en los bancos le dicen "DSCR")
    # =========================================================================

    # -------------------------------------------------------------------------
    # ¿QUÉ SIGNIFICA "DSCR"?
    # Son las siglas en inglés de "Debt Service Coverage Ratio", que en
    # español sería "razón de cobertura de deuda". Nombre horrible, idea
    # simple:
    #
    #      ¿Cuántas veces alcanza tu ingreso para pagar lo obligatorio?
    #
    # FÓRMULA:
    #      cobertura = ingreso_al_mes / gastos_fijos_al_mes
    #
    # CÓMO LEERLO:
    #      2.0 = ganas el DOBLE de lo que debes pagar. Excelente.
    #      1.5 = te sobra la mitad. Bien.
    #      1.0 = ganas exactamente lo que gastas. No sobra nada. Riesgoso.
    #      0.8 = gastas más de lo que ganas. Vas en picada.
    #
    # Los bancos normalmente piden mínimo 1.25 para prestarte.
    #
    # Variables que usa:
    #   - ingreso_al_mes      → del PASO 1
    #   - gastos_fijos_al_mes → del PASO 2
    # -------------------------------------------------------------------------
    if gastos_fijos_al_mes > 0:
        cobertura = round(ingreso_al_mes / gastos_fijos_al_mes, 2)
    else:
        cobertura = 99.0


    # =========================================================================
    #  PASO 7 — TASA DE AHORRO  (qué porcentaje de lo que gana le sobra)
    # =========================================================================

    # -------------------------------------------------------------------------
    # FÓRMULA:
    #      ahorro = (ingreso_al_mes - gasto_total_al_mes) / ingreso_al_mes
    #
    # En palabras: de cada peso que entra, ¿qué fracción sobrevive al final
    # del mes?
    #
    # CÓMO LEERLO:
    #      0.30 = ahorra 30 centavos de cada peso. Muy bien.
    #      0.05 = ahorra 5 centavos. Apenas.
    #     -0.10 = NEGATIVO: gasta 10% más de lo que gana. Se está comiendo
    #             sus ahorros y va directo al sobregiro.
    # -------------------------------------------------------------------------
    if ingreso_al_mes > 0:
        ahorro = round((ingreso_al_mes - gasto_total_al_mes) / ingreso_al_mes, 2)
    else:
        ahorro = -1.0


    # =========================================================================
    #  PASO 8 — ¿CUÁNDO LLEGA EL PRÓXIMO PAGO?
    # =========================================================================

    # -------------------------------------------------------------------------
    # ¿QUÉ ESTAMOS ADIVINANDO?
    # Cuántos días faltan para que le caiga el siguiente pago.
    #
    # CÓMO LO ADIVINAMOS (sin inteligencia artificial, solo con un promedio):
    #   1. Medimos cuántos días pasaron entre cada pago pasado.
    #        Ejemplo María: 14, 13, 9, 14, 9, 12, 11 días
    #   2. Sacamos el promedio de esos huecos → 11.7 días
    #   3. Decimos: "si su ritmo se mantiene, el próximo cae en ~12 días"
    #
    # LIMITACIÓN HONESTA (dilo en la presentación, suma puntos):
    # Esto NO es una bola de cristal. Asume que el pasado se repite. Si un
    # cliente la deja mañana, la predicción se equivoca. Por eso en la
    # interfaz lo mostramos como "estimado", no como un hecho.
    # -------------------------------------------------------------------------

    # Sacamos solo las fechas, sin montos.
    fechas_de_pago = [p["fecha"] for p in cliente["pagos_recibidos"]]

    # Las ordenamos de más vieja a más nueva.
    #
    # "sorted(...)" es una función de Python que ordena. Como las fechas están
    # escritas "AAAA-MM-DD", ordenarlas como texto da el mismo resultado que
    # ordenarlas como fechas (por eso ese formato es tan usado).
    #
    # ORDENAR ES OBLIGATORIO PARA LA CONSISTENCIA: si los datos llegaran
    # desordenados de la API, los huecos entre pagos saldrían mal y el
    # resultado cambiaría. Ordenar garantiza que siempre calculemos igual.
    fechas_de_pago = sorted(fechas_de_pago)

    # Lista donde vamos a guardar los huecos (en días) entre pago y pago.
    huecos_entre_pagos = []

    # Recorremos las fechas de dos en dos para medir la distancia.
    #
    # "range(1, len(fechas))" genera los números 1, 2, 3... hasta el final.
    # Empezamos en 1 (no en 0) porque comparamos cada fecha con la ANTERIOR,
    # y la primera no tiene anterior.
    for i in range(1, len(fechas_de_pago)):

        # Convertimos el texto "2026-08-14" a un objeto fecha de verdad,
        # para poder restarlas.
        #
        # "date.fromisoformat(texto)" es una función de Python que hace
        # justo eso: lee un texto con formato AAAA-MM-DD y devuelve una fecha.
        from datetime import date as _date
        fecha_anterior = _date.fromisoformat(fechas_de_pago[i - 1])
        fecha_actual = _date.fromisoformat(fechas_de_pago[i])

        # Al restar dos fechas, Python devuelve un objeto "timedelta".
        # Su campo ".days" nos da cuántos días de diferencia hay.
        huecos_entre_pagos.append((fecha_actual - fecha_anterior).days)

    # Si logramos medir al menos un hueco, sacamos el promedio.
    if huecos_entre_pagos:

        # El ritmo típico de cobro de esta persona.
        # "int(...)" convierte el resultado a número entero (sin decimales),
        # porque "en 11.7 días" se lee raro; mejor "en 11 días".
        ritmo_de_cobro = int(statistics.mean(huecos_entre_pagos))

        # Cuántos días han pasado desde el último pago que recibió.
        from datetime import date as _date2
        ultimo_pago = _date2.fromisoformat(fechas_de_pago[-1])   # [-1] = el último
        dias_desde_ultimo_pago = (_date2.today() - ultimo_pago).days

        # Lo que falta = el ritmo normal menos lo que ya esperó.
        #
        # "max(1, ...)" garantiza que nunca digamos "0 días" ni un número
        # negativo. Si ya se pasó de su ritmo normal, decimos "1 día"
        # (o sea: "ya te toca, debería caer pronto").
        dias_para_el_proximo_pago = max(1, ritmo_de_cobro - dias_desde_ultimo_pago)

        # Cuánto esperamos que sea ese pago: el promedio de los anteriores.
        monto_del_proximo_pago = int(statistics.mean(montos_de_los_pagos))
    else:
        # Sin historial no podemos adivinar nada. Ponemos valores neutros.
        dias_para_el_proximo_pago = 30
        monto_del_proximo_pago = 0


    # =========================================================================
    #  PASO 9 — EMPAQUETAR TODO Y DEVOLVERLO
    # =========================================================================

    # -------------------------------------------------------------------------
    # Regresamos un diccionario con los 9 indicadores + algunos datos de
    # apoyo. Este paquete es el que van a leer score.py, prediccion.py y
    # la página web.
    #
    # Las etiquetas están en español a propósito: así cuando el JSON llegue
    # a la página web, el código de JavaScript también se lee en español y
    # no hay que andar traduciendo.
    # -------------------------------------------------------------------------
    return {
        # --- Datos que solo copiamos tal cual, para tenerlos a la mano ---
        "nombre": cliente["nombre"],
        "profesion": cliente["profesion"],
        "dinero_en_el_banco": cliente["dinero_en_el_banco"],
        "veces_sin_dinero": cliente["veces_sin_dinero"],
        "gastos_fijos_lista": cliente["gastos_fijos"],
        "pagos_recibidos": cliente["pagos_recibidos"],

        # --- Los 9 indicadores calculados arriba ---
        "ingreso_al_mes": round(ingreso_al_mes),              # PASO 1
        "gastos_fijos_al_mes": gastos_fijos_al_mes,           # PASO 2
        "gasto_total_por_dia": round(gasto_total_por_dia),    # PASO 2
        "gasto_total_al_mes": round(gasto_total_al_mes),      # PASO 2
        "dias_de_colchon": dias_de_colchon,                   # PASO 3
        "volatilidad": volatilidad,                           # PASO 4
        "concentracion": concentracion,                       # PASO 5
        "cuantos_clientes_tiene": cuantos_clientes_tiene,     # PASO 5
        "cobertura": cobertura,                               # PASO 6
        "ahorro": ahorro,                                     # PASO 7
        "dias_para_el_proximo_pago": dias_para_el_proximo_pago,   # PASO 8
        "monto_del_proximo_pago": monto_del_proximo_pago,         # PASO 8
    }
