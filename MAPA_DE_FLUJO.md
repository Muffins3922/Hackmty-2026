# MAPA DE FLUJO — Consola de Liquidez

> **Este documento está escrito para dos lectores:**
> 1. **Abdiel**, para repasar el proyecto antes de presentarlo.
> 2. **Otra inteligencia artificial** que tome el proyecto sin haber visto
>    la conversación anterior. Todo lo que necesita saber está aquí.
>
> Si eres una IA leyendo esto: el proyecto está **completo y funcionando**.
> No lo reescribas. Lee la sección "Reglas que no se pueden romper" antes
> de tocar cualquier archivo.

---

## 1. Qué es el proyecto

Un sistema de **score de crédito alternativo** para trabajadores independientes
(freelancers) en México, hecho para el reto de Capital One en HackMTY 2026.

**El problema:** los bancos califican con historial de pagos de tarjetas. Un
freelancer sin tarjeta pero con buen flujo de efectivo sale mal calificado o
directamente no califica.

**La solución:** calificar por **flujo de caja real** — cuánto entra, cuándo
entra, cuánto sale, y cuánto aguantas sin cobrar.

**Tres entregables visibles en la pantalla:**
1. Cuatro indicadores en lenguaje simple (cuánto tienes, cuánto te dura, etc.)
2. Una predicción de saldo día por día a 21 días, con gráfica
3. Un puntaje 300–850 con desglose auditable de sus 6 componentes
4. Un simulador de "¿qué pasa si compro esto?" que redibuja la gráfica

---

## 2. Estructura de archivos

```
proyecto_nuevo/
├── datos/
│   └── clientes.py          ARCHIVO 1  — 3 perfiles de ejemplo (SEMILLA)
├── logica/
│   ├── calculos.py          ARCHIVO 2  — los 9 indicadores
│   ├── score.py             ARCHIVO 3  — el puntaje 300-850
│   └── prediccion.py        ARCHIVO 4  — los 21 días + simulador de compra
├── ia/
│   └── explicador.py        ARCHIVO 5  — Groq (solo redacta, no calcula)
├── servidor.py              ARCHIVO 6  — FastAPI, 7 endpoints
├── web/
│   └── index.html           ARCHIVO 7  — toda la interfaz (4 pantallas)
├── seguridad/                          ←── CAPA DE SEGURIDAD
│   ├── base_datos.py        ARCHIVO 8  — crea banco.db y copia la semilla
│   ├── guardia.py           ARCHIVO 9  — hash, sesiones, RLS, bitácora
│   ├── consultas.py         ARCHIVO 10 — el único acceso a datos, con RLS
│   └── politicas.sql        ARCHIVO 11 — RLS nativo de PostgreSQL (docs)
├── banco.db                 ←── se crea SOLO al primer arranque
├── requirements.txt
├── README.md
└── MAPA_DE_FLUJO.md         este archivo
```

**Ningún archivo importa a otro que esté por debajo de él en esa lista**, con
una sola excepción documentada: `seguridad/base_datos.py` importa
`datos/clientes.py` para copiar los datos iniciales, y `seguridad/guardia.py`
para revolver las contraseñas. Las dependencias van en una dirección. No hay
importaciones circulares.

### El cambio más importante respecto a la versión anterior

`datos/clientes.py` **ya no es la fuente de datos en tiempo de ejecución**.
Ahora es la semilla: se lee una sola vez, al crear `banco.db`. Después de eso
todo el programa lee de la base de datos, que es la única capaz de aplicar RLS.

Si modificas un dato en `clientes.py`, hay que **borrar `banco.db`** y volver
a arrancar para que el cambio se vea. Es el error más probable al retomar
este proyecto.

---

## 3. El flujo completo, paso a paso

### Al arrancar el servidor (una sola vez)

