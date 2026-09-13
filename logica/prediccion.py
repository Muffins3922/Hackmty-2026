# =============================================================================
#  ARCHIVO 4 de 7:  logica/prediccion.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Adivina cuánto dinero va a tener la persona cada uno de los próximos
#  21 días, y arma la tabla que la página web usa para dibujar la gráfica.
#
#  ANALOGÍA: es como el pronóstico del clima, pero de tu cartera.
#  "Si todo sigue igual, el jueves 25 te quedas en números rojos."
#
#  ¿POR QUÉ 21 DÍAS Y NO 30?
#  Porque 21 días es el hueco típico entre pagos de un freelancer. Es lo
#  suficientemente largo para ver el problema venir, y lo suficientemente
#  corto para que la predicción todavía sea creíble. A 90 días cualquier
#  predicción es adivinanza pura.
#
#  ===========================================================================
#  IMPORTANTÍSIMO: AQUÍ NO HAY INTELIGENCIA ARTIFICIAL
#  ===========================================================================
#  Todo esto es una resta repetida 21 veces. No hay red neuronal, no hay
#  modelo entrenado, no hay azar.
#
#  ¿POR QUÉ NO USAR IA AQUÍ?
#  Porque una IA puede dar un resultado distinto cada vez que le preguntas
#  lo mismo. Para dibujar una gráfica de dinero eso es inaceptable: si el
#  usuario recarga la página y la gráfica cambia sola, deja de creerle al
#  sistema (y con razón).
#
#  Esta función es DETERMINISTA: mismos datos de entrada → misma gráfica,
#  siempre, hoy y en un año. Eso se puede auditar y se puede defender
#  frente a un juez o un regulador.
# =============================================================================


# -----------------------------------------------------------------------------
# Traemos las herramientas de fecha de Python, igual que en datos/clientes.py
#   - date      → representa un día del calendario
#   - timedelta → permite sumar o restar días
# -----------------------------------------------------------------------------
from datetime import date, timedelta


# -----------------------------------------------------------------------------
# Cuántos días hacia el futuro vamos a predecir.
# Está aquí arriba como constante para que sea fácil cambiarlo a 30 o a 14
# sin tener que buscar el número regado por todo el código.
# -----------------------------------------------------------------------------
DIAS_A_PREDECIR = 21


