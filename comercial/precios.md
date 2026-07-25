# Precios — licencia, implementación y comisión de canal

## Punto de partida: lo que ya está definido

El precio de **licencia** ya vive en el código (`mvpm/licensing.py`), no hay que inventarlo:

| Plan | Precio | Cupo IA/mes |
|---|---|---|
| Demo / prueba | USD 0 | 20 consultas |
| Professional | **USD 9 / usuario / mes** | 1.000 |
| Professional anual | **USD 90 / usuario / año** (12 meses al precio de 10) | 1.000 |
| Enterprise | a cotizar por proyecto | ilimitado |

Lo que **no** está definido —y es lo que bloquea la conversación con un socio— es
el precio del **servicio de implementación**.

---

## ⚠️ El hallazgo importante: la licencia sola no financia un canal

Hagamos la cuenta con una empresa de 25 usuarios:

- Licencia anual: 25 × USD 90 = **USD 2.250/año**
- Comisión del socio al 20%: **USD 450/año**, cobrados de a poco

**Ningún socio de canal mueve un dedo por eso.** Un consultor de Power BI que
factura por hora no va a arriesgar una relación con su cliente por USD 450 diferidos.

La implementación es lo que hace viable el modelo de canal: es un monto grande,
al principio, y cobrado de una vez. Sin ella, el socio no tiene incentivo — y vos
tampoco tenés ingreso en los primeros 12 meses.

> **Conclusión: el ingreso de corto plazo es el servicio. La licencia es la cola larga.**
> Al menos hasta que haya volumen. Vender esto como "SaaS de USD 9" a tu escala
> actual no es un negocio; vender implementación con licencia adentro, sí.

---

## Las tres líneas de ingreso

| Línea | Cuándo se cobra | Quién lo hace |
|---|---|---|
| **1. Implementación** | Una vez, al inicio | Vos (o el socio) |
| **2. Licencia** | Mensual o anual | Automático |
| **3. Soporte y evolución** | Mensual, opcional | Vos |

---

## Línea 1 — Implementación: los tres paquetes

Alcance basado en lo que el producto realmente necesita para arrancar en una
empresa: instalación, conexión al origen de datos, carga de organigrama,
configuración de gobernanza/PMBOK, conector de Power BI y capacitación.

> **Parámetros confirmados por vos:** implementación típica de **10-25 horas**,
> valor hora objetivo **USD 30-50**, modelo **proyecto + mantenimiento mensual**.
> Todo lo que sigue está calculado con un piso de **USD 40/h** (mitad del rango).

| | **Básico** | **Estándar** | **Completo** |
|---|---|---|---|
| Instalación y puesta en marcha | ✅ | ✅ | ✅ |
| Carga de proyectos existentes | Hasta 20 | Hasta 100 | Sin límite |
| Organigrama y responsables | — | ✅ | ✅ |
| Conexión a ERP / base existente | — | 1 origen | Hasta 3 |
| Conector Power BI configurado | ✅ | ✅ | ✅ |
| Gobernanza / PMBOK a medida | — | Preestablecido | A medida |
| Capacitación | 1 sesión (2h) | 2 sesiones | 4 sesiones + manual |
| **Horas estimadas** | **~10 h** | **~18 h** | **~32 h** |

### La lista de precios

| Paquete | Horas | Costo a USD 40/h | **Precio de lista** | Margen |
|---|---|---|---|---|
| Básico | 10 h | USD 400 | **USD 600** | 1,5× |
| Estándar | 18 h | USD 720 | **USD 1.200** | 1,7× |
| Completo | 32 h | USD 1.280 | **USD 2.200** | 1,7× |

Ese margen de 1,5-1,7× no es ganancia extra: cubre lo que **siempre** aparece y
nunca está en la estimación — el dato sucio, el ERP sin esquema documentado, la
reunión que se repite, y el tiempo comercial que no facturás.

### ⚠️ La regla que evita que trabajes gratis

**La comisión del socio sale de tu precio, no se suma arriba.** Entonces el piso
real no es `horas × tu hora`, es:

```
precio mínimo = (horas × valor hora) ÷ (1 − comisión)
```

Verificación del paquete Estándar con un socio al 25%:

| | |
|---|---|
| Precio de lista | USD 1.200 |
| − comisión 25% | − USD 300 |
| **Te queda** | **USD 900** por 18 h = **USD 50/h** ✅ |

Queda por encima de tu piso de USD 40. **Si algún día negociás una comisión del
40%, el Estándar a USD 1.200 te deja USD 720 → USD 40/h justo, sin colchón.** Ahí
subís el precio o bajás la comisión — no las dos cosas.

**No cotices por hora.** Cotizá precio cerrado: el cliente compra un resultado, y
si mejorás el proceso y tardás menos, ganás más. Por hora, mejorar te castiga.