```
1. python servidor.py
2. Llama construir_la_base()          seguridad/base_datos.py
3. ¿Existe banco.db con usuarios?
      SÍ  → no hace nada, sigue
      NO  → crea las 6 tablas y copia los 3 clientes de datos/clientes.py,
            revolviendo sus contraseñas, y crea al usuario "admin"
4. uvicorn empieza a escuchar en el puerto 8000
```

### Cuando alguien abre la página

```
1. Navegador pide       GET /
2. servidor.py responde web/index.html
3. Se ve la PANTALLA 1 (login). Las otras 3 existen pero tienen clase "oculto"
4. No se pide ningún dato todavía: sin sesión no hay nada que mostrar
```

### Cuando alguien inicia sesión

```
1. JavaScript manda     POST /api/login   body: { correo, contrasena }
2. servidor.py llama    intentar_entrar()          seguridad/guardia.py
3. Esa función, EN ESTE ORDEN:
      a) busca al usuario por id o correo
      b) ¿está bloqueado por intentos fallidos?   → sale con None
      c) revuelve lo que escribió con LA SAL DE ESA PERSONA
      d) compara jugo contra jugo con compare_digest (tiempo constante)
      e) si falla: +1 al contador, bitácora, None
      f) si acierta: contador a 0, genera token, lo guarda en sesiones
4. Responde { token, id, nombre, profesion, rol }
5. El JavaScript guarda el token en la variable miPulsera
6. SEGÚN EL ROL:
      "cliente" → mostrarSolo("pantallaBanco")  + cargarDatosDelBanco()
      "admin"   → mostrarSolo("pantallaAdmin")  + cargarListaDeClientes()
```

### Cuando un CLIENTE ve su cuenta

```
1. JavaScript pide      GET /api/analisis/{id}
                        header: Authorization: Bearer <token>
2. servidor.py llama    quien_esta_pidiendo(authorization)
      → si el token no sirve, corta con 401 y la función termina ahí
3. Llama traer_ficha_completa(quien_pide, rol, de_quien)
      quien_pide y rol salen DEL TOKEN, no de lo que mandó el navegador
4. Esa función abre la base con conectar_como(), que crea las vistas del RLS
5. Lee de mis_datos, mi_cuenta, mis_pagos, mis_gastos  (VISTAS, no tablas)
6. Si el id pedido no es suyo, las vistas devuelven vacío → None → 404
7. Con la ficha en mano, servidor.py ejecuta la cadena de siempre:

   analizar_cliente(cliente)    logica/calculos.py
        ↓ devuelve los 9 indicadores
   calcular_score(analisis)     logica/score.py        ← necesita el anterior
   predecir_21_dias(analisis)   logica/prediccion.py   ← necesita el mismo
        ↓
   explicar_con_ia(...)         ia/explicador.py       ← necesita los tres

8. Devuelve JSON con 4 llaves: analisis, score, prediccion, consejo
9. El JavaScript llama a las funciones de pintado:
      pintarSaldo() · pintarIndicadores() · pintarConsejo()
      pintarMovimientos() · pintarScore() · pintarPrediccion()
```

### Cuando el ADMINISTRADOR abre su panel

```
1. JavaScript pide      GET /api/admin/clientes    (con el token)
2. servidor.py verifica el token y llama traer_lista_de_clientes()
3. Esa función tiene DOS candados:
      candado 1 (Python) → if rol != "admin": return None  → 403
      candado 2 (SQL)    → lee de las vistas, que de todos modos filtrarían
4. Hace un JOIN de mis_datos con mi_cuenta y devuelve la lista
5. El JavaScript pinta la tabla con un botón "Ver análisis" por fila

Al hacer clic en "Ver análisis":
6. verFichaDeCliente(id) pide GET /api/analisis/{id} con el MISMO token
7. Como el rol del token es "admin", las vistas del RLS sí le dan esos datos
8. Reutiliza dibujarGrafica() y el mismo formato de barras del panel cliente

En la pestaña "Bitácora de seguridad":
9. Pide GET /api/admin/bitacora → las últimas 50 líneas del diario
10. Pinta en rojo las filas donde permitido = 0
```

