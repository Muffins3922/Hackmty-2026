# =============================================================================
#  ARCHIVO 5 de 7:  ia/explicador.py
#
#  ¿QUÉ HACE ESTE ARCHIVO?
#  Le pide a una inteligencia artificial que escriba un consejo en español
#  simple, a partir de los números que YA calculamos nosotros.
#
#  ===========================================================================
#  LO MÁS IMPORTANTE DE TODO EL PROYECTO (di esto en la presentación)
#  ===========================================================================
#
#  LA IA NO CALCULA NADA. LA IA NO PREDICE NADA. LA IA NO DECIDE NADA.
#  La IA solamente REDACTA.
#
#  Piénsalo así:
#     - El contador (nuestro código Python) saca las cuentas.
#     - El traductor (la IA) toma esas cuentas y las explica bonito.
#
#  El traductor nunca cambia los números. Si el contador dice "te quedan
#  24 días", el traductor dice "te queda casi un mes, vas bien", pero jamás
#  dice "te quedan 30 días".
#
#  ¿POR QUÉ ESTA SEPARACIÓN ES TAN IMPORTANTE?
#
#  1) CONSISTENCIA. Una IA puede responder distinto cada vez que le
#     preguntas lo mismo. Si el score saliera de la IA, hoy te daría 604 y
#     mañana 618 con los mismos datos. Un banco no puede trabajar así.
#
#  2) AUDITORÍA. Si un cliente reclama "¿por qué me rechazaron?", podemos
#     mostrarle la fórmula exacta línea por línea. Con una IA no podrías:
#     no hay forma de abrirle la cabeza y ver por qué dijo lo que dijo.
#
#  3) LEY. En muchos países es ilegal negar un crédito con un modelo que no
#     puedes explicar. A eso se le llama "derecho a explicación".
#
#  4) LA IA PUEDE INVENTAR. A eso se le dice "alucinar": inventar datos con
#     mucha seguridad. Si le pides que calcule, se puede equivocar y sonar
#     convincente. Si solo le pides que redacte números que ya le diste,
#     el riesgo baja muchísimo.
#
#  ===========================================================================
#  ¿Y SI NO HAY INTERNET O NO HAY LLAVE DE LA IA?
#  ===========================================================================
#  No pasa nada: este archivo tiene un plan B escrito a mano que arma el
#  consejo con puros "if". El sistema NUNCA se cae por culpa de la IA.
#  Eso es crítico en un hackathon, donde el wifi siempre falla justo en la
#  demo.
# =============================================================================


# -----------------------------------------------------------------------------
# "os" es una caja de herramientas de Python para hablar con el sistema
# operativo. La usamos solo para leer las "variables de entorno", que son
# como notas pegadas afuera del programa donde guardamos contraseñas.
#
# ¿Por qué no escribir la contraseña directo en el código?
# Porque el código se sube a GitHub y cualquiera podría verla y usar tu
# cuenta. GitHub incluso bloquea el envío si detecta una llave.
# -----------------------------------------------------------------------------
import os


# -----------------------------------------------------------------------------
# Leemos la llave de la IA desde las variables de entorno.
#
# "os.environ.get("GROQ_API_KEY", "")" busca una nota llamada GROQ_API_KEY.
# Si no la encuentra, devuelve "" (texto vacío) en vez de tronar.
#
# Para ponerla, en la terminal se escribe:
#     Windows:  set GROQ_API_KEY=gsk_tu_llave_aqui
#     Mac/Linux: export GROQ_API_KEY=gsk_tu_llave_aqui
#
# La llave se saca gratis en console.groq.com
# -----------------------------------------------------------------------------
LLAVE_DE_LA_IA = os.environ.get("GROQ_API_KEY", "")


# -----------------------------------------------------------------------------
# Qué modelo de IA vamos a usar.
#
# "llama-3.3-70b-versatile" es un modelo gratuito que corre en los
# servidores de Groq. El "70b" significa 70 mil millones de parámetros
# (o sea, es un modelo grande y capaz).
#
# Usamos Groq y no otro porque: es gratis, y responde en ~1 segundo en vez
# de 4-5 segundos. En una demo en vivo eso se nota muchísimo.
# -----------------------------------------------------------------------------
MODELO_DE_IA = "llama-3.3-70b-versatile"