# =============================================================================
#  FUNCIÓN PRINCIPAL
#
#  Recibe: el paquete de indicadores que devolvió calculos.py
#  Devuelve: una lista de 21 días, más un resumen de si hay peligro
# =============================================================================
def predecir_21_dias(analisis):

    # =========================================================================
    #  PREPARATIVOS ANTES DE EMPEZAR A CONTAR DÍAS
    # =========================================================================

    # -------------------------------------------------------------------------
    # El saldo con el que arrancamos: el dinero que tiene HOY en el banco.
    #
    # Esta variable "saldo" es la que vamos a ir modificando día con día.
    # Es como el marcador de un partido: empieza en un número y va cambiando
    # conforme pasan las jugadas.
    #
    # Viene de datos/clientes.py → campo "dinero_en_el_banco"
    # -------------------------------------------------------------------------
    saldo = analisis["dinero_en_el_banco"]

    # -------------------------------------------------------------------------
    # Cuánto se le va CADA DÍA por vivir (comida, gasolina, transporte...).
    #
    # OJO: aquí usamos SOLO el gasto variable, NO el total.
    #
    # ¿POR QUÉ?
    # Porque los gastos fijos (la renta, la luz) no se pagan poquito a poquito
    # todos los días: se pagan de golpe el día que toca. Si los repartiéramos
    # entre 30, la gráfica saldría como una rampa suave y perderíamos el
    # momento exacto del golpe, que es justo lo que queremos mostrar.
    #
    # Más abajo, en el ciclo, los gastos fijos se restan COMPLETOS el día que
    # les toca. Así la gráfica muestra escalones, que es lo que de verdad
    # le pasa a tu cuenta.
    #
    # analisis["gasto_total_por_dia"] incluye ambos, así que le restamos la
    # parte fija para quedarnos solo con la variable.
    # -------------------------------------------------------------------------
    gasto_fijo_prorrateado = analisis["gastos_fijos_al_mes"] / 30
    gasto_variable_del_dia = analisis["gasto_total_por_dia"] - gasto_fijo_prorrateado

    # -------------------------------------------------------------------------
    # La fecha de hoy, para poder ponerle nombre a cada día de la gráfica.
    # -------------------------------------------------------------------------
    hoy = date.today()

    # -------------------------------------------------------------------------
    # La lista donde vamos a ir guardando el resultado de cada día.
    # Empieza vacía y al final va a tener 21 elementos, uno por día.
    # Esta lista es literalmente lo que la página web convierte en gráfica.
    # -------------------------------------------------------------------------
    dias = []

    # -------------------------------------------------------------------------
    # Banderas de aviso. "Bandera" es como se le dice en programación a una
    # variable que solo guarda sí/no (True/False) para recordar si algo pasó.
    #
    #   - se_queda_sin_dinero  → ¿en algún momento el saldo llega a negativo?
    #   - dia_del_problema     → ¿qué día exactamente? (None = todavía ninguno)
    #
    # "None" es la forma de Python de decir "aquí no hay nada todavía".
    # -------------------------------------------------------------------------
    se_queda_sin_dinero = False
    dia_del_problema = None

    # -------------------------------------------------------------------------
    # Guardamos el saldo más bajo al que llega durante los 21 días.
    # Arranca con el saldo de hoy y lo vamos bajando si encontramos algo menor.
    # Sirve para decirle al usuario "tu peor momento va a ser de $X".
    # -------------------------------------------------------------------------
    saldo_mas_bajo = saldo


    # =========================================================================
    #  EL CICLO: REPETIR LO MISMO 21 VECES, UNA POR CADA DÍA
    # =========================================================================

    # -------------------------------------------------------------------------
    # "for numero_de_dia in range(1, 22)" genera los números 1, 2, 3... 21.
    #
    # ¿Por qué range(1, 22) y no range(1, 21)?
    # Porque range() en Python NO incluye el último número. range(1, 22) da
    # del 1 al 21. Es una de las cosas que más confunde al empezar.
    #
    # Empezamos en 1 (no en 0) porque para una persona "el día 1" es mañana,
    # no hoy.
    # -------------------------------------------------------------------------
    for numero_de_dia in range(1, DIAS_A_PREDECIR + 1):

        # ---------------------------------------------------------------------
        # La fecha real de este día, para mostrarla en el eje de la gráfica.
        # ---------------------------------------------------------------------
        fecha_de_este_dia = hoy + timedelta(days=numero_de_dia)

        # ---------------------------------------------------------------------
        # Contadores de lo que pasa HOY. Arrancan en cero cada vuelta del
        # ciclo, porque cada día es independiente.
        #
        #   - entra_hoy → dinero que ENTRA (pagos de clientes)
        #   - sale_hoy  → dinero que SALE  (gastos fijos + gasto de vivir)
        # ---------------------------------------------------------------------
        entra_hoy = 0
        sale_hoy = 0

        # Lista de textos explicando qué pasó hoy, para el globito que aparece
        # cuando pasas el mouse sobre la gráfica. Ejemplo: ["Renta: -$6,800"]
        que_paso_hoy = []


        # =====================================================================
        #  REGLA 1 — ¿ENTRA DINERO HOY?
        # =====================================================================

        # ---------------------------------------------------------------------
        # Comparamos el día que estamos simulando contra el día en que
        # esperamos el próximo pago (calculado en el PASO 8 de calculos.py).
        #
        # Si coinciden, sumamos el pago esperado.
        #
        # Variables que usa:
        #   - analisis["dias_para_el_proximo_pago"]  ← de calculos.py PASO 8
        #   - analisis["monto_del_proximo_pago"]     ← de calculos.py PASO 8
        # ---------------------------------------------------------------------
        if numero_de_dia == analisis["dias_para_el_proximo_pago"]:

            # Guardamos cuánto entra.
            entra_hoy = analisis["monto_del_proximo_pago"]

            # Y lo anotamos para el globito de la gráfica.
            # La "f" antes de las comillas permite meter variables dentro del
            # texto usando llaves { }. Se llama "f-string".
            # El ":,"  dentro de las llaves pone comas separadoras de miles:
            # 14500 se muestra como 14,500.
            que_paso_hoy.append(f"Te pagan aprox. ${entra_hoy:,}")

        # ---------------------------------------------------------------------
        # SEGUNDO PAGO: si el freelancer cobra cada ~11 días, en 21 días
        # debería cobrar DOS veces, no una. Esta línea revisa eso.
        #
        # El segundo pago cae en: día_del_primer_pago + su ritmo de cobro.
        # Como el ritmo de cobro es justamente "dias_para_el_proximo_pago"
        # ajustado, usamos el doble como aproximación simple.
        # ---------------------------------------------------------------------
        segundo_pago_cae_en = analisis["dias_para_el_proximo_pago"] * 2
        if numero_de_dia == segundo_pago_cae_en and segundo_pago_cae_en <= DIAS_A_PREDECIR:
            entra_hoy = analisis["monto_del_proximo_pago"]
            que_paso_hoy.append(f"Segundo pago estimado ${entra_hoy:,}")


        # =====================================================================
        #  REGLA 2 — ¿HAY QUE PAGAR ALGÚN GASTO FIJO HOY?
        # =====================================================================

        # ---------------------------------------------------------------------
        # Recorremos la lista de gastos fijos (renta, luz, internet...) y
        # revisamos si alguno cae justo en este día.
        #
        # Cada gasto tiene un campo "se_paga_en" que dice en cuántos días
        # toca pagarlo (viene de datos/clientes.py).
        # ---------------------------------------------------------------------
        for gasto in analisis["gastos_fijos_lista"]:

            # ¿Este gasto se paga justo hoy?
            if gasto["se_paga_en"] == numero_de_dia:

                # Le sumamos su monto a lo que sale hoy.
                # "+=" significa "súmale esto a lo que ya tenías".
                sale_hoy += gasto["monto"]

                # Y lo anotamos para el globito.
                que_paso_hoy.append(f"{gasto['concepto']}: -${gasto['monto']:,}")


        # =====================================================================
        #  REGLA 3 — EL GASTO DE VIVIR (esto pasa TODOS los días)
        # =====================================================================

        # ---------------------------------------------------------------------
        # Comida, transporte, el café, la farmacia. No lo planeas pero pasa.
        # Se resta todos los días sin excepción.
        # ---------------------------------------------------------------------
        sale_hoy += gasto_variable_del_dia


        # =====================================================================
        #  REGLA 4 — ACTUALIZAR EL SALDO
        # =====================================================================

        # ---------------------------------------------------------------------
        # LA ECUACIÓN CENTRAL DE TODA LA PREDICCIÓN:
        #
        #      saldo_nuevo = saldo_anterior + lo_que_entra - lo_que_sale
        #
        # Es exactamente lo que haces mentalmente cuando revisas tu cuenta.
        # Nada más. Repetida 21 veces.
        #
        # Como "saldo" se guarda fuera del ciclo, el valor que queda al final
        # de esta vuelta es el que arranca la siguiente. Así se va encadenando
        # día tras día.
        # ---------------------------------------------------------------------
        saldo = saldo + entra_hoy - sale_hoy


        # =====================================================================
        #  REGLA 5 — ¿HAY PELIGRO?
        # =====================================================================

        # ---------------------------------------------------------------------
        # Clasificamos cada día en uno de tres niveles, para pintarlo de
        # color en la gráfica:
        #
        #   "peligro"  (rojo)     → el saldo se fue a negativo. Ya tronó.
        #   "cuidado"  (amarillo) → le queda menos de lo que gasta en 5 días.
        #                            Todavía no truena pero va muy justo.
        #   "bien"     (azul)     → todo en orden.
        #
        # El umbral de "cuidado" son 5 días de gasto. Lo elegimos porque es
        # el tiempo mínimo razonable para reaccionar: cobrar algo, pedir un
        # adelanto, mover dinero del ahorro.
        # ---------------------------------------------------------------------
        umbral_de_cuidado = analisis["gasto_total_por_dia"] * 5

        if saldo < 0:
            nivel = "peligro"

            # Si es la PRIMERA vez que pasa, lo anotamos como el día del
            # problema. El "if not se_queda_sin_dinero" garantiza que solo
            # guardemos el primero, no el último.
            if not se_queda_sin_dinero:
                se_queda_sin_dinero = True
                dia_del_problema = numero_de_dia

        elif saldo < umbral_de_cuidado:
            nivel = "cuidado"
        else:
            nivel = "bien"

        # ---------------------------------------------------------------------
        # Si este saldo es el más bajo que hemos visto, lo guardamos.
        # "min(a, b)" devuelve el menor de los dos números.
        # ---------------------------------------------------------------------
        saldo_mas_bajo = min(saldo_mas_bajo, saldo)


        # =====================================================================
        #  REGLA 6 — GUARDAR EL RESULTADO DE ESTE DÍA
        # =====================================================================

        # ---------------------------------------------------------------------
        # Metemos todo lo de hoy en un diccionario y lo agregamos a la lista.
        #
        # ".append(...)" es la función de las listas de Python que agrega un
        # elemento al final. Es como poner otra hoja encima del montón.
        #
        # Cada uno de estos campos se usa en la gráfica de la página web:
        #   "dia"        → etiqueta del eje horizontal ("Día 5")
        #   "fecha"      → la fecha real, para el globito
        #   "saldo"      → la ALTURA de la línea azul (lo más importante)
        #   "entra"      → altura de la barra verde
        #   "sale"       → altura de la barra roja
        #   "nivel"      → de qué color pintar el punto
        #   "que_paso"   → el texto del globito al pasar el mouse
        # ---------------------------------------------------------------------
        dias.append({
            "dia": numero_de_dia,
            "fecha": fecha_de_este_dia.isoformat(),
            "saldo": int(round(saldo)),
            "entra": int(round(entra_hoy)),
            "sale": int(round(sale_hoy)),
            "nivel": nivel,
            "que_paso": que_paso_hoy,
        })


    # =========================================================================
    #  DESPUÉS DEL CICLO: ARMAR EL RESUMEN EN ESPAÑOL
    # =========================================================================

    # -------------------------------------------------------------------------
    # Escribimos una frase que resuma los 21 días, para mostrarla grande en
    # la página. Es lo primero que va a leer el usuario, así que tiene que
    # decirle qué hacer, no solo qué pasa.
    # -------------------------------------------------------------------------
    if se_queda_sin_dinero:
        # -------------------------------------------------------------------------
        # Detalle de redacción: "en 1 días" suena mal. Esta línea elige entre
        # "día" y "días" según el número, para que el texto se lea natural.
        #
        # Se lee: si el día es 1, usa "día"; si no, usa "días".
        # A esta forma corta de escribir un if se le llama "operador ternario".
        # -------------------------------------------------------------------------
        palabra_dia = "día" if dia_del_problema == 1 else "días"

        # "f-string" otra vez: mete el número del día dentro del texto.
        resumen = (
            f"En {dia_del_problema} {palabra_dia} te quedas sin dinero. "
            f"Necesitas cobrar algo antes de esa fecha o recortar gastos."
        )
        hay_alerta = True

    elif saldo_mas_bajo < analisis["gasto_total_por_dia"] * 5:
        resumen = (
            f"Vas a pasar muy justo: tu punto más bajo será de "
            f"${saldo_mas_bajo:,.0f}. No es momento de gastos grandes."
        )
        hay_alerta = True

    else:
        resumen = (
            f"Vas bien. En 21 días deberías terminar con "
            f"${dias[-1]['saldo']:,} en la cuenta."
        )
        hay_alerta = False

    # -------------------------------------------------------------------------
    # Devolvemos todo empaquetado.
    #
    # "dias[-1]" significa "el último elemento de la lista". En Python los
    # índices negativos cuentan desde el final: [-1] es el último, [-2] el
    # penúltimo. Aquí lo usamos para sacar el saldo del día 21.
    # -------------------------------------------------------------------------
    return {
        "dias": dias,
        "resumen": resumen,
        "hay_alerta": hay_alerta,
        "se_queda_sin_dinero": se_queda_sin_dinero,
        "dia_del_problema": dia_del_problema,
        "saldo_mas_bajo": int(round(saldo_mas_bajo)),
        "saldo_final": dias[-1]["saldo"],
        "saldo_inicial": analisis["dinero_en_el_banco"],
    }