### Cuando el usuario simula una compra

```
1. JavaScript manda     POST /api/simular-compra   (con el token)
                        body: { id_del_cliente, monto }
2. servidor.py verifica el token y trae la ficha CON RLS
      → mandar el id de otra persona aquí no sirve de nada
3. Ejecuta simular_compra(analisis, monto)
4. Esa función corre predecir_21_dias() DOS VECES:
      - una con el saldo normal          → "antes"
      - una con el saldo menos la compra → "despues"
   (reusa la misma función a propósito, ver "Reglas" abajo)
5. Compara los dos resultados y decide semáforo: verde / amarillo / rojo
6. El JavaScript pinta el veredicto y redibuja la gráfica con DOS líneas:
      gris punteada = sin la compra
      azul sólida   = con la compra
```

### Cuando alguien cierra sesión

```
1. JavaScript manda     POST /api/salir   (con el token)
2. servidor.py borra esa fila de la tabla sesiones
      → el token deja de servir EN ESE INSTANTE, no cuando venza
3. El JavaScript borra miPulsera, miRol y datosDelUsuario
4. mostrarSolo("pantallaLogin")
```

---

## 3-bis. LA CAPA DE SEGURIDAD

Esta sección es nueva y es la más importante si vas a tocar el proyecto.

### Las 8 medidas implementadas

| # | Medida | Dónde vive | Qué ataque detiene |
|---|--------|-----------|--------------------|
| 1 | Hash PBKDF2 + sal por usuario | `guardia.py` línea 150 | Robo de la base = robo de contraseñas |
| 2 | Comparación en tiempo constante | `guardia.py` línea 205 | Adivinar la clave midiendo microsegundos |
| 3 | Bloqueo tras 5 intentos | `guardia.py` línea 290 | Fuerza bruta |
| 4 | Tokens de sesión con vencimiento | `guardia.py` línea 330 | Sesiones eternas, tokens robados |
| 5 | **RLS con vistas** | `guardia.py` línea 380 | Que un cliente vea datos de otro |
| 6 | Consultas parametrizadas (`?`) | todos los archivos SQL | Inyección SQL |
| 7 | Bitácora de auditoría | `guardia.py` línea 470 | No saber qué pasó tras una fuga |
| 8 | Mensajes de error vagos | `servidor.py` login y 404 | Enumeración de usuarios |

### Cómo funciona el RLS en SQLite (lo que hay que entender)

SQLite no tiene RLS nativo. Lo construimos con dos piezas:

1. **Una tabla temporal** `sesion_actual` que se crea al conectar y guarda
   quién eres. Al ser `TEMP`, **solo existe en esa conexión** — dos usuarios
   simultáneos tienen cada uno la suya y no se ven entre sí.

2. **Cuatro vistas temporales** que llevan el filtro metido adentro:

```sql
CREATE TEMP VIEW mis_pagos AS
SELECT * FROM pagos_recibidos
WHERE id_usuario = (SELECT id_usuario FROM sesion_actual)
   OR (SELECT rol FROM sesion_actual) = 'admin'
```

**La regla que no se puede romper:** el código de la aplicación lee de
`mis_pagos`, `mis_gastos`, `mi_cuenta` y `mis_datos`. **Nunca** de
`pagos_recibidos`, `gastos_fijos`, `cuentas` ni `usuarios`.

Si escribes una consulta nueva que lea de una tabla real en vez de su vista,
rompes el RLS y el filtro deja de aplicarse. Ese es el único punto frágil
del diseño y por eso todo el acceso está concentrado en `consultas.py`.

### Qué cambia en PostgreSQL

