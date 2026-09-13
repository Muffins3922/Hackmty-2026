# =============================================================================
#  ARCHIVO 3 de 7:  logica/score.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Convierte los 9 indicadores del archivo anterior en UN SOLO NÚMERO
#  del 300 al 850: el puntaje de crédito.
#
#  ¿POR QUÉ 300 A 850?
#  Porque es la escala que ya usan los bancos (FICO, Buró de Crédito).
#  Si usáramos 0 a 100, un juez o un banquero tendría que traducir
#  mentalmente. Usando su escala, entienden al instante.
#
# =============================================================================
#  LA IDEA MATEMÁTICA DE TODO ESTE ARCHIVO, EXPLICADA CON UN EJEMPLO
# =============================================================================
#
#  Usamos una SUMA PONDERADA. En estadística se le llama REGRESIÓN LINEAL,
#  y es la fórmula más común del mundo en modelos financieros.
#
#  Su forma es siempre esta:
#
#       resultado = (nota1 × peso1) + (nota2 × peso2) + ... + base
#
#  ---------------------------------------------------------------------------
#  EJEMPLO 1: CALIFICAR A UN ESTUDIANTE (para entender la idea)
#
#       calificación = (examen × 0.50) + (tareas × 0.30) + (asistencia × 0.20)
#
#       - "examen", "tareas", "asistencia" son las NOTAS (qué tan bien salió)
#       - 0.50, 0.30, 0.20 son los PESOS (qué tan importante es cada cosa)
#       - los pesos suman 1.00, o sea 100%
#
#  ---------------------------------------------------------------------------
#  EJEMPLO 2: CALCULAR EL SUELDO DE UN EMPLEADO (el ejemplo del sesgo)
#
#       sueldo = (años_trabajados × 2000) + 15000
#                 └──── variable ────┘  └peso┘  └base┘
#
#       - "años_trabajados" es la VARIABLE (cambia según la persona)
#       - 2000 es el PESO: cuánto sube el sueldo por cada año trabajado
#       - 15000 es la BASE (en estadística le dicen SESGO, en inglés "bias"):
#         el sueldo mínimo que recibe TODO el mundo nada más por entrar,
#         aunque lleve cero años. Es el punto de arranque.
#
#  ---------------------------------------------------------------------------
#  EJEMPLO 3: NUESTRO CASO REAL (lo que hace este archivo)
#
#       score = (colchón×0.25 + estabilidad×0.20 + ... ) × 550 + 300
#               └──────────── suma ponderada ─────────┘   └esc┘ └base┘
#
#       - Cada "nota" va de 0.0 (pésimo) a 1.0 (perfecto)
#       - Los pesos suman 1.00, así que la suma también queda entre 0.0 y 1.0
#       - × 550 estira ese 0-1 hasta el tamaño de la escala bancaria
#         (porque de 300 a 850 hay exactamente 550 puntos de distancia)
#       - + 300 es la BASE / SESGO: los puntos que recibe cualquiera solo
#         por existir, porque el mínimo de la escala bancaria es 300, no 0.
#
#  La fórmula final está en la LÍNEA marcada como "AQUÍ ESTÁ LA FÓRMULA"
#  más abajo en este mismo archivo.
# =============================================================================


