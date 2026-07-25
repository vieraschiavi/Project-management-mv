# Precios — licencia, implementación y comisión de canal

## ⚠️ Leer primero: dos respuestas que se contradicen

Contestaste dos veces sobre lo mismo, con números muy distintos:

| Variable | Primera respuesta | Segunda respuesta |
|---|---|---|
| Horas de implementación | 10-25 h | **60-100 h** |
| Valor de tu hora | USD 30-50 | **USD 15-25** |

No es un error tuyo: las preguntas no eran iguales. La segunda incluía
explícitamente **"relevamiento"**, y ahí está casi toda la diferencia. Nadie
cuenta el relevamiento cuando estima "cuánto lleva instalar".

**Uso 80 horas como número de planificación** (medio del segundo rango), porque
es la estimación que incluye el trabajo completo. Si la primera resulta ser la
correcta, el error te favorece; si planificás con la primera y la real es la
segunda, trabajás dos meses gratis.

### Y sobre el valor hora, las dos respuestas son correctas

- **USD 20/h** es lo que vale tu hora **hoy**, como empleado. Es tu costo de oportunidad.
- **USD 40/h** es lo que tenés que cobrar **como independiente** para no ir para atrás.

No es codicia, es aritmética: como freelance no cobrás las horas no facturables
(vender, cotizar, administrar), no tenés licencia paga ni aguinaldo, y asumís el
riesgo de que el cliente no pague. La regla estándar es **×2 sobre el equivalente
en relación de dependencia**. Tu segunda respuesta (20) y tu primera (30-50)
coinciden perfectamente con esa cuenta.

> **Piso de trabajo: USD 40/h.** Por debajo de eso, te conviene quedarte en tu
> trabajo actual y no tocar el teléfono.

---

## 🔴 El problema: el precio que publiqué ayer pierde plata

La lista anterior ponía el paquete Estándar en USD 1.200. Con los números reales:

| | |
|---|---|
| Precio de lista | USD 1.200 |
| − comisión del socio (25%) | − USD 300 |
| Te queda | USD 900 |
| Horas reales | 80 h |
| **Tu hora efectiva** | **USD 11,2/h** |

**Eso es casi la mitad de lo que ganás hoy como empleado**, con todo el riesgo
encima. Para cobrar tus USD 40/h con 80 horas y 25% de comisión, el precio tendría
que ser **USD 4.270**, no 1.200.

Esa lista quedó anulada. Lo que sigue la reemplaza.

---

## 🔴 El problema más grande: no te da el tiempo

Esto importa más que el precio. Vos hacés esto **en paralelo a un trabajo full-time**.

| | |
|---|---|
| Horas disponibles por semana (noches + fines de semana) | ~10-12 h |
| Horas por mes | ~45 h |
| Horas por implementación | **80 h** |
| **Tiempo real por cliente** | **~2 meses de todas tus noches** |

Con soporte de clientes anteriores comiéndote horas, el techo real es **4 o 5
clientes por año**. Y eso trabajando todas las noches, sin margen para nada más.

**Esto rompe el modelo de canal.** Un socio que te trae 6 clientes te satura y te
deja quedando mal con la mitad. No podés vender por canal algo que consume 80
horas tuyas por unidad.

> **La conclusión incómoda: el problema no es el precio, son las 80 horas.**
> Si implementar requiere un mes de trabajo experto, el producto todavía no está
> terminado — necesita un consultor al lado para ser usable. Eso es trabajo de
> producto, no de ventas, y es la palanca más importante que tenés.

---

## Lo que ya está definido (no se toca)

Precio de **licencia**, ya en el código (`mvpm/licensing.py`):

| Plan | Precio |
|---|---|
| Demo / prueba | USD 0 (20 consultas IA/mes) |
| Professional | **USD 9 / usuario / mes** |
| Professional anual | **USD 90 / usuario / año** |
| Enterprise | a cotizar |

Y un hallazgo que sigue vigente: **la licencia sola no financia un canal.** Una
empresa de 25 usuarios deja USD 450/año de comisión al 20%, diferidos. Ningún
socio se mueve por eso. El servicio es lo que hace viable el modelo.

---

## La lista nueva: una escalera, no un paquete

La respuesta a "accesible para entrar" **no es cobrar poco por 80 horas**. Es
tener un producto chico y honesto que de verdad lleve poco tiempo.

### 0 · Relevamiento — USD 350 · 8-10 h

Diagnóstico pago: qué datos hay, dónde están, qué se puede conectar. Entregás un
documento de alcance y **una cotización cerrada para el resto**.

**Esto es lo más importante de toda la lista.** Nunca des precio cerrado por una
integración antes del relevamiento — es la forma número uno de perder plata en
consultoría. Y se descuenta si contratan, así que al cliente no le duele.

> *"El relevamiento son USD 350 y te queda el informe sea que sigamos o no. Si
> seguimos, te lo descuento de la implementación."*