`seguridad/politicas.sql` tiene la versión con RLS nativo. La diferencia
práctica: en SQLite nuestras vistas protegen a quien las usa, pero alguien
que abra `banco.db` con otra herramienta ve todo. En PostgreSQL la regla vive
en el motor y no se puede esquivar desde ninguna consulta.

Ese archivo **no se ejecuta** al correr el proyecto. Es documentación y ruta
de migración.

### Las 3 pruebas que demuestran que funciona

```bash
# 1. María pide TODOS los pagos, sin filtrar → solo salen los suyos
python -c "
from seguridad.guardia import conectar_como
c = conectar_como('maria','cliente')
print([f[0] for f in c.execute('SELECT DISTINCT id_usuario FROM mis_pagos')])
"   # → ['maria']

# 2. María pide la ficha de Carlos → None
python -c "
from seguridad.consultas import traer_ficha_completa
print(traer_ficha_completa('maria','cliente','carlos'))
"   # → None

# 3. Vía HTTP, con token de María pidiendo a Carlos → 404
curl -H "Authorization: Bearer <token_de_maria>" \
     http://127.0.0.1:8000/api/analisis/carlos
```

---

## 4. Contratos de datos

> Un "contrato" es la forma exacta que tiene cada paquete de datos.
> Si cambias uno de estos campos, tienes que cambiarlo también donde se usa.

### 4.1 Ficha de cliente — `datos/clientes.py`

```python
{
  "id": str,                      # "maria"
  "nombre": str,
  "profesion": str,
  "dinero_en_el_banco": int,      # pesos
  "pagos_recibidos": [            # últimos 90 días
      {"fecha": "AAAA-MM-DD", "monto": int, "cliente": str}
  ],
  "gastos_fijos": [
      {"concepto": str, "monto": int, "se_paga_en": int}   # días desde hoy
  ],
  "gasto_diario_promedio": int,   # gasto variable por día
  "veces_sin_dinero": int         # sobregiros en 90 días
}
```

### 4.2 Análisis — salida de `analizar_cliente()`

```python
{
  # copiados tal cual de la ficha
  "nombre", "profesion", "dinero_en_el_banco", "veces_sin_dinero",
  "gastos_fijos_lista", "pagos_recibidos",

  # los 9 indicadores calculados
  "ingreso_al_mes": int,              # total 90 días / 3
  "gastos_fijos_al_mes": int,
  "gasto_total_por_dia": int,         # fijo prorrateado + variable
  "gasto_total_al_mes": int,
  "dias_de_colchon": float,           # saldo / gasto_total_por_dia
  "volatilidad": float,               # 0=parejo, 1+=caótico
  "concentracion": float,             # 0=repartido, 1=un solo cliente
  "cuantos_clientes_tiene": int,
  "cobertura": float,                 # ingreso / gastos fijos (DSCR)
  "ahorro": float,                    # puede ser negativo
  "dias_para_el_proximo_pago": int,
  "monto_del_proximo_pago": int
}
```

### 4.3 Score — salida de `calcular_score()`

```python
{
  "score": int,                   # 300 a 850
  "categoria": str,               # "Excelente" | "Muy bueno" | "Bueno" |
                                  # "Regular" | "En riesgo"
  "color": str,                   # "verde" | "amarillo" | "rojo"
  "explicacion_corta": str,
  "linea_recomendada": int,       # redondeado a múltiplos de 500
  "pago_mensual_maximo": int,
  "dinero_que_le_sobra": int,
  "puntos_base": int,             # siempre 300
  "detalle_de_notas": [           # exactamente 6 elementos
      {"nombre": str, "nota": int,     # 0-100
       "peso": int,                    # porcentaje
       "puntos": int,                  # aporte real al score
       "que_significa": str}
  ]
}
```

### 4.4 Predicción — salida de `predecir_21_dias()`

