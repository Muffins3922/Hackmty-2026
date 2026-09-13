# Consola de Liquidez

Score de crédito alternativo para trabajadores independientes,
con seguridad a nivel de fila (RLS).
Reto Capital One — HackMTY 2026.

---

## Cómo correrlo en 3 pasos

```bash
# 1) Instalar las librerías
pip install -r requirements.txt

# 2) Arrancar el servidor
python servidor.py

# 3) Abrir en el navegador
#    http://localhost:8000
```

Para apagarlo: `Ctrl + C` en la terminal.

La primera vez crea solo el archivo `banco.db` con la base de datos.
Si quieres empezar de cero, bórralo y vuelve a arrancar.

> **Si Windows dice que no reconoce `pip`**, usa `python -m pip install -r requirements.txt`.
> Si tampoco reconoce `python`, instálalo desde python.org marcando la casilla
> **"Add Python to PATH"** durante la instalación.

### Cuentas para entrar

La página abre en una pantalla de inicio de sesión. Puedes hacer clic en
cualquiera de las filas de abajo del formulario para que se llene sola.

| Usuario | Contraseña | Qué ve |
|---|---|---|
| `maria` | `123` | Solo su cuenta. Riesgo medio, el freelancer típico |
| `carlos` | `123` | Solo su cuenta. Riesgo bajo, ingresos estables |
| `ana` | `123` | Solo su cuenta. Riesgo alto, se queda sin dinero |
| `admin` | `admin123` | Los tres clientes y la bitácora de seguridad |

También sirve el correo completo (`maria@capitalone.mx`).

Tras 5 intentos fallidos la cuenta se bloquea 15 minutos, a propósito.

### Opcional: activar la inteligencia artificial

Sin esto el proyecto funciona igual, solo que el consejo lo escribe el
sistema en vez de la IA.

```bash
# Mac / Linux
export GROQ_API_KEY=gsk_tu_llave_aqui

# Windows (CMD)
set GROQ_API_KEY=gsk_tu_llave_aqui
```

La llave se saca gratis en <https://console.groq.com/keys>

---

## Qué hace

Califica a un freelancer por su **flujo de caja real**, no por su historial
de tarjetas de crédito.

**El cliente ve cuatro cosas:**

1. **Cuatro indicadores en lenguaje normal** — cuánto tienes, cuántos días
   te dura, cuándo te pagan, cuánto se te va al día.
2. **Una predicción de 21 días** con gráfica, que avisa si vas a quedarte
   sin dinero y qué día.
3. **Un puntaje del 300 al 850** con el desglose de sus 6 componentes, para
   que se vea de dónde salió cada punto.
4. **Un simulador de compras** — escribes cuánto cuesta algo y te dice si
   te alcanza, redibujando la gráfica para que veas la diferencia.

**El analista del banco ve otras dos:**

1. **La lista de clientes** con su saldo y su historial de sobregiros, y
   puede abrir el análisis completo de cualquiera.
2. **La bitácora de seguridad** — quién entró, qué consultó, y qué intentos
   bloqueó el sistema. Las filas en rojo son los accesos negados.

---

## La seguridad

Esta es la parte que separa una demo de algo presentable a un banco.

**El problema que resuelve:** ¿qué impide que María vea la cuenta de Carlos
si escribe su nombre en la dirección del navegador?

**La respuesta corta:** la regla no está en el programa, está dentro de la
base de datos. Aunque el programa pida todos los datos sin filtrar, la base
solo devuelve los de quien está conectado. Eso se llama RLS.

### Las 8 medidas, en una tabla

| Medida | Qué ataque detiene |
|---|---|
| Contraseñas hasheadas con PBKDF2 + sal única | Robar la base ya no es robar las contraseñas |
| Comparación en tiempo constante | Adivinar la clave midiendo microsegundos |
| Bloqueo tras 5 intentos fallidos | Probar miles de contraseñas por segundo |
| Tokens de sesión que vencen a los 30 min | Sesiones eternas y tokens robados |
| **RLS: cada quien ve solo sus filas** | Que un cliente vea datos de otro |
| Consultas parametrizadas en todo el código | Inyección SQL |
| Bitácora de todos los accesos | No poder investigar después de una fuga |
| Mensajes de error deliberadamente vagos | Armar la lista de clientes probando correos |

### Cómo demostrarlo en 30 segundos

1. Entra como `maria` y fíjate en su saldo.
2. Abre la consola del navegador (F12) y escribe:
   `fetch('/api/analisis/carlos', {headers:{Authorization:'Bearer '+miPulsera}})`
3. Responde **404**. Ni siquiera confirma que Carlos exista.
4. Cierra sesión, entra como `admin`, abre **Bitácora de seguridad**.
5. Ahí está el renglón rojo: *"maria · intentó ver los datos de: carlos · Bloqueado"*.

---

## Los archivos, en el orden en que se leen

| # | Archivo | Qué hace |
|---|---|---|
| 1 | `datos/clientes.py` | Los 3 perfiles de ejemplo. **Solo es la semilla** |
| 2 | `logica/calculos.py` | Convierte esos datos en 9 indicadores |
| 3 | `logica/score.py` | Convierte los indicadores en el puntaje 300–850 |
| 4 | `logica/prediccion.py` | Proyecta el saldo día por día a 21 días |
| 5 | `ia/explicador.py` | Le pide a la IA que lo explique en español |
| 6 | `servidor.py` | Recibe las peticiones de la página y las reparte |
| 7 | `web/index.html` | Todo lo que ve el usuario (4 pantallas) |
| 8 | `seguridad/base_datos.py` | Crea `banco.db` y copia la semilla |
| 9 | `seguridad/guardia.py` | Contraseñas, sesiones, **RLS**, bitácora |
| 10 | `seguridad/consultas.py` | La única puerta a los datos |
| 11 | `seguridad/politicas.sql` | El mismo RLS en PostgreSQL nativo |

Todos los archivos están comentados línea por línea. Cada término técnico
trae su explicación en palabras normales la primera vez que aparece.

> **Ojo con `datos/clientes.py`:** se lee una sola vez, al crear la base.
> Si cambias un número ahí, borra `banco.db` y vuelve a arrancar para verlo.

---

## Lo más importante del proyecto

**La inteligencia artificial no calcula nada.** Solo redacta.

Todos los números — el score, la predicción, la línea de crédito — salen de
fórmulas de Python que puedes leer y verificar. La IA recibe esos números ya
resueltos y los explica en español simple.

Esto importa por tres razones:

- **Consistencia**: los mismos datos siempre dan el mismo score. Probado con
  50 corridas seguidas.
- **Auditoría**: si alguien pregunta "¿por qué me dio 642?", se puede señalar
  la línea exacta del código.
- **Legalidad**: negar un crédito con un modelo que no puedes explicar es
  ilegal en muchos países.

---

## Documentación adicional

- **`MAPA_DE_FLUJO.md`** — arquitectura completa, la capa de seguridad
  explicada, contratos de datos, todas las fórmulas juntas, y el contexto
  necesario para que otra persona (o una IA) retome el proyecto desde cero.
- **`seguridad/politicas.sql`** — las políticas RLS de PostgreSQL comentadas,
  con las pruebas que hay que correr para verificar que funcionan.
- **`http://localhost:8000/docs`** — documentación interactiva de la API que
  FastAPI genera solo. Sirve para probar los endpoints en vivo.

---

