-- ============================================================================
--  ARCHIVO 11 de 11:  seguridad/politicas.sql
--
--  ¿QUÉ ES ESTE ARCHIVO Y POR QUÉ NO SE EJECUTA?
--
--  Este archivo es la versión PROFESIONAL de la seguridad que implementamos.
--  No se ejecuta al correr el proyecto. Está aquí por dos razones:
--
--     1) Para enseñar cómo se vería este mismo sistema en un banco real
--     2) Para que si mañana se migra de SQLite a PostgreSQL, el trabajo
--        de seguridad ya esté escrito
--
--  ¿CUÁL ES LA DIFERENCIA CON LO QUE SÍ CORRE?
--
--  Nuestro proyecto usa SQLite porque no necesita instalación y funciona en
--  cualquier computadora. SQLite NO tiene RLS de fábrica, así que lo logramos
--  con vistas temporales (está explicado en seguridad/guardia.py línea 380).
--  El efecto es el mismo, pero lo construimos nosotros.
--
--  PostgreSQL SÍ trae RLS de fábrica, metido en el motor de la base. Es lo
--  que usan los bancos de verdad. Este archivo es esa versión.
--
--  ¿POR QUÉ IMPORTA LA DIFERENCIA?
--  En SQLite, nuestras vistas protegen a quien las usa. Pero si alguien se
--  conecta a la base y escribe "SELECT * FROM pagos_recibidos" a mano, ve
--  todo. En PostgreSQL eso es imposible: la regla está en el motor, debajo
--  de cualquier consulta que alguien pueda escribir. Ni el programa, ni una
--  consulta manual, ni una herramienta externa pueden saltársela.
--
--  ¿CÓMO SE USARÍA ESTE ARCHIVO?
--     psql -U postgres -d banco -f seguridad/politicas.sql
-- ============================================================================


-- ============================================================================
--  PARTE 1 — LOS ROLES
--
--  ¿QUÉ ES UN "ROL" EN POSTGRESQL?
--  Es una identidad con la que alguien se conecta a la base. Como una cuenta
--  de usuario del sistema operativo, pero de la base de datos.
--
--  La gracia es que los permisos se le dan al ROL, no a la persona. Si mañana
--  contratan a otro analista, le asignas el rol y ya tiene exactamente los
--  mismos permisos, sin tener que acordarte de cuáles eran.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- El rol de los clientes. Es el que usa la aplicación cuando entra María.
--
-- NOLOGIN significa que nadie se puede conectar directamente con este rol.
-- Solo se puede "adoptar" desde adentro de una sesión ya abierta. Es una
-- protección extra: aunque alguien se robara el nombre del rol, no le sirve
-- para entrar desde afuera.
-- ----------------------------------------------------------------------------
CREATE ROLE rol_cliente NOLOGIN;

-- ----------------------------------------------------------------------------
-- El rol del analista de riesgo (nuestro "admin"). Puede ver a todos los
-- clientes, pero fíjate más abajo que NO puede modificar sus datos.
-- ----------------------------------------------------------------------------
CREATE ROLE rol_analista NOLOGIN;

-- ----------------------------------------------------------------------------
-- El rol de la aplicación. Es con el que se conecta el servidor de Python.
--
-- Dos cosas importantes de esta línea:
--   LOGIN      → este sí se puede conectar desde afuera (lo necesita el server)
--   NOBYPASSRLS → "no puede saltarse el RLS".
--
-- Esa última palabra es crítica. En PostgreSQL, el superusuario y el dueño de
-- una tabla SE SALTAN el RLS por defecto. O sea: si tu aplicación se conecta
-- como superusuario, escribes todas las políticas del mundo y NO SIRVEN DE
-- NADA porque el motor las ignora para ese rol.
--
-- Es el error más común al implementar RLS. Escribes las políticas, las
-- pruebas conectado como admin, "funciona" (o sea, ves todo), y te vas
-- tranquilo a producción con la base completamente abierta.
-- ----------------------------------------------------------------------------
CREATE ROLE app_banco LOGIN PASSWORD 'cambiar_esta_clave_en_produccion' NOBYPASSRLS;