```python
{
  "dias": [                       # exactamente 21 elementos
      {"dia": int,                # 1 a 21
       "fecha": "AAAA-MM-DD",
       "saldo": int,              # puede ser negativo
       "entra": int,
       "sale": int,
       "nivel": str,              # "bien" | "cuidado" | "peligro"
       "que_paso": [str]}         # textos para el tooltip
  ],
  "resumen": str,
  "hay_alerta": bool,
  "se_queda_sin_dinero": bool,
  "dia_del_problema": int | None,
  "saldo_mas_bajo": int,
  "saldo_final": int,
  "saldo_inicial": int
}
```

### 4.5 Simulación de compra — salida de `simular_compra()`

```python
{
  "semaforo": str,                    # "verde" | "amarillo" | "rojo"
  "mensaje": str,
  "monto_de_la_compra": float,
  "antes": {...},                     # una predicción completa (4.4)
  "despues": {...},                   # otra predicción completa (4.4)
  "dias_de_colchon_que_cuesta": float
}
```

---

## 5. Las fórmulas, en un solo lugar

| Indicador | Fórmula | Archivo · paso |
|---|---|---|
| Ingreso mensual | `suma(pagos 90d) / 3` | calculos.py · PASO 1 |
| Gasto por día | `gastos_fijos/30 + gasto_variable` | calculos.py · PASO 2 |
| **Días de colchón** | `saldo / gasto_por_dia` | calculos.py · PASO 3 |
| Volatilidad (CV) | `desviacion_estandar(pagos) / promedio(pagos)` | calculos.py · PASO 4 |
| Concentración | `pago_del_cliente_mayor / total_ganado` | calculos.py · PASO 5 |
| **Cobertura (DSCR)** | `ingreso_mensual / gastos_fijos_mensuales` | calculos.py · PASO 6 |
| Tasa de ahorro | `(ingreso - gasto_total) / ingreso` | calculos.py · PASO 7 |
| Próximo pago | `promedio(huecos entre pagos) - días desde el último` | calculos.py · PASO 8 |
| **SCORE** | `suma_ponderada × 550 + 300` | score.py · PARTE 2 |
| Saldo del día | `saldo_ayer + entra_hoy - sale_hoy` | prediccion.py · REGLA 4 |
| Línea de crédito | `(ingreso - gasto) × %segun_score × 12` | score.py · PARTE 4 |

### Los 6 pesos del score (deben sumar 1.00)

| Componente | Peso | Escala de la nota |
|---|---|---|
| Días de colchón | 25% | 0 días → 0.0 ; 60 días → 1.0 |
| Estabilidad de ingresos | 20% | `1 - volatilidad`, acotado a 0–1 |
| Cobertura de gastos | 20% | 1.0 → 0.0 ; 2.5 → 1.0 |
| Variedad de clientes | 15% | `1 - concentracion` |
| Capacidad de ahorro | 10% | 0% → 0.0 ; 30% → 1.0 |
| Sin sobregiros | 10% | `1 - (veces × 0.25)` |

Hay un `assert` al final de `score.py` que verifica la suma automáticamente.

### Cortes de categoría

| Score | Categoría | Color | % del sobrante que se presta |
|---|---|---|---|
| 750+ | Excelente | verde | 40% |
| 680–749 | Muy bueno | verde | 30% |
| 620–679 | Bueno | amarillo | 20% |
| 560–619 | Regular | amarillo | 10% |
| <560 | En riesgo | rojo | 0% |

---

## 6. Reglas que no se pueden romper

> Si eres una IA modificando este proyecto, estas son las restricciones
> que le dan valor. Romper cualquiera destruye el argumento del proyecto.

**R1 — La IA nunca calcula.**
`ia/explicador.py` solo redacta texto a partir de números que ya vienen
resueltos. Nunca le pidas a Groq que calcule un score, una predicción o una
recomendación numérica. El prompt le prohíbe expresamente inventar números.
Motivo: auditabilidad y consistencia.