# =============================================================================
#  LOS PESOS: QUÉ TAN IMPORTANTE ES CADA COSA
#
#  Están todos juntos aquí arriba a propósito, para que cualquiera pueda
#  verlos y cambiarlos sin bucear en el código.
#
#  ESTOS NÚMEROS SON UNA DECISIÓN DE NEGOCIO, NO UNA VERDAD CIENTÍFICA.
#  Los elegimos nosotros según qué tan peligroso es cada problema para un
#  freelancer. Un banco real los ajustaría con datos históricos de miles
#  de clientes. Dilo así en la presentación: es honesto y suma puntos.
#
#  REGLA QUE NO SE PUEDE ROMPER: los 6 números deben sumar exactamente 1.00
#  (o sea 100%). Si no suman 1, el score se sale de la escala 300-850.
#  Hay una revisión automática al final del archivo que lo verifica.
# =============================================================================
PESOS = {

    # 25% — Días de colchón.
    # Es el más importante porque si te quedas sin dinero, ya no importa
    # nada más: no puedes pagar aunque quieras.
    "colchon": 0.25,

    # 20% — Estabilidad del ingreso.
    # Un banco le presta con gusto a quien puede PREDECIR. Alguien que cobra
    # parejo es predecible aunque gane poco.
    "estabilidad": 0.20,

    # 20% — Cobertura de obligaciones (DSCR).
    # Mide si le sobra dinero después de pagar lo obligatorio. Si apenas
    # empata, no hay de dónde sacar para pagar un préstamo nuevo.
    "cobertura": 0.20,

    # 15% — Diversidad de clientes.
    # Protege contra el peor escenario: que el cliente principal se vaya.
    "diversidad": 0.15,

    # 10% — Tasa de ahorro.
    # Habla del hábito de la persona, no solo de su situación actual.
    "ahorro": 0.10,

    # 10% — Historial de sobregiros.
    # Es el único indicador de comportamiento PASADO. Quien ya se quedó sin
    # dinero varias veces, es probable que vuelva a hacerlo.
    "sin_sobregiros": 0.10,
}


# =============================================================================
#  LA BASE (el "sesgo" o "bias") Y LA ESCALA
# =============================================================================

# -----------------------------------------------------------------------------
# PUNTOS_BASE = el piso de la escala. Nadie puede sacar menos de 300.
# Este es el "sesgo" o "bias" del que habla la estadística: el valor que
# recibe todo el mundo antes de que empiece a contar su desempeño.
# -----------------------------------------------------------------------------
PUNTOS_BASE = 300

# -----------------------------------------------------------------------------
# RANGO_DE_PUNTOS = cuántos puntos hay entre el piso y el techo.
#      850 (máximo) - 300 (mínimo) = 550 puntos de recorrido
# Sirve para estirar nuestro resultado de 0.0-1.0 hasta la escala bancaria.
# -----------------------------------------------------------------------------
RANGO_DE_PUNTOS = 550


# =============================================================================
#  FUNCIÓN AYUDANTE: convertir cualquier número a una nota de 0.0 a 1.0
# =============================================================================
# -----------------------------------------------------------------------------
# ¿POR QUÉ NECESITAMOS ESTO?
# Porque los indicadores vienen en unidades totalmente distintas:
#    - días de colchón viene en DÍAS       (ej: 24)
#    - la cobertura viene en VECES         (ej: 1.8)
#    - la volatilidad viene en PORCENTAJE  (ej: 0.45)
#
# No puedes sumar días con veces con porcentajes, igual que no puedes sumar
# manzanas con litros. Primero hay que pasarlos todos a la misma unidad.
#
# Esa unidad común va a ser "una nota del 0 al 1", donde:
#      0.0 = lo peor posible
#      1.0 = lo mejor posible
#
# En ciencia de datos a este paso se le llama NORMALIZAR. Es el paso que
# más se olvida y el que más errores causa en los modelos.
#
# CÓMO FUNCIONA ESTA FUNCIÓN:
# Le das un valor, un mínimo y un máximo, y te dice en qué parte del camino
# está, como una regla de tres:
#
#      nota = (valor - minimo) / (maximo - minimo)
#
# EJEMPLO: valor=15 días, minimo=0, maximo=30
#      (15 - 0) / (30 - 0) = 0.5  →  "va a la mitad del camino"
#
# Los dos "if" de abajo son topes de seguridad: si alguien tiene 200 días de
# colchón, no le damos nota 6.6, le damos 1.0 (ya es perfecto, no hay más).
# -----------------------------------------------------------------------------
def poner_nota(valor, minimo, maximo):

    # Si está por debajo del mínimo, la nota es 0 (lo peor).
    if valor <= minimo:
        return 0.0

    # Si está por encima del máximo, la nota es 1 (lo mejor).
    if valor >= maximo:
        return 1.0

    # Si está en medio, la regla de tres.
    return (valor - minimo) / (maximo - minimo)