# =============================================================================
#  PLAN B: EL CONSEJO ESCRITO A MANO (sin IA)
#
#  Esta función se usa cuando no hay internet o no hay llave.
#  Son puros "if". No es tan bonito como lo que escribe la IA, pero SIEMPRE
#  funciona y siempre dice la verdad.
# =============================================================================
def consejo_sin_ia(analisis, resultado_score, prediccion):

    # -------------------------------------------------------------------------
    # Vamos a ir juntando frases en una lista y al final las pegamos.
    # -------------------------------------------------------------------------
    frases = []

    # -------------------------------------------------------------------------
    # Frase 1: el diagnóstico general, según la categoría del score.
    # -------------------------------------------------------------------------
    if resultado_score["score"] >= 680:
        frases.append(
            f"Tu situación se ve sólida. Con {analisis['dias_de_colchon']} días "
            f"de colchón y clientes que te pagan de forma pareja, un banco te "
            f"vería como alguien confiable."
        )
    elif resultado_score["score"] >= 600:
        frases.append(
            f"Vas bien pero sin margen de sobra. Tienes "
            f"{analisis['dias_de_colchon']} días de colchón, que está aceptable, "
            f"aunque un imprevisto grande te movería el piso."
        )
    else:
        frases.append(
            f"Tu situación necesita atención. Solo tienes "
            f"{analisis['dias_de_colchon']} días de colchón, y eso significa "
            f"que cualquier retraso de un cliente te pega directo."
        )

    # -------------------------------------------------------------------------
    # Frase 2: el problema más grande que encontramos.
    #
    # Buscamos cuál de las 6 notas salió más baja. Esa es la que más le está
    # costando puntos, y por lo tanto la que más le conviene arreglar.
    #
    # "min(lista, key=...)" devuelve el elemento más chico de una lista, pero
    # comparando según lo que le digas en "key". Aquí le decimos "compáralos
    # por su campo nota".
    #
    # "lambda d: d['nota']" es una función chiquita sin nombre. Se lee:
    # "dado un elemento d, dame su campo nota".
    # -------------------------------------------------------------------------
    nota_mas_baja = min(resultado_score["detalle_de_notas"], key=lambda d: d["nota"])

    frases.append(
        f"Lo que más te está bajando el puntaje es \"{nota_mas_baja['nombre']}\": "
        f"{nota_mas_baja['que_significa']}"
    )

    # -------------------------------------------------------------------------
    # Frase 3: la alerta de los próximos 21 días, si la hay.
    # -------------------------------------------------------------------------
    if prediccion["se_queda_sin_dinero"]:
        frases.append(
            f"Ojo con los próximos días: según tus gastos programados, en "
            f"{prediccion['dia_del_problema']} días te quedarías en ceros. "
            f"Lo más práctico ahorita sería adelantar el cobro de algún cliente."
        )
    else:
        frases.append(
            f"En los próximos 21 días no se te acaba el dinero. Tu punto más "
            f"bajo sería de ${prediccion['saldo_mas_bajo']:,}."
        )

    # -------------------------------------------------------------------------
    # Pegamos las frases separadas por un espacio.
    #
    # " ".join(lista) es una función de los textos de Python que une todos
    # los elementos de una lista poniendo el texto de enfrente entre cada uno.
    # -------------------------------------------------------------------------
    return " ".join(frases)