**R2 — Todo lo numérico es determinista.**
No hay `random` sin semilla, no hay dependencias de la hora, no hay llamadas
de red en la ruta de cálculo. Correr el score 1000 veces con los mismos datos
da 1000 veces el mismo número. Verificado en las pruebas.

**R3 — Las listas se ordenan antes de procesarse.**
En `calculos.py` PASO 8 se hace `sorted(fechas_de_pago)`. Si los datos
llegaran desordenados desde una API real, los huecos entre pagos saldrían mal.
No quites ese `sorted`.

**R4 — El simulador de compra reusa `predecir_21_dias()`.**
No escribas una segunda implementación de la proyección para el caso "con
compra". Si existieran dos, tarde o temprano divergirían y el "antes" y el
"después" dejarían de ser comparables.

**R5 — El frontend no calcula dinero.**
`web/index.html` solo formatea y dibuja. Si necesitas un número nuevo en la
pantalla, agrégalo a la salida del backend, no lo calcules en JavaScript.

**R6 — El sistema nunca se cae por la IA.**
`explicar_con_ia()` tiene un `try/except` que cae a `consejo_sin_ia()`, una
versión escrita a mano con puros `if`. Sin internet la app funciona igual.

**R7 — Los pesos suman 1.00.**
Protegido por un `assert`. Si cambias uno, ajusta otro.

### Reglas de la capa de seguridad

**R8 — Nunca leas de las tablas reales, siempre de las vistas.**
Usa `mis_pagos`, `mis_gastos`, `mi_cuenta`, `mis_datos`. Nunca
`pagos_recibidos`, `gastos_fijos`, `cuentas` ni `usuarios`. Las vistas traen
el filtro del RLS adentro; las tablas no. Esta es la regla más importante
de todas: romperla desactiva el RLS sin que nada falle ni avise.

**R9 — La identidad sale del token, nunca del cliente.**
`usuario["id"]` y `usuario["rol"]` vienen de `revisar_pulsera()`. Jamás uses
un id que venga en el cuerpo de la petición o en la URL para decidir permisos.
El navegador está en la computadora del usuario y puede mandar lo que sea.

**R10 — Todo acceso a datos pasa por `seguridad/consultas.py`.**
No agregues consultas SQL sueltas en `servidor.py` ni en los archivos de
lógica. Un solo cuello de botella es lo que hace auditable el sistema.

**R11 — SQL siempre con `?`, nunca pegando texto.**
`conexion.execute("SELECT ... WHERE id = ?", (valor,))`. Nunca uses f-strings
ni concatenación para armar consultas. Es la única defensa contra inyección SQL.

**R12 — El login responde el mismo mensaje para todos los fallos.**
Contraseña mala, usuario inexistente y cuenta bloqueada dan exactamente
"Correo o contraseña incorrectos". Distinguirlos permite enumerar usuarios.

---

## 7. Cómo correrlo

```bash
pip install -r requirements.txt
python servidor.py
```
Luego abrir **http://localhost:8000**

La primera vez crea `banco.db` solo. Si quieres empezar de cero, borra ese
archivo y vuelve a arrancar.

**Cuentas:**

| Usuario | Contraseña | Rol | Qué ve |
|---|---|---|---|
| `maria` | `123` | cliente | Solo su cuenta. Riesgo medio |
| `carlos` | `123` | cliente | Solo su cuenta. Riesgo bajo |
| `ana` | `123` | cliente | Solo su cuenta. Riesgo alto, dispara alerta |
| `admin` | `admin123` | admin | Los 3 clientes + la bitácora |

Tras 5 intentos fallidos la cuenta se bloquea 15 minutos. Para desbloquear
a mano: borra `banco.db` y reinicia, o corre
`UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL`.

Para activar la IA (opcional — sin esto funciona igual con el texto automático):
```bash
# Mac / Linux
export GROQ_API_KEY=gsk_tu_llave

# Windows
set GROQ_API_KEY=gsk_tu_llave
```
La llave se saca gratis en console.groq.com