-- ============================================================================
--  PARTE 2 — QUIÉN ESTÁ CONECTADO
--
--  Para que una política pueda decir "solo tus filas", la base necesita saber
--  quién eres TÚ. En PostgreSQL eso se hace con una "variable de sesión":
--  un dato que vive mientras dure tu conexión y que nadie más ve.
--
--  Es el equivalente exacto de nuestra tabla temporal sesion_actual en SQLite.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Esta función lee la variable de sesión y devuelve el id del usuario conectado.
--
-- Desglose:
--   current_setting('app.usuario_actual', true)
--       → lee la variable llamada app.usuario_actual
--       → el "true" significa "si no existe, devuelve vacío en vez de tronar"
--
--   STABLE → le avisa a PostgreSQL que esta función siempre devuelve lo mismo
--            durante una misma consulta, así puede optimizarla y no llamarla
--            una vez por cada fila (que sería lentísimo en tablas grandes)
--
--   SECURITY DEFINER → la función corre con los permisos de QUIEN LA CREÓ,
--            no de quien la llama. Así un cliente no puede modificarla.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION usuario_actual()
RETURNS TEXT AS $$
    SELECT current_setting('app.usuario_actual', true);
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- ----------------------------------------------------------------------------
-- Lo mismo pero para el rol.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION rol_actual()
RETURNS TEXT AS $$
    SELECT current_setting('app.rol_actual', true);
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- ----------------------------------------------------------------------------
-- Así las pone la aplicación justo después de conectarse, una vez que ya
-- verificó la contraseña:
--
--     SET LOCAL app.usuario_actual = 'maria';
--     SET LOCAL app.rol_actual = 'cliente';
--
-- El "LOCAL" es importantísimo: hace que el valor dure solo hasta el final de
-- la transacción actual. Sin LOCAL, el valor se queda pegado a la conexión, y
-- como los servidores reutilizan conexiones (un "pool"), la siguiente petición
-- de OTRO usuario heredaría la identidad del anterior. Ese bug ha causado
-- fugas de datos reales en producción.
-- ----------------------------------------------------------------------------


-- ============================================================================
--  PARTE 3 — ENCENDER EL RLS
--
--  Ojo: crear políticas NO las activa. Son dos pasos separados y hay que
--  hacer los dos. Si solo creas las políticas, no pasa absolutamente nada
--  y la tabla sigue abierta para todos.
-- ============================================================================

ALTER TABLE cuentas         ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos_recibidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE gastos_fijos    ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios        ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- Esta segunda línea por tabla es la que casi todos olvidan.
--
-- FORCE ROW LEVEL SECURITY hace que el RLS aplique TAMBIÉN al dueño de la
-- tabla. Sin ella, el dueño ve todo sin restricción, y como el dueño suele
-- ser justo el usuario con el que se hicieron las migraciones... otra vez
-- la base queda abierta sin que nadie se dé cuenta.
-- ----------------------------------------------------------------------------
ALTER TABLE cuentas         FORCE ROW LEVEL SECURITY;
ALTER TABLE pagos_recibidos FORCE ROW LEVEL SECURITY;
ALTER TABLE gastos_fijos    FORCE ROW LEVEL SECURITY;
ALTER TABLE usuarios        FORCE ROW LEVEL SECURITY;


-- ============================================================================
--  PARTE 4 — LAS POLÍTICAS
--
--  Una política es una regla que dice: "para esta tabla, y esta operación,
--  solo deja pasar las filas que cumplan esta condición".
--
--  Anatomía de una política:
--     CREATE POLICY <nombre> ON <tabla>
--     FOR <operación>        -- SELECT, INSERT, UPDATE, DELETE o ALL
--     TO <rol>               -- a quién se le aplica
--     USING (<condición>)    -- qué filas puede VER
--     WITH CHECK (<cond>)    -- qué filas puede ESCRIBIR
--
--  La diferencia entre USING y WITH CHECK es sutil pero importante:
--     USING      → filtra lo que ya está en la tabla (al leer o al buscar
--                  cuáles modificar)
--     WITH CHECK → revisa lo que estás intentando meter o dejar (al insertar
--                  o al terminar de actualizar)
--
--  Si solo pones USING en un UPDATE, un cliente podría modificar SU fila
--  para ponerle el id de otra persona, y regalársela. WITH CHECK lo impide.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- POLÍTICA 1: un cliente solo ve SU cuenta.
--
-- La condición compara la columna id_usuario de cada fila contra el resultado
-- de usuario_actual(). PostgreSQL evalúa esto para CADA fila, y las que no
-- cumplen simplemente no existen para esa consulta. No da error, no avisa:
-- la fila no aparece, como si nunca se hubiera creado.
-- ----------------------------------------------------------------------------
CREATE POLICY cliente_ve_su_cuenta ON cuentas
    FOR SELECT
    TO rol_cliente
    USING (id_usuario = usuario_actual());