# =============================================================================
#  FUNCIÓN PRINCIPAL: CALCULAR EL SCORE
#
#  Recibe: el paquete de indicadores que devolvió calculos.py
#  Devuelve: el score, la categoría, cuánto se le puede prestar, y el
#            desglose de cómo salió cada nota (para mostrarlo en pantalla)
# =============================================================================
def calcular_score(analisis):

    # =========================================================================
    #  PARTE 1 — CONVERTIR CADA INDICADOR EN UNA NOTA DE 0 A 1
    # =========================================================================

    # -------------------------------------------------------------------------
    # NOTA 1: DÍAS DE COLCHÓN
    #
    #   Escala:  0 días = nota 0.0   |   60 días o más = nota 1.0
    #
    # ¿Por qué 60 días como techo?
    # Porque dos meses de colchón es el estándar que usan los asesores
    # financieros para considerar que alguien está "tranquilo". Más de eso
    # ya no te hace más seguro para un préstamo a 12 meses.
    #
    # Variable que usa: analisis["dias_de_colchon"], calculada en el PASO 3
    # de logica/calculos.py
    # -------------------------------------------------------------------------
    nota_colchon = poner_nota(analisis["dias_de_colchon"], 0, 60)

    # -------------------------------------------------------------------------
    # NOTA 2: ESTABILIDAD DEL INGRESO
    #
    # ¡OJO CON ESTA! Aquí hay una vuelta de tuerca importante.
    #
    # La volatilidad funciona AL REVÉS que las demás: volatilidad ALTA es
    # MALA. Pero nuestras notas siempre deben ser "más alto = mejor".
    #
    # Solución: le damos la vuelta restándola de 1.
    #
    #      estabilidad = 1 - volatilidad
    #
    # EJEMPLO: si la volatilidad es 0.3 (poco brincona),
    #          la estabilidad es 1 - 0.3 = 0.7 (buena nota). Correcto.
    #
    # "max(0, ...)" evita que quede negativa si la volatilidad pasara de 1.0
    # (que sí puede pasar con ingresos muy caóticos).
    #
    # Variable que usa: analisis["volatilidad"], calculada en el PASO 4
    # de logica/calculos.py
    # -------------------------------------------------------------------------
    estabilidad = max(0, 1 - analisis["volatilidad"])
    nota_estabilidad = poner_nota(estabilidad, 0, 1)

    # -------------------------------------------------------------------------
    # NOTA 3: COBERTURA DE OBLIGACIONES (DSCR)
    #
    #   Escala:  1.0 o menos = nota 0.0   |   2.5 o más = nota 1.0
    #
    # ¿Por qué el piso es 1.0 y no 0?
    # Porque cobertura 1.0 significa "gano exactamente lo que debo pagar,
    # no me sobra nada". Ese ya es el caso malo. Cualquier cosa por debajo
    # (gastar más de lo que ganas) es igual de mala, así que todas esas
    # situaciones reciben 0.
    #
    # ¿Por qué el techo es 2.5?
    # Ganar 2.5 veces tus obligaciones ya es muy holgado. Ganar 10 veces no
    # te hace 4 veces más confiable, así que ahí topamos.
    #
    # Variable que usa: analisis["cobertura"], calculada en el PASO 6
    # de logica/calculos.py
    # -------------------------------------------------------------------------
    nota_cobertura = poner_nota(analisis["cobertura"], 1.0, 2.5)

    # -------------------------------------------------------------------------
    # NOTA 4: DIVERSIDAD DE CLIENTES
    #
    # Otra que va al revés: concentración ALTA es MALA (depender de uno solo).
    # Le damos la vuelta igual que con la volatilidad.
    #
    #      diversidad = 1 - concentracion
    #
    # EJEMPLO: si el cliente más grande representa el 70% (concentración 0.7),
    #          la diversidad es 1 - 0.7 = 0.3 (nota baja). Correcto, es malo.
    #
    # Variable que usa: analisis["concentracion"], calculada en el PASO 5
    # de logica/calculos.py
    # -------------------------------------------------------------------------
    diversidad = 1 - analisis["concentracion"]
    nota_diversidad = poner_nota(diversidad, 0, 1)

    # -------------------------------------------------------------------------
    # NOTA 5: TASA DE AHORRO
    #
    #   Escala:  0% o menos = nota 0.0   |   30% o más = nota 1.0
    #
    # El piso es 0 porque ahorrar negativo (gastar más de lo que ganas) es
    # todo igual de malo. El techo es 30% porque ahorrar casi un tercio de
    # tu ingreso ya es excelente para cualquier persona.
    #
    # Variable que usa: analisis["ahorro"], calculada en el PASO 7
    # de logica/calculos.py
    # -------------------------------------------------------------------------
    nota_ahorro = poner_nota(analisis["ahorro"], 0, 0.30)

    # -------------------------------------------------------------------------
    # NOTA 6: NO HABERSE QUEDADO SIN DINERO
    #
    # Esta no usa poner_nota porque no es una escala continua, son eventos
    # contables (0 veces, 1 vez, 2 veces...). Aplicamos un castigo directo:
    #
    #      nota = 1.0 - (veces_sin_dinero × 0.25)
    #
    # Cada sobregiro le quita 25% de esta nota:
    #      0 veces → 1.00  (perfecto)
    #      1 vez   → 0.75
    #      2 veces → 0.50
    #      3 veces → 0.25
    #      4+ veces→ 0.00  (el max(0,...) evita que se vaya a negativo)
    #
    # Variable que usa: analisis["veces_sin_dinero"], que viene directo de
    # datos/clientes.py sin transformación.
    # -------------------------------------------------------------------------
    nota_sin_sobregiros = max(0, 1.0 - (analisis["veces_sin_dinero"] * 0.25))


    # =========================================================================
    #  PARTE 2 — LA FÓRMULA PRINCIPAL  ⬅⬅⬅  AQUÍ ESTÁ LA FÓRMULA
    # =========================================================================

    # -------------------------------------------------------------------------
    # Multiplicamos cada nota por su peso y sumamos todo.
    #
    # El resultado "suma_ponderada" queda entre 0.0 y 1.0, porque cada nota
    # está entre 0 y 1 y los pesos suman 1.
    #
    # Es exactamente la fórmula del examen del estudiante, pero con 6 materias
    # en vez de 3:
    #
    #   suma = (nota1×peso1)+(nota2×peso2)+(nota3×peso3)+
    #          (nota4×peso4)+(nota5×peso5)+(nota6×peso6)
    # -------------------------------------------------------------------------
    suma_ponderada = (
        nota_colchon         * PESOS["colchon"]          # 25% del total
        + nota_estabilidad   * PESOS["estabilidad"]      # 20% del total
        + nota_cobertura     * PESOS["cobertura"]        # 20% del total
        + nota_diversidad    * PESOS["diversidad"]       # 15% del total
        + nota_ahorro        * PESOS["ahorro"]           # 10% del total
        + nota_sin_sobregiros * PESOS["sin_sobregiros"]  # 10% del total
    )

    # -------------------------------------------------------------------------
    # Estiramos el resultado (que va de 0 a 1) a la escala bancaria 300-850.
    #
    #      score = suma_ponderada × 550 + 300
    #              └── variable ──┘  └esc┘ └base o "sesgo"┘
    #
    # COMPROBACIÓN DE QUE LA FÓRMULA ESTÁ BIEN:
    #      Si alguien saca 0.0 en todo:  0.0 × 550 + 300 = 300  ✓ (el mínimo)
    #      Si alguien saca 1.0 en todo:  1.0 × 550 + 300 = 850  ✓ (el máximo)
    #
    # "int(round(...))" hace dos cosas:
    #   - round() redondea al entero más cercano (604.7 → 605)
    #   - int() se asegura de que el tipo de dato sea un entero, no un
    #     decimal, para que en la página web salga "605" y no "605.0"
    # -------------------------------------------------------------------------
    score = int(round(suma_ponderada * RANGO_DE_PUNTOS + PUNTOS_BASE))


    # =========================================================================
    #  PARTE 3 — TRADUCIR EL NÚMERO A UNA CATEGORÍA EN ESPAÑOL
    # =========================================================================

    # -------------------------------------------------------------------------
    # Un número solo no le dice nada a una persona normal. "605" ¿es bueno?
    # Por eso lo traducimos a palabras y a un color para la interfaz.
    #
    # Los cortes (750, 680, 620, 560) son los mismos que usa la industria
    # bancaria, para que un juez que conozca el tema los reconozca.
    #
    # ¿Qué es "elif"? Es la abreviatura de "else if", o sea "si no, entonces
    # revisa si...". Python va revisando de arriba hacia abajo y se queda en
    # el primero que se cumple.
    # -------------------------------------------------------------------------
    if score >= 750:
        categoria = "Excelente"
        color = "verde"
        explicacion_corta = "Perfil muy sólido. Riesgo muy bajo para prestar."
    elif score >= 680:
        categoria = "Muy bueno"
        color = "verde"
        explicacion_corta = "Buen perfil. Riesgo bajo."
    elif score >= 620:
        categoria = "Bueno"
        color = "amarillo"
        explicacion_corta = "Perfil aceptable. Riesgo moderado."
    elif score >= 560:
        categoria = "Regular"
        color = "amarillo"
        explicacion_corta = "Hay señales de alerta. Riesgo medio-alto."
    else:
        categoria = "En riesgo"
        color = "rojo"
        explicacion_corta = "Situación delicada. Riesgo alto."


    # =========================================================================
    #  PARTE 4 — ¿CUÁNTO DINERO SE LE PUEDE PRESTAR?
    # =========================================================================

    # -------------------------------------------------------------------------
    # LA IDEA: solo le prestamos una parte de lo que le SOBRA cada mes,
    # nunca una parte de lo que gana. Porque lo que gana ya está
    # comprometido con la renta, la luz, la comida.
    #
    # PASO A: cuánto le sobra al mes después de TODOS sus gastos.
    #
    #      dinero_que_le_sobra = ingreso_al_mes - gasto_total_al_mes
    #
    # "max(0, ...)" evita que sea negativo. Si gasta más de lo que gana,
    # le sobra 0, no "menos 3000".
    # -------------------------------------------------------------------------
    dinero_que_le_sobra = max(0, analisis["ingreso_al_mes"] - analisis["gasto_total_al_mes"])

    # -------------------------------------------------------------------------
    # PASO B: de ese sobrante, ¿qué porcentaje nos atrevemos a comprometer?
    #
    # No le pedimos TODO lo que le sobra, porque entonces cualquier
    # imprevisto (se enferma, se le descompone la compu) lo tumba.
    #
    # El porcentaje depende de qué tan confiable sea, o sea, de su score:
    #
    #   Score 750+ → 40% de su sobrante (le confiamos bastante)
    #   Score 680+ → 30%
    #   Score 620+ → 20%
    #   Score 560+ → 10% (apenas un colchoncito)
    #   Score <560 → 0%  (no le prestamos, por su propio bien)
    #
    # Estos porcentajes también son decisión de negocio, igual que los pesos.
    # -------------------------------------------------------------------------
    if score >= 750:
        porcentaje_que_comprometemos = 0.40
    elif score >= 680:
        porcentaje_que_comprometemos = 0.30
    elif score >= 620:
        porcentaje_que_comprometemos = 0.20
    elif score >= 560:
        porcentaje_que_comprometemos = 0.10
    else:
        porcentaje_que_comprometemos = 0.0

    # -------------------------------------------------------------------------
    # PASO C: el pago mensual máximo que puede aguantar.
    #
    #      pago_mensual_maximo = dinero_que_le_sobra × porcentaje
    # -------------------------------------------------------------------------
    pago_mensual_maximo = dinero_que_le_sobra * porcentaje_que_comprometemos

    # -------------------------------------------------------------------------
    # PASO D: la línea de crédito = ese pago mensual × 12 meses.
    #
    #      linea_recomendada = pago_mensual_maximo × 12
    #
    # Asumimos préstamos a 12 meses porque es el plazo más común para
    # créditos personales chicos.
    #
    # NOTA HONESTA PARA LA PRESENTACIÓN: aquí NO estamos cobrando intereses.
    # Un banco real le sumaría la tasa de interés. Lo dejamos sin intereses
    # a propósito para que la demo sea fácil de entender y de auditar.
    #
    # "int(round(... / 500)) * 500" redondea a múltiplos de 500 pesos,
    # porque un banco nunca te ofrece "$8,347 de línea", te ofrece "$8,500".
    # Se ve más profesional y realista.
    # -------------------------------------------------------------------------
    linea_recomendada = int(round((pago_mensual_maximo * 12) / 500)) * 500


    # =========================================================================
    #  PARTE 5 — DEVOLVER TODO, INCLUYENDO EL DESGLOSE
    # =========================================================================

    # -------------------------------------------------------------------------
    # Devolvemos el score PERO TAMBIÉN el detalle de cada nota.
    #
    # ¿POR QUÉ DEVOLVER EL DESGLOSE?
    # Porque un score sin explicación es una caja negra, y las cajas negras
    # en finanzas son ilegales en muchos países (el cliente tiene derecho a
    # saber por qué lo rechazaron). Con este desglose, la página web puede
    # dibujar una barra por cada nota y el usuario ve exactamente qué lo
    # está frenando.
    #
    # Cada detalle trae:
    #   "nombre"      → cómo se llama en español, para la etiqueta
    #   "nota"        → la nota de 0 a 100 (multiplicamos por 100 para que
    #                   se lea como porcentaje, es más intuitivo que 0.73)
    #   "peso"        → cuánto pesa, también en porcentaje
    #   "puntos"      → cuántos de los 550 puntos aportó realmente
    #   "que_significa" → una frase en español simple para el tooltip
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # Preparamos la frase del ahorro antes de armar la lista, porque cambia
    # según si le sobra o le falta dinero.
    #
    # Sin esto, cuando el ahorro es negativo la pantalla diría
    # "te sobran -41 pesos", que se lee mal. Mejor decirle "te faltan 41".
    #
    # "abs(...)" quita el signo negativo del número.
    # -------------------------------------------------------------------------
    centavos_de_ahorro = round(analisis["ahorro"] * 100)

    if centavos_de_ahorro >= 0:
        frase_del_ahorro = f"De cada 100 pesos que ganas, te sobran {centavos_de_ahorro}."
    else:
        frase_del_ahorro = (
            f"De cada 100 pesos que ganas, te faltan {abs(centavos_de_ahorro)}. "
            f"Estás gastando más de lo que entra."
        )

    detalle_de_notas = [
        {
            "nombre": "Colchón de días",
            "nota": round(nota_colchon * 100),
            "peso": round(PESOS["colchon"] * 100),
            "puntos": round(nota_colchon * PESOS["colchon"] * RANGO_DE_PUNTOS),
            "que_significa": f"Puedes vivir {analisis['dias_de_colchon']} días sin cobrar nada.",
        },
        {
            "nombre": "Estabilidad de ingresos",
            "nota": round(nota_estabilidad * 100),
            "peso": round(PESOS["estabilidad"] * 100),
            "puntos": round(nota_estabilidad * PESOS["estabilidad"] * RANGO_DE_PUNTOS),
            "que_significa": "Qué tan parecidos son tus pagos entre sí. Pagos parejos = más confianza.",
        },
        {
            "nombre": "Cobertura de gastos fijos",
            "nota": round(nota_cobertura * 100),
            "peso": round(PESOS["cobertura"] * 100),
            "puntos": round(nota_cobertura * PESOS["cobertura"] * RANGO_DE_PUNTOS),
            "que_significa": f"Tu ingreso alcanza {analisis['cobertura']} veces para pagar lo obligatorio.",
        },
        {
            "nombre": "Variedad de clientes",
            "nota": round(nota_diversidad * 100),
            "peso": round(PESOS["diversidad"] * 100),
            "puntos": round(nota_diversidad * PESOS["diversidad"] * RANGO_DE_PUNTOS),
            "que_significa": f"Tienes {analisis['cuantos_clientes_tiene']} clientes. Entre más, menos riesgo si uno se va.",
        },
        {
            "nombre": "Capacidad de ahorro",
            "nota": round(nota_ahorro * 100),
            "peso": round(PESOS["ahorro"] * 100),
            "puntos": round(nota_ahorro * PESOS["ahorro"] * RANGO_DE_PUNTOS),
            "que_significa": frase_del_ahorro,
        },
        {
            "nombre": "Historial sin sobregiros",
            "nota": round(nota_sin_sobregiros * 100),
            "peso": round(PESOS["sin_sobregiros"] * 100),
            "puntos": round(nota_sin_sobregiros * PESOS["sin_sobregiros"] * RANGO_DE_PUNTOS),
            "que_significa": f"Te has quedado sin dinero {analisis['veces_sin_dinero']} veces en 3 meses.",
        },
    ]

    # El paquete final que devolvemos.
    return {
        "score": score,
        "categoria": categoria,
        "color": color,
        "explicacion_corta": explicacion_corta,
        "linea_recomendada": linea_recomendada,
        "pago_mensual_maximo": int(round(pago_mensual_maximo)),
        "dinero_que_le_sobra": int(round(dinero_que_le_sobra)),
        "detalle_de_notas": detalle_de_notas,
        "puntos_base": PUNTOS_BASE,
    }