Documentación automática de la API: **http://localhost:8000/docs**

---

## 8. Estado actual y resultados verificados

Probado el 13 de septiembre de 2026. Los tres perfiles se separan
correctamente, que es la prueba de que el modelo discrimina:

| Persona | Score | Categoría | Colchón | Volatilidad | DSCR | Línea |
|---|---|---|---|---|---|---|
| Carlos Iván | 715 | Muy bueno | 45.0 días | 0.21 | 4.26 | $129,000 |
| María Fernanda | 642 | Bueno | 24.7 días | 0.43 | 2.84 | $13,000 |
| Ana Sofía | 441 | En riesgo | 6.3 días | 0.55 | 1.71 | $0 |

Ana además dispara la alerta de la predicción: *"En 4 días te quedas sin
dinero"*. Es el caso que demuestra que el sistema sí detecta el peligro.

**Prueba de consistencia:** 50 corridas consecutivas del score de María
devolvieron `{642}` — un único valor.

**Endpoints probados:** los 7 responden lo esperado.

### Pruebas de seguridad (9 de 9 pasan)

| Escenario | Esperado | Resultado |
|---|---|---|
| María pide sus propios datos | 200 | 200 |
| María pide los datos de Carlos | 404 | 404 |
| Petición sin token | 401 | 401 |
| Petición con token inventado | 401 | 401 |
| María pide `/api/admin/clientes` | 403 | 403 |
| María pide `/api/admin/bitacora` | 403 | 403 |
| Admin pide el panel | 200 | 200 |
| Admin pide los datos de Carlos | 200 | 200 |
| María simula compra sobre la cuenta de Ana | 404 | 404 |

**Prueba a nivel base de datos:** conectado como `maria`, la consulta
`SELECT DISTINCT id_usuario FROM mis_pagos` (sin ningún WHERE) devuelve
únicamente `['maria']`. Conectado como `admin`, devuelve los tres.

**Interfaz:** 4 pantallas, 0 errores de consola, probado con Playwright.

---

## 9. Lo que NO está hecho (limitaciones honestas)

Decirlas en la presentación suma credibilidad. Ocultarlas y que un juez las
encuentre, resta mucho.

1. **No hay conexión en vivo con Nessie.** Los datos son 3 perfiles fijos en
   `datos/clientes.py`. Tienen exactamente la misma forma que devuelve Nessie
   (`/accounts/{id}`, `/deposits`, `/purchases`, `/bills`), así que conectarla
   es reemplazar una función, no reescribir el motor.
2. **La línea de crédito no calcula intereses.** Es capital puro a 12 meses.
   Un banco real sumaría la tasa.
3. **Los pesos del score no están calibrados con datos históricos.** Son una
   decisión de negocio razonada, no un modelo entrenado. Un banco los ajustaría
   con miles de casos reales y mediría el default rate.
4. **La predicción del próximo pago asume que el pasado se repite.** Si un
   cliente se va mañana, se equivoca. Por eso la interfaz dice "estimado".
5. **El RLS es simulado, no nativo.** SQLite no tiene RLS de fábrica; lo
   construimos con vistas temporales. Protege a la aplicación, pero quien
   abra `banco.db` con otra herramienta ve todo. `seguridad/politicas.sql`
   tiene la versión con RLS nativo de PostgreSQL, que sí es inesquivable.
6. **No hay HTTPS.** El token viaja sin cifrar entre la página y el servidor.
   En una red pública cualquiera lo intercepta.
7. **No hay segundo factor (2FA).** Con la contraseña basta para entrar.
8. **La bitácora vive en la misma base que los datos.** Quien tenga escritura
   podría alterarla. Lo correcto es mandarla a otro servidor.
9. **El bloqueo es por cuenta, no por IP.** Alguien podría probar una misma
   contraseña en miles de cuentas distintas sin llegar al límite de ninguna.