**Por qué cerrado y no por hora:**
1. El cliente compra un resultado, no tu tiempo. Cotizar horas te convierte en proveedor de horas.
2. Si mejorás el proceso y tardás menos, ganás más. Por hora, mejorar te castiga.
3. Elimina la discusión de "¿por qué tantas horas?".
4. El margen sobre el costo cubre lo que **siempre** aparece: el dato sucio, el
   ERP que no documenta su esquema, la reunión que se repite.

---

## Línea 3 — Soporte y evolución (el que más importa a largo plazo)

**USD 150-400/mes** según tamaño, aparte de la licencia. Incluye soporte,
ajustes menores, un reporte nuevo por trimestre.

Es el ingreso que se acumula: 10 clientes en soporte = USD 1.500-4.000/mes
recurrente, sin vender nada nuevo. Ofrecelo **siempre**, desde el primer cliente.

---

## Cómo queda un negocio completo (ejemplo, 25 usuarios)

| Concepto | Año 1 |
|---|---|
| Implementación Estándar | USD 1.200 |
| Licencia (25 × USD 90) | USD 2.250 |
| Mantenimiento (USD 250 × 12) | USD 3.000 |
| **Total año 1** | **USD 6.450** |
| **Recurrente año 2+** | **USD 5.250/año** |

Mirá la proporción: **la implementación es solo el 19% del año 1**. El resto es
recurrente. Por eso elegiste bien el modelo — la implementación te abre la puerta,
el mantenimiento es el negocio.

### Lo que se lleva el socio de canal

Con las comisiones de `socios-de-canal.md` (referido acompañado, 25% + 10% recurrente):

| Concepto | Comisión |
|---|---|
| 25% de implementación | USD 300 |
| 10% de licencia + mantenimiento año 1 | USD 525 |
| **Total año 1 por un cliente** | **~USD 825** |
| Recurrente año 2+ | ~USD 525/año |

**Ese número sí mueve a un socio.** Es lo que le podés decir en la reunión:
> *"Por cada cliente que me presentes, son unos USD 800 el primer año y USD 500
> por año mientras el cliente siga. Con tres clientes tuyos ya es un ingreso real."*

Notá que **la mayor parte de su comisión es recurrente, no de la implementación**.
Eso juega a tu favor: al socio le conviene que el cliente se quede contento y siga
pagando, no cerrar una venta y desaparecer.

---

## Reglas para no romper el precio

**1. Nunca cotices en la primera reunión.**
Necesitás saber: cuántos usuarios, cuántos proyectos activos, de dónde sale el dato
hoy. Sin esas tres respuestas, cualquier número es un disparo al aire.
> *"Te lo mando por escrito mañana con el alcance definido."*

**2. Mostrá tres opciones, no una.**
Con un solo precio la pregunta es "sí o no". Con tres es "cuál". Casi todos eligen
el del medio — por eso Estándar es el que querés vender.

**3. No bajes el precio: bajá el alcance.**
Si dice que es caro, no descuentes. Sacá el conector al ERP y ofrecé Básico. El
precio por unidad de valor tiene que quedar intacto, o el próximo cliente se entera.

**4. Para los primeros 2 clientes, canjeá precio por prueba social.**
Está bien cobrar menos al principio — pero **cobrá algo** (lo gratis no se usa ni
se valora) y pedí a cambio algo que valga:
> *"Te hago la implementación a mitad de precio. A cambio te pido: usarlo de caso
> de referencia con nombre, y una reseña cuando lleves tres meses."*

Eso vale más que la diferencia de plata, y alimenta directo el módulo de reseñas
verificadas del producto.

**5. Precio en USD, cobro en pesos al tipo de cambio del día.**
Estándar para software en Uruguay y te protege de la devaluación en proyectos
que duran meses.

---

## Estado de la lista

| Definido | Valor |
|---|---|
| Valor hora piso | USD 40 (rango 30-50) |
| Implementación | 600 / 1.200 / 2.200 |
| Mantenimiento mensual | USD 150-400 |
| Licencia | USD 9 usuario/mes · USD 90 anual |
| Comisión de canal | 25% implementación + 10% recurrente |

**La lista está cerrada. Ya podés abrir la conversación con socios.**

### Dos cosas para hacer en paralelo (no bloquean nada)

- [ ] **Cronometrá la primera implementación real.** Tu estimación de 10-25 h es
      una hipótesis razonable, no un dato — nadie acierta la primera. Anotá las
      horas reales del primer cliente y recalculá la lista con eso. Si te lleva
      35 h en vez de 18, el Estándar a USD 1.200 te deja USD 26/h después de
      comisión, muy por debajo del piso.
- [ ] **Contrastá las tres cifras con 2-3 colegas independientes** en Uruguay.
      Los valores de hora que usé son estimaciones de referencia, no un dato de
      mercado verificado. Es una llamada de 15 minutos.

> Si la primera implementación se va muy por encima de 25 h, el problema no es el
> precio: es que el producto todavía necesita trabajo manual que debería ser
> automático. Eso es información de producto, no de ventas — y vale más que la
> diferencia de plata.