# =============================================================================
#  REVISIÓN AUTOMÁTICA DE SEGURIDAD
#
#  Esta línea se ejecuta sola cada vez que alguien importa este archivo.
#  Verifica que los 6 pesos sumen exactamente 1.00.
#
#  ¿Qué es "assert"?
#  Es una palabra de Python que significa "esto TIENE que ser verdad".
#  Si es verdad, no pasa nada y el programa sigue. Si es falso, el programa
#  se detiene de inmediato y muestra el mensaje que escribiste.
#
#  ¿Por qué usarlo aquí?
#  Porque si alguien (tú dentro de 3 semanas, o un compañero de equipo)
#  cambia un peso de 0.25 a 0.35 y se le olvida bajar otro, los scores
#  saldrían mal SIN AVISAR. Este assert hace que el error aparezca de
#  inmediato y no en la presentación frente a los jueces.
#
#  ¿Qué es "abs(...)"?
#  Devuelve el valor absoluto (el número sin signo). abs(-0.3) = 0.3
#
#  ¿Por qué no escribimos simplemente "suma == 1.0"?
#  Porque las computadoras guardan los decimales con un error minúsculo.
#  0.25 + 0.20 + 0.20 + 0.15 + 0.10 + 0.10 a veces da 0.9999999999999999
#  en vez de 1.0 exacto. Por eso pedimos que la diferencia contra 1.0 sea
#  menor a 0.001, o sea "prácticamente igual a 1".
# =============================================================================
assert abs(sum(PESOS.values()) - 1.0) < 0.001, "ERROR: los pesos del score deben sumar 1.00"