-- ----------------------------------------------------------------------------
-- POLÍTICA 2: un cliente solo ve SUS pagos.
-- ----------------------------------------------------------------------------
CREATE POLICY cliente_ve_sus_pagos ON pagos_recibidos
    FOR SELECT
    TO rol_cliente
    USING (id_usuario = usuario_actual());

-- ----------------------------------------------------------------------------
-- POLÍTICA 3: un cliente solo ve SUS gastos.
-- ----------------------------------------------------------------------------
CREATE POLICY cliente_ve_sus_gastos ON gastos_fijos
    FOR SELECT
    TO rol_cliente
    USING (id_usuario = usuario_actual());

-- ----------------------------------------------------------------------------
-- POLÍTICA 4: un cliente solo ve SU propia ficha de usuario.
--
-- Esto evita algo que se ve mucho y está mal: pantallas donde un usuario
-- puede cambiar el número de su URL y ver el perfil de otro. Se llama
-- "IDOR" (Insecure Direct Object Reference, referencia directa insegura) y
-- es de las vulnerabilidades más comunes que existen. Con esta política,
-- cambiar el número en la URL simplemente no devuelve nada.
-- ----------------------------------------------------------------------------
CREATE POLICY cliente_ve_su_ficha ON usuarios
    FOR SELECT
    TO rol_cliente
    USING (id = usuario_actual());

-- ----------------------------------------------------------------------------
-- POLÍTICA 5: el analista ve TODAS las cuentas, pero solo leer.
--
-- USING (true) significa "todas las filas pasan el filtro".
--
-- Y fíjate en el FOR SELECT: es solo lectura. El analista NO tiene política
-- de INSERT, UPDATE ni DELETE, y en PostgreSQL lo que no está explícitamente
-- permitido está prohibido. O sea que aunque quisiera, no puede cambiarle el
-- saldo a un cliente. Eso se llama "separación de funciones": quien evalúa
-- el riesgo no debe poder alterar los números que evalúa.
-- ----------------------------------------------------------------------------
CREATE POLICY analista_ve_todas_las_cuentas ON cuentas
    FOR SELECT
    TO rol_analista
    USING (true);

CREATE POLICY analista_ve_todos_los_pagos ON pagos_recibidos
    FOR SELECT
    TO rol_analista
    USING (true);

CREATE POLICY analista_ve_todos_los_gastos ON gastos_fijos
    FOR SELECT
    TO rol_analista
    USING (true);

-- ----------------------------------------------------------------------------
-- POLÍTICA 6: el analista ve la lista de usuarios, PERO no de todos.
--
-- La condición dice: solo las filas cuyo rol sea 'cliente'.
--
-- ¿Por qué? Para que un analista no pueda enumerar a los otros analistas ni
-- a los administradores del sistema. Es reducir la superficie: si alguien
-- roba la cuenta de un analista, al menos no obtiene el directorio completo
-- de empleados del banco para seguir atacando.
-- ----------------------------------------------------------------------------
CREATE POLICY analista_ve_clientes ON usuarios
    FOR SELECT
    TO rol_analista
    USING (rol = 'cliente');

-- ----------------------------------------------------------------------------
-- POLÍTICA 7: nadie, ni el analista, puede borrar datos financieros.
--
-- No escribimos ninguna política de DELETE para ninguna tabla. Como PostgreSQL
-- niega por defecto lo que no está permitido, DELETE queda bloqueado para
-- todos los roles de la aplicación.
--
-- Los movimientos bancarios nunca se borran: se corrigen metiendo un
-- movimiento contrario. Eso permite reconstruir la historia completa y es
-- requisito legal en casi cualquier país. A un libro contable que solo
-- acepta agregar y nunca borrar se le llama "append-only" (solo añadir).
-- ----------------------------------------------------------------------------


-- ============================================================================
--  PARTE 5 — PERMISOS DE TABLA
--
--  El RLS decide QUÉ FILAS. Los permisos deciden QUÉ OPERACIONES.
--  Son dos candados distintos y hay que poner los dos.
--
--  Si le das permiso de SELECT sobre una tabla pero sin política de RLS, no
--  ve nada. Si le pones política pero no le das el permiso, tampoco.
--  Tienen que coincidir los dos.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Primero quitamos TODO a todo el mundo. Se empieza cerrando la puerta y
-- después se abren rendijas, nunca al revés.
--
-- PUBLIC es un rol especial que significa "absolutamente todos".
-- ----------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;

