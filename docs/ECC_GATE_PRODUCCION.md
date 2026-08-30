# MV Project Management — Gate de producción ECC

> Puntaje bajo la rúbrica de `.claude/skills/ecc/SKILL.md` (ECC v2.2.0,
> skill `production-audit`). **Evidencia ejecutada o no cuenta.**

**Veredicto: 91/100 → 9/10. Sin bloqueantes. La suite más grande de los
productos MV (932 tests) en verde, y las cinco funciones de pago probadas una
por una como las corre CI.**

## Evidencia ejecutada

| Verificación | Comando | Resultado |
|---|---|---|
| Linter | `ruff check .` | ✅ `All checks passed!` |
| Suite Python | `pytest tests/ -q` | ✅ **932 pasaron**, 5 skip, 0 fallas, 75 s |
| Pago: verify_payment | `node tests/test_verify_payment.js` | ✅ |
| Pago: licencias | `node tests/test_licencias.js` | ✅ |
| Pago: checkout | `node tests/test_checkout.js` | ✅ |
| Pago: rotación de claves | `node tests/test_rotar_claves.js` | ✅ |
| Pago: métricas | `node tests/test_metricas.js` | ✅ |
| Health check | `/api/salud` y `/health` | ✅ presentes |
| Secretos versionados | `git ls-files \| grep -E '\.env$\|\.pem\|\.keystore'` | ✅ ninguno |

Los cinco de pago se corrieron **igual que CI**: uno por uno, no con
`node --test`. El repo no tiene `package-lock.json`, así que `npm ci` no
aplica acá y CI tampoco lo usa para este paso.

## Por qué 9 y no 10

Ningún tope duro aplica: las funciones de pago tienen su propio gate, hay
rotación de claves de licencia con test, y hay dos health checks.

Lo que falta:

1. **El job de interfaz de escritorio.** `tests.yml` tiene un job de React +
   lanzador que no se corrió acá. 932 tests de Python no prueban que la
   ventana abra.
2. **5 tests salteados.** Un skip permanente no cuida nada. Vale saber cuáles
   son y por qué.
3. **Sin `package-lock.json`.** Las dependencias de Node no están fijadas: dos
   instalaciones en fechas distintas pueden traer versiones distintas de lo
   que firma y valida licencias. Para un producto que se vende, la
   reproducibilidad del build de pagos importa.
4. **Sin humo post-deploy.**

## Arreglos de alto valor

1. Commitear un `package-lock.json`. Es el que más pesa: fija el árbol de
   dependencias del código que toca plata.
2. Revisar los 5 skips.

## Próxima acción

Antes de cada push: `ruff check . && pytest tests/ -q`, más los cinco tests de
pago. Antes de un release, además el job de escritorio.