10. **Las contraseñas de la demo son débiles a propósito** (`123`) para que
    cualquiera pueda probar. El sistema las guarda hasheadas igual.

---

## 10. Si vas a extender el proyecto

**Para conectar Nessie de verdad:** escribe una función
`obtener_cliente_de_nessie(account_id)` que haga los 4 GET y devuelva un
diccionario con el contrato de la sección 4.1. Sustitúyela en `servidor.py`.
Nada más cambia — ese es el punto de haber separado los archivos así.

**Para agregar un indicador nuevo al score:** hay que tocar tres lugares y
en este orden: (1) calcularlo en `calculos.py` y agregarlo al `return`,
(2) agregar su peso en `PESOS` de `score.py` **bajando otro peso** para que
sigan sumando 1.00, y (3) agregar su entrada a `detalle_de_notas` para que
aparezca como barra en la pantalla.

**Para cambiar el horizonte de 21 días:** la constante `DIAS_A_PREDECIR` está
arriba de `prediccion.py`. Pero ojo: en `web/index.html`, la función `posX()`
tiene el 21 escrito a mano en dos lugares y las etiquetas del eje también.

**Paleta de colores usada (Capital One):**
`#023373` azul profundo · `#024873` azul medio · `#D92525` rojo ·
`#D97171` rojo suave · `#F2F2F2` gris fondo.
Están definidas como variables CSS en `:root`, arriba de `index.html`.

**Logo:** en `web/index.html` hay un `div` con clase `logo-espacio` en el
encabezado. Ahí va el archivo oficial que entregó Capital One en el hackathon,
reemplazándolo por `<img src="logo-capital-one.png" alt="Capital One" style="height:30px">`.

---

## 11. Diagrama resumido

```
                          NAVEGADOR
                       web/index.html
     ┌───────────────────────┴───────────────────────┐
     │  PANTALLA 1  login                            │
     │  PANTALLA 2  cuenta del cliente (5 pestañas)  │
     │  PANTALLA 3  panel del analista (2 pestañas)  │
     │  PANTALLA 4  ficha de un cliente              │
     └───────────────────────┬───────────────────────┘
                             │  todas las peticiones pasan por
                             │  pedirAlServidor(), que agrega
                             │  Authorization: Bearer <token>
                             ▼
                        servidor.py
                         (FastAPI)
                             │
                  quien_esta_pidiendo()  ←── EL TORNIQUETE
                             │            sin token válido → 401
                             ▼
                  seguridad/consultas.py  ←── ÚNICA PUERTA A LOS DATOS
                             │
                  conectar_como(id, rol)
                             │
        ┌────────────────────┴────────────────────┐
        │   banco.db                              │
        │                                         │
        │   TEMP TABLE sesion_actual (quién eres) │
        │        ↓                                │
        │   VISTAS con el filtro RLS adentro:     │
        │     mis_pagos · mis_gastos              │
        │     mi_cuenta · mis_datos               │
        │        ↓                                │
        │   tablas reales (nadie las toca)        │
        └────────────────────┬────────────────────┘
                             │ la ficha, ya filtrada
                             ▼
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
  logica/calculos.py         │              ia/explicador.py
  (9 indicadores)            │              (Groq, solo texto)
        │                    │                    ▲
        ├────────────────────┤                    │
        ▼                    ▼                    │
  logica/score.py    logica/prediccion.py         │
  (300-850)          (21 días + compras)          │
        │                    │                    │
        └────────────────────┴────────────────────┘
                    JSON de vuelta al navegador

  En paralelo, CADA acceso escribe una línea en la tabla bitacora.
```

---

**Última actualización:** 13 de septiembre de 2026
**Estado:** funcionando, probado, listo para presentar.
**Incluye:** capa de seguridad con RLS, autenticación por token, hash de
contraseñas, bitácora de auditoría y los dos paneles (cliente y analista).