-- ----------------------------------------------------------------------------
-- Ahora damos solo lo mínimo necesario.
--
-- Los clientes: solo leer sus 4 tablas. No pueden modificar su propio saldo,
-- que sería lo primero que intentaría alguien malicioso.
-- ----------------------------------------------------------------------------
GRANT SELECT ON cuentas, pagos_recibidos, gastos_fijos, usuarios TO rol_cliente;

-- El analista: exactamente lo mismo, solo lectura.
GRANT SELECT ON cuentas, pagos_recibidos, gastos_fijos, usuarios TO rol_analista;

-- ----------------------------------------------------------------------------
-- La bitácora es el caso especial: todos pueden ESCRIBIR en ella, nadie
-- puede leerla ni borrarla.
--
-- Es a propósito y es como una urna de votación: puedes meter papeles, no
-- puedes sacarlos ni ver los de otros. Así un atacante que entre con la
-- cuenta de un cliente no puede borrar el rastro de lo que hizo.
--
-- Solo un auditor externo (un rol aparte que no creamos aquí) debería poder
-- leerla.
-- ----------------------------------------------------------------------------
GRANT INSERT ON bitacora TO rol_cliente, rol_analista;

-- ----------------------------------------------------------------------------
-- La aplicación necesita poder adoptar cualquiera de los dos roles, según
-- quién haya entrado. Lo hace con:  SET ROLE rol_cliente;
-- ----------------------------------------------------------------------------
GRANT rol_cliente, rol_analista TO app_banco;


-- ============================================================================
--  PARTE 6 — CÓMO SE PRUEBA QUE FUNCIONA
--
--  Escribir políticas sin probarlas es peor que no escribirlas, porque te da
--  una falsa sensación de seguridad. Estas 3 pruebas se corren a mano en
--  PostgreSQL y deben dar exactamente el resultado que dice el comentario.
-- ============================================================================

-- PRUEBA 1: María entra y pide TODOS los pagos de la tabla, sin filtrar nada.
--
--     SET ROLE rol_cliente;
--     SET LOCAL app.usuario_actual = 'maria';
--     SELECT DISTINCT id_usuario FROM pagos_recibidos;
--
--     RESULTADO ESPERADO: una sola fila, que dice 'maria'.
--     Aunque la consulta pidió todo, el RLS solo dejó pasar lo suyo.

-- PRUEBA 2: María intenta espiar a Carlos directamente.
--
--     SET ROLE rol_cliente;
--     SET LOCAL app.usuario_actual = 'maria';
--     SELECT * FROM cuentas WHERE id_usuario = 'carlos';
--
--     RESULTADO ESPERADO: cero filas.
--     Fíjate que NO da error de permisos. Simplemente no hay nada. Eso es
--     mejor que un error: un mensaje de "acceso denegado" le confirmaría al
--     atacante que Carlos existe. El silencio no le confirma nada.

-- PRUEBA 3: el analista pide lo mismo.
--
--     SET ROLE rol_analista;
--     SET LOCAL app.rol_actual = 'admin';
--     SELECT DISTINCT id_usuario FROM pagos_recibidos;
--
--     RESULTADO ESPERADO: las tres, 'maria', 'carlos' y 'ana'.


-- ============================================================================
--  PARTE 7 — LO QUE FALTARÍA PARA UN BANCO DE VERDAD
--
--  Este proyecto es una demo de hackathon. Somos honestos sobre lo que NO
--  tiene, porque decir "esto ya es seguro" sería mentira:
--
--   1. CIFRADO EN REPOSO: el archivo de la base está en texto plano. Quien
--      copie banco.db se lleva todo (menos las contraseñas, que sí están
--      revueltas). En producción se usa cifrado de disco o pgcrypto.
--
--   2. HTTPS: hoy el token viaja sin cifrar entre la página y el servidor.
--      En una red pública cualquiera lo intercepta y se hace pasar por ti.
--
--   3. SEGUNDO FACTOR (2FA): con solo la contraseña basta para entrar.
--      Un código del celular haría que una contraseña robada no sirva sola.
--
--   4. ROTACIÓN DE TOKENS: el nuestro dura 30 minutos fijos. Lo correcto es
--      un token corto (5 min) más uno de refresco que se renueve.
--
--   5. LÍMITE DE PETICIONES POR IP: bloqueamos por cuenta, pero alguien podría
--      probar una contraseña en miles de cuentas distintas ("password spraying")
--      sin llegar al límite de ninguna.
--
--   6. BITÁCORA A PRUEBA DE MANIPULACIÓN: la nuestra vive en la misma base.
--      Quien tenga acceso de escritura podría alterarla. Lo correcto es
--      mandarla a otro servidor, encadenada con hashes.
-- ============================================================================