# =============================================================================
#  FUNCIÓN EXTRA: ¿QUÉ PASARÍA SI COMPRO ALGO?
#
#  Esta es la que le da vida al botón "¿Qué pasa si compro esto?" de la
#  página web. Es la parte más útil para el usuario final.
#
#  CÓMO FUNCIONA: le restamos la compra al saldo inicial y volvemos a correr
#  la MISMA predicción de arriba. Luego comparamos los dos resultados.
#
#  ¿POR QUÉ REUSAR LA MISMA FUNCIÓN Y NO ESCRIBIR OTRA?
#  Porque si escribiéramos la lógica dos veces, tarde o temprano una de las
#  dos se quedaría desactualizada y darían resultados distintos. Reusar
#  garantiza que el "antes" y el "después" se calculen EXACTAMENTE igual.
#  Esa es la regla de oro para que un sistema sea consistente.
# =============================================================================
def simular_compra(analisis, monto_de_la_compra):

    # -------------------------------------------------------------------------
    # Primero calculamos cómo se ve el futuro SIN la compra.
    # -------------------------------------------------------------------------
    antes = predecir_21_dias(analisis)

    # -------------------------------------------------------------------------
    # Hacemos una COPIA del análisis para no dañar el original.
    #
    # ¿Por qué una copia?
    # Porque en Python, si dos variables apuntan al mismo diccionario y
    # modificas una, la otra también cambia (están unidas). Eso causaría que
    # el "antes" se corrompiera al calcular el "después".
    #
    # "dict(analisis)" crea un diccionario nuevo con los mismos datos, pero
    # independiente. Es como fotocopiar un documento en vez de prestarlo.
    # -------------------------------------------------------------------------
    analisis_con_compra = dict(analisis)

    # -------------------------------------------------------------------------
    # Le quitamos el dinero de la compra al saldo inicial de la copia.
    # -------------------------------------------------------------------------
    analisis_con_compra["dinero_en_el_banco"] = analisis["dinero_en_el_banco"] - monto_de_la_compra

    # -------------------------------------------------------------------------
    # Y corremos la misma predicción con el saldo ya reducido.
    # -------------------------------------------------------------------------
    despues = predecir_21_dias(analisis_con_compra)

    # =========================================================================
    #  DECIDIR EL SEMÁFORO: ¿le conviene o no?
    # =========================================================================

    # -------------------------------------------------------------------------
    # CASO ROJO: antes NO se quedaba sin dinero, y con la compra SÍ.
    # Esta compra es la que lo tumba. Hay que ser directo.
    # -------------------------------------------------------------------------
    if despues["se_queda_sin_dinero"] and not antes["se_queda_sin_dinero"]:
        semaforo = "rojo"

        # Mismo truco del singular/plural que arriba, para que no diga "1 días".
        palabra = "día" if despues["dia_del_problema"] == 1 else "días"

        mensaje = (
            f"Si compras esto, te quedas sin dinero en "
            f"{despues['dia_del_problema']} {palabra}. Antes de comprarlo, ibas bien."
        )

    # -------------------------------------------------------------------------
    # CASO ROJO 2: ya iba a quedarse sin dinero, y la compra lo adelanta.
    # -------------------------------------------------------------------------
    elif despues["se_queda_sin_dinero"]:
        semaforo = "rojo"
        mensaje = (
            f"Ya venías justo. Con esta compra te quedas sin dinero en "
            f"{despues['dia_del_problema']} días en vez de {antes['dia_del_problema']}."
        )

    # -------------------------------------------------------------------------
    # CASO AMARILLO: no truena, pero se queda demasiado al límite.
    # -------------------------------------------------------------------------
    elif despues["saldo_mas_bajo"] < analisis["gasto_total_por_dia"] * 5:
        semaforo = "amarillo"
        mensaje = (
            f"Puedes comprarlo, pero vas a quedar muy justo: tu punto más bajo "
            f"sería de ${despues['saldo_mas_bajo']:,}. Piénsalo dos veces."
        )

    # -------------------------------------------------------------------------
    # CASO VERDE: sin problema.
    # -------------------------------------------------------------------------
    else:
        semaforo = "verde"
        mensaje = (
            f"Sí te alcanza sin problema. Aun comprándolo, terminas los 21 días "
            f"con ${despues['saldo_final']:,}."
        )

    # -------------------------------------------------------------------------
    # Devolvemos las DOS proyecciones (para dibujar ambas líneas en la
    # gráfica y que el usuario vea la diferencia con sus propios ojos)
    # más el veredicto.
    # -------------------------------------------------------------------------
    return {
        "semaforo": semaforo,
        "mensaje": mensaje,
        "monto_de_la_compra": monto_de_la_compra,
        "antes": antes,
        "despues": despues,

        # Cuántos días de colchón le costó esta compra. Es la forma más
        # intuitiva de explicar el precio real de algo:
        # "este celular te cuesta 8 días de tranquilidad".
        "dias_de_colchon_que_cuesta": round(
            monto_de_la_compra / analisis["gasto_total_por_dia"], 1
        ),
    }