### 1 · Arranque — USD 700 · 12-15 h ← **tu producto de entrada**

Sin integración al ERP. El cliente importa de Excel/CSV, configuración estándar,
conector de Power BI, una capacitación.

Este es el paquete accesible, el que vende el socio de canal, y el que tiene que
funcionar sin que vos estés un mes. Verificación: USD 700 − 25% = 525 ÷ 14 h =
**USD 37/h**. Justo en el piso — sirve para entrar, no para vivir.

### 2 · Integración — desde USD 4.500 · 60-100 h

Conexión al ERP, migración de histórico, gobernanza a medida, capacitación por área.
**Solo se cotiza después del relevamiento**, con número cerrado sobre alcance escrito.

Verificación a 80 h: USD 4.500 − 25% = 3.375 ÷ 80 h = **USD 42/h**. ✅

> Si el precio te suena alto, mirá la cuenta al revés: es un mes de trabajo
> profesional. USD 4.500 por un mes es un sueldo razonable, no un abuso.

### 3 · Mantenimiento — USD 150-400/mes

Soporte, ajustes menores, un reporte nuevo por trimestre. **Ofrecelo siempre**,
desde el primer cliente. Es el ingreso que se acumula sin vender nada nuevo.

---

## Cómo queda un negocio (25 usuarios, con Arranque)

| Concepto | Año 1 |
|---|---|
| Relevamiento | USD 350 |
| Arranque | USD 700 |
| Licencia (25 × USD 90) | USD 2.250 |
| Mantenimiento (USD 250 × 12) | USD 3.000 |
| **Total año 1** | **USD 6.300** |
| **Recurrente año 2+** | **USD 5.250/año** |

El servicio inicial es el 17% del año 1. **El negocio es el recurrente** — que es
exactamente el modelo que elegiste.

### Comisión del socio (25% servicio + 10% recurrente)

| Concepto | Comisión |
|---|---|
| 25% de relevamiento + arranque | USD 263 |
| 10% de licencia + mantenimiento | USD 525 |
| **Año 1 por cliente** | **~USD 790** |
| Recurrente año 2+ | ~USD 525/año |

Sigue siendo el número que mueve a un socio: **~USD 800 el primer año, ~USD 500
por año mientras el cliente siga.** Y la mayor parte es recurrente, así que al
socio le conviene que el cliente se quede contento.

---

## Tu posición: accesible para entrar, sin regalar trabajo

Elegiste entrar accesible. Correcto sin cartera — pero se hace así:

**1. Accesible = paquete chico, no precio bajo por trabajo grande.**
Vendé Arranque a USD 700, no Integración a USD 700.

**2. Para los primeros 2 clientes, canjeá precio por prueba social.**
Cobrá algo (lo gratis no se usa ni se valora) y pedí a cambio algo que valga:
> *"Te hago el arranque a mitad de precio. A cambio: usarte de caso de referencia
> con nombre, y una reseña a los tres meses."*

Eso alimenta directo el módulo de reseñas verificadas del producto.

**3. Descuento con fecha de vencimiento explícita.**
> *"Este precio es de lanzamiento, para los primeros tres clientes."*
Sin eso, el precio bajo es tu precio para siempre y el cliente se siente estafado
cuando subís.

**4. Bajá alcance, nunca precio.**
Si dice que es caro, sacá la integración y ofrecé Arranque. El precio por unidad
de valor queda intacto.

**5. Nunca cotices en la primera reunión.** Vendé el relevamiento.

**6. Precio en USD, cobro en pesos al tipo de cambio del día.**

---

## Lo que de verdad mueve la aguja: bajar las 80 horas

Cada hora que le sacás a la implementación vale más que cualquier ajuste de precio.
De 80 h a 25 h, el mismo paquete a USD 4.500 pasa de USD 42/h a **USD 135/h** — y
recién ahí el canal escala, porque un socio te puede traer 10 clientes.

Candidatos concretos, en orden de impacto:

- [ ] **Conectores estándar** para los 2-3 ERP más comunes en PyMEs uruguayas, en
      vez de integración a medida cada vez. Es donde se van la mayoría de las horas.
- [ ] **Importador guiado** que el cliente pueda correr solo (mapeo de columnas
      asistido), en vez de que migres vos.
- [ ] **Plantillas de gobernanza por rubro** (construcción, software, pharma) para
      no configurar PMBOK desde cero en cada empresa.
- [ ] **Capacitación grabada** en vez de sesiones en vivo repetidas. Ya tenés el
      video y el tutorial: faltaría el recorrido por rol.

## Antes de cerrar la lista

- [ ] **Cronometrá el primer relevamiento y el primer arranque de verdad.** Las
      80 h son tu estimación, no un dato. El relevamiento pago existe justamente
      para que midas sin arriesgar plata.
- [ ] **Contrastá las cifras con 2-3 colegas independientes.** Los valores de hora
      son de referencia, no un dato de mercado verificado.