# =============================================================================
#  FUNCIÓN PRINCIPAL: PEDIRLE EL CONSEJO A LA IA
# =============================================================================
def explicar_con_ia(analisis, resultado_score, prediccion):

    # -------------------------------------------------------------------------
    # REVISIÓN 1: ¿tenemos llave? Si no, usamos el plan B y ya.
    #
    # "if not LLAVE_DE_LA_IA" se lee "si la llave está vacía".
    # -------------------------------------------------------------------------
    if not LLAVE_DE_LA_IA:
        return {
            "texto": consejo_sin_ia(analisis, resultado_score, prediccion),
            "vino_de_la_ia": False,
            "nota": "Sin llave de IA configurada. Usando explicación automática.",
        }

    # -------------------------------------------------------------------------
    # "try" significa "intenta hacer esto, y si truena no te mueras".
    # Todo lo que está adentro se ejecuta normal; si algo falla, Python salta
    # al bloque "except" de hasta abajo en vez de detener el programa.
    #
    # Lo usamos porque hablar por internet SIEMPRE puede fallar: se cae el
    # wifi, el servidor de la IA está saturado, la llave venció...
    # -------------------------------------------------------------------------
    try:

        # ---------------------------------------------------------------------
        # Traemos la librería de Groq. La importamos AQUÍ ADENTRO y no hasta
        # arriba del archivo a propósito: así, si alguien no la tiene
        # instalada, el programa completo sigue funcionando con el plan B en
        # vez de negarse a arrancar.
        #
        # Se instala con:  pip install groq
        # ---------------------------------------------------------------------
        from groq import Groq

        # ---------------------------------------------------------------------
        # Creamos el "cliente": el objeto que sabe hablar con los servidores
        # de Groq usando nuestra llave.
        # ---------------------------------------------------------------------
        cliente = Groq(api_key=LLAVE_DE_LA_IA)

        # =====================================================================
        #  ARMAR EL "PROMPT" (la instrucción que le damos a la IA)
        # =====================================================================

        # ---------------------------------------------------------------------
        # ¿QUÉ ES UN "PROMPT"?
        # Es el mensaje que le escribes a la IA. Literalmente es como
        # escribirle a un asistente por WhatsApp.
        #
        # LA REGLA DE ORO: entre más específico seas y más datos ya masticados
        # le des, menos se inventa. Por eso le pasamos TODOS los números ya
        # calculados y le prohibimos expresamente calcular.
        #
        # Fíjate en las tres cosas que hacemos para amarrarle las manos:
        #   1. Le damos los números exactos (no tiene que sacarlos él).
        #   2. Le decimos "NO inventes números que no estén en esta lista".
        #   3. Le ponemos un límite de palabras, para que no divague.
        #
        # Las tres comillas """ permiten escribir texto de varias líneas.
        # La "f" del inicio permite meter variables con llaves { }.
        # ---------------------------------------------------------------------
        instruccion = f"""Eres un asesor financiero que le habla a un trabajador independiente en México.

DATOS REALES DE ESTA PERSONA (ya calculados, NO los cambies):
- Nombre: {analisis['nombre']}
- Profesión: {analisis['profesion']}
- Dinero en el banco hoy: ${analisis['dinero_en_el_banco']:,}
- Gana al mes (promedio): ${analisis['ingreso_al_mes']:,}
- Gasta al mes: ${analisis['gasto_total_al_mes']:,}
- Días que aguanta sin cobrar: {analisis['dias_de_colchon']}
- Qué tan disparejos son sus pagos (0=parejo, 1=caótico): {analisis['volatilidad']}
- Cuántos clientes tiene: {analisis['cuantos_clientes_tiene']}
- Su ingreso cubre sus gastos fijos: {analisis['cobertura']} veces
- Veces que se quedó sin dinero en 3 meses: {analisis['veces_sin_dinero']}
- Su puntaje de crédito: {resultado_score['score']} de 850 ({resultado_score['categoria']})
- Predicción a 21 días: {prediccion['resumen']}

REGLAS QUE DEBES SEGUIR:
1. Escribe máximo 4 frases, en español de México, sencillo.
2. Habla de "tú", como un amigo que sabe de dinero. Nada de "usted".
3. NO uses palabras técnicas como volatilidad, DSCR, liquidez o score.
   Si necesitas decirlo, dilo con palabras normales.
4. NO inventes ningún número que no esté en la lista de arriba.
5. Empieza diciendo cómo está, y termina con UNA acción concreta que
   pueda hacer esta semana.
6. No uses viñetas ni listas, solo texto corrido."""

        # =====================================================================
        #  MANDAR LA PREGUNTA Y ESPERAR LA RESPUESTA
        # =====================================================================

        # ---------------------------------------------------------------------
        # Esta es la llamada por internet a los servidores de Groq.
        #
        # Los ajustes que le pasamos:
        #
        #   model       → cuál modelo usar (el que definimos hasta arriba)
        #
        #   messages    → la conversación. Es una lista porque puedes mandar
        #                 varios mensajes de ida y vuelta. Aquí mandamos uno
        #                 solo, de parte del "user" (nosotros).
        #
        #   max_tokens  → cuánto texto máximo puede responder. Un "token" es
        #                 más o menos media palabra. 250 tokens ≈ 180 palabras.
        #                 Ponemos un tope para que no escriba un ensayo y para
        #                 que responda rápido.
        #
        #   temperature → QUÉ TAN CREATIVA puede ser, de 0 a 1.
        #                 0.0 = siempre responde casi lo mismo, muy predecible
        #                 1.0 = muy creativa, cambia mucho entre intentos
        #                 Usamos 0.3 (bajo) a propósito: queremos que suene
        #                 natural pero que NO se ponga creativa con el dinero
        #                 de alguien. En finanzas, aburrido es bueno.
        # ---------------------------------------------------------------------
        respuesta = cliente.chat.completions.create(
            model=MODELO_DE_IA,
            messages=[{"role": "user", "content": instruccion}],
            max_tokens=250,
            temperature=0.3,
        )

        # ---------------------------------------------------------------------
        # Sacamos el texto de adentro de la respuesta.
        #
        # La respuesta viene como una caja con muchas capas:
        #   respuesta
        #     └── choices        (lista de respuestas posibles)
        #          └── [0]       (la primera, que es la única que pedimos)
        #               └── message
        #                    └── content   ← aquí está el texto
        #
        # ".strip()" es una función de los textos que quita los espacios y
        # saltos de línea sobrantes al principio y al final.
        # ---------------------------------------------------------------------
        texto = respuesta.choices[0].message.content.strip()

        # ---------------------------------------------------------------------
        # Devolvemos el texto y avisamos que sí vino de la IA.
        # ---------------------------------------------------------------------
        return {
            "texto": texto,
            "vino_de_la_ia": True,
            "nota": f"Generado con {MODELO_DE_IA}",
        }

    # -------------------------------------------------------------------------
    # Si CUALQUIER cosa falló allá arriba, caemos aquí.
    #
    # "except Exception as error" atrapa cualquier tipo de falla y guarda la
    # descripción en una variable llamada "error".
    #
    # En vez de mostrarle el error feo al usuario, le damos el consejo del
    # plan B. Para él la página funciona igual de bien; solo nosotros vemos
    # en la nota que la IA falló.
    #
    # "str(error)[:120]" convierte el error a texto y se queda con los
    # primeros 120 caracteres (los errores de red pueden ser larguísimos).
    # -------------------------------------------------------------------------
    except Exception as error:
        return {
            "texto": consejo_sin_ia(analisis, resultado_score, prediccion),
            "vino_de_la_ia": False,
            "nota": f"La IA no respondió, usando explicación automática. Detalle: {str(error)[:120]}",
        }
