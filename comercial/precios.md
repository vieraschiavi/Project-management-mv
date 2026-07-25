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

| | **Básico** | **Estándar** | **Completo** |
|---|---|---|---|
| Instalación y puesta en marcha | ✅ | ✅ | ✅ |
| Carga de proyectos existentes | Hasta 20 | Hasta 100 | Sin límite |
| Organigrama y responsables | — | ✅ | ✅ |
| Conexión a ERP / base existente | — | 1 origen | Hasta 3 |
| Conector Power BI configurado | ✅ | ✅ | ✅ |
| Gobernanza / PMBOK a medida | — | Preestablecido | A medida |
| Capacitación | 1 sesión (2h) | 2 sesiones | 4 sesiones + manual |
| **Horas estimadas** | **10-14 h** | **22-30 h** | **45-60 h** |

### Cuánto cobrar por eso

> 🔴 **Estos valores de hora son estimaciones de referencia para el mercado
> uruguayo, no un dato verificado.** Validalos con 2 o 3 colegas que facturen
> como independientes antes de fijar tu lista.

| Tu hora | Básico (12h) | Estándar (26h) | Completo (52h) |
|---|---|---|---|
| USD 25/h | ~USD 300 | ~USD 650 | ~USD 1.300 |
| USD 35/h | ~USD 420 | ~USD 910 | ~USD 1.820 |
| USD 45/h | ~USD 540 | ~USD 1.170 | ~USD 2.340 |

**Pero no cotices por hora.** Cotizá **precio cerrado por paquete**, redondeado
hacia arriba:

| Paquete | Precio de lista sugerido |
|---|---|
| Básico | **USD 600** |
| Estándar | **USD 1.500** |
| Completo | **USD 3.000** |

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
| Implementación Estándar | USD 1.500 |
| Licencia (25 × USD 90) | USD 2.250 |
| Soporte (USD 250 × 12) | USD 3.000 |
| **Total año 1** | **USD 6.750** |
| **Recurrente año 2+** | **USD 5.250/año** |

### Lo que se lleva el socio de canal

Con las comisiones de `socios-de-canal.md` (referido acompañado, 25% + 10% recurrente):

| Concepto | Comisión |
|---|---|
| 25% de implementación | USD 375 |
| 10% de licencia + soporte año 1 | USD 525 |
| **Total año 1 por un cliente** | **~USD 900** |
| Recurrente año 2+ | ~USD 525/año |

**Ese número sí mueve a un socio.** Es lo que le podés decir en la reunión:
> *"Por cada cliente que me presentes, son unos USD 900 el primer año y USD 500
> por año mientras el cliente siga. Con tres clientes tuyos ya es un ingreso real."*

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

## Lo único que falta que puedas decidir solo vos

- [ ] **Tu valor hora real.** Fijate cuánto ganás por hora en tu trabajo actual y
      no cobres menos que eso como independiente — asumís más riesgo, no menos.
- [ ] **Validar las tres cifras de lista** (600 / 1.500 / 3.000) con 2-3 colegas
      que facturen como independientes en Uruguay. Es una llamada de 15 minutos
      y te evita fijar la lista con datos míos que son estimados.

Con eso, la lista queda cerrada y ya podés abrir la conversación con socios.
