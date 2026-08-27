# © 2026 Martín Viera. Todos los derechos reservados.
"""Plantillas de gobernanza por rubro, alineadas a PMBOK.

Sin esto, cada implementación arranca en blanco: hay que sentarse con el cliente
a definir etapas, entregables y quién aprueba qué. Son horas de consultoría que
se repiten casi iguales entre empresas del mismo rubro, porque una obra vial y
otra obra vial se gobiernan parecido.

Cada plantilla trae:

* **Etapas con puerta de salida.** Qué tiene que estar listo y quién firma para
  pasar a la siguiente. Es lo que convierte una lista de tareas en gobernanza.
* **Riesgos típicos del rubro**, cada uno atado a su área de PMBOK, para que el
  registro de riesgos no arranque vacío.
* **Indicadores** que en ese rubro se miran de verdad.
* **Normativa aplicable**, que es lo que más tiempo lleva averiguar.

Tres aclaraciones sobre lo que esto es y lo que no:

1. Es un **punto de partida discutible**, no una norma. La plantilla se carga y
   después se edita con el cliente; queda versionada como cualquier definición.
2. Las **referencias normativas son orientativas y de Uruguay** salvo que digan
   otra cosa. Las normas cambian y cada empresa tiene su interpretación: hay que
   confirmarlas con quien lleva calidad, legales o compliance ahí adentro. El
   producto no da asesoramiento legal.
3. El **peso de las áreas de PMBOK** dice dónde poner el esfuerzo en ese rubro,
   no qué áreas ignorar. Las diez aplican siempre.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import db, pmbok

ENTIDAD = "plantilla_rubro"

# Claves de área válidas, tomadas de pmbok.py para que no se desincronicen.
_AREAS_VALIDAS = {a["clave"] for a in pmbok.AREAS}
_GRUPOS_VALIDOS = {g["clave"] for g in pmbok.GRUPOS_PROCESO}


@dataclass(frozen=True)
class Etapa:
    clave: str
    nombre: str
    grupo_pmbok: str                  # inicio | planificacion | ejecucion | monitoreo | cierre
    objetivo: str
    entregables: tuple[str, ...]
    criterio_salida: str
    aprueba: str


@dataclass(frozen=True)
class Riesgo:
    titulo: str
    area_pmbok: str
    senal_temprana: str
    mitigacion: str


@dataclass(frozen=True)
class Plantilla:
    clave: str
    rubro: str
    resumen: str
    etapas: tuple[Etapa, ...]
    roles: tuple[tuple[str, str], ...]          # (rol, qué decide)
    riesgos: tuple[Riesgo, ...]
    indicadores: tuple[str, ...]
    normativa: tuple[str, ...]
    portafolios_sugeridos: tuple[str, ...]
    areas_criticas: tuple[str, ...]             # claves de pmbok.AREAS
    nota: str = ""


# ---------------------------------------------------------------- construcción

CONSTRUCCION = Plantilla(
    clave="construccion",
    rubro="Construcción e infraestructura",
    resumen="Obra civil, vial e infraestructura. Se gobierna por certificación de "
            "avance y por seguridad: el riesgo de accidente es el que puede parar "
            "la obra entera.",
    etapas=(
        Etapa("anteproyecto", "Anteproyecto", "inicio",
              "Definir qué se va a construir y si cierra económicamente.",
              ("Memoria descriptiva", "Estimación de costo ±30%", "Estudio de suelos preliminar",
               "Análisis de factibilidad"),
              "El sponsor aprueba seguir invirtiendo en el proyecto ejecutivo.",
              "Sponsor / Dirección"),
        Etapa("ejecutivo", "Proyecto ejecutivo", "planificacion",
              "Llevar el diseño a nivel constructivo, con cómputo y presupuesto firme.",
              ("Planos ejecutivos", "Cómputo métrico", "Presupuesto detallado",
               "Cronograma con ruta crítica", "Pliego de especificaciones técnicas"),
              "Presupuesto y plazo aprobados; permisos municipales iniciados.",
              "Dirección de obra"),
        Etapa("permisos", "Permisos y habilitaciones", "planificacion",
              "Obtener todo lo que habilita a empezar sin riesgo de clausura.",
              ("Permiso de construcción", "Aviso de obra a BPS",
               "Plan de seguridad e higiene", "Estudio de impacto ambiental si corresponde"),
              "Permisos otorgados y obra registrada.",
              "Responsable técnico"),
        Etapa("licitacion", "Contratación", "planificacion",
              "Elegir contratistas y cerrar condiciones.",
              ("Pliego de licitación", "Comparativa de ofertas", "Contratos firmados",
               "Garantías de cumplimiento"),
              "Contratos firmados con plazos y penalidades definidas.",
              "Compras / Dirección"),
        Etapa("obra", "Ejecución de obra", "ejecucion",
              "Construir según proyecto, controlando avance, costo y seguridad.",
              ("Certificados de avance mensuales", "Libro de obra al día",
               "Registro de no conformidades", "Órdenes de cambio documentadas"),
              "Obra terminada conforme a planos y con observaciones levantadas.",
              "Dirección de obra"),
        Etapa("recepcion_provisoria", "Recepción provisoria", "cierre",
              "Recibir la obra dejando registrado lo que falta corregir.",
              ("Acta de recepción provisoria", "Lista de observaciones (punch list)",
               "Planos conforme a obra"),
              "Acta firmada; arranca el período de garantía.",
              "Comitente"),
        Etapa("recepcion_definitiva", "Recepción definitiva", "cierre",
              "Cerrar el contrato una vez vencida la garantía.",
              ("Acta de recepción definitiva", "Liberación de garantías",
               "Manual de mantenimiento", "Lecciones aprendidas"),
              "Garantías liberadas y contrato cerrado.",
              "Comitente / Legales"),
    ),
    roles=(
        ("Comitente", "Aprueba adicionales y firma las recepciones."),
        ("Dirección de obra", "Certifica avance y acepta o rechaza trabajos."),
        ("Responsable técnico", "Responde ante el municipio por la obra."),
        ("Técnico prevencionista", "Puede parar la obra por riesgo de accidente."),
        ("Capataz / Jefe de obra", "Ejecuta el día a día y reporta avance real."),
    ),
    riesgos=(
        Riesgo("Accidente de trabajo", "riesgos",
               "Observaciones de seguridad sin levantar, o personal sin protección.",
               "Plan de seguridad vigente, charlas diarias y auditorías del prevencionista."),
        Riesgo("Adicionales de obra no controlados", "costos",
               "Trabajos ejecutados sin orden de cambio firmada.",
               "Nada se ejecuta sin orden de cambio aprobada por escrito."),
        Riesgo("Atraso por clima", "cronograma",
               "Días perdidos acumulados por encima de lo previsto en el cronograma.",
               "Prever días de lluvia por estación y dejar holgura en tareas a la intemperie."),
        Riesgo("Faltante o suba de materiales", "adquisiciones",
               "Plazos de entrega que se estiran o cotizaciones que vencen antes de comprar.",
               "Compras anticipadas de lo crítico y cláusulas de ajuste en los contratos."),
        Riesgo("Diferencias con el proyecto ejecutivo", "alcance",
               "Consultas recurrentes de obra por planos incompletos o contradictorios.",
               "Revisión cruzada de planos antes de licitar."),
    ),
    indicadores=("Avance físico vs. avance certificado", "Desvío de plazo por hito",
                 "Costo ejecutado vs. presupuestado por rubro",
                 "Accidentes y días perdidos", "Adicionales aprobados sobre contrato original"),
    normativa=("Ley 16.074 — seguro de accidentes de trabajo (Uruguay)",
               "Decreto 125/014 — seguridad e higiene en la industria de la construcción",
               "Registro de obra y aportes al BPS",
               "Normativa municipal de construcción de la intendencia que corresponda",
               "Normas UNIT aplicables a materiales y ensayos"),
    portafolios_sugeridos=("Obra vial", "Obra civil", "Instalaciones", "Mantenimiento"),
    areas_criticas=("costos", "cronograma", "riesgos", "adquisiciones"),
)

# ------------------------------------------------------------------- software

SOFTWARE = Plantilla(
    clave="software",
    rubro="Software y tecnología",
    resumen="Desarrollo de producto y proyectos de TI. El riesgo dominante no es "
            "el costo sino el alcance móvil y lo que se rompe al desplegar.",
    etapas=(
        Etapa("descubrimiento", "Descubrimiento", "inicio",
              "Entender el problema antes de proponer solución.",
              ("Problema y usuarios definidos", "Criterios de éxito medibles",
               "Alcance mínimo viable", "Estimación gruesa"),
              "El sponsor acuerda qué problema se resuelve y cómo se mide.",
              "Sponsor / Product Owner"),
        Etapa("diseno", "Diseño técnico y funcional", "planificacion",
              "Definir cómo se construye y qué se integra.",
              ("Arquitectura de la solución", "Modelo de datos",
               "Definición de integraciones", "Requisitos no funcionales"),
              "Arquitectura revisada; dependencias externas confirmadas.",
              "Líder técnico"),
        Etapa("construccion", "Construcción iterativa", "ejecucion",
              "Entregar incrementos usables y revisables.",
              ("Incrementos desplegables", "Pruebas automatizadas",
               "Documentación técnica mínima", "Demo por iteración"),
              "Funcionalidad acordada terminada y probada.",
              "Product Owner"),
        Etapa("uat", "Pruebas de aceptación", "monitoreo",
              "Que el usuario real confirme que sirve.",
              ("Casos de prueba de negocio", "Registro de incidencias",
               "Acta de aceptación del usuario"),
              "Incidencias críticas y altas cerradas; usuario firma aceptación.",
              "Referente de negocio"),
        Etapa("despliegue", "Despliegue", "ejecucion",
              "Poner en producción sin romper lo que funciona.",
              ("Plan de despliegue", "Plan de vuelta atrás", "Migración de datos probada",
               "Capacitación a usuarios"),
              "Sistema en producción con vuelta atrás disponible.",
              "Líder técnico / Operaciones"),
        Etapa("hipercuidado", "Hipercuidado", "monitoreo",
              "Acompañar de cerca las primeras semanas.",
              ("Guardia definida", "Tablero de incidencias",
               "Ajustes de posdespliegue"),
              "Incidencias estabilizadas por debajo del umbral acordado.",
              "Líder técnico"),
        Etapa("cierre_sw", "Traspaso a operación", "cierre",
              "Que el equipo de soporte pueda sostenerlo sin el equipo de proyecto.",
              ("Documentación de operación", "Traspaso a soporte",
               "Deuda técnica registrada", "Lecciones aprendidas"),
              "Soporte acepta el traspaso.",
              "Responsable de operaciones"),
    ),
    roles=(
        ("Sponsor", "Aprueba presupuesto y prioridades."),
        ("Product Owner", "Decide qué entra y qué no en cada entrega."),
        ("Líder técnico", "Decide la arquitectura y acepta la calidad técnica."),
        ("Referente de negocio", "Valida que la solución sirva para trabajar."),
        ("Operaciones / Soporte", "Acepta o rechaza el traspaso a producción."),
    ),
    riesgos=(
        Riesgo("Alcance móvil", "alcance",
               "Pedidos nuevos que entran sin sacar nada a cambio.",
               "Backlog priorizado y único: lo que entra desplaza a algo."),
        Riesgo("Dependencia de un tercero", "adquisiciones",
               "Una integración o proveedor que no confirma fechas.",
               "Confirmar disponibilidad de la API o el proveedor antes de comprometer el plazo."),
        Riesgo("Deuda técnica acumulada", "calidad",
               "La velocidad de entrega baja iteración a iteración.",
               "Reservar capacidad fija por iteración para deuda técnica."),
        Riesgo("Datos personales mal tratados", "riesgos",
               "Datos productivos usados en ambientes de prueba.",
               "Anonimizar los datos de prueba y registrar la base ante la unidad reguladora."),
        Riesgo("Concentración de conocimiento", "recursos",
               "Una sola persona entiende un componente crítico.",
               "Revisión de código cruzada y documentación mínima obligatoria."),
    ),
    indicadores=("Incremento entregado por iteración", "Incidencias abiertas por severidad",
                 "Cobertura de pruebas automatizadas", "Tiempo de despliegue",
                 "Retrabajo sobre entregado"),
    normativa=("Ley 18.331 — protección de datos personales (Uruguay) y decreto 414/009",
               "ISO/IEC 27001 si la empresa maneja información sensible",
               "Reglamento GDPR si hay usuarios o clientes en la Unión Europea",
               "Licencias de los componentes de terceros que se incorporen"),
    portafolios_sugeridos=("Producto", "Integraciones", "Infraestructura", "Cumplimiento"),
    areas_criticas=("alcance", "calidad", "interesados", "riesgos"),
)

# ---------------------------------------------------------------- farmacéutica

FARMA = Plantilla(
    clave="farma",
    rubro="Farmacéutica, laboratorios y dispositivos médicos",
    resumen="Rubro regulado: la trazabilidad de la evidencia vale tanto como el "
            "resultado. Lo que no está documentado, para el regulador no pasó.",
    etapas=(
        Etapa("factibilidad", "Factibilidad", "inicio",
              "Confirmar viabilidad técnica y regulatoria antes de invertir.",
              ("Perfil del producto", "Análisis de vía regulatoria",
               "Evaluación de propiedad intelectual", "Estimación de inversión"),
              "Vía regulatoria definida y aprobada por Asuntos Regulatorios.",
              "Dirección técnica"),
        Etapa("desarrollo", "Desarrollo y formulación", "planificacion",
              "Llegar a una fórmula y un proceso reproducibles.",
              ("Protocolo de desarrollo", "Estudios de preformulación",
               "Especificaciones de producto", "Estudios de estabilidad iniciados"),
              "Fórmula y proceso congelados; estabilidad en curso.",
              "I+D / Dirección técnica"),
        Etapa("validacion", "Validación (IQ / OQ / PQ)", "ejecucion",
              "Demostrar documentalmente que equipos y procesos hacen lo que deben.",
              ("Plan maestro de validación", "Protocolos y reportes IQ, OQ y PQ",
               "Calificación de proveedores", "Validación de métodos analíticos"),
              "Validación aprobada por Aseguramiento de Calidad.",
              "Aseguramiento de Calidad"),
        Etapa("registro", "Registro sanitario", "monitoreo",
              "Obtener la autorización para comercializar.",
              ("Dossier de registro", "Datos de estabilidad",
               "Respuestas a observaciones de la autoridad"),
              "Registro otorgado por la autoridad sanitaria.",
              "Asuntos Regulatorios"),
        Etapa("transferencia", "Transferencia tecnológica", "ejecucion",
              "Pasar de escala piloto a producción industrial.",
              ("Protocolo de transferencia", "Lotes piloto y de validación",
               "Capacitación de planta", "Procedimientos operativos actualizados"),
              "Lotes de validación conformes a especificación.",
              "Producción / Calidad"),
        Etapa("lanzamiento", "Lanzamiento y farmacovigilancia", "cierre",
              "Producir en rutina y vigilar el comportamiento del producto.",
              ("Liberación del primer lote comercial",
               "Sistema de farmacovigilancia activo", "Plan de seguimiento post-comercialización"),
              "Primer lote liberado por la dirección técnica.",
              "Dirección técnica"),
    ),
    roles=(
        ("Dirección técnica", "Libera lotes y responde ante la autoridad sanitaria."),
        ("Aseguramiento de Calidad", "Aprueba validaciones y cierra desvíos. Puede frenar todo."),
        ("Asuntos Regulatorios", "Define la vía de registro y habla con la autoridad."),
        ("Producción", "Ejecuta según procedimientos aprobados."),
        ("I+D", "Desarrolla y documenta la evidencia técnica."),
    ),
    riesgos=(
        Riesgo("Desvío no documentado", "calidad",
               "Diferencias entre lo ejecutado y el procedimiento, sin registro.",
               "Sistema de desvíos y CAPA con plazos y responsable por cada uno."),
        Riesgo("Integridad de datos comprometida", "calidad",
               "Registros sin trazabilidad de quién los cargó o modificó.",
               "Principios ALCOA+ y registros con auditoría de cambios."),
        Riesgo("Observación de la autoridad en inspección", "riesgos",
               "Hallazgos repetidos en auditorías internas sin cerrar.",
               "Auditorías internas periódicas y cierre efectivo de hallazgos."),
        Riesgo("Atraso regulatorio", "cronograma",
               "Observaciones del regulador que reabren el expediente.",
               "Revisión del dossier antes de presentar y holgura en el cronograma."),
        Riesgo("Proveedor de insumo crítico no calificado", "adquisiciones",
               "Cambios de proveedor sin recalificación.",
               "Calificación formal y auditoría de proveedores críticos."),
    ),
    indicadores=("Desvíos abiertos y su antigüedad", "CAPA vencidas",
                 "Lotes rechazados sobre producidos", "Cumplimiento del plan de validación",
                 "Tiempo de respuesta a observaciones de la autoridad"),
    normativa=("Buenas Prácticas de Fabricación (GMP) exigidas por el MSP (Uruguay)",
               "Guías ICH Q7 a Q10 para calidad farmacéutica",
               "21 CFR Part 11 si se exporta a Estados Unidos (registros electrónicos)",
               "Principios ALCOA+ de integridad de datos",
               "Normativa de farmacovigilancia del MSP"),
    portafolios_sugeridos=("Desarrollo de producto", "Validaciones", "Registros",
                           "Mejora de planta"),
    areas_criticas=("calidad", "riesgos", "integracion", "adquisiciones"),
    nota="El regulador evalúa la evidencia documental, no la intención. Cada etapa "
         "tiene que dejar registro firmado y fechado.",
)

# ---------------------------------------------------------------- manufactura

MANUFACTURA = Plantilla(
    clave="manufactura",
    rubro="Manufactura e industria",
    resumen="Proyectos de producto, línea o planta. La puerta que importa es la "
            "de arranque de producción en serie: antes de eso todo es reversible, "
            "después no.",
    etapas=(
        Etapa("concepto", "Concepto y factibilidad", "inicio",
              "Definir qué se produce y si el negocio cierra.",
              ("Especificación de producto", "Análisis de factibilidad",
               "Costo objetivo", "Volumen estimado"),
              "Dirección aprueba avanzar al diseño.",
              "Dirección industrial"),
        Etapa("diseno_prod", "Diseño de producto y proceso", "planificacion",
              "Diseñar el producto y cómo se va a fabricar.",
              ("Planos y especificaciones", "Diagrama de flujo de proceso",
               "AMFE de diseño y de proceso", "Plan de control"),
              "Diseño congelado y AMFE con acciones cerradas.",
              "Ingeniería"),
        Etapa("utillaje", "Utillaje y equipamiento", "ejecucion",
              "Tener herramientas, moldes y equipos listos.",
              ("Utillaje fabricado y probado", "Instrucciones de trabajo",
               "Capacitación de operarios", "Calibración de instrumentos"),
              "Utillaje aprobado con piezas conformes.",
              "Ingeniería de proceso"),
        Etapa("preserie", "Preserie y aprobación de muestras", "monitoreo",
              "Probar el proceso en condiciones reales antes de arrancar.",
              ("Corrida piloto", "Estudio de capacidad de proceso",
               "Muestras aprobadas por el cliente", "Ajustes al plan de control"),
              "Capacidad de proceso dentro de lo requerido y muestras aprobadas.",
              "Calidad"),
        Etapa("serie", "Producción en serie", "ejecucion",
              "Producir en rutina sosteniendo calidad y costo.",
              ("Indicadores de línea", "Registro de no conformidades",
               "Mantenimiento preventivo en marcha"),
              "Producción estable en el volumen y la calidad comprometidos.",
              "Producción"),
        Etapa("cierre_mf", "Cierre y mejora continua", "cierre",
              "Traspasar a operación y capturar lo aprendido.",
              ("Traspaso a producción", "Lecciones aprendidas",
               "Plan de mejora continua"),
              "Operación acepta el traspaso.",
              "Dirección industrial"),
    ),
    roles=(
        ("Dirección industrial", "Aprueba inversión y arranque de serie."),
        ("Ingeniería de producto", "Responde por el diseño."),
        ("Ingeniería de proceso", "Responde por cómo se fabrica."),
        ("Calidad", "Aprueba muestras y puede frenar el arranque."),
        ("Producción", "Ejecuta y reporta indicadores de línea."),
    ),
    riesgos=(
        Riesgo("Utillaje que no llega a tiempo", "cronograma",
               "Atrasos del proveedor de moldes o herramientas.",
               "Seguimiento semanal del proveedor e hitos de pago atados a avance."),
        Riesgo("Capacidad de proceso insuficiente", "calidad",
               "Estudios de capacidad por debajo del objetivo en la preserie.",
               "No arrancar serie sin capacidad demostrada; ajustar proceso antes."),
        Riesgo("Costo unitario por encima del objetivo", "costos",
               "Desvíos de consumo de material o de tiempo de ciclo en piloto.",
               "Costeo por corrida piloto y revisión antes de comprometer precio."),
        Riesgo("Rotura de equipo crítico", "riesgos",
               "Mantenimientos preventivos postergados.",
               "Plan de mantenimiento y repuestos críticos en stock."),
    ),
    indicadores=("OEE de la línea", "Scrap y retrabajo", "Costo unitario real vs. objetivo",
                 "Cumplimiento del plan de producción", "Reclamos de cliente"),
    normativa=("ISO 9001 — sistema de gestión de calidad",
               "IATF 16949 si se produce para la industria automotriz",
               "ISO 14001 si hay compromisos ambientales",
               "Reglamentos de seguridad de máquinas aplicables"),
    portafolios_sugeridos=("Nuevos productos", "Mejora de proceso", "Inversión en planta",
                           "Calidad"),
    areas_criticas=("calidad", "costos", "cronograma", "adquisiciones"),
)

# ------------------------------------------------------- servicios profesionales

SERVICIOS = Plantilla(
    clave="servicios",
    rubro="Servicios profesionales y consultoría",
    resumen="Proyectos vendidos por horas o por entregable. El margen se pierde "
            "en el trabajo no facturado, no en el precio.",
    etapas=(
        Etapa("propuesta", "Propuesta", "inicio",
              "Acordar alcance, precio y forma de trabajo antes de empezar.",
              ("Propuesta con alcance explícito", "Estimación de horas",
               "Condiciones comerciales", "Supuestos y exclusiones por escrito"),
              "Propuesta aceptada por escrito.",
              "Socio / Dirección"),
        Etapa("arranque", "Arranque", "planificacion",
              "Alinear expectativas y armar el equipo.",
              ("Reunión de arranque", "Plan de trabajo", "Equipo asignado",
               "Canal y frecuencia de reporte acordados"),
              "Cliente y equipo alineados sobre entregables y fechas.",
              "Responsable del proyecto"),
        Etapa("ejecucion_srv", "Ejecución", "ejecucion",
              "Entregar lo comprometido controlando horas.",
              ("Entregables parciales", "Registro de horas por persona",
               "Actas de reunión", "Control de cambios de alcance"),
              "Entregables aceptados por el cliente.",
              "Responsable del proyecto"),
        Etapa("cierre_srv", "Cierre y facturación", "cierre",
              "Cobrar, cerrar y capturar la referencia.",
              ("Acta de cierre", "Factura final emitida",
               "Encuesta de satisfacción", "Caso de referencia si el cliente acepta"),
              "Facturado y cobrado; cliente conforme.",
              "Socio / Administración"),
    ),
    roles=(
        ("Socio / Dirección", "Aprueba la propuesta y responde por el margen."),
        ("Responsable del proyecto", "Gestiona alcance, equipo y relación con el cliente."),
        ("Equipo asignado", "Ejecuta y registra horas."),
        ("Administración", "Factura y controla cobranza."),
    ),
    riesgos=(
        Riesgo("Horas no facturadas", "costos",
               "Horas cargadas por encima de lo estimado sin cambio de alcance.",
               "Revisión semanal de horas contra estimado y aviso temprano al cliente."),
        Riesgo("Alcance que se estira de a poco", "alcance",
               "Pedidos chicos fuera de propuesta que nadie cotiza.",
               "Todo pedido fuera de alcance se cotiza, aunque sea menor."),
        Riesgo("Cliente que no dispone de su gente", "interesados",
               "Reuniones postergadas o entregables sin revisar.",
               "Dejar la disponibilidad del cliente como supuesto explícito de la propuesta."),
        Riesgo("Cobranza demorada", "costos",
               "Facturas vencidas sin gestión.",
               "Hitos de facturación atados a entregables aceptados."),
    ),
    indicadores=("Horas reales vs. estimadas", "Margen por proyecto",
                 "Porcentaje de horas facturables", "Días de cobranza",
                 "Satisfacción del cliente"),
    normativa=("Contrato de servicios con alcance y propiedad intelectual definidos",
               "Acuerdos de confidencialidad con el cliente",
               "Ley 18.331 si se procesan datos personales del cliente (Uruguay)"),
    portafolios_sugeridos=("Clientes", "Interno", "Preventa"),
    areas_criticas=("alcance", "costos", "interesados", "recursos"),
)

# ----------------------------------------------------------------- energía

ENERGIA = Plantilla(
    clave="energia",
    rubro="Energía y servicios públicos",
    resumen="Generación, transmisión y eficiencia energética. Los permisos "
            "ambientales y la conexión a la red mandan sobre el cronograma.",
    etapas=(
        Etapa("prefactibilidad", "Prefactibilidad", "inicio",
              "Ver si el recurso y el sitio dan.",
              ("Estudio de recurso", "Análisis de sitio", "Modelo económico preliminar",
               "Consulta previa de conexión a la red"),
              "Dirección aprueba invertir en estudios definitivos.",
              "Dirección"),
        Etapa("ambiental", "Autorización ambiental", "planificacion",
              "Conseguir la habilitación ambiental, que suele ser la ruta crítica.",
              ("Estudio de impacto ambiental", "Plan de gestión ambiental",
               "Instancia de participación pública si corresponde"),
              "Autorización ambiental previa otorgada.",
              "Responsable ambiental"),
        Etapa("conexion", "Acuerdo de conexión", "planificacion",
              "Asegurar el punto de conexión y las condiciones técnicas.",
              ("Estudio de conexión", "Acuerdo con el operador de red",
               "Especificación de la subestación"),
              "Punto de conexión confirmado por escrito.",
              "Ingeniería"),
        Etapa("epc", "Ingeniería, compras y construcción", "ejecucion",
              "Construir la instalación.",
              ("Ingeniería de detalle", "Equipos principales comprados",
               "Obra civil y montaje", "Pruebas de equipos"),
              "Instalación montada y probada.",
              "Dirección de proyecto"),
        Etapa("puesta_marcha", "Puesta en marcha", "monitoreo",
              "Sincronizar con la red y demostrar desempeño.",
              ("Protocolo de pruebas", "Sincronización con la red",
               "Prueba de desempeño garantizado"),
              "Desempeño garantizado demostrado y aceptado.",
              "Operador de red / Comitente"),
        Etapa("operacion", "Operación y mantenimiento", "cierre",
              "Traspasar a operación con contrato de mantenimiento.",
              ("Manual de operación", "Contrato de O&M",
               "Capacitación del personal", "Traspaso documentado"),
              "Operación acepta la instalación.",
              "Operaciones"),
    ),
    roles=(
        ("Dirección", "Aprueba la inversión."),
        ("Responsable ambiental", "Responde por el cumplimiento ambiental."),
        ("Ingeniería", "Define la solución técnica y la conexión."),
        ("Operador de red", "Autoriza la conexión y la sincronización."),
        ("Operaciones", "Recibe la instalación."),
    ),
    riesgos=(
        Riesgo("Atraso en la habilitación ambiental", "cronograma",
               "Observaciones del organismo ambiental que reabren el expediente.",
               "Presentar el estudio completo y prever plazos reales de respuesta."),
        Riesgo("Rechazo social del proyecto", "interesados",
               "Oposición de vecinos en la instancia de participación pública.",
               "Comunicación temprana con la comunidad, antes de la instancia formal."),
        Riesgo("Restricción de la red", "riesgos",
               "El operador limita la potencia inyectable en el punto pedido.",
               "Consulta previa de conexión antes de comprometer la inversión."),
        Riesgo("Equipos principales con plazo largo", "adquisiciones",
               "Plazos de entrega de turbinas o transformadores que no cierran.",
               "Reservar equipos críticos apenas se aprueba la inversión."),
    ),
    indicadores=("Avance de obra vs. plan", "Desvío de inversión",
                 "Energía generada vs. proyectada", "Disponibilidad de la instalación",
                 "Cumplimiento del plan de gestión ambiental"),
    normativa=("Autorización Ambiental Previa ante el Ministerio de Ambiente (Uruguay)",
               "Reglamentación de URSEC para el sector energético",
               "Condiciones de conexión del operador de red (UTE en Uruguay)",
               "Normativa de seguridad eléctrica aplicable"),
    portafolios_sugeridos=("Generación", "Transmisión y distribución", "Eficiencia energética"),
    areas_criticas=("riesgos", "interesados", "adquisiciones", "cronograma"),
)

# ------------------------------------------------------------------- salud

SALUD = Plantilla(
    clave="salud",
    rubro="Salud e instituciones médicas",
    resumen="Proyectos en prestadores de salud. Todo cambio toca la atención de "
            "pacientes, así que la puerta clave es no degradar el servicio.",
    etapas=(
        Etapa("necesidad", "Necesidad asistencial", "inicio",
              "Definir qué problema asistencial se resuelve.",
              ("Justificación clínica", "Población afectada",
               "Indicadores asistenciales de base"),
              "Dirección médica avala la necesidad.",
              "Dirección médica"),
        Etapa("diseno_salud", "Diseño del servicio", "planificacion",
              "Definir el proceso asistencial y los recursos.",
              ("Protocolo asistencial", "Recursos humanos y equipamiento necesarios",
               "Circuito del paciente", "Requisitos de habilitación"),
              "Protocolo aprobado por el comité correspondiente.",
              "Dirección médica / Comité"),
        Etapa("habilitacion", "Habilitación", "planificacion",
              "Cumplir con lo que exige la autoridad sanitaria.",
              ("Expediente de habilitación", "Adecuación edilicia",
               "Habilitación de equipos", "Personal con títulos registrados"),
              "Habilitación otorgada.",
              "Responsable de habilitaciones"),
        Etapa("implementacion", "Implementación", "ejecucion",
              "Poner en marcha sin interrumpir la asistencia.",
              ("Plan de transición", "Capacitación del personal asistencial",
               "Pruebas en paralelo si reemplaza un proceso existente"),
              "Servicio funcionando con el personal capacitado.",
              "Jefatura del servicio"),
        Etapa("seguimiento", "Seguimiento asistencial", "monitoreo",
              "Verificar que mejoró lo que se quería mejorar.",
              ("Indicadores asistenciales post-implementación",
               "Registro de eventos adversos", "Ajustes al protocolo"),
              "Indicadores en el nivel comprometido, sin eventos adversos atribuibles.",
              "Dirección médica"),
        Etapa("cierre_salud", "Cierre", "cierre",
              "Incorporar el servicio a la operación normal.",
              ("Protocolo incorporado al manual", "Traspaso a operación",
               "Lecciones aprendidas"),
              "Servicio incorporado a la operación de rutina.",
              "Dirección"),
    ),
    roles=(
        ("Dirección médica", "Avala la pertinencia clínica. Puede frenar el proyecto."),
        ("Jefatura del servicio", "Ejecuta y responde por la operación diaria."),
        ("Comité de calidad / seguridad del paciente", "Revisa riesgos asistenciales."),
        ("Responsable de habilitaciones", "Gestiona ante la autoridad sanitaria."),
        ("Referente de sistemas", "Integra con la historia clínica electrónica."),
    ),
    riesgos=(
        Riesgo("Interrupción de la asistencia", "riesgos",
               "Cambios puestos en producción sin plan de contingencia.",
               "Transición en paralelo y plan de vuelta atrás siempre disponible."),
        Riesgo("Personal no capacitado a tiempo", "recursos",
               "Capacitaciones postergadas por carga asistencial.",
               "Capacitación dentro de la jornada y con suplencias previstas."),
        Riesgo("Datos de pacientes expuestos", "riesgos",
               "Accesos amplios o datos productivos en pruebas.",
               "Acceso mínimo necesario y datos anonimizados en ambientes de prueba."),
        Riesgo("Evento adverso asociado al cambio", "calidad",
               "Aumento de incidentes reportados tras la implementación.",
               "Seguimiento intensivo las primeras semanas y criterio de reversión definido."),
    ),
    indicadores=("Tiempo de espera del paciente", "Eventos adversos reportados",
                 "Cobertura de la población objetivo", "Adherencia al protocolo",
                 "Satisfacción del usuario"),
    normativa=("Habilitación de servicios de salud ante el MSP (Uruguay)",
               "Ley 18.335 — derechos y obligaciones de pacientes y usuarios",
               "Ley 18.331 — datos personales, con los datos de salud como categoría sensible",
               "Normativa de historia clínica electrónica nacional"),
    portafolios_sugeridos=("Servicios asistenciales", "Equipamiento", "Sistemas",
                           "Calidad y seguridad"),
    areas_criticas=("riesgos", "calidad", "interesados", "recursos"),
)

# ---------------------------------------------------------------- financiero

FINANCIERO = Plantilla(
    clave="financiero",
    rubro="Banca, finanzas y seguros",
    resumen="Rubro supervisado. Cada cambio relevante tiene que poder explicarse "
            "ante el regulador y ante auditoría interna.",
    etapas=(
        Etapa("caso_negocio", "Caso de negocio", "inicio",
              "Justificar la inversión y el impacto en riesgo.",
              ("Caso de negocio", "Evaluación de riesgo operacional",
               "Impacto regulatorio", "Aprobación del comité"),
              "Comité aprueba la iniciativa.",
              "Comité de dirección"),
        Etapa("diseno_fin", "Diseño y controles", "planificacion",
              "Definir la solución y los controles que la acompañan.",
              ("Diseño funcional", "Matriz de controles",
               "Evaluación de seguridad de la información",
               "Análisis de continuidad del negocio"),
              "Riesgos y Seguridad aprueban el diseño.",
              "Riesgos / Seguridad de la información"),
        Etapa("construccion_fin", "Construcción y pruebas", "ejecucion",
              "Construir con evidencia de prueba suficiente para auditoría.",
              ("Desarrollo o parametrización", "Pruebas funcionales documentadas",
               "Pruebas de seguridad", "Segregación de ambientes"),
              "Pruebas cerradas con evidencia archivada.",
              "Líder de proyecto"),
        Etapa("aprobacion_reg", "Aprobación regulatoria", "monitoreo",
              "Obtener las autorizaciones o hacer las comunicaciones que correspondan.",
              ("Comunicación al regulador si aplica",
               "Actualización de manuales y políticas", "Registro de la aprobación"),
              "Autorización obtenida o comunicación cursada.",
              "Cumplimiento"),
        Etapa("salida_prod", "Salida a producción", "ejecucion",
              "Implantar con control de cambios formal.",
              ("Solicitud de cambio aprobada", "Plan de vuelta atrás",
               "Capacitación a usuarios", "Monitoreo reforzado"),
              "Cambio en producción con evidencia de aprobación.",
              "Comité de cambios"),
        Etapa("cierre_fin", "Cierre y revisión", "cierre",
              "Verificar que los controles funcionan en la vida real.",
              ("Revisión post-implementación", "Controles operando",
               "Cierre de hallazgos", "Lecciones aprendidas"),
              "Auditoría interna sin hallazgos abiertos.",
              "Auditoría interna"),
    ),
    roles=(
        ("Comité de dirección", "Aprueba la inversión y el apetito de riesgo."),
        ("Riesgos", "Evalúa el riesgo operacional. Puede bloquear."),
        ("Cumplimiento", "Responde por lo regulatorio."),
        ("Seguridad de la información", "Aprueba el diseño de seguridad."),
        ("Auditoría interna", "Revisa evidencia y levanta hallazgos."),
    ),
    riesgos=(
        Riesgo("Hallazgo regulatorio", "riesgos",
               "Controles diseñados pero no operando en la práctica.",
               "Probar los controles en producción, no sólo documentarlos."),
        Riesgo("Fuga o exposición de datos de clientes", "riesgos",
               "Accesos no revisados o datos productivos fuera del ambiente seguro.",
               "Revisión periódica de accesos y enmascarado en ambientes no productivos."),
        Riesgo("Indisponibilidad del servicio", "calidad",
               "Cambios sin ventana ni plan de vuelta atrás.",
               "Ventanas de cambio definidas y vuelta atrás probada."),
        Riesgo("Evidencia insuficiente para auditoría", "integracion",
               "Aprobaciones verbales o por canales informales.",
               "Toda aprobación queda registrada con responsable y fecha."),
    ),
    indicadores=("Hallazgos de auditoría abiertos", "Incidentes de seguridad",
                 "Disponibilidad de servicios críticos",
                 "Cambios con vuelta atrás ejecutada", "Cumplimiento del plan de controles"),
    normativa=("Normativa del Banco Central del Uruguay para la institución que corresponda",
               "Ley 18.331 — protección de datos personales",
               "Ley 19.574 — prevención de lavado de activos",
               "PCI-DSS si se procesan datos de tarjetas",
               "ISO/IEC 27001 para gestión de seguridad de la información"),
    portafolios_sugeridos=("Regulatorio", "Productos", "Canales digitales",
                           "Riesgo y control"),
    areas_criticas=("riesgos", "integracion", "calidad", "interesados"),
)

# --------------------------------------------------------------------- agro

AGRO = Plantilla(
    clave="agro",
    rubro="Agro y agroindustria",
    resumen="La zafra manda: la ventana de siembra o cosecha no se negocia, y un "
            "atraso de dos semanas puede costar el año entero.",
    etapas=(
        Etapa("planificacion_zafra", "Planificación de zafra", "inicio",
              "Definir qué, dónde y cuánto, antes de que abra la ventana.",
              ("Plan de zafra", "Presupuesto de insumos",
               "Disponibilidad de maquinaria", "Análisis de suelo"),
              "Plan aprobado antes del inicio de la ventana.",
              "Dirección / Gerencia de producción"),
        Etapa("insumos", "Compra de insumos", "planificacion",
              "Asegurar semilla, fertilizante y agroquímicos a tiempo.",
              ("Órdenes de compra", "Logística de entrega acordada",
               "Financiamiento confirmado"),
              "Insumos en campo antes de la ventana.",
              "Compras"),
        Etapa("implantacion", "Implantación", "ejecucion",
              "Sembrar o plantar en la ventana correcta.",
              ("Registro de labores", "Control de calidad de siembra",
               "Registro de aplicaciones"),
              "Superficie implantada dentro de la ventana.",
              "Gerencia de producción"),
        Etapa("seguimiento_cultivo", "Seguimiento de cultivo", "monitoreo",
              "Monitorear y actuar a tiempo.",
              ("Monitoreo de plagas y enfermedades", "Registro de aplicaciones",
               "Estimación de rendimiento"),
              "Cultivo sin problemas sanitarios sin resolver.",
              "Técnico agrónomo"),
        Etapa("cosecha", "Cosecha", "ejecucion",
              "Levantar la producción con la menor pérdida posible.",
              ("Plan de cosecha", "Registro de rendimiento por chacra",
               "Control de humedad y calidad", "Trazabilidad de lotes"),
              "Producción cosechada y almacenada o entregada.",
              "Gerencia de producción"),
        Etapa("cierre_zafra", "Cierre de zafra", "cierre",
              "Cerrar números y aprender para la próxima.",
              ("Resultado económico por chacra", "Análisis de desvíos",
               "Plan para la zafra siguiente"),
              "Resultado cerrado y analizado.",
              "Dirección"),
    ),
    roles=(
        ("Dirección", "Aprueba el plan de zafra y la inversión."),
        ("Gerencia de producción", "Ejecuta las labores en tiempo."),
        ("Técnico agrónomo", "Decide manejo sanitario y nutricional."),
        ("Compras", "Asegura insumos antes de la ventana."),
        ("Responsable de trazabilidad", "Responde ante certificadoras y organismos."),
    ),
    riesgos=(
        Riesgo("Ventana de siembra o cosecha perdida", "cronograma",
               "Insumos o maquinaria que no están cuando abre la ventana.",
               "Insumos en campo con anticipación y maquinaria contratada por adelantado."),
        Riesgo("Evento climático", "riesgos",
               "Pronósticos adversos sostenidos en el período crítico.",
               "Diversificar fechas y chacras; evaluar seguro agrícola."),
        Riesgo("Precio de commodity en baja", "costos",
               "Caída de precios frente al costo ya comprometido.",
               "Cobertura parcial de precio al momento de comprometer insumos."),
        Riesgo("Falla de trazabilidad", "calidad",
               "Registros de aplicación incompletos o fuera de fecha.",
               "Registro de labores en el momento, no al final de la zafra."),
    ),
    indicadores=("Rendimiento por hectárea", "Costo por hectárea",
                 "Superficie implantada dentro de ventana", "Margen por chacra",
                 "Cumplimiento de registros de trazabilidad"),
    normativa=("Registros de la Dirección General de Servicios Agrícolas (Uruguay)",
               "Trazabilidad ganadera del INAC / SNIG si aplica",
               "Plan de uso y manejo de suelos ante el Ministerio de Ganadería",
               "Certificaciones voluntarias del mercado destino"),
    portafolios_sugeridos=("Agrícola", "Ganadero", "Infraestructura de campo",
                           "Certificaciones"),
    areas_criticas=("cronograma", "riesgos", "adquisiciones", "costos"),
)

# ------------------------------------------------------------------- público

PUBLICO = Plantilla(
    clave="publico",
    rubro="Sector público y organismos estatales",
    resumen="Todo pasa por el procedimiento de compra y por el control previo. "
            "El cronograma lo define la normativa, no el equipo de proyecto.",
    etapas=(
        Etapa("necesidad_pub", "Definición de la necesidad", "inicio",
              "Fundamentar la necesidad y conseguir la disponibilidad presupuestal.",
              ("Fundamentación de la necesidad", "Disponibilidad presupuestal",
               "Autorización del jerarca"),
              "Gasto autorizado con crédito disponible.",
              "Jerarca del organismo"),
        Etapa("pliego", "Elaboración del pliego", "planificacion",
              "Definir qué se compra y cómo se evalúa, sin direccionar.",
              ("Pliego de condiciones particulares", "Especificaciones técnicas",
               "Criterios de evaluación objetivos", "Cronograma del llamado"),
              "Pliego aprobado por la autoridad competente.",
              "Comisión asesora / Jurídica"),
        Etapa("llamado", "Llamado y adjudicación", "planificacion",
              "Correr el procedimiento con transparencia.",
              ("Publicación del llamado", "Acta de apertura de ofertas",
               "Informe de la comisión asesora", "Resolución de adjudicación"),
              "Adjudicación resuelta e intervenida por el control previo.",
              "Ordenador del gasto"),
        Etapa("ejecucion_pub", "Ejecución del contrato", "ejecucion",
              "Controlar que se entregue lo contratado.",
              ("Actas de recepción parcial", "Control de cumplimiento contractual",
               "Registro de incumplimientos y multas"),
              "Prestación recibida conforme al contrato.",
              "Responsable del contrato"),
        Etapa("rendicion", "Rendición y cierre", "cierre",
              "Rendir cuentas del gasto y cerrar el expediente.",
              ("Rendición de cuentas", "Expediente completo",
               "Informe de resultados", "Cierre del contrato"),
              "Rendición aprobada sin observaciones pendientes.",
              "Contaduría / Auditoría"),
    ),
    roles=(
        ("Jerarca del organismo", "Autoriza el gasto."),
        ("Ordenador del gasto", "Resuelve la adjudicación."),
        ("Comisión asesora de adjudicaciones", "Evalúa ofertas y recomienda."),
        ("Jurídica", "Controla la legalidad del procedimiento."),
        ("Contaduría / control previo", "Interviene el gasto. Puede observarlo."),
    ),
    riesgos=(
        Riesgo("Observación del control previo", "integracion",
               "Expedientes que vuelven por documentación faltante.",
               "Checklist de expediente completo antes de elevar."),
        Riesgo("Llamado desierto o con oferta única", "adquisiciones",
               "Consultas escasas o requisitos que restringen la competencia.",
               "Consulta previa al mercado y revisión de requisitos excluyentes."),
        Riesgo("Impugnación del procedimiento", "riesgos",
               "Criterios de evaluación ambiguos o discrecionales.",
               "Criterios objetivos y ponderados, publicados desde el inicio."),
        Riesgo("Vencimiento del ejercicio presupuestal", "cronograma",
               "Procedimientos que no cierran antes del cierre del ejercicio.",
               "Planificar el llamado contando los plazos legales reales, no los deseados."),
    ),
    indicadores=("Plazo del procedimiento de compra", "Llamados desiertos o impugnados",
                 "Ejecución presupuestal", "Observaciones de control previo",
                 "Cumplimiento de plazos contractuales"),
    normativa=("TOCAF — Texto Ordenado de Contabilidad y Administración Financiera (Uruguay)",
               "Intervención preventiva del Tribunal de Cuentas",
               "Publicación en el sitio de Compras Estatales",
               "Ley 18.381 — acceso a la información pública",
               "Ley 19.889 y normas de procedimiento administrativo aplicables"),
    portafolios_sugeridos=("Inversión pública", "Compras y suministros",
                           "Modernización de gestión", "Convenios"),
    areas_criticas=("adquisiciones", "integracion", "interesados", "cronograma"),
    nota="En el Estado el cronograma lo fija la normativa de compras. Planificar "
         "con los plazos legales reales, y no con los deseados, es la diferencia "
         "entre ejecutar el presupuesto y perderlo.",
)

# -------------------------------------------------------------------- retail

RETAIL = Plantilla(
    clave="retail",
    rubro="Retail y consumo masivo",
    resumen="Todo se ordena alrededor de la temporada. Llegar tarde a una fecha "
            "comercial no se recupera: esa venta no vuelve.",
    etapas=(
        Etapa("plan_comercial", "Plan comercial", "inicio",
              "Definir surtido, temporada y objetivo de venta.",
              ("Plan de surtido", "Objetivo de venta y margen",
               "Calendario comercial", "Presupuesto de compra"),
              "Plan aprobado antes del inicio de la temporada de compra.",
              "Gerencia comercial"),
        Etapa("abastecimiento", "Abastecimiento", "planificacion",
              "Comprar y traer la mercadería a tiempo.",
              ("Órdenes de compra", "Plan logístico y de importación",
               "Control de calidad de proveedor"),
              "Mercadería en depósito antes de la fecha de salida a piso.",
              "Compras / Logística"),
        Etapa("implantacion_retail", "Implantación en tienda", "ejecucion",
              "Poner el producto en piso con la exhibición definida.",
              ("Planograma", "Material de punto de venta",
               "Capacitación al personal de tienda", "Precios cargados"),
              "Producto en piso según planograma en todas las tiendas.",
              "Operaciones de tienda"),
        Etapa("temporada", "Temporada", "monitoreo",
              "Vender y reaccionar rápido a lo que pasa.",
              ("Seguimiento de venta diaria", "Reposición",
               "Ajustes de precio y promoción"),
              "Objetivo de venta y margen alcanzado.",
              "Gerencia comercial"),
        Etapa("liquidacion", "Liquidación y cierre", "cierre",
              "Sacar el remanente y cerrar el resultado.",
              ("Plan de liquidación", "Resultado de temporada",
               "Análisis de quiebres y sobrantes"),
              "Stock remanente dentro del objetivo.",
              "Gerencia comercial"),
    ),
    roles=(
        ("Gerencia comercial", "Define surtido y aprueba el plan."),
        ("Compras", "Negocia y asegura el abastecimiento."),
        ("Logística", "Responde por que la mercadería llegue a tiempo."),
        ("Operaciones de tienda", "Ejecuta la implantación en piso."),
        ("Marketing", "Sostiene la campaña de la temporada."),
    ),
    riesgos=(
        Riesgo("Mercadería que llega tarde", "cronograma",
               "Atrasos de embarque o demoras en aduana.",
               "Márgenes de tiempo en el plan de importación y seguimiento del embarque."),
        Riesgo("Quiebre de stock en producto estrella", "adquisiciones",
               "Velocidad de venta por encima de la proyectada sin reposición.",
               "Reposición automática por umbral y proveedor alternativo definido."),
        Riesgo("Sobrestock al cierre", "costos",
               "Venta por debajo de lo proyectado a mitad de temporada.",
               "Puntos de control con decisión de promoción anticipada."),
        Riesgo("Implantación despareja entre tiendas", "calidad",
               "Auditorías de piso con desvíos respecto al planograma.",
               "Auditoría de implantación en los primeros días de temporada."),
    ),
    indicadores=("Venta vs. objetivo por categoría", "Margen por categoría",
                 "Quiebres de stock", "Rotación de inventario",
                 "Cumplimiento de planograma"),
    normativa=("Ley 17.250 — relaciones de consumo y defensa del consumidor (Uruguay)",
               "Normativa de etiquetado y rotulado del producto",
               "Reglamentación de promociones y ofertas",
               "Normativa aduanera para mercadería importada"),
    portafolios_sugeridos=("Temporadas", "Nuevas tiendas", "Comercio electrónico",
                           "Cadena de suministro"),
    areas_criticas=("cronograma", "adquisiciones", "costos", "calidad"),
)

# ----------------------------------------------------------------- educación

EDUCACION = Plantilla(
    clave="educacion",
    rubro="Educación y formación",
    resumen="El calendario académico es una restricción dura: lo que no está "
            "listo para el inicio de cursos espera al período siguiente.",
    etapas=(
        Etapa("diseno_academico", "Diseño académico", "inicio",
              "Definir la propuesta formativa y su fundamento.",
              ("Perfil de egreso", "Plan de estudios", "Justificación de la propuesta",
               "Estimación de matrícula"),
              "Propuesta aprobada por el órgano académico.",
              "Consejo / Dirección académica"),
        Etapa("aprobacion_academica", "Aprobación y acreditación", "planificacion",
              "Conseguir el reconocimiento oficial si corresponde.",
              ("Expediente de aprobación", "Documentación de acreditación",
               "Respuestas a observaciones"),
              "Propuesta aprobada o acreditada por la autoridad educativa.",
              "Dirección académica"),
        Etapa("preparacion", "Preparación del dictado", "planificacion",
              "Tener docentes, materiales y aulas listos.",
              ("Docentes designados", "Materiales y bibliografía",
               "Aulas y plataforma asignadas", "Cronograma de cursada"),
              "Todo listo antes del inicio de cursos.",
              "Coordinación académica"),
        Etapa("dictado", "Dictado", "ejecucion",
              "Dictar el curso y acompañar a los estudiantes.",
              ("Registro de asistencia", "Evaluaciones aplicadas",
               "Seguimiento de deserción"),
              "Curso dictado completo según plan.",
              "Coordinación académica"),
        Etapa("evaluacion_curso", "Evaluación del curso", "monitoreo",
              "Medir resultados y satisfacción.",
              ("Resultados de aprobación", "Encuesta a estudiantes",
               "Evaluación docente"),
              "Indicadores dentro de lo esperado.",
              "Dirección académica"),
        Etapa("cierre_edu", "Cierre y mejora", "cierre",
              "Cerrar la edición y ajustar la siguiente.",
              ("Actas de calificación cerradas", "Titulación o certificación emitida",
               "Plan de mejora para la próxima edición"),
              "Actas cerradas y certificados emitidos.",
              "Bedelía / Dirección"),
    ),
    roles=(
        ("Dirección académica", "Aprueba la propuesta y responde por la calidad."),
        ("Coordinación académica", "Gestiona el dictado."),
        ("Cuerpo docente", "Dicta y evalúa."),
        ("Bedelía / registro", "Responde por actas y certificaciones."),
        ("Dirección administrativa", "Aprueba presupuesto y recursos."),
    ),
    riesgos=(
        Riesgo("Matrícula por debajo del punto de equilibrio", "costos",
               "Inscripciones lentas cerca del cierre.",
               "Punto de decisión con fecha para abrir o postergar la edición."),
        Riesgo("Docente clave que se cae", "recursos",
               "Confirmaciones de disponibilidad que no llegan.",
               "Suplente identificado para cada asignatura crítica."),
        Riesgo("Deserción alta", "interesados",
               "Asistencia que cae en las primeras semanas.",
               "Seguimiento temprano y contacto con quienes faltan."),
        Riesgo("Aprobación oficial fuera de plazo", "cronograma",
               "Expediente con observaciones cerca del inicio de cursos.",
               "Iniciar el trámite con un período académico de anticipación."),
    ),
    indicadores=("Matrícula vs. objetivo", "Tasa de aprobación", "Deserción",
                 "Satisfacción de estudiantes", "Costo por estudiante"),
    normativa=("Reconocimiento del nivel educativo correspondiente (MEC / ANEP en Uruguay)",
               "Normativa de acreditación de carreras si aplica",
               "Ley 18.331 — datos personales de estudiantes, con menores como categoría sensible",
               "Reglamento académico de la institución"),
    portafolios_sugeridos=("Oferta académica", "Infraestructura", "Tecnología educativa",
                           "Extensión"),
    areas_criticas=("cronograma", "recursos", "interesados", "calidad"),
)

# ------------------------------------------------------------------ logística

LOGISTICA = Plantilla(
    clave="logistica",
    rubro="Logística, transporte y comercio exterior",
    resumen="Proyectos de red, depósito y transporte. Los tiempos de aduana y de "
            "tránsito no dependen del equipo, y hay que planificar con eso.",
    etapas=(
        Etapa("diseno_red", "Diseño de la operación", "inicio",
              "Definir cómo va a fluir la mercadería.",
              ("Análisis de flujos y volúmenes", "Diseño de red",
               "Modelo de costos logísticos"),
              "Dirección aprueba el diseño y la inversión.",
              "Dirección de operaciones"),
        Etapa("infraestructura", "Infraestructura y sistemas", "planificacion",
              "Tener depósito, flota y sistemas listos.",
              ("Depósito habilitado", "Flota o transportistas contratados",
               "Sistema de gestión de almacén configurado", "Habilitaciones de transporte"),
              "Infraestructura habilitada y sistemas probados.",
              "Operaciones / Sistemas"),
        Etapa("puesta_operacion", "Puesta en operación", "ejecucion",
              "Arrancar la operación sin cortar el servicio.",
              ("Plan de migración de operación", "Capacitación de personal",
               "Operación en paralelo si reemplaza otra"),
              "Operación funcionando con niveles de servicio acordados.",
              "Dirección de operaciones"),
        Etapa("estabilizacion", "Estabilización", "monitoreo",
              "Ajustar hasta que la operación sea previsible.",
              ("Indicadores de nivel de servicio", "Registro de incidencias",
               "Ajustes de proceso"),
              "Nivel de servicio sostenido en el objetivo.",
              "Dirección de operaciones"),
        Etapa("cierre_log", "Cierre", "cierre",
              "Traspasar a la operación de rutina.",
              ("Procedimientos documentados", "Traspaso a operación",
               "Resultado vs. modelo de costos"),
              "Operación aceptada como rutina.",
              "Dirección"),
    ),
    roles=(
        ("Dirección de operaciones", "Aprueba el diseño y responde por el servicio."),
        ("Jefatura de depósito", "Ejecuta la operación diaria."),
        ("Despachante de aduana", "Responde por el trámite de comercio exterior."),
        ("Sistemas", "Configura e integra el sistema de gestión."),
        ("Comercial", "Compromete niveles de servicio con el cliente."),
    ),
    riesgos=(
        Riesgo("Demora en aduana", "cronograma",
               "Documentación incompleta o clasificación arancelaria dudosa.",
               "Revisión documental previa al embarque y clasificación confirmada."),
        Riesgo("Corte de servicio en la migración", "riesgos",
               "Migración sin operación en paralelo ni plan de contingencia.",
               "Operación en paralelo y criterio de reversión definido."),
        Riesgo("Costo logístico por encima del modelo", "costos",
               "Desvíos de tarifa de flete o de ocupación de depósito.",
               "Contratos con tarifa acordada y seguimiento mensual contra modelo."),
        Riesgo("Faltantes o daños de mercadería", "calidad",
               "Diferencias de inventario recurrentes.",
               "Inventarios cíclicos y control de acceso al depósito."),
    ),
    indicadores=("Entregas a tiempo y completas", "Costo logístico sobre venta",
                 "Exactitud de inventario", "Tiempo de despacho aduanero",
                 "Ocupación de depósito"),
    normativa=("Código Aduanero y normativa de la Dirección Nacional de Aduanas (Uruguay)",
               "Ventanilla Única de Comercio Exterior (VUCE)",
               "Habilitaciones de transporte de carga del MTOP",
               "Normativa de mercancías peligrosas si corresponde"),
    portafolios_sugeridos=("Red logística", "Depósitos", "Transporte", "Comercio exterior"),
    areas_criticas=("cronograma", "costos", "adquisiciones", "riesgos"),
)

# ---------------------------------------------------------------- telecomunicaciones

TELECOM = Plantilla(
    clave="telecom",
    rubro="Telecomunicaciones",
    resumen="Despliegue de red y servicios. El permiso de sitio y el espectro "
            "definen el cronograma, y son lo menos controlable del proyecto.",
    etapas=(
        Etapa("diseno_red_tel", "Diseño de red", "inicio",
              "Definir cobertura, capacidad y tecnología.",
              ("Estudio de cobertura", "Dimensionamiento de capacidad",
               "Selección de tecnología", "Modelo económico"),
              "Dirección aprueba el diseño y la inversión.",
              "Dirección técnica"),
        Etapa("espectro_permisos", "Espectro y permisos", "planificacion",
              "Asegurar espectro y permisos de sitio.",
              ("Autorización de uso de espectro", "Permisos municipales de sitio",
               "Contratos de arrendamiento de sitios", "Estudios de radiación no ionizante"),
              "Permisos otorgados para los sitios de la primera etapa.",
              "Regulatorio"),
        Etapa("despliegue", "Despliegue", "ejecucion",
              "Instalar y poner en servicio los sitios.",
              ("Sitios construidos", "Equipos instalados y configurados",
               "Enlaces de transmisión operativos", "Pruebas de cobertura"),
              "Sitios en servicio con cobertura medida.",
              "Ingeniería de despliegue"),
        Etapa("integracion_serv", "Integración de servicios", "ejecucion",
              "Que el servicio funcione punta a punta.",
              ("Integración con el núcleo de red", "Pruebas de servicio",
               "Configuración de facturación y provisión"),
              "Servicio probado punta a punta.",
              "Ingeniería"),
        Etapa("lanzamiento_tel", "Lanzamiento comercial", "monitoreo",
              "Salir al mercado con la operación lista para sostenerlo.",
              ("Plan comercial", "Capacitación de atención al cliente",
               "Monitoreo de calidad de servicio"),
              "Servicio comercializado con calidad dentro del objetivo.",
              "Dirección comercial"),
        Etapa("cierre_tel", "Traspaso a operación", "cierre",
              "Que operaciones sostenga la red sin el equipo de proyecto.",
              ("Documentación de red", "Traspaso a operación y mantenimiento",
               "Lecciones aprendidas"),
              "Operaciones acepta el traspaso.",
              "Dirección técnica"),
    ),
    roles=(
        ("Dirección técnica", "Aprueba diseño e inversión."),
        ("Regulatorio", "Gestiona espectro y permisos ante el regulador."),
        ("Ingeniería de despliegue", "Ejecuta la instalación."),
        ("Operaciones de red", "Recibe y sostiene la red."),
        ("Dirección comercial", "Define el lanzamiento."),
    ),
    riesgos=(
        Riesgo("Permiso de sitio denegado", "riesgos",
               "Oposición vecinal o rechazo municipal en sitios clave.",
               "Sitios alternativos identificados desde el diseño."),
        Riesgo("Atraso en la asignación de espectro", "cronograma",
               "Trámite regulatorio sin fecha de resolución.",
               "Iniciar el trámite antes de comprometer fecha de lanzamiento."),
        Riesgo("Equipos con plazo de entrega largo", "adquisiciones",
               "Plazos de fabricante que no cierran con el plan.",
               "Órdenes anticipadas de equipamiento crítico."),
        Riesgo("Calidad de servicio por debajo de lo comprometido", "calidad",
               "Mediciones de cobertura o capacidad por debajo del diseño.",
               "Medición en cada sitio antes de habilitar comercialmente."),
    ),
    indicadores=("Sitios en servicio vs. plan", "Cobertura alcanzada",
                 "Calidad de servicio medida", "Inversión ejecutada vs. presupuesto",
                 "Altas comerciales"),
    normativa=("Reglamentación de URSEC — Unidad Reguladora de Servicios de Comunicaciones (Uruguay)",
               "Autorización de uso de espectro radioeléctrico",
               "Normativa municipal de instalación de antenas",
               "Límites de exposición a radiación no ionizante"),
    portafolios_sugeridos=("Despliegue de red", "Servicios", "Transformación digital",
                           "Regulatorio"),
    areas_criticas=("riesgos", "cronograma", "adquisiciones", "interesados"),
)

# ------------------------------------------------------------------ registro

PLANTILLAS: dict[str, Plantilla] = {
    p.clave: p for p in (
        CONSTRUCCION, SOFTWARE, FARMA, MANUFACTURA, SERVICIOS, ENERGIA, SALUD,
        FINANCIERO, AGRO, PUBLICO, RETAIL, EDUCACION, LOGISTICA, TELECOM,
    )
}


# ------------------------------------------------------------- traducciones
#
# Estas plantillas son contenido de metodología real para un producto pago:
# la traducción vive acá, superpuesta sobre las 14 constantes en español de
# arriba, que son la fuente de verdad y NUNCA se tocan. `clave` (de Plantilla
# y de Etapa), `grupo_pmbok`, `area_pmbok` y `areas_criticas` no se traducen
# nunca: son identificadores cruzados contra pmbok.py y contra la clave de
# versionado en la base (`plantillas.adoptar`).
#
# Las referencias normativas (`normativa`) son mayormente uruguayas: la cita
# (ley, decreto, sigla del organismo) se mantiene igual en los tres idiomas;
# sólo se traduce la glosa después del guion, y en inglés/portugués se agrega
# una aclaración de que es una referencia de Uruguay cuando el nombre del
# organismo no alcanza para dejarlo claro por sí solo.
#
# Estructura por (lang, plantilla_clave):
#   rubro, resumen, nota            -> strings sueltos (nota sólo si aplica)
#   etapas                          -> {etapa_clave: {nombre, objetivo,
#                                        entregables, criterio_salida, aprueba}}
#   roles                           -> tupla de (rol, qué_decide), mismo orden
#   riesgos                         -> tupla de (titulo, señal_temprana,
#                                        mitigación), mismo orden que p.riesgos
#   indicadores, normativa,
#   portafolios_sugeridos           -> tuplas paralelas al original

_TRAD: dict[str, dict[str, dict]] = {
    "en": {
        "construccion": {
            "rubro": "Construction and infrastructure",
            "resumen": "Civil, road, and infrastructure works. Governed by progress "
                       "certification and safety: a workplace accident is the one risk "
                       "that can shut the whole site down.",
            "etapas": {
                "anteproyecto": {
                    "nombre": "Preliminary design",
                    "objetivo": "Define what will be built and whether it makes economic "
                                "sense.",
                    "entregables": ("Descriptive report", "±30% cost estimate",
                                     "Preliminary soil study", "Feasibility analysis"),
                    "criterio_salida": "The sponsor approves moving forward with detailed "
                                        "design.",
                    "aprueba": "Sponsor / Management",
                },
                "ejecutivo": {
                    "nombre": "Detailed design",
                    "objetivo": "Take the design to construction level, with firm "
                                "quantities and budget.",
                    "entregables": ("Construction drawings", "Bill of quantities",
                                     "Detailed budget", "Critical-path schedule",
                                     "Technical specifications"),
                    "criterio_salida": "Budget and timeline approved; municipal permits "
                                        "filed.",
                    "aprueba": "Site management",
                },
                "permisos": {
                    "nombre": "Permits and approvals",
                    "objetivo": "Get everything needed to start without risk of a shutdown "
                                "order.",
                    "entregables": ("Building permit", "Site notice filed with BPS",
                                     "Health and safety plan",
                                     "Environmental impact study if applicable"),
                    "criterio_salida": "Permits granted and the site registered.",
                    "aprueba": "Technical lead",
                },
                "licitacion": {
                    "nombre": "Procurement",
                    "objetivo": "Select contractors and close terms.",
                    "entregables": ("Bid package", "Bid comparison", "Signed contracts",
                                     "Performance guarantees"),
                    "criterio_salida": "Contracts signed with defined timelines and "
                                        "penalties.",
                    "aprueba": "Procurement / Management",
                },
                "obra": {
                    "nombre": "Construction",
                    "objetivo": "Build to the design, controlling progress, cost, and "
                                "safety.",
                    "entregables": ("Monthly progress certificates",
                                     "Site logbook kept current", "Non-conformance log",
                                     "Documented change orders"),
                    "criterio_salida": "Work finished to drawings, with punch-list items "
                                        "resolved.",
                    "aprueba": "Site management",
                },
                "recepcion_provisoria": {
                    "nombre": "Provisional handover",
                    "objetivo": "Take delivery of the site while logging what still needs "
                                "fixing.",
                    "entregables": ("Provisional handover certificate", "Punch list",
                                     "As-built drawings"),
                    "criterio_salida": "Certificate signed; the warranty period starts.",
                    "aprueba": "Owner",
                },
                "recepcion_definitiva": {
                    "nombre": "Final handover",
                    "objetivo": "Close the contract once the warranty period ends.",
                    "entregables": ("Final handover certificate", "Guarantee release",
                                     "Maintenance manual", "Lessons learned"),
                    "criterio_salida": "Guarantees released and contract closed.",
                    "aprueba": "Owner / Legal",
                },
            },
            "roles": (
                ("Owner", "Approves change orders and signs off on handovers."),
                ("Site management", "Certifies progress and accepts or rejects work."),
                ("Technical lead", "Answers to the municipality for the site."),
                ("Safety officer", "Can stop work over accident risk."),
                ("Foreman / Site supervisor",
                 "Runs the day-to-day and reports real progress."),
            ),
            "riesgos": (
                ("Workplace accident",
                 "Safety observations left unresolved, or staff without protective "
                 "equipment.",
                 "An active safety plan, daily toolbox talks, and audits by the safety "
                 "officer."),
                ("Uncontrolled change orders",
                 "Work carried out without a signed change order.",
                 "Nothing gets built without a change order approved in writing."),
                ("Weather delay",
                 "Lost days piling up beyond what the schedule allowed for.",
                 "Budget for seasonal rain days and leave slack on weather-exposed "
                 "tasks."),
                ("Material shortages or price hikes",
                 "Delivery times stretching out, or quotes expiring before purchase.",
                 "Buy critical materials early and include price-adjustment clauses in "
                 "contracts."),
                ("Mismatches with the detailed design",
                 "Recurring site queries over incomplete or contradictory drawings.",
                 "Cross-check drawings before putting the job out to bid."),
            ),
            "indicadores": ("Physical progress vs. certified progress",
                             "Schedule slippage by milestone",
                             "Cost incurred vs. budgeted by trade",
                             "Accidents and lost days",
                             "Change orders approved as a share of original contract"),
            "normativa": ("Ley 16.074 — workplace accident insurance (Uruguay)",
                           "Decreto 125/014 — health and safety in construction "
                           "(Uruguay)",
                           "Site registration and contributions to BPS, Uruguay's social "
                           "security agency",
                           "Municipal building code of the relevant local government "
                           "(Uruguay)",
                           "UNIT standards (Uruguay's technical standards body) for "
                           "materials and testing"),
            "portafolios_sugeridos": ("Road works", "Civil works", "Installations",
                                       "Maintenance"),
        },
        "software": {
            "rubro": "Software and technology",
            "resumen": "Product development and IT projects. The dominant risk isn't "
                       "cost — it's scope creep and what breaks on deployment.",
            "etapas": {
                "descubrimiento": {
                    "nombre": "Discovery",
                    "objetivo": "Understand the problem before proposing a solution.",
                    "entregables": ("Problem and users defined",
                                     "Measurable success criteria",
                                     "Minimum viable scope", "Rough estimate"),
                    "criterio_salida": "The sponsor agrees on what problem is being "
                                        "solved and how it's measured.",
                    "aprueba": "Sponsor / Product Owner",
                },
                "diseno": {
                    "nombre": "Technical and functional design",
                    "objetivo": "Define how it gets built and what it integrates with.",
                    "entregables": ("Solution architecture", "Data model",
                                     "Integration definitions",
                                     "Non-functional requirements"),
                    "criterio_salida": "Architecture reviewed; external dependencies "
                                        "confirmed.",
                    "aprueba": "Tech lead",
                },
                "construccion": {
                    "nombre": "Iterative build",
                    "objetivo": "Ship usable, reviewable increments.",
                    "entregables": ("Deployable increments", "Automated tests",
                                     "Minimum technical documentation",
                                     "Demo per iteration"),
                    "criterio_salida": "Agreed functionality built and tested.",
                    "aprueba": "Product Owner",
                },
                "uat": {
                    "nombre": "User acceptance testing",
                    "objetivo": "Have real users confirm it works for them.",
                    "entregables": ("Business test cases", "Issue log",
                                     "User acceptance sign-off"),
                    "criterio_salida": "Critical and high-severity issues closed; user "
                                        "signs off.",
                    "aprueba": "Business stakeholder",
                },
                "despliegue": {
                    "nombre": "Deployment",
                    "objetivo": "Go live without breaking what already works.",
                    "entregables": ("Deployment plan", "Rollback plan",
                                     "Data migration tested", "User training"),
                    "criterio_salida": "System live in production with rollback "
                                        "available.",
                    "aprueba": "Tech lead / Operations",
                },
                "hipercuidado": {
                    "nombre": "Hypercare",
                    "objetivo": "Watch closely through the first few weeks.",
                    "entregables": ("On-call rotation defined", "Issue tracking board",
                                     "Post-launch adjustments"),
                    "criterio_salida": "Incidents stabilized below the agreed threshold.",
                    "aprueba": "Tech lead",
                },
                "cierre_sw": {
                    "nombre": "Handover to operations",
                    "objetivo": "Get the support team able to sustain it without the "
                                "project team.",
                    "entregables": ("Operations documentation", "Handover to support",
                                     "Technical debt logged", "Lessons learned"),
                    "criterio_salida": "Support accepts the handover.",
                    "aprueba": "Operations lead",
                },
            },
            "roles": (
                ("Sponsor", "Approves budget and priorities."),
                ("Product Owner",
                 "Decides what goes into each release and what doesn't."),
                ("Tech lead",
                 "Owns the architecture and signs off on technical quality."),
                ("Business stakeholder",
                 "Confirms the solution actually works for the job."),
                ("Operations / Support",
                 "Accepts or rejects the handover to production."),
            ),
            "riesgos": (
                ("Scope creep",
                 "New requests coming in without anything being dropped in exchange.",
                 "One prioritized backlog: anything that comes in displaces something "
                 "else."),
                ("Third-party dependency",
                 "An integration or vendor that won't confirm dates.",
                 "Confirm API or vendor availability before committing to a deadline."),
                ("Accumulating technical debt",
                 "Delivery velocity dropping iteration over iteration.",
                 "Reserve fixed capacity each iteration for technical debt."),
                ("Mishandled personal data",
                 "Production data used in test environments.",
                 "Anonymize test data and register the database with the data "
                 "protection authority."),
                ("Knowledge concentration",
                 "One person is the only one who understands a critical component.",
                 "Cross-review code and require minimum documentation."),
            ),
            "indicadores": ("Increment delivered per iteration",
                             "Open issues by severity",
                             "Automated test coverage", "Deployment time",
                             "Rework as a share of delivered work"),
            "normativa": ("Ley 18.331 — personal data protection (Uruguay) and "
                           "decreto 414/009",
                           "ISO/IEC 27001 if the company handles sensitive information",
                           "GDPR if there are users or customers in the European Union",
                           "Licenses of any third-party components used"),
            "portafolios_sugeridos": ("Product", "Integrations", "Infrastructure",
                                       "Compliance"),
        },
        "farma": {
            "rubro": "Pharmaceuticals, labs, and medical devices",
            "resumen": "A regulated industry: the traceability of the evidence matters "
                       "as much as the result. If it isn't documented, as far as the "
                       "regulator is concerned it didn't happen.",
            "etapas": {
                "factibilidad": {
                    "nombre": "Feasibility",
                    "objetivo": "Confirm technical and regulatory viability before "
                                "investing.",
                    "entregables": ("Product profile", "Regulatory pathway analysis",
                                     "Intellectual property assessment",
                                     "Investment estimate"),
                    "criterio_salida": "Regulatory pathway defined and approved by "
                                        "Regulatory Affairs.",
                    "aprueba": "Technical management",
                },
                "desarrollo": {
                    "nombre": "Development and formulation",
                    "objetivo": "Arrive at a reproducible formula and process.",
                    "entregables": ("Development protocol", "Preformulation studies",
                                     "Product specifications",
                                     "Stability studies underway"),
                    "criterio_salida": "Formula and process frozen; stability studies "
                                        "in progress.",
                    "aprueba": "R&D / Technical management",
                },
                "validacion": {
                    "nombre": "Validation (IQ / OQ / PQ)",
                    "objetivo": "Document, with evidence, that equipment and processes "
                                "do what they're supposed to.",
                    "entregables": ("Master validation plan",
                                     "IQ, OQ, and PQ protocols and reports",
                                     "Supplier qualification",
                                     "Analytical method validation"),
                    "criterio_salida": "Validation approved by Quality Assurance.",
                    "aprueba": "Quality Assurance",
                },
                "registro": {
                    "nombre": "Regulatory registration",
                    "objetivo": "Obtain authorization to market the product.",
                    "entregables": ("Registration dossier", "Stability data",
                                     "Responses to authority observations"),
                    "criterio_salida": "Registration granted by the health authority.",
                    "aprueba": "Regulatory Affairs",
                },
                "transferencia": {
                    "nombre": "Technology transfer",
                    "objetivo": "Move from pilot scale to industrial production.",
                    "entregables": ("Transfer protocol", "Pilot and validation batches",
                                     "Plant training", "Updated operating procedures"),
                    "criterio_salida": "Validation batches conforming to specification.",
                    "aprueba": "Production / Quality",
                },
                "lanzamiento": {
                    "nombre": "Launch and pharmacovigilance",
                    "objetivo": "Produce at routine scale and monitor the product's "
                                "real-world behavior.",
                    "entregables": ("First commercial batch released",
                                     "Pharmacovigilance system active",
                                     "Post-marketing surveillance plan"),
                    "criterio_salida": "First batch released by Technical management.",
                    "aprueba": "Technical management",
                },
            },
            "roles": (
                ("Technical management",
                 "Releases batches and answers to the health authority."),
                ("Quality Assurance",
                 "Approves validations and closes deviations. Can stop everything."),
                ("Regulatory Affairs",
                 "Defines the registration pathway and liaises with the authority."),
                ("Production", "Executes according to approved procedures."),
                ("R&D", "Develops and documents the technical evidence."),
            ),
            "riesgos": (
                ("Undocumented deviation",
                 "Differences between what was done and the procedure, with no "
                 "record.",
                 "A deviation and CAPA system with deadlines and a named owner for "
                 "each one."),
                ("Compromised data integrity",
                 "Records with no trace of who entered or changed them.",
                 "ALCOA+ principles and records with an audit trail of changes."),
                ("Authority observation during inspection",
                 "Recurring internal-audit findings that never get closed.",
                 "Periodic internal audits and effective closure of findings."),
                ("Regulatory delay",
                 "Regulator observations that reopen the submission.",
                 "Review the dossier before filing and build slack into the "
                 "schedule."),
                ("Unqualified critical-supply vendor",
                 "Supplier changes without requalification.",
                 "Formal qualification and audits of critical suppliers."),
            ),
            "indicadores": ("Open deviations and their age", "Overdue CAPAs",
                             "Rejected batches as a share of production",
                             "Validation plan compliance",
                             "Turnaround time on authority observations"),
            "normativa": ("Good Manufacturing Practice (GMP) as required by the MSP, "
                           "Uruguay's health ministry",
                           "ICH Q7–Q10 guidelines for pharmaceutical quality",
                           "21 CFR Part 11 if exporting to the United States "
                           "(electronic records)",
                           "ALCOA+ data integrity principles",
                           "MSP pharmacovigilance regulations (Uruguay)"),
            "portafolios_sugeridos": ("Product development", "Validations",
                                       "Registrations", "Plant improvement"),
            "nota": "The regulator evaluates the documented evidence, not the intent. "
                    "Every stage has to leave a signed, dated record.",
        },
        "manufactura": {
            "rubro": "Manufacturing and industry",
            "resumen": "Product, line, or plant projects. The gate that matters is the "
                       "start of serial production: everything before it is "
                       "reversible, nothing after it is.",
            "etapas": {
                "concepto": {
                    "nombre": "Concept and feasibility",
                    "objetivo": "Define what will be produced and whether the business "
                                "case holds up.",
                    "entregables": ("Product specification", "Feasibility analysis",
                                     "Target cost", "Estimated volume"),
                    "criterio_salida": "Management approves moving into design.",
                    "aprueba": "Industrial management",
                },
                "diseno_prod": {
                    "nombre": "Product and process design",
                    "objetivo": "Design the product and how it will be manufactured.",
                    "entregables": ("Drawings and specifications",
                                     "Process flow diagram",
                                     "Design and process FMEA", "Control plan"),
                    "criterio_salida": "Design frozen and FMEA actions closed.",
                    "aprueba": "Engineering",
                },
                "utillaje": {
                    "nombre": "Tooling and equipment",
                    "objetivo": "Have tools, molds, and equipment ready.",
                    "entregables": ("Tooling built and tested", "Work instructions",
                                     "Operator training", "Instrument calibration"),
                    "criterio_salida": "Tooling approved, with conforming parts.",
                    "aprueba": "Process engineering",
                },
                "preserie": {
                    "nombre": "Pre-series and sample approval",
                    "objetivo": "Test the process under real conditions before ramping "
                                "up.",
                    "entregables": ("Pilot run", "Process capability study",
                                     "Samples approved by the customer",
                                     "Control plan adjustments"),
                    "criterio_salida": "Process capability within requirements and "
                                        "samples approved.",
                    "aprueba": "Quality",
                },
                "serie": {
                    "nombre": "Serial production",
                    "objetivo": "Produce at routine scale while holding quality and "
                                "cost.",
                    "entregables": ("Line indicators", "Non-conformance log",
                                     "Preventive maintenance in progress"),
                    "criterio_salida": "Production stable at the committed volume and "
                                        "quality.",
                    "aprueba": "Production",
                },
                "cierre_mf": {
                    "nombre": "Close-out and continuous improvement",
                    "objetivo": "Hand over to operations and capture what was learned.",
                    "entregables": ("Handover to production", "Lessons learned",
                                     "Continuous improvement plan"),
                    "criterio_salida": "Operations accepts the handover.",
                    "aprueba": "Industrial management",
                },
            },
            "roles": (
                ("Industrial management",
                 "Approves investment and the start of serial production."),
                ("Product engineering", "Owns the design."),
                ("Process engineering", "Owns how it gets manufactured."),
                ("Quality", "Approves samples and can stop the ramp-up."),
                ("Production", "Executes and reports line indicators."),
            ),
            "riesgos": (
                ("Tooling arrives late",
                 "Delays from the mold or tooling supplier.",
                 "Weekly supplier follow-up, with payment milestones tied to "
                 "progress."),
                ("Insufficient process capability",
                 "Capability studies below target during the pre-series run.",
                 "Don't start serial production without demonstrated capability; fix "
                 "the process first."),
                ("Unit cost above target",
                 "Material consumption or cycle-time overruns in the pilot run.",
                 "Cost the pilot run and review it before committing to a price."),
                ("Critical equipment breakdown",
                 "Preventive maintenance kept getting postponed.",
                 "A maintenance plan with critical spare parts in stock."),
            ),
            "indicadores": ("Line OEE", "Scrap and rework",
                             "Actual vs. target unit cost",
                             "Production plan compliance", "Customer complaints"),
            "normativa": ("ISO 9001 — quality management system",
                           "IATF 16949 for automotive-industry production",
                           "ISO 14001 for environmental commitments",
                           "Applicable machine-safety regulations"),
            "portafolios_sugeridos": ("New products", "Process improvement",
                                       "Plant investment", "Quality"),
        },
        "servicios": {
            "rubro": "Professional and consulting services",
            "resumen": "Projects sold by the hour or by deliverable. Margin is lost in "
                       "unbilled work, not in pricing.",
            "etapas": {
                "propuesta": {
                    "nombre": "Proposal",
                    "objetivo": "Agree on scope, price, and working arrangement before "
                                "starting.",
                    "entregables": ("Proposal with explicit scope", "Hours estimate",
                                     "Commercial terms",
                                     "Assumptions and exclusions in writing"),
                    "criterio_salida": "Proposal accepted in writing.",
                    "aprueba": "Partner / Management",
                },
                "arranque": {
                    "nombre": "Kickoff",
                    "objetivo": "Align expectations and staff the team.",
                    "entregables": ("Kickoff meeting", "Work plan", "Team assigned",
                                     "Reporting channel and frequency agreed"),
                    "criterio_salida": "Client and team aligned on deliverables and "
                                        "dates.",
                    "aprueba": "Project lead",
                },
                "ejecucion_srv": {
                    "nombre": "Delivery",
                    "objetivo": "Deliver what was committed while controlling hours.",
                    "entregables": ("Partial deliverables", "Time log by person",
                                     "Meeting minutes", "Scope-change control"),
                    "criterio_salida": "Deliverables accepted by the client.",
                    "aprueba": "Project lead",
                },
                "cierre_srv": {
                    "nombre": "Close-out and billing",
                    "objetivo": "Collect, close out, and capture the reference.",
                    "entregables": ("Closing report", "Final invoice issued",
                                     "Satisfaction survey",
                                     "Reference case, if the client agrees"),
                    "criterio_salida": "Invoiced and collected; client satisfied.",
                    "aprueba": "Partner / Administration",
                },
            },
            "roles": (
                ("Partner / Management",
                 "Approves the proposal and answers for the margin."),
                ("Project lead",
                 "Manages scope, team, and the client relationship."),
                ("Assigned team", "Delivers the work and logs hours."),
                ("Administration", "Invoices and tracks collections."),
            ),
            "riesgos": (
                ("Unbilled hours",
                 "Hours logged above estimate with no scope change.",
                 "Weekly review of hours against estimate, with early warning to the "
                 "client."),
                ("Scope that stretches bit by bit",
                 "Small out-of-scope requests that nobody quotes.",
                 "Every out-of-scope request gets quoted, however small."),
                ("Client who can't free up their people",
                 "Meetings postponed or deliverables left unreviewed.",
                 "Leave client availability as an explicit assumption in the "
                 "proposal."),
                ("Delayed collections",
                 "Overdue invoices with no follow-up.",
                 "Billing milestones tied to accepted deliverables."),
            ),
            "indicadores": ("Actual vs. estimated hours", "Margin per project",
                             "Share of billable hours", "Days sales outstanding",
                             "Client satisfaction"),
            "normativa": ("Services contract with scope and IP ownership clearly "
                           "defined",
                           "Confidentiality agreements with the client",
                           "Ley 18.331 if client personal data is processed "
                           "(Uruguay)"),
            "portafolios_sugeridos": ("Clients", "Internal", "Pre-sales"),
        },
        "energia": {
            "rubro": "Energy and utilities",
            "resumen": "Generation, transmission, and energy efficiency. "
                       "Environmental permits and the grid connection dictate the "
                       "schedule, not the project team.",
            "etapas": {
                "prefactibilidad": {
                    "nombre": "Pre-feasibility",
                    "objetivo": "Check whether the resource and the site stack up.",
                    "entregables": ("Resource study", "Site analysis",
                                     "Preliminary economic model",
                                     "Preliminary grid-connection inquiry"),
                    "criterio_salida": "Management approves investing in definitive "
                                        "studies.",
                    "aprueba": "Management",
                },
                "ambiental": {
                    "nombre": "Environmental authorization",
                    "objetivo": "Obtain environmental clearance, usually the critical "
                                "path.",
                    "entregables": ("Environmental impact study",
                                     "Environmental management plan",
                                     "Public participation process if applicable"),
                    "criterio_salida": "Preliminary environmental authorization "
                                        "granted.",
                    "aprueba": "Environmental lead",
                },
                "conexion": {
                    "nombre": "Connection agreement",
                    "objetivo": "Secure the connection point and its technical "
                                "conditions.",
                    "entregables": ("Connection study",
                                     "Agreement with the grid operator",
                                     "Substation specification"),
                    "criterio_salida": "Connection point confirmed in writing.",
                    "aprueba": "Engineering",
                },
                "epc": {
                    "nombre": "Engineering, procurement, and construction",
                    "objetivo": "Build the facility.",
                    "entregables": ("Detailed engineering",
                                     "Major equipment purchased",
                                     "Civil works and installation",
                                     "Equipment testing"),
                    "criterio_salida": "Facility installed and tested.",
                    "aprueba": "Project management",
                },
                "puesta_marcha": {
                    "nombre": "Commissioning",
                    "objetivo": "Synchronize with the grid and demonstrate "
                                "performance.",
                    "entregables": ("Test protocol", "Grid synchronization",
                                     "Guaranteed-performance test"),
                    "criterio_salida": "Guaranteed performance demonstrated and "
                                        "accepted.",
                    "aprueba": "Grid operator / Owner",
                },
                "operacion": {
                    "nombre": "Operation and maintenance",
                    "objetivo": "Hand over to operations with a maintenance contract "
                                "in place.",
                    "entregables": ("Operations manual", "O&M contract",
                                     "Staff training", "Documented handover"),
                    "criterio_salida": "Operations accepts the facility.",
                    "aprueba": "Operations",
                },
            },
            "roles": (
                ("Management", "Approves the investment."),
                ("Environmental lead", "Owns environmental compliance."),
                ("Engineering", "Defines the technical solution and the connection."),
                ("Grid operator", "Authorizes connection and synchronization."),
                ("Operations", "Takes delivery of the facility."),
            ),
            "riesgos": (
                ("Delay in environmental clearance",
                 "Observations from the environmental authority that reopen the "
                 "filing.",
                 "File a complete study and plan for realistic response times."),
                ("Social opposition to the project",
                 "Neighbor opposition during the public participation process.",
                 "Early community outreach, ahead of the formal process."),
                ("Grid constraints",
                 "The operator caps the injectable capacity at the requested point.",
                 "Run a preliminary connection inquiry before committing the "
                 "investment."),
                ("Long lead times on major equipment",
                 "Turbine or transformer delivery times that don't fit the "
                 "schedule.",
                 "Reserve critical equipment as soon as the investment is "
                 "approved."),
            ),
            "indicadores": ("Construction progress vs. plan", "Investment variance",
                             "Energy generated vs. forecast", "Facility availability",
                             "Environmental management plan compliance"),
            "normativa": ("Preliminary Environmental Authorization from Uruguay's "
                           "Ministry of Environment",
                           "URSEC regulations for the energy sector (Uruguay)",
                           "Grid operator's connection conditions (UTE, in Uruguay)",
                           "Applicable electrical safety regulations"),
            "portafolios_sugeridos": ("Generation", "Transmission and distribution",
                                       "Energy efficiency"),
        },
        "salud": {
            "rubro": "Healthcare and medical institutions",
            "resumen": "Projects inside healthcare providers. Every change touches "
                       "patient care, so the gate that matters is not degrading the "
                       "service.",
            "etapas": {
                "necesidad": {
                    "nombre": "Care need",
                    "objetivo": "Define what care problem is being solved.",
                    "entregables": ("Clinical justification", "Affected population",
                                     "Baseline care indicators"),
                    "criterio_salida": "Medical management endorses the need.",
                    "aprueba": "Medical management",
                },
                "diseno_salud": {
                    "nombre": "Service design",
                    "objetivo": "Define the care process and the resources it needs.",
                    "entregables": ("Care protocol",
                                     "Required staff and equipment",
                                     "Patient pathway", "Licensing requirements"),
                    "criterio_salida": "Protocol approved by the relevant committee.",
                    "aprueba": "Medical management / Committee",
                },
                "habilitacion": {
                    "nombre": "Licensing",
                    "objetivo": "Meet what the health authority requires.",
                    "entregables": ("Licensing file", "Facility adaptation",
                                     "Equipment authorization",
                                     "Staff with registered credentials"),
                    "criterio_salida": "License granted.",
                    "aprueba": "Licensing lead",
                },
                "implementacion": {
                    "nombre": "Implementation",
                    "objetivo": "Go live without interrupting care.",
                    "entregables": ("Transition plan",
                                     "Care staff training",
                                     "Parallel run if replacing an existing process"),
                    "criterio_salida": "Service running with staff trained.",
                    "aprueba": "Service head",
                },
                "seguimiento": {
                    "nombre": "Care follow-up",
                    "objetivo": "Verify that what needed improving actually "
                                "improved.",
                    "entregables": ("Post-implementation care indicators",
                                     "Adverse event log", "Protocol adjustments"),
                    "criterio_salida": "Indicators at the committed level, with no "
                                        "attributable adverse events.",
                    "aprueba": "Medical management",
                },
                "cierre_salud": {
                    "nombre": "Close-out",
                    "objetivo": "Fold the service into normal operations.",
                    "entregables": ("Protocol added to the manual",
                                     "Handover to operations", "Lessons learned"),
                    "criterio_salida": "Service folded into routine operations.",
                    "aprueba": "Management",
                },
            },
            "roles": (
                ("Medical management",
                 "Endorses clinical fit. Can stop the project."),
                ("Service head", "Runs and answers for day-to-day operations."),
                ("Quality / patient safety committee",
                 "Reviews care-related risks."),
                ("Licensing lead", "Handles matters with the health authority."),
                ("Systems liaison", "Integrates with the electronic health record."),
            ),
            "riesgos": (
                ("Interruption of care",
                 "Changes pushed to production with no contingency plan.",
                 "Parallel transition, with a rollback plan always available."),
                ("Staff not trained in time",
                 "Training postponed due to care workload.",
                 "Train within working hours, with coverage arranged in advance."),
                ("Patient data exposed",
                 "Overly broad access, or production data used in testing.",
                 "Least-privilege access and anonymized data in test environments."),
                ("Adverse event tied to the change",
                 "A rise in reported incidents after implementation.",
                 "Intensive monitoring for the first few weeks and a defined "
                 "rollback trigger."),
            ),
            "indicadores": ("Patient wait time", "Reported adverse events",
                             "Coverage of the target population",
                             "Protocol adherence", "Patient satisfaction"),
            "normativa": ("Health service licensing with the MSP, Uruguay's health "
                           "ministry",
                           "Ley 18.335 — patient and user rights and obligations "
                           "(Uruguay)",
                           "Ley 18.331 — personal data, with health data as a "
                           "sensitive category (Uruguay)",
                           "National electronic health record regulations "
                           "(Uruguay)"),
            "portafolios_sugeridos": ("Care services", "Equipment", "Systems",
                                       "Quality and safety"),
        },
        "financiero": {
            "rubro": "Banking, finance, and insurance",
            "resumen": "A supervised industry. Every significant change has to be "
                       "explainable to the regulator and to internal audit.",
            "etapas": {
                "caso_negocio": {
                    "nombre": "Business case",
                    "objetivo": "Justify the investment and its impact on risk.",
                    "entregables": ("Business case",
                                     "Operational risk assessment",
                                     "Regulatory impact", "Committee approval"),
                    "criterio_salida": "Committee approves the initiative.",
                    "aprueba": "Management committee",
                },
                "diseno_fin": {
                    "nombre": "Design and controls",
                    "objetivo": "Define the solution and the controls that go with "
                                "it.",
                    "entregables": ("Functional design", "Control matrix",
                                     "Information security assessment",
                                     "Business continuity analysis"),
                    "criterio_salida": "Risk and Security approve the design.",
                    "aprueba": "Risk / Information security",
                },
                "construccion_fin": {
                    "nombre": "Build and testing",
                    "objetivo": "Build with enough test evidence to satisfy an "
                                "audit.",
                    "entregables": ("Development or configuration",
                                     "Documented functional testing",
                                     "Security testing", "Environment segregation"),
                    "criterio_salida": "Testing closed with evidence on file.",
                    "aprueba": "Project lead",
                },
                "aprobacion_reg": {
                    "nombre": "Regulatory approval",
                    "objetivo": "Obtain any required authorizations or make the "
                                "required disclosures.",
                    "entregables": ("Regulator notification, if applicable",
                                     "Manuals and policies updated",
                                     "Approval on record"),
                    "criterio_salida": "Authorization obtained or notification "
                                        "filed.",
                    "aprueba": "Compliance",
                },
                "salida_prod": {
                    "nombre": "Go-live",
                    "objetivo": "Deploy under formal change control.",
                    "entregables": ("Approved change request", "Rollback plan",
                                     "User training", "Enhanced monitoring"),
                    "criterio_salida": "Change live in production with approval on "
                                        "record.",
                    "aprueba": "Change advisory board",
                },
                "cierre_fin": {
                    "nombre": "Close-out and review",
                    "objetivo": "Verify the controls actually work in practice.",
                    "entregables": ("Post-implementation review",
                                     "Controls operating", "Findings closed",
                                     "Lessons learned"),
                    "criterio_salida": "Internal audit with no open findings.",
                    "aprueba": "Internal audit",
                },
            },
            "roles": (
                ("Management committee",
                 "Approves the investment and the risk appetite."),
                ("Risk", "Assesses operational risk. Can block."),
                ("Compliance", "Owns regulatory matters."),
                ("Information security", "Approves the security design."),
                ("Internal audit", "Reviews evidence and raises findings."),
            ),
            "riesgos": (
                ("Regulatory finding",
                 "Controls designed on paper but not operating in practice.",
                 "Test controls in production, not just document them."),
                ("Customer data breach or exposure",
                 "Unreviewed access, or production data outside the secure "
                 "environment.",
                 "Periodic access reviews and masking in non-production "
                 "environments."),
                ("Service unavailability",
                 "Changes made with no window or rollback plan.",
                 "Defined change windows and a tested rollback plan."),
                ("Insufficient evidence for audit",
                 "Approvals given verbally or over informal channels.",
                 "Every approval is logged with owner and date."),
            ),
            "indicadores": ("Open audit findings", "Security incidents",
                             "Availability of critical services",
                             "Changes with rollback executed",
                             "Control plan compliance"),
            "normativa": ("Banco Central del Uruguay regulations applicable to the "
                           "institution",
                           "Ley 18.331 — personal data protection (Uruguay)",
                           "Ley 19.574 — anti–money laundering (Uruguay)",
                           "PCI-DSS if card data is processed",
                           "ISO/IEC 27001 for information security management"),
            "portafolios_sugeridos": ("Regulatory", "Products", "Digital channels",
                                       "Risk and control"),
        },
        "agro": {
            "rubro": "Agriculture and agribusiness",
            "resumen": "The season calls the shots: the planting or harvest window "
                       "isn't negotiable, and a two-week delay can cost the whole "
                       "year.",
            "etapas": {
                "planificacion_zafra": {
                    "nombre": "Season planning",
                    "objetivo": "Decide what, where, and how much, before the window "
                                "opens.",
                    "entregables": ("Season plan", "Input budget",
                                     "Machinery availability", "Soil analysis"),
                    "criterio_salida": "Plan approved before the window opens.",
                    "aprueba": "Management / Production management",
                },
                "insumos": {
                    "nombre": "Input purchasing",
                    "objetivo": "Secure seed, fertilizer, and agrochemicals on time.",
                    "entregables": ("Purchase orders",
                                     "Delivery logistics agreed",
                                     "Financing confirmed"),
                    "criterio_salida": "Inputs on the ground before the window "
                                        "opens.",
                    "aprueba": "Procurement",
                },
                "implantacion": {
                    "nombre": "Planting",
                    "objetivo": "Plant within the correct window.",
                    "entregables": ("Field-work log", "Planting quality control",
                                     "Application log"),
                    "criterio_salida": "Area planted within the window.",
                    "aprueba": "Production management",
                },
                "seguimiento_cultivo": {
                    "nombre": "Crop monitoring",
                    "objetivo": "Monitor and act in time.",
                    "entregables": ("Pest and disease monitoring", "Application log",
                                     "Yield estimate"),
                    "criterio_salida": "Crop with no unresolved health issues.",
                    "aprueba": "Agronomist",
                },
                "cosecha": {
                    "nombre": "Harvest",
                    "objetivo": "Bring in the crop with the least possible loss.",
                    "entregables": ("Harvest plan", "Yield log by field",
                                     "Moisture and quality control",
                                     "Lot traceability"),
                    "criterio_salida": "Crop harvested and stored or delivered.",
                    "aprueba": "Production management",
                },
                "cierre_zafra": {
                    "nombre": "Season close-out",
                    "objetivo": "Close the numbers and learn for next time.",
                    "entregables": ("Financial result by field",
                                     "Variance analysis",
                                     "Plan for the next season"),
                    "criterio_salida": "Result closed and analyzed.",
                    "aprueba": "Management",
                },
            },
            "roles": (
                ("Management", "Approves the season plan and the investment."),
                ("Production management", "Executes field work on time."),
                ("Agronomist", "Decides crop and nutrition management."),
                ("Procurement", "Secures inputs before the window opens."),
                ("Traceability lead",
                 "Answers to certifiers and regulatory bodies."),
            ),
            "riesgos": (
                ("Missed planting or harvest window",
                 "Inputs or machinery not ready when the window opens.",
                 "Inputs on the ground well ahead of time, and machinery "
                 "contracted in advance."),
                ("Weather event",
                 "Adverse forecasts holding through the critical period.",
                 "Spread dates and fields; consider crop insurance."),
                ("Falling commodity price",
                 "Prices dropping against costs already committed.",
                 "Partial price hedging at the point inputs are committed."),
                ("Traceability failure",
                 "Application records incomplete or logged late.",
                 "Log field work as it happens, not at the end of the season."),
            ),
            "indicadores": ("Yield per hectare", "Cost per hectare",
                             "Area planted within window", "Margin per field",
                             "Traceability record compliance"),
            "normativa": ("Registrations with Uruguay's Dirección General de "
                           "Servicios Agrícolas",
                           "INAC / SNIG livestock traceability (Uruguay), if "
                           "applicable",
                           "Soil use and management plan filed with the Ministry of "
                           "Livestock (Uruguay)",
                           "Voluntary certifications required by the destination "
                           "market"),
            "portafolios_sugeridos": ("Crops", "Livestock", "Farm infrastructure",
                                       "Certifications"),
        },
        "publico": {
            "rubro": "Public sector and government agencies",
            "resumen": "Everything runs through the procurement process and prior "
                       "oversight review. The regulations set the schedule, not the "
                       "project team.",
            "etapas": {
                "necesidad_pub": {
                    "nombre": "Defining the need",
                    "objetivo": "Justify the need and secure budget availability.",
                    "entregables": ("Justification of the need",
                                     "Budget availability",
                                     "Authorization from the agency head"),
                    "criterio_salida": "Spending authorized with funds available.",
                    "aprueba": "Agency head",
                },
                "pliego": {
                    "nombre": "Drafting the bid documents",
                    "objetivo": "Define what's being procured and how it will be "
                                "evaluated, without steering the outcome.",
                    "entregables": ("Bid-specific terms", "Technical specifications",
                                     "Objective evaluation criteria",
                                     "Timeline for the call"),
                    "criterio_salida": "Bid documents approved by the competent "
                                        "authority.",
                    "aprueba": "Advisory committee / Legal",
                },
                "llamado": {
                    "nombre": "Call for bids and award",
                    "objetivo": "Run the process transparently.",
                    "entregables": ("Call published", "Bid-opening record",
                                     "Advisory committee report",
                                     "Award resolution"),
                    "criterio_salida": "Award resolved and cleared by prior "
                                        "oversight review.",
                    "aprueba": "Spending officer",
                },
                "ejecucion_pub": {
                    "nombre": "Contract execution",
                    "objetivo": "Confirm that what was contracted actually gets "
                                "delivered.",
                    "entregables": ("Partial acceptance records",
                                     "Contract compliance monitoring",
                                     "Log of breaches and penalties"),
                    "criterio_salida": "Delivery accepted as contracted.",
                    "aprueba": "Contract manager",
                },
                "rendicion": {
                    "nombre": "Accountability and close-out",
                    "objetivo": "Account for the spending and close the file.",
                    "entregables": ("Accountability report", "Complete file",
                                     "Results report", "Contract closed"),
                    "criterio_salida": "Accountability approved with no pending "
                                        "observations.",
                    "aprueba": "Comptroller / Audit",
                },
            },
            "roles": (
                ("Agency head", "Authorizes the spending."),
                ("Spending officer", "Resolves the award."),
                ("Bid advisory committee",
                 "Evaluates bids and makes a recommendation."),
                ("Legal", "Reviews the legality of the process."),
                ("Comptroller / prior oversight",
                 "Clears the spending. Can raise an observation."),
            ),
            "riesgos": (
                ("Observation from prior oversight review",
                 "Files sent back for missing documentation.",
                 "A complete-file checklist before submitting it up the chain."),
                ("Void call, or a single bidder",
                 "Few inquiries, or requirements that limit competition.",
                 "Consult the market beforehand and review any overly restrictive "
                 "requirements."),
                ("Challenge to the process",
                 "Ambiguous or discretionary evaluation criteria.",
                 "Objective, weighted criteria, published from the start."),
                ("Fiscal year deadline missed",
                 "Processes that don't close before the fiscal year ends.",
                 "Plan the call around the real legal deadlines, not the desired "
                 "ones."),
            ),
            "indicadores": ("Procurement process duration",
                             "Void or challenged calls", "Budget execution",
                             "Prior oversight observations",
                             "Contractual deadline compliance"),
            "normativa": ("TOCAF — Uruguay's public accounting and financial "
                           "administration code",
                           "Prior oversight by the Tribunal de Cuentas (Uruguay's "
                           "court of audit)",
                           "Publication on Uruguay's Compras Estatales portal",
                           "Ley 18.381 — access to public information "
                           "(Uruguay)",
                           "Ley 19.889 and applicable administrative procedure "
                           "rules (Uruguay)"),
            "portafolios_sugeridos": ("Public investment", "Procurement and "
                                       "supplies", "Management modernization",
                                       "Agreements"),
            "nota": "In government, the schedule is set by procurement law. "
                    "Planning around the real legal deadlines, not the desired "
                    "ones, is the difference between spending the budget and "
                    "losing it.",
        },
        "retail": {
            "rubro": "Retail and consumer goods",
            "resumen": "Everything revolves around the season. Missing a commercial "
                       "date doesn't come back around — that sale is gone for "
                       "good.",
            "etapas": {
                "plan_comercial": {
                    "nombre": "Commercial plan",
                    "objetivo": "Define assortment, season, and sales target.",
                    "entregables": ("Assortment plan", "Sales and margin target",
                                     "Commercial calendar", "Buying budget"),
                    "criterio_salida": "Plan approved before the buying season "
                                        "starts.",
                    "aprueba": "Commercial management",
                },
                "abastecimiento": {
                    "nombre": "Sourcing",
                    "objetivo": "Buy and bring in merchandise on time.",
                    "entregables": ("Purchase orders", "Logistics and import plan",
                                     "Supplier quality control"),
                    "criterio_salida": "Merchandise in the warehouse before the "
                                        "floor-set date.",
                    "aprueba": "Buying / Logistics",
                },
                "implantacion_retail": {
                    "nombre": "Store rollout",
                    "objetivo": "Get the product on the floor with the defined "
                                "display.",
                    "entregables": ("Planogram", "Point-of-sale material",
                                     "Store staff training", "Prices loaded"),
                    "criterio_salida": "Product on the floor per planogram in every "
                                        "store.",
                    "aprueba": "Store operations",
                },
                "temporada": {
                    "nombre": "Season",
                    "objetivo": "Sell and react fast to what's happening.",
                    "entregables": ("Daily sales tracking", "Replenishment",
                                     "Price and promotion adjustments"),
                    "criterio_salida": "Sales and margin target reached.",
                    "aprueba": "Commercial management",
                },
                "liquidacion": {
                    "nombre": "Markdown and close-out",
                    "objetivo": "Clear the remainder and close the result.",
                    "entregables": ("Markdown plan", "Season result",
                                     "Stockout and overstock analysis"),
                    "criterio_salida": "Remaining stock within target.",
                    "aprueba": "Commercial management",
                },
            },
            "roles": (
                ("Commercial management",
                 "Defines the assortment and approves the plan."),
                ("Buying", "Negotiates and secures supply."),
                ("Logistics", "Owns getting the merchandise there on time."),
                ("Store operations", "Executes the store rollout."),
                ("Marketing", "Drives the season's campaign."),
            ),
            "riesgos": (
                ("Merchandise arriving late",
                 "Shipping delays or customs holdups.",
                 "Build slack into the import plan and track the shipment."),
                ("Stockout on a hero product",
                 "Sell-through outpacing the forecast with no replenishment in "
                 "place.",
                 "Automatic threshold-based replenishment and a backup supplier "
                 "identified."),
                ("Overstock at close-out",
                 "Sales tracking below forecast mid-season.",
                 "Checkpoints with an early markdown decision."),
                ("Uneven rollout across stores",
                 "Floor audits showing gaps against the planogram.",
                 "Audit the rollout in the first days of the season."),
            ),
            "indicadores": ("Sales vs. target by category", "Margin by category",
                             "Stockouts", "Inventory turnover",
                             "Planogram compliance"),
            "normativa": ("Ley 17.250 — consumer protection (Uruguay)",
                           "Product labeling regulations",
                           "Promotions and sales-offer regulations",
                           "Customs regulations for imported merchandise"),
            "portafolios_sugeridos": ("Seasons", "New stores", "E-commerce",
                                       "Supply chain"),
        },
        "educacion": {
            "rubro": "Education and training",
            "resumen": "The academic calendar is a hard constraint: whatever isn't "
                       "ready by the start of the term waits for the next one.",
            "etapas": {
                "diseno_academico": {
                    "nombre": "Academic design",
                    "objetivo": "Define the program and its rationale.",
                    "entregables": ("Graduate profile", "Curriculum",
                                     "Rationale for the program",
                                     "Enrollment estimate"),
                    "criterio_salida": "Proposal approved by the academic body.",
                    "aprueba": "Council / Academic management",
                },
                "aprobacion_academica": {
                    "nombre": "Approval and accreditation",
                    "objetivo": "Obtain official recognition, if required.",
                    "entregables": ("Approval file",
                                     "Accreditation documentation",
                                     "Responses to observations"),
                    "criterio_salida": "Proposal approved or accredited by the "
                                        "education authority.",
                    "aprueba": "Academic management",
                },
                "preparacion": {
                    "nombre": "Course preparation",
                    "objetivo": "Have instructors, materials, and classrooms ready.",
                    "entregables": ("Instructors assigned",
                                     "Materials and reading list",
                                     "Classrooms and platform assigned",
                                     "Course schedule"),
                    "criterio_salida": "Everything ready before the term starts.",
                    "aprueba": "Academic coordination",
                },
                "dictado": {
                    "nombre": "Delivery",
                    "objetivo": "Teach the course and support students.",
                    "entregables": ("Attendance record", "Assessments administered",
                                     "Dropout tracking"),
                    "criterio_salida": "Course fully delivered as planned.",
                    "aprueba": "Academic coordination",
                },
                "evaluacion_curso": {
                    "nombre": "Course evaluation",
                    "objetivo": "Measure results and satisfaction.",
                    "entregables": ("Pass rate results", "Student survey",
                                     "Instructor evaluation"),
                    "criterio_salida": "Indicators within expected range.",
                    "aprueba": "Academic management",
                },
                "cierre_edu": {
                    "nombre": "Close-out and improvement",
                    "objetivo": "Close the term and adjust the next one.",
                    "entregables": ("Grade records closed",
                                     "Diploma or certificate issued",
                                     "Improvement plan for the next term"),
                    "criterio_salida": "Grades closed and certificates issued.",
                    "aprueba": "Registrar / Management",
                },
            },
            "roles": (
                ("Academic management",
                 "Approves the program and owns quality."),
                ("Academic coordination", "Manages delivery."),
                ("Faculty", "Teaches and grades."),
                ("Registrar", "Owns grade records and certifications."),
                ("Administrative management",
                 "Approves budget and resources."),
            ),
            "riesgos": (
                ("Enrollment below break-even",
                 "Slow sign-ups close to the deadline.",
                 "A decision point with a firm date to launch or postpone the "
                 "term."),
                ("Key instructor falls through",
                 "Availability confirmations that never arrive.",
                 "A backup identified for every critical subject."),
                ("High dropout",
                 "Attendance drops in the first weeks.",
                 "Early follow-up and outreach to whoever is missing."),
                ("Official approval running late",
                 "Filing with observations close to the start of term.",
                 "Start the process a full academic term ahead."),
            ),
            "indicadores": ("Enrollment vs. target", "Pass rate", "Dropout rate",
                             "Student satisfaction", "Cost per student"),
            "normativa": ("Recognition of the relevant education level (MEC / ANEP "
                           "in Uruguay)",
                           "Program accreditation regulations, if applicable",
                           "Ley 18.331 — student personal data, with minors as "
                           "a sensitive category (Uruguay)",
                           "Institution's academic regulations"),
            "portafolios_sugeridos": ("Academic offering", "Infrastructure",
                                       "Educational technology", "Outreach"),
        },
        "logistica": {
            "rubro": "Logistics, transport, and foreign trade",
            "resumen": "Network, warehouse, and transport projects. Customs and "
                       "transit times don't depend on the team, and the plan has to "
                       "account for that.",
            "etapas": {
                "diseno_red": {
                    "nombre": "Operation design",
                    "objetivo": "Define how goods will flow.",
                    "entregables": ("Flow and volume analysis", "Network design",
                                     "Logistics cost model"),
                    "criterio_salida": "Management approves the design and the "
                                        "investment.",
                    "aprueba": "Operations management",
                },
                "infraestructura": {
                    "nombre": "Infrastructure and systems",
                    "objetivo": "Have warehouse, fleet, and systems ready.",
                    "entregables": ("Warehouse licensed",
                                     "Fleet or carriers contracted",
                                     "Warehouse management system configured",
                                     "Transport permits"),
                    "criterio_salida": "Infrastructure licensed and systems "
                                        "tested.",
                    "aprueba": "Operations / Systems",
                },
                "puesta_operacion": {
                    "nombre": "Go-live",
                    "objetivo": "Start operations without cutting off service.",
                    "entregables": ("Operation migration plan", "Staff training",
                                     "Parallel run if replacing another "
                                     "operation"),
                    "criterio_salida": "Operation running at the agreed service "
                                        "levels.",
                    "aprueba": "Operations management",
                },
                "estabilizacion": {
                    "nombre": "Stabilization",
                    "objetivo": "Adjust until the operation is predictable.",
                    "entregables": ("Service-level indicators", "Incident log",
                                     "Process adjustments"),
                    "criterio_salida": "Service level sustained at target.",
                    "aprueba": "Operations management",
                },
                "cierre_log": {
                    "nombre": "Close-out",
                    "objetivo": "Hand over to routine operations.",
                    "entregables": ("Documented procedures",
                                     "Handover to operations",
                                     "Result vs. cost model"),
                    "criterio_salida": "Operation accepted as routine.",
                    "aprueba": "Management",
                },
            },
            "roles": (
                ("Operations management",
                 "Approves the design and owns the service."),
                ("Warehouse management", "Runs day-to-day operations."),
                ("Customs broker", "Owns the foreign-trade paperwork."),
                ("Systems", "Configures and integrates the management system."),
                ("Commercial", "Commits service levels to the client."),
            ),
            "riesgos": (
                ("Customs delay",
                 "Incomplete documentation or a disputed tariff classification.",
                 "Document review before shipping and a confirmed "
                 "classification."),
                ("Service cut during the migration",
                 "Migration with no parallel run and no contingency plan.",
                 "Run in parallel with a defined rollback trigger."),
                ("Logistics cost above model",
                 "Freight-rate or warehouse-occupancy variances.",
                 "Contracts with agreed rates and monthly tracking against the "
                 "model."),
                ("Missing or damaged goods",
                 "Recurring inventory discrepancies.",
                 "Cycle counts and access control at the warehouse."),
            ),
            "indicadores": ("On-time, in-full deliveries",
                             "Logistics cost as a share of sales",
                             "Inventory accuracy", "Customs clearance time",
                             "Warehouse occupancy"),
            "normativa": ("Uruguay's customs code and Dirección Nacional de "
                           "Aduanas regulations",
                           "Foreign trade single window (VUCE, Uruguay)",
                           "MTOP freight transport permits (Uruguay)",
                           "Dangerous goods regulations, if applicable"),
            "portafolios_sugeridos": ("Logistics network", "Warehouses",
                                       "Transport", "Foreign trade"),
        },
        "telecom": {
            "rubro": "Telecommunications",
            "resumen": "Network and service rollout. Site permits and spectrum "
                       "drive the schedule, and they're the least controllable part "
                       "of the project.",
            "etapas": {
                "diseno_red_tel": {
                    "nombre": "Network design",
                    "objetivo": "Define coverage, capacity, and technology.",
                    "entregables": ("Coverage study", "Capacity sizing",
                                     "Technology selection", "Business case"),
                    "criterio_salida": "Management approves the design and the "
                                        "investment.",
                    "aprueba": "Technical management",
                },
                "espectro_permisos": {
                    "nombre": "Spectrum and permits",
                    "objetivo": "Secure spectrum and site permits.",
                    "entregables": ("Spectrum-use authorization",
                                     "Municipal site permits",
                                     "Site lease agreements",
                                     "Non-ionizing radiation studies"),
                    "criterio_salida": "Permits granted for the first-phase sites.",
                    "aprueba": "Regulatory",
                },
                "despliegue": {
                    "nombre": "Rollout",
                    "objetivo": "Install and bring the sites into service.",
                    "entregables": ("Sites built",
                                     "Equipment installed and configured",
                                     "Transmission links live",
                                     "Coverage tests"),
                    "criterio_salida": "Sites in service with measured coverage.",
                    "aprueba": "Deployment engineering",
                },
                "integracion_serv": {
                    "nombre": "Service integration",
                    "objetivo": "Get the service working end to end.",
                    "entregables": ("Core network integration", "Service testing",
                                     "Billing and provisioning configuration"),
                    "criterio_salida": "Service tested end to end.",
                    "aprueba": "Engineering",
                },
                "lanzamiento_tel": {
                    "nombre": "Commercial launch",
                    "objetivo": "Go to market with operations ready to sustain "
                                "it.",
                    "entregables": ("Commercial plan",
                                     "Customer care training",
                                     "Service quality monitoring"),
                    "criterio_salida": "Service commercialized with quality within "
                                        "target.",
                    "aprueba": "Commercial management",
                },
                "cierre_tel": {
                    "nombre": "Handover to operations",
                    "objetivo": "Get operations able to sustain the network "
                                "without the project team.",
                    "entregables": ("Network documentation",
                                     "Handover to operations and maintenance",
                                     "Lessons learned"),
                    "criterio_salida": "Operations accepts the handover.",
                    "aprueba": "Technical management",
                },
            },
            "roles": (
                ("Technical management",
                 "Approves the design and the investment."),
                ("Regulatory", "Manages spectrum and permits with the regulator."),
                ("Deployment engineering", "Executes the installation."),
                ("Network operations", "Receives and sustains the network."),
                ("Commercial management", "Defines the launch."),
            ),
            "riesgos": (
                ("Site permit denied",
                 "Neighbor opposition or a municipal rejection at key sites.",
                 "Alternate sites identified from the design stage."),
                ("Delay in spectrum allocation",
                 "A regulatory process with no resolution date.",
                 "Start the process before committing to a launch date."),
                ("Long equipment lead times",
                 "Manufacturer delivery times that don't fit the plan.",
                 "Early orders for critical equipment."),
                ("Service quality below commitment",
                 "Coverage or capacity measurements below design.",
                 "Measure every site before commercial activation."),
            ),
            "indicadores": ("Sites in service vs. plan", "Coverage achieved",
                             "Measured service quality",
                             "Investment executed vs. budget",
                             "Commercial activations"),
            "normativa": ("URSEC regulations — Uruguay's communications "
                           "services regulator",
                           "Radio spectrum use authorization",
                           "Municipal antenna installation regulations",
                           "Non-ionizing radiation exposure limits"),
            "portafolios_sugeridos": ("Network rollout", "Services",
                                       "Digital transformation", "Regulatory"),
        },
    },
    "pt": {
        "construccion": {
            "rubro": "Construção e infraestrutura",
            "resumen": "Obras civis, viárias e de infraestrutura. Governadas "
                       "por certificação de avanço e por "
                       "segurança: o acidente de trabalho é o risco que "
                       "pode parar a obra inteira.",
            "etapas": {
                "anteproyecto": {
                    "nombre": "Anteprojeto",
                    "objetivo": "Definir o que será construído e se o "
                                "negócio fecha economicamente.",
                    "entregables": ("Memorial descritivo", "Estimativa de custo "
                                     "±30%", "Estudo de solo preliminar",
                                     "Análise de viabilidade"),
                    "criterio_salida": "O patrocinador aprova seguir investindo no "
                                        "projeto executivo.",
                    "aprueba": "Patrocinador / Diretoria",
                },
                "ejecutivo": {
                    "nombre": "Projeto executivo",
                    "objetivo": "Levar o projeto ao nível construtivo, com "
                                "quantitativos e orçamento fechado.",
                    "entregables": ("Plantas executivas",
                                     "Levantamento quantitativo",
                                     "Orçamento detalhado",
                                     "Cronograma com caminho crítico",
                                     "Caderno de especificações "
                                     "técnicas"),
                    "criterio_salida": "Orçamento e prazo aprovados; "
                                        "licenças municipais iniciadas.",
                    "aprueba": "Direção de obra",
                },
                "permisos": {
                    "nombre": "Licenças e autorizações",
                    "objetivo": "Obter tudo o que habilita a começar sem "
                                "risco de embargo.",
                    "entregables": ("Alvará de construção",
                                     "Comunicação de obra ao BPS",
                                     "Plano de segurança e saúde",
                                     "Estudo de impacto ambiental, se "
                                     "aplicável"),
                    "criterio_salida": "Licenças concedidas e obra "
                                        "registrada.",
                    "aprueba": "Responsável técnico",
                },
                "licitacion": {
                    "nombre": "Contratação",
                    "objetivo": "Escolher empreiteiros e fechar condições.",
                    "entregables": ("Edital de licitação",
                                     "Comparativo de propostas",
                                     "Contratos assinados",
                                     "Garantias de cumprimento"),
                    "criterio_salida": "Contratos assinados com prazos e multas "
                                        "definidos.",
                    "aprueba": "Compras / Diretoria",
                },
                "obra": {
                    "nombre": "Execução da obra",
                    "objetivo": "Construir conforme o projeto, controlando "
                                "avanço, custo e segurança.",
                    "entregables": ("Certificados de avanço mensais",
                                     "Diário de obra em dia",
                                     "Registro de não conformidades",
                                     "Ordens de alteração documentadas"),
                    "criterio_salida": "Obra concluída conforme projeto e "
                                        "com as observações resolvidas.",
                    "aprueba": "Direção de obra",
                },
                "recepcion_provisoria": {
                    "nombre": "Recebimento provisório",
                    "objetivo": "Receber a obra registrando o que ainda falta "
                                "corrigir.",
                    "entregables": ("Termo de recebimento provisório",
                                     "Lista de pendências (punch list)",
                                     "Plantas as built"),
                    "criterio_salida": "Termo assinado; começa o período "
                                        "de garantia.",
                    "aprueba": "Contratante",
                },
                "recepcion_definitiva": {
                    "nombre": "Recebimento definitivo",
                    "objetivo": "Encerrar o contrato após vencida a "
                                "garantia.",
                    "entregables": ("Termo de recebimento definitivo",
                                     "Liberação das garantias",
                                     "Manual de manutenção",
                                     "Lições aprendidas"),
                    "criterio_salida": "Garantias liberadas e contrato "
                                        "encerrado.",
                    "aprueba": "Contratante / Jurídico",
                },
            },
            "roles": (
                ("Contratante", "Aprova aditivos e assina os recebimentos."),
                ("Direção de obra",
                 "Certifica o avanço e aceita ou recusa serviços."),
                ("Responsável técnico",
                 "Responde perante a prefeitura pela obra."),
                ("Técnico de segurança do trabalho",
                 "Pode parar a obra por risco de acidente."),
                ("Encarregado / Mestre de obras",
                 "Executa o dia a dia e reporta o avanço real."),
            ),
            "riesgos": (
                ("Acidente de trabalho",
                 "Observações de segurança sem solução, "
                 "ou pessoal sem equipamento de proteção.",
                 "Plano de segurança vigente, diálogos diários de "
                 "segurança e auditorias do técnico de "
                 "segurança."),
                ("Aditivos de obra não controlados",
                 "Serviços executados sem ordem de alteração "
                 "assinada.",
                 "Nada é executado sem ordem de alteração "
                 "aprovada por escrito."),
                ("Atraso por clima",
                 "Dias perdidos acumulados acima do previsto no cronograma.",
                 "Prever dias de chuva por estação e deixar folga nas "
                 "tarefas a céu aberto."),
                ("Falta ou alta de materiais",
                 "Prazos de entrega que se estendem ou cotações que "
                 "vencem antes da compra.",
                 "Compras antecipadas do que é crítico e cláusulas "
                 "de reajuste nos contratos."),
                ("Divergências com o projeto executivo",
                 "Consultas recorrentes da obra por plantas incompletas ou "
                 "contraditórias.",
                 "Revisão cruzada das plantas antes de licitar."),
            ),
            "indicadores": ("Avanço físico vs. avanço certificado",
                             "Desvio de prazo por marco",
                             "Custo executado vs. orçado por item",
                             "Acidentes e dias perdidos",
                             "Aditivos aprovados sobre o contrato original"),
            "normativa": ("Ley 16.074 — seguro de acidentes de trabalho "
                           "(Uruguai)",
                           "Decreto 125/014 — segurança e saúde na "
                           "indústria da construção (Uruguai)",
                           "Registro de obra e contribuições ao BPS, a "
                           "previdência social uruguaia",
                           "Normativa municipal de construção da "
                           "prefeitura correspondente (Uruguai)",
                           "Normas UNIT (padrões técnicos uruguaios) "
                           "aplicáveis a materiais e ensaios"),
            "portafolios_sugeridos": ("Obras viárias", "Obras civis",
                                       "Instalações",
                                       "Manutenção"),
        },
        "software": {
            "rubro": "Software e tecnologia",
            "resumen": "Desenvolvimento de produto e projetos de TI. O risco "
                       "dominante não é o custo, e sim o escopo que se move e o "
                       "que quebra na hora do deploy.",
            "etapas": {
                "descubrimiento": {
                    "nombre": "Descoberta",
                    "objetivo": "Entender o problema antes de propor a solução.",
                    "entregables": ("Problema e usuários definidos",
                                     "Critérios de sucesso mensuráveis",
                                     "Escopo mínimo viável",
                                     "Estimativa preliminar"),
                    "criterio_salida": "O patrocinador combina qual problema será "
                                        "resolvido e como será medido.",
                    "aprueba": "Patrocinador / Product Owner",
                },
                "diseno": {
                    "nombre": "Design técnico e funcional",
                    "objetivo": "Definir como será construído e o que será "
                                "integrado.",
                    "entregables": ("Arquitetura da solução", "Modelo de dados",
                                     "Definição das integrações",
                                     "Requisitos não funcionais"),
                    "criterio_salida": "Arquitetura revisada; dependências "
                                        "externas confirmadas.",
                    "aprueba": "Líder técnico",
                },
                "construccion": {
                    "nombre": "Construção iterativa",
                    "objetivo": "Entregar incrementos utilizáveis e revisáveis.",
                    "entregables": ("Incrementos implantáveis", "Testes "
                                     "automatizados", "Documentação técnica "
                                     "mínima", "Demonstração a cada iteração"),
                    "criterio_salida": "Funcionalidade combinada concluída e "
                                        "testada.",
                    "aprueba": "Product Owner",
                },
                "uat": {
                    "nombre": "Testes de aceitação",
                    "objetivo": "Que o usuário real confirme que atende.",
                    "entregables": ("Casos de teste de negócio",
                                     "Registro de incidentes",
                                     "Termo de aceite do usuário"),
                    "criterio_salida": "Incidentes críticos e altos encerrados; "
                                        "usuário assina o aceite.",
                    "aprueba": "Representante de negócio",
                },
                "despliegue": {
                    "nombre": "Implantação (deploy)",
                    "objetivo": "Colocar em produção sem quebrar o que já "
                                "funciona.",
                    "entregables": ("Plano de implantação", "Plano de rollback",
                                     "Migração de dados testada",
                                     "Capacitação dos usuários"),
                    "criterio_salida": "Sistema em produção com rollback "
                                        "disponível.",
                    "aprueba": "Líder técnico / Operações",
                },
                "hipercuidado": {
                    "nombre": "Hipercuidado (hypercare)",
                    "objetivo": "Acompanhar de perto as primeiras semanas.",
                    "entregables": ("Plantão definido", "Painel de incidentes",
                                     "Ajustes pós-implantação"),
                    "criterio_salida": "Incidentes estabilizados abaixo do limite "
                                        "combinado.",
                    "aprueba": "Líder técnico",
                },
                "cierre_sw": {
                    "nombre": "Transição para operação",
                    "objetivo": "Que a equipe de suporte consiga sustentar sem a "
                                "equipe de projeto.",
                    "entregables": ("Documentação de operação",
                                     "Transição para o suporte",
                                     "Dívida técnica registrada",
                                     "Lições aprendidas"),
                    "criterio_salida": "Suporte aceita a transição.",
                    "aprueba": "Responsável por operações",
                },
            },
            "roles": (
                ("Patrocinador", "Aprova orçamento e prioridades."),
                ("Product Owner",
                 "Decide o que entra e o que não entra em cada entrega."),
                ("Líder técnico",
                 "Define a arquitetura e aceita a qualidade técnica."),
                ("Representante de negócio",
                 "Valida que a solução serve para o trabalho real."),
                ("Operações / Suporte",
                 "Aceita ou recusa a transição para produção."),
            ),
            "riesgos": (
                ("Escopo que se move",
                 "Pedidos novos que entram sem nada sair em troca.",
                 "Backlog único e priorizado: o que entra desloca algo."),
                ("Dependência de terceiros",
                 "Uma integração ou fornecedor que não confirma datas.",
                 "Confirmar a disponibilidade da API ou do fornecedor antes de "
                 "comprometer o prazo."),
                ("Dívida técnica acumulada",
                 "A velocidade de entrega cai a cada iteração.",
                 "Reservar capacidade fixa por iteração para dívida técnica."),
                ("Dados pessoais mal tratados",
                 "Dados de produção usados em ambientes de teste.",
                 "Anonimizar os dados de teste e registrar a base junto ao "
                 "órgão regulador."),
                ("Concentração de conhecimento",
                 "Só uma pessoa entende um componente crítico.",
                 "Revisão cruzada de código e documentação mínima "
                 "obrigatória."),
            ),
            "indicadores": ("Incremento entregue por iteração",
                             "Incidentes abertos por severidade",
                             "Cobertura de testes automatizados",
                             "Tempo de implantação", "Retrabalho sobre o "
                             "entregue"),
            "normativa": ("Ley 18.331 — proteção de dados pessoais "
                           "(Uruguai) e decreto 414/009",
                           "ISO/IEC 27001 se a empresa lida com informação "
                           "sensível",
                           "Regulamento GDPR se houver usuários ou clientes na "
                           "União Europeia",
                           "Licenças dos componentes de terceiros "
                           "incorporados"),
            "portafolios_sugeridos": ("Produto", "Integrações", "Infraestrutura",
                                       "Conformidade"),
        },
        "farma": {
            "rubro": "Farmacêutica, laboratórios e dispositivos médicos",
            "resumen": "Setor regulado: a rastreabilidade da evidência vale "
                       "tanto quanto o resultado. O que não está documentado, "
                       "para o regulador não aconteceu.",
            "etapas": {
                "factibilidad": {
                    "nombre": "Viabilidade",
                    "objetivo": "Confirmar a viabilidade técnica e regulatória "
                                "antes de investir.",
                    "entregables": ("Perfil do produto",
                                     "Análise da via regulatória",
                                     "Avaliação de propriedade intelectual",
                                     "Estimativa de investimento"),
                    "criterio_salida": "Via regulatória definida e aprovada por "
                                        "Assuntos Regulatórios.",
                    "aprueba": "Direção técnica",
                },
                "desarrollo": {
                    "nombre": "Desenvolvimento e formulação",
                    "objetivo": "Chegar a uma fórmula e um processo "
                                "reprodutíveis.",
                    "entregables": ("Protocolo de desenvolvimento",
                                     "Estudos de pré-formulação",
                                     "Especificações do produto",
                                     "Estudos de estabilidade iniciados"),
                    "criterio_salida": "Fórmula e processo congelados; "
                                        "estabilidade em andamento.",
                    "aprueba": "P&D / Direção técnica",
                },
                "validacion": {
                    "nombre": "Validação (IQ / OQ / PQ)",
                    "objetivo": "Demonstrar documentalmente que equipamentos e "
                                "processos fazem o que devem.",
                    "entregables": ("Plano mestre de validação",
                                     "Protocolos e relatórios de IQ, OQ e PQ",
                                     "Qualificação de fornecedores",
                                     "Validação de métodos analíticos"),
                    "criterio_salida": "Validação aprovada pela Garantia da "
                                        "Qualidade.",
                    "aprueba": "Garantia da Qualidade",
                },
                "registro": {
                    "nombre": "Registro sanitário",
                    "objetivo": "Obter a autorização para comercializar.",
                    "entregables": ("Dossiê de registro", "Dados de "
                                     "estabilidade",
                                     "Respostas a exigências da autoridade"),
                    "criterio_salida": "Registro concedido pela autoridade "
                                        "sanitária.",
                    "aprueba": "Assuntos Regulatórios",
                },
                "transferencia": {
                    "nombre": "Transferência de tecnologia",
                    "objetivo": "Passar da escala piloto para a produção "
                                "industrial.",
                    "entregables": ("Protocolo de transferência",
                                     "Lotes piloto e de validação",
                                     "Capacitação da planta",
                                     "Procedimentos operacionais "
                                     "atualizados"),
                    "criterio_salida": "Lotes de validação conformes à "
                                        "especificação.",
                    "aprueba": "Produção / Qualidade",
                },
                "lanzamiento": {
                    "nombre": "Lançamento e farmacovigilância",
                    "objetivo": "Produzir em rotina e vigiar o comportamento do "
                                "produto.",
                    "entregables": ("Liberação do primeiro lote comercial",
                                     "Sistema de farmacovigilância ativo",
                                     "Plano de acompanhamento "
                                     "pós-comercialização"),
                    "criterio_salida": "Primeiro lote liberado pela direção "
                                        "técnica.",
                    "aprueba": "Direção técnica",
                },
            },
            "roles": (
                ("Direção técnica",
                 "Libera lotes e responde perante a autoridade sanitária."),
                ("Garantia da Qualidade",
                 "Aprova validações e encerra desvios. Pode parar tudo."),
                ("Assuntos Regulatórios",
                 "Define a via de registro e fala com a autoridade."),
                ("Produção", "Executa conforme os procedimentos aprovados."),
                ("P&D", "Desenvolve e documenta a evidência técnica."),
            ),
            "riesgos": (
                ("Desvio não documentado",
                 "Diferenças entre o que foi executado e o procedimento, sem "
                 "registro.",
                 "Sistema de desvios e CAPA com prazos e responsável para "
                 "cada um."),
                ("Integridade de dados comprometida",
                 "Registros sem rastreabilidade de quem os lançou ou "
                 "alterou.",
                 "Princípios ALCOA+ e registros com trilha de auditoria de "
                 "alterações."),
                ("Observação da autoridade em inspeção",
                 "Achados repetidos em auditorias internas sem fechamento.",
                 "Auditorias internas periódicas e fechamento efetivo dos "
                 "achados."),
                ("Atraso regulatório",
                 "Exigências do regulador que reabrem o processo.",
                 "Revisar o dossiê antes de submeter e deixar folga no "
                 "cronograma."),
                ("Fornecedor de insumo crítico não qualificado",
                 "Trocas de fornecedor sem requalificação.",
                 "Qualificação formal e auditoria dos fornecedores "
                 "críticos."),
            ),
            "indicadores": ("Desvios abertos e sua antiguidade",
                             "CAPAs vencidas",
                             "Lotes reprovados sobre produzidos",
                             "Cumprimento do plano de validação",
                             "Tempo de resposta a exigências da autoridade"),
            "normativa": ("Boas Práticas de Fabricação (GMP) exigidas pelo "
                           "MSP, o ministério da saúde do Uruguai",
                           "Guias ICH Q7 a Q10 para qualidade farmacêutica",
                           "21 CFR Part 11 em caso de exportação para os "
                           "Estados Unidos (registros eletrônicos)",
                           "Princípios ALCOA+ de integridade de dados",
                           "Normativa de farmacovigilância do MSP "
                           "(Uruguai)"),
            "portafolios_sugeridos": ("Desenvolvimento de produto",
                                       "Validações", "Registros",
                                       "Melhoria de planta"),
            "nota": "O regulador avalia a evidência documental, não a "
                    "intenção. Cada etapa precisa deixar um registro assinado "
                    "e datado.",
        },
        "manufactura": {
            "rubro": "Manufatura e indústria",
            "resumen": "Projetos de produto, linha ou planta. O portão que "
                       "importa é o início da produção em série: antes disso "
                       "tudo é reversível, depois não.",
            "etapas": {
                "concepto": {
                    "nombre": "Conceito e viabilidade",
                    "objetivo": "Definir o que será produzido e se o negócio "
                                "fecha.",
                    "entregables": ("Especificação do produto",
                                     "Análise de viabilidade", "Custo alvo",
                                     "Volume estimado"),
                    "criterio_salida": "A diretoria aprova avançar para o "
                                        "design.",
                    "aprueba": "Diretoria industrial",
                },
                "diseno_prod": {
                    "nombre": "Design de produto e processo",
                    "objetivo": "Projetar o produto e como ele será "
                                "fabricado.",
                    "entregables": ("Plantas e especificações",
                                     "Fluxograma de processo",
                                     "FMEA de design e de processo",
                                     "Plano de controle"),
                    "criterio_salida": "Design congelado e ações do FMEA "
                                        "fechadas.",
                    "aprueba": "Engenharia",
                },
                "utillaje": {
                    "nombre": "Ferramental e equipamentos",
                    "objetivo": "Ter ferramentas, moldes e equipamentos "
                                "prontos.",
                    "entregables": ("Ferramental fabricado e testado",
                                     "Instruções de trabalho",
                                     "Capacitação dos operadores",
                                     "Calibração de instrumentos"),
                    "criterio_salida": "Ferramental aprovado, com peças "
                                        "conformes.",
                    "aprueba": "Engenharia de processo",
                },
                "preserie": {
                    "nombre": "Pré-série e aprovação de amostras",
                    "objetivo": "Testar o processo em condições reais antes de "
                                "arrancar.",
                    "entregables": ("Corrida piloto",
                                     "Estudo de capacidade de processo",
                                     "Amostras aprovadas pelo cliente",
                                     "Ajustes ao plano de controle"),
                    "criterio_salida": "Capacidade de processo dentro do "
                                        "exigido e amostras aprovadas.",
                    "aprueba": "Qualidade",
                },
                "serie": {
                    "nombre": "Produção em série",
                    "objetivo": "Produzir em rotina mantendo qualidade e "
                                "custo.",
                    "entregables": ("Indicadores de linha",
                                     "Registro de não conformidades",
                                     "Manutenção preventiva em andamento"),
                    "criterio_salida": "Produção estável no volume e na "
                                        "qualidade combinados.",
                    "aprueba": "Produção",
                },
                "cierre_mf": {
                    "nombre": "Encerramento e melhoria contínua",
                    "objetivo": "Transferir para a operação e capturar o "
                                "aprendizado.",
                    "entregables": ("Transição para a produção",
                                     "Lições aprendidas",
                                     "Plano de melhoria contínua"),
                    "criterio_salida": "Operação aceita a transição.",
                    "aprueba": "Diretoria industrial",
                },
            },
            "roles": (
                ("Diretoria industrial",
                 "Aprova investimento e o início da produção em série."),
                ("Engenharia de produto", "Responde pelo design."),
                ("Engenharia de processo",
                 "Responde por como o produto é fabricado."),
                ("Qualidade", "Aprova amostras e pode travar o arranque."),
                ("Produção", "Executa e reporta os indicadores de linha."),
            ),
            "riesgos": (
                ("Ferramental que não chega a tempo",
                 "Atrasos do fornecedor de moldes ou ferramentas.",
                 "Acompanhamento semanal do fornecedor e marcos de "
                 "pagamento atrelados ao avanço."),
                ("Capacidade de processo insuficiente",
                 "Estudos de capacidade abaixo do alvo na pré-série.",
                 "Não iniciar a série sem capacidade comprovada; ajustar o "
                 "processo antes."),
                ("Custo unitário acima do alvo",
                 "Desvios de consumo de material ou de tempo de ciclo na "
                 "corrida piloto.",
                 "Custeio por corrida piloto e revisão antes de comprometer "
                 "o preço."),
                ("Quebra de equipamento crítico",
                 "Manutenções preventivas adiadas.",
                 "Plano de manutenção e peças de reposição críticas em "
                 "estoque."),
            ),
            "indicadores": ("OEE da linha", "Refugo e retrabalho",
                             "Custo unitário real vs. alvo",
                             "Cumprimento do plano de produção",
                             "Reclamações de clientes"),
            "normativa": ("ISO 9001 — sistema de gestão da qualidade",
                           "IATF 16949 para produção destinada à indústria "
                           "automotiva",
                           "ISO 14001 em caso de compromissos ambientais",
                           "Regulamentos de segurança de máquinas "
                           "aplicáveis"),
            "portafolios_sugeridos": ("Novos produtos", "Melhoria de processo",
                                       "Investimento em planta", "Qualidade"),
        },
        "servicios": {
            "rubro": "Serviços profissionais e consultoria",
            "resumen": "Projetos vendidos por hora ou por entregável. A margem "
                       "se perde no trabalho não faturado, não no preço.",
            "etapas": {
                "propuesta": {
                    "nombre": "Proposta",
                    "objetivo": "Combinar escopo, preço e forma de trabalho "
                                "antes de começar.",
                    "entregables": ("Proposta com escopo explícito",
                                     "Estimativa de horas",
                                     "Condições comerciais",
                                     "Premissas e exclusões por escrito"),
                    "criterio_salida": "Proposta aceita por escrito.",
                    "aprueba": "Sócio / Diretoria",
                },
                "arranque": {
                    "nombre": "Início do projeto (kickoff)",
                    "objetivo": "Alinhar expectativas e montar a equipe.",
                    "entregables": ("Reunião de kickoff", "Plano de trabalho",
                                     "Equipe designada",
                                     "Canal e frequência de reporte "
                                     "combinados"),
                    "criterio_salida": "Cliente e equipe alinhados sobre "
                                        "entregáveis e prazos.",
                    "aprueba": "Responsável pelo projeto",
                },
                "ejecucion_srv": {
                    "nombre": "Execução",
                    "objetivo": "Entregar o combinado controlando as horas.",
                    "entregables": ("Entregáveis parciais",
                                     "Registro de horas por pessoa",
                                     "Atas de reunião",
                                     "Controle de mudanças de escopo"),
                    "criterio_salida": "Entregáveis aceitos pelo cliente.",
                    "aprueba": "Responsável pelo projeto",
                },
                "cierre_srv": {
                    "nombre": "Encerramento e faturamento",
                    "objetivo": "Receber, encerrar e capturar a referência.",
                    "entregables": ("Termo de encerramento",
                                     "Fatura final emitida",
                                     "Pesquisa de satisfação",
                                     "Case de referência, se o cliente "
                                     "aceitar"),
                    "criterio_salida": "Faturado e recebido; cliente "
                                        "satisfeito.",
                    "aprueba": "Sócio / Administração",
                },
            },
            "roles": (
                ("Sócio / Diretoria",
                 "Aprova a proposta e responde pela margem."),
                ("Responsável pelo projeto",
                 "Gerencia escopo, equipe e relação com o cliente."),
                ("Equipe designada", "Executa e registra horas."),
                ("Administração", "Fatura e controla o recebimento."),
            ),
            "riesgos": (
                ("Horas não faturadas",
                 "Horas lançadas acima do estimado sem mudança de escopo.",
                 "Revisão semanal das horas contra o estimado e aviso "
                 "antecipado ao cliente."),
                ("Escopo que se estica aos poucos",
                 "Pedidos pequenos fora da proposta que ninguém cota.",
                 "Todo pedido fora do escopo é cotado, mesmo que pequeno."),
                ("Cliente que não disponibiliza sua equipe",
                 "Reuniões adiadas ou entregáveis sem revisão.",
                 "Deixar a disponibilidade do cliente como premissa "
                 "explícita da proposta."),
                ("Recebimento atrasado",
                 "Faturas vencidas sem cobrança.",
                 "Marcos de faturamento atrelados a entregáveis aceitos."),
            ),
            "indicadores": ("Horas reais vs. estimadas", "Margem por projeto",
                             "Percentual de horas faturáveis",
                             "Prazo médio de recebimento",
                             "Satisfação do cliente"),
            "normativa": ("Contrato de serviços com escopo e propriedade "
                           "intelectual definidos",
                           "Acordos de confidencialidade com o cliente",
                           "Ley 18.331 em caso de tratamento de dados "
                           "pessoais do cliente (Uruguai)"),
            "portafolios_sugeridos": ("Clientes", "Interno", "Pré-vendas"),
        },
        "energia": {
            "rubro": "Energia e serviços públicos",
            "resumen": "Geração, transmissão e eficiência energética. As "
                       "licenças ambientais e a conexão à rede mandam mais no "
                       "cronograma do que a equipe do projeto.",
            "etapas": {
                "prefactibilidad": {
                    "nombre": "Pré-viabilidade",
                    "objetivo": "Ver se o recurso e o local se sustentam.",
                    "entregables": ("Estudo de recurso", "Análise do local",
                                     "Modelo econômico preliminar",
                                     "Consulta prévia de conexão à rede"),
                    "criterio_salida": "A diretoria aprova investir em "
                                        "estudos definitivos.",
                    "aprueba": "Diretoria",
                },
                "ambiental": {
                    "nombre": "Licenciamento ambiental",
                    "objetivo": "Conseguir a licença ambiental, geralmente o "
                                "caminho crítico.",
                    "entregables": ("Estudo de impacto ambiental",
                                     "Plano de gestão ambiental",
                                     "Instância de participação pública, se "
                                     "aplicável"),
                    "criterio_salida": "Licença ambiental prévia concedida.",
                    "aprueba": "Responsável ambiental",
                },
                "conexion": {
                    "nombre": "Acordo de conexão",
                    "objetivo": "Garantir o ponto de conexão e as condições "
                                "técnicas.",
                    "entregables": ("Estudo de conexão",
                                     "Acordo com a operadora da rede",
                                     "Especificação da subestação"),
                    "criterio_salida": "Ponto de conexão confirmado por "
                                        "escrito.",
                    "aprueba": "Engenharia",
                },
                "epc": {
                    "nombre": "Engenharia, suprimentos e construção",
                    "objetivo": "Construir a instalação.",
                    "entregables": ("Engenharia de detalhamento",
                                     "Equipamentos principais comprados",
                                     "Obra civil e montagem",
                                     "Testes de equipamentos"),
                    "criterio_salida": "Instalação montada e testada.",
                    "aprueba": "Direção do projeto",
                },
                "puesta_marcha": {
                    "nombre": "Comissionamento",
                    "objetivo": "Sincronizar com a rede e comprovar o "
                                "desempenho.",
                    "entregables": ("Protocolo de testes",
                                     "Sincronização com a rede",
                                     "Teste de desempenho garantido"),
                    "criterio_salida": "Desempenho garantido comprovado e "
                                        "aceito.",
                    "aprueba": "Operadora da rede / Contratante",
                },
                "operacion": {
                    "nombre": "Operação e manutenção",
                    "objetivo": "Transferir para a operação com contrato de "
                                "manutenção.",
                    "entregables": ("Manual de operação", "Contrato de O&M",
                                     "Capacitação da equipe",
                                     "Transição documentada"),
                    "criterio_salida": "Operação aceita a instalação.",
                    "aprueba": "Operações",
                },
            },
            "roles": (
                ("Diretoria", "Aprova o investimento."),
                ("Responsável ambiental",
                 "Responde pelo cumprimento ambiental."),
                ("Engenharia", "Define a solução técnica e a conexão."),
                ("Operadora da rede", "Autoriza a conexão e a sincronização."),
                ("Operações", "Recebe a instalação."),
            ),
            "riesgos": (
                ("Atraso no licenciamento ambiental",
                 "Exigências do órgão ambiental que reabrem o processo.",
                 "Apresentar o estudo completo e prever prazos reais de "
                 "resposta."),
                ("Rejeição social ao projeto",
                 "Oposição de vizinhos na instância de participação "
                 "pública.",
                 "Comunicação antecipada com a comunidade, antes da "
                 "instância formal."),
                ("Restrição da rede",
                 "A operadora limita a potência injetável no ponto "
                 "solicitado.",
                 "Consulta prévia de conexão antes de comprometer o "
                 "investimento."),
                ("Equipamentos principais com prazo longo",
                 "Prazos de entrega de turbinas ou transformadores que não "
                 "fecham com o cronograma.",
                 "Reservar equipamentos críticos assim que o investimento "
                 "for aprovado."),
            ),
            "indicadores": ("Avanço da obra vs. plano", "Desvio de "
                             "investimento", "Energia gerada vs. projetada",
                             "Disponibilidade da instalação",
                             "Cumprimento do plano de gestão ambiental"),
            "normativa": ("Licença Ambiental Prévia junto ao Ministério do "
                           "Ambiente (Uruguai)",
                           "Regulamentação da URSEC para o setor "
                           "energético (Uruguai)",
                           "Condições de conexão da operadora da rede "
                           "(UTE, no Uruguai)",
                           "Normativa de segurança elétrica aplicável"),
            "portafolios_sugeridos": ("Geração", "Transmissão e distribuição",
                                       "Eficiência energética"),
        },
        "salud": {
            "rubro": "Saúde e instituições médicas",
            "resumen": "Projetos dentro de prestadores de saúde. Toda mudança "
                       "afeta o atendimento ao paciente, então o portão que "
                       "importa é não degradar o serviço.",
            "etapas": {
                "necesidad": {
                    "nombre": "Necessidade assistencial",
                    "objetivo": "Definir qual problema assistencial será "
                                "resolvido.",
                    "entregables": ("Justificativa clínica",
                                     "População afetada",
                                     "Indicadores assistenciais de base"),
                    "criterio_salida": "A direção médica avaliza a "
                                        "necessidade.",
                    "aprueba": "Direção médica",
                },
                "diseno_salud": {
                    "nombre": "Design do serviço",
                    "objetivo": "Definir o processo assistencial e os "
                                "recursos necessários.",
                    "entregables": ("Protocolo assistencial",
                                     "Recursos humanos e equipamentos "
                                     "necessários", "Fluxo do paciente",
                                     "Requisitos de habilitação"),
                    "criterio_salida": "Protocolo aprovado pelo comitê "
                                        "correspondente.",
                    "aprueba": "Direção médica / Comitê",
                },
                "habilitacion": {
                    "nombre": "Habilitação",
                    "objetivo": "Cumprir as exigências da autoridade "
                                "sanitária.",
                    "entregables": ("Processo de habilitação",
                                     "Adequação predial",
                                     "Habilitação de equipamentos",
                                     "Equipe com registros profissionais "
                                     "em dia"),
                    "criterio_salida": "Habilitação concedida.",
                    "aprueba": "Responsável pela habilitação",
                },
                "implementacion": {
                    "nombre": "Implementação",
                    "objetivo": "Entrar em operação sem interromper o "
                                "atendimento.",
                    "entregables": ("Plano de transição",
                                     "Capacitação da equipe assistencial",
                                     "Testes em paralelo, se substituir um "
                                     "processo existente"),
                    "criterio_salida": "Serviço funcionando com a equipe "
                                        "capacitada.",
                    "aprueba": "Chefia do serviço",
                },
                "seguimiento": {
                    "nombre": "Acompanhamento assistencial",
                    "objetivo": "Verificar se o que precisava melhorar "
                                "melhorou de fato.",
                    "entregables": ("Indicadores assistenciais "
                                     "pós-implementação",
                                     "Registro de eventos adversos",
                                     "Ajustes ao protocolo"),
                    "criterio_salida": "Indicadores no nível combinado, sem "
                                        "eventos adversos atribuíveis.",
                    "aprueba": "Direção médica",
                },
                "cierre_salud": {
                    "nombre": "Encerramento",
                    "objetivo": "Incorporar o serviço à operação normal.",
                    "entregables": ("Protocolo incorporado ao manual",
                                     "Transição para a operação",
                                     "Lições aprendidas"),
                    "criterio_salida": "Serviço incorporado à operação de "
                                        "rotina.",
                    "aprueba": "Direção",
                },
            },
            "roles": (
                ("Direção médica",
                 "Avaliza a pertinência clínica. Pode travar o projeto."),
                ("Chefia do serviço",
                 "Executa e responde pela operação diária."),
                ("Comitê de qualidade / segurança do paciente",
                 "Revisa riscos assistenciais."),
                ("Responsável pela habilitação",
                 "Trata com a autoridade sanitária."),
                ("Referência de sistemas",
                 "Integra com o prontuário eletrônico."),
            ),
            "riesgos": (
                ("Interrupção do atendimento",
                 "Mudanças colocadas em produção sem plano de "
                 "contingência.",
                 "Transição em paralelo e plano de rollback sempre "
                 "disponível."),
                ("Equipe não capacitada a tempo",
                 "Capacitações adiadas por causa da carga assistencial.",
                 "Capacitação dentro da jornada e com substituições "
                 "previstas."),
                ("Dados de pacientes expostos",
                 "Acessos amplos demais ou dados de produção em testes.",
                 "Acesso mínimo necessário e dados anonimizados nos "
                 "ambientes de teste."),
                ("Evento adverso associado à mudança",
                 "Aumento de incidentes reportados após a implementação.",
                 "Acompanhamento intensivo nas primeiras semanas e "
                 "critério de reversão definido."),
            ),
            "indicadores": ("Tempo de espera do paciente",
                             "Eventos adversos reportados",
                             "Cobertura da população-alvo",
                             "Adesão ao protocolo",
                             "Satisfação do usuário"),
            "normativa": ("Habilitação de serviços de saúde junto ao MSP, "
                           "o ministério da saúde do Uruguai",
                           "Ley 18.335 — direitos e obrigações de "
                           "pacientes e usuários (Uruguai)",
                           "Ley 18.331 — dados pessoais, com dados de "
                           "saúde como categoria sensível (Uruguai)",
                           "Normativa do prontuário eletrônico nacional "
                           "(Uruguai)"),
            "portafolios_sugeridos": ("Serviços assistenciais", "Equipamentos",
                                       "Sistemas", "Qualidade e segurança"),
        },
        "financiero": {
            "rubro": "Bancos, finanças e seguros",
            "resumen": "Setor supervisionado. Toda mudança relevante precisa "
                       "poder ser explicada ao regulador e à auditoria "
                       "interna.",
            "etapas": {
                "caso_negocio": {
                    "nombre": "Caso de negócio",
                    "objetivo": "Justificar o investimento e o impacto em "
                                "risco.",
                    "entregables": ("Caso de negócio",
                                     "Avaliação de risco operacional",
                                     "Impacto regulatório",
                                     "Aprovação do comitê"),
                    "criterio_salida": "O comitê aprova a iniciativa.",
                    "aprueba": "Comitê de diretoria",
                },
                "diseno_fin": {
                    "nombre": "Design e controles",
                    "objetivo": "Definir a solução e os controles que a "
                                "acompanham.",
                    "entregables": ("Design funcional", "Matriz de "
                                     "controles",
                                     "Avaliação de segurança da "
                                     "informação",
                                     "Análise de continuidade de "
                                     "negócio"),
                    "criterio_salida": "Risco e Segurança aprovam o design.",
                    "aprueba": "Risco / Segurança da informação",
                },
                "construccion_fin": {
                    "nombre": "Construção e testes",
                    "objetivo": "Construir com evidência de teste suficiente "
                                "para auditoria.",
                    "entregables": ("Desenvolvimento ou parametrização",
                                     "Testes funcionais documentados",
                                     "Testes de segurança",
                                     "Segregação de ambientes"),
                    "criterio_salida": "Testes encerrados com evidência "
                                        "arquivada.",
                    "aprueba": "Líder do projeto",
                },
                "aprobacion_reg": {
                    "nombre": "Aprovação regulatória",
                    "objetivo": "Obter as autorizações ou fazer as "
                                "comunicações cabíveis.",
                    "entregables": ("Comunicação ao regulador, se "
                                     "aplicável",
                                     "Atualização de manuais e políticas",
                                     "Registro da aprovação"),
                    "criterio_salida": "Autorização obtida ou comunicação "
                                        "enviada.",
                    "aprueba": "Compliance",
                },
                "salida_prod": {
                    "nombre": "Entrada em produção",
                    "objetivo": "Implantar com controle de mudanças formal.",
                    "entregables": ("Solicitação de mudança aprovada",
                                     "Plano de rollback",
                                     "Capacitação dos usuários",
                                     "Monitoramento reforçado"),
                    "criterio_salida": "Mudança em produção com evidência "
                                        "de aprovação.",
                    "aprueba": "Comitê de mudanças",
                },
                "cierre_fin": {
                    "nombre": "Encerramento e revisão",
                    "objetivo": "Verificar se os controles funcionam na "
                                "prática.",
                    "entregables": ("Revisão pós-implementação",
                                     "Controles em operação",
                                     "Fechamento dos achados",
                                     "Lições aprendidas"),
                    "criterio_salida": "Auditoria interna sem achados em "
                                        "aberto.",
                    "aprueba": "Auditoria interna",
                },
            },
            "roles": (
                ("Comitê de diretoria",
                 "Aprova o investimento e o apetite de risco."),
                ("Risco", "Avalia o risco operacional. Pode bloquear."),
                ("Compliance", "Responde pela parte regulatória."),
                ("Segurança da informação",
                 "Aprova o design de segurança."),
                ("Auditoria interna",
                 "Revisa evidências e registra achados."),
            ),
            "riesgos": (
                ("Achado regulatório",
                 "Controles desenhados no papel, mas não operando na "
                 "prática.",
                 "Testar os controles em produção, não só documentá-los."),
                ("Vazamento ou exposição de dados de clientes",
                 "Acessos não revisados ou dados de produção fora do "
                 "ambiente seguro.",
                 "Revisão periódica de acessos e mascaramento em "
                 "ambientes não produtivos."),
                ("Indisponibilidade do serviço",
                 "Mudanças sem janela nem plano de rollback.",
                 "Janelas de mudança definidas e rollback testado."),
                ("Evidência insuficiente para auditoria",
                 "Aprovações verbais ou por canais informais.",
                 "Toda aprovação fica registrada com responsável e "
                 "data."),
            ),
            "indicadores": ("Achados de auditoria em aberto",
                             "Incidentes de segurança",
                             "Disponibilidade de serviços críticos",
                             "Mudanças com rollback executado",
                             "Cumprimento do plano de controles"),
            "normativa": ("Normativa do Banco Central del Uruguay "
                           "aplicável à instituição",
                           "Ley 18.331 — proteção de dados pessoais "
                           "(Uruguai)",
                           "Ley 19.574 — prevenção de lavagem de dinheiro "
                           "(Uruguai)",
                           "PCI-DSS em caso de tratamento de dados de "
                           "cartões",
                           "ISO/IEC 27001 para gestão de segurança da "
                           "informação"),
            "portafolios_sugeridos": ("Regulatório", "Produtos",
                                       "Canais digitais", "Risco e controle"),
        },
        "agro": {
            "rubro": "Agro e agroindústria",
            "resumen": "A safra manda: a janela de plantio ou colheita não é "
                       "negociável, e um atraso de duas semanas pode custar o "
                       "ano inteiro.",
            "etapas": {
                "planificacion_zafra": {
                    "nombre": "Planejamento da safra",
                    "objetivo": "Definir o quê, onde e quanto, antes de a "
                                "janela abrir.",
                    "entregables": ("Plano de safra", "Orçamento de insumos",
                                     "Disponibilidade de maquinário",
                                     "Análise de solo"),
                    "criterio_salida": "Plano aprovado antes do início da "
                                        "janela.",
                    "aprueba": "Diretoria / Gerência de produção",
                },
                "insumos": {
                    "nombre": "Compra de insumos",
                    "objetivo": "Garantir semente, fertilizante e defensivos a "
                                "tempo.",
                    "entregables": ("Ordens de compra", "Logística de "
                                     "entrega combinada",
                                     "Financiamento confirmado"),
                    "criterio_salida": "Insumos no campo antes da janela.",
                    "aprueba": "Compras",
                },
                "implantacion": {
                    "nombre": "Plantio",
                    "objetivo": "Plantar dentro da janela correta.",
                    "entregables": ("Registro das operações",
                                     "Controle de qualidade do plantio",
                                     "Registro de aplicações"),
                    "criterio_salida": "Área plantada dentro da janela.",
                    "aprueba": "Gerência de produção",
                },
                "seguimiento_cultivo": {
                    "nombre": "Acompanhamento da lavoura",
                    "objetivo": "Monitorar e agir a tempo.",
                    "entregables": ("Monitoramento de pragas e doenças",
                                     "Registro de aplicações",
                                     "Estimativa de produtividade"),
                    "criterio_salida": "Lavoura sem problemas sanitários "
                                        "pendentes.",
                    "aprueba": "Engenheiro agrônomo",
                },
                "cosecha": {
                    "nombre": "Colheita",
                    "objetivo": "Colher a produção com a menor perda "
                                "possível.",
                    "entregables": ("Plano de colheita",
                                     "Registro de produtividade por "
                                     "talhão",
                                     "Controle de umidade e qualidade",
                                     "Rastreabilidade dos lotes"),
                    "criterio_salida": "Produção colhida e armazenada ou "
                                        "entregue.",
                    "aprueba": "Gerência de produção",
                },
                "cierre_zafra": {
                    "nombre": "Encerramento da safra",
                    "objetivo": "Fechar os números e aprender para a "
                                "próxima.",
                    "entregables": ("Resultado econômico por talhão",
                                     "Análise de desvios",
                                     "Plano para a próxima safra"),
                    "criterio_salida": "Resultado fechado e analisado.",
                    "aprueba": "Diretoria",
                },
            },
            "roles": (
                ("Diretoria", "Aprova o plano de safra e o investimento."),
                ("Gerência de produção", "Executa as operações no prazo."),
                ("Engenheiro agrônomo",
                 "Decide manejo sanitário e nutricional."),
                ("Compras", "Garante os insumos antes da janela."),
                ("Responsável pela rastreabilidade",
                 "Responde perante certificadoras e órgãos reguladores."),
            ),
            "riesgos": (
                ("Janela de plantio ou colheita perdida",
                 "Insumos ou maquinário que não estão prontos quando a "
                 "janela abre.",
                 "Insumos no campo com antecedência e maquinário "
                 "contratado com antecipação."),
                ("Evento climático",
                 "Previsões adversas sustentadas no período crítico.",
                 "Diversificar datas e talhões; avaliar seguro agrícola."),
                ("Preço de commodity em queda",
                 "Queda de preços frente ao custo já comprometido.",
                 "Proteção parcial de preço no momento de comprometer os "
                 "insumos."),
                ("Falha de rastreabilidade",
                 "Registros de aplicação incompletos ou fora do prazo.",
                 "Registrar as operações no momento, não ao final da "
                 "safra."),
            ),
            "indicadores": ("Produtividade por hectare", "Custo por hectare",
                             "Área plantada dentro da janela",
                             "Margem por talhão",
                             "Cumprimento dos registros de "
                             "rastreabilidade"),
            "normativa": ("Registros junto à Dirección General de "
                           "Servicios Agrícolas (Uruguai)",
                           "Rastreabilidade pecuária do INAC / SNIG, se "
                           "aplicável (Uruguai)",
                           "Plano de uso e manejo de solos junto ao "
                           "Ministério da Pecuária (Uruguai)",
                           "Certificações voluntárias exigidas pelo "
                           "mercado de destino"),
            "portafolios_sugeridos": ("Agrícola", "Pecuária",
                                       "Infraestrutura de campo",
                                       "Certificações"),
        },
        "publico": {
            "rubro": "Setor público e órgãos estatais",
            "resumen": "Tudo passa pelo processo de compra e pelo controle "
                       "prévio. Quem define o cronograma é a legislação, não "
                       "a equipe do projeto.",
            "etapas": {
                "necesidad_pub": {
                    "nombre": "Definição da necessidade",
                    "objetivo": "Fundamentar a necessidade e conseguir a "
                                "disponibilidade orçamentária.",
                    "entregables": ("Fundamentação da necessidade",
                                     "Disponibilidade orçamentária",
                                     "Autorização da autoridade máxima "
                                     "do órgão"),
                    "criterio_salida": "Gasto autorizado com crédito "
                                        "disponível.",
                    "aprueba": "Autoridade máxima do órgão",
                },
                "pliego": {
                    "nombre": "Elaboração do edital",
                    "objetivo": "Definir o que se compra e como se avalia, "
                                "sem direcionar.",
                    "entregables": ("Edital com condições particulares",
                                     "Especificações técnicas",
                                     "Critérios de avaliação objetivos",
                                     "Cronograma do processo"),
                    "criterio_salida": "Edital aprovado pela autoridade "
                                        "competente.",
                    "aprueba": "Comissão assessora / Jurídico",
                },
                "llamado": {
                    "nombre": "Chamada pública e adjudicação",
                    "objetivo": "Conduzir o processo com transparência.",
                    "entregables": ("Publicação do edital",
                                     "Ata de abertura das propostas",
                                     "Parecer da comissão assessora",
                                     "Resolução de adjudicação"),
                    "criterio_salida": "Adjudicação resolvida e aprovada "
                                        "pelo controle prévio.",
                    "aprueba": "Ordenador da despesa",
                },
                "ejecucion_pub": {
                    "nombre": "Execução do contrato",
                    "objetivo": "Controlar se o que foi contratado está "
                                "sendo entregue.",
                    "entregables": ("Termos de recebimento parcial",
                                     "Controle de cumprimento contratual",
                                     "Registro de descumprimentos e "
                                     "multas"),
                    "criterio_salida": "Prestação recebida conforme o "
                                        "contrato.",
                    "aprueba": "Responsável pelo contrato",
                },
                "rendicion": {
                    "nombre": "Prestação de contas e encerramento",
                    "objetivo": "Prestar contas do gasto e encerrar o "
                                "processo.",
                    "entregables": ("Prestação de contas", "Processo "
                                     "completo", "Relatório de resultados",
                                     "Encerramento do contrato"),
                    "criterio_salida": "Prestação de contas aprovada sem "
                                        "pendências.",
                    "aprueba": "Contadoria / Auditoria",
                },
            },
            "roles": (
                ("Autoridade máxima do órgão", "Autoriza o gasto."),
                ("Ordenador da despesa", "Resolve a adjudicação."),
                ("Comissão assessora de adjudicações",
                 "Avalia propostas e recomenda."),
                ("Jurídico", "Controla a legalidade do processo."),
                ("Contadoria / controle prévio",
                 "Aprova o gasto. Pode fazer uma observação."),
            ),
            "riesgos": (
                ("Observação do controle prévio",
                 "Processos que voltam por falta de documentação.",
                 "Checklist de processo completo antes de enviar."),
                ("Chamada deserta ou com proposta única",
                 "Poucas consultas ou requisitos que restringem a "
                 "concorrência.",
                 "Consulta prévia ao mercado e revisão de requisitos "
                 "excludentes."),
                ("Impugnação do processo",
                 "Critérios de avaliação ambíguos ou discricionários.",
                 "Critérios objetivos e ponderados, publicados desde o "
                 "início."),
                ("Vencimento do exercício orçamentário",
                 "Processos que não fecham antes do fim do exercício.",
                 "Planejar a chamada contando os prazos legais reais, "
                 "não os desejados."),
            ),
            "indicadores": ("Prazo do processo de compra", "Chamadas "
                             "desertas ou impugnadas",
                             "Execução orçamentária",
                             "Observações do controle prévio",
                             "Cumprimento de prazos contratuais"),
            "normativa": ("TOCAF — Texto Ordenado de Contabilidad y "
                           "Administración Financiera (Uruguai)",
                           "Intervenção prévia do Tribunal de Cuentas "
                           "(tribunal de contas do Uruguai)",
                           "Publicação no portal Compras Estatales "
                           "(Uruguai)",
                           "Ley 18.381 — acesso à informação pública "
                           "(Uruguai)",
                           "Ley 19.889 e normas de processo "
                           "administrativo aplicáveis (Uruguai)"),
            "portafolios_sugeridos": ("Investimento público", "Compras e "
                                       "suprimentos", "Modernização da "
                                       "gestão", "Convênios"),
            "nota": "No setor público, quem define o cronograma é a "
                    "legislação de compras. Planejar com os prazos legais "
                    "reais, e não com os desejados, é a diferença entre "
                    "executar o orçamento e perdê-lo.",
        },
        "retail": {
            "rubro": "Varejo e consumo de massa",
            "resumen": "Tudo se organiza em torno da temporada. Chegar "
                       "atrasado numa data comercial não se recupera: aquela "
                       "venda não volta.",
            "etapas": {
                "plan_comercial": {
                    "nombre": "Plano comercial",
                    "objetivo": "Definir sortimento, temporada e meta de "
                                "venda.",
                    "entregables": ("Plano de sortimento",
                                     "Meta de venda e margem",
                                     "Calendário comercial",
                                     "Orçamento de compra"),
                    "criterio_salida": "Plano aprovado antes do início da "
                                        "temporada de compra.",
                    "aprueba": "Gerência comercial",
                },
                "abastecimiento": {
                    "nombre": "Abastecimento",
                    "objetivo": "Comprar e trazer a mercadoria a tempo.",
                    "entregables": ("Ordens de compra",
                                     "Plano logístico e de importação",
                                     "Controle de qualidade do "
                                     "fornecedor"),
                    "criterio_salida": "Mercadoria no depósito antes da "
                                        "data de ida para a loja.",
                    "aprueba": "Compras / Logística",
                },
                "implantacion_retail": {
                    "nombre": "Implantação na loja",
                    "objetivo": "Colocar o produto na loja com a exposição "
                                "definida.",
                    "entregables": ("Planograma", "Material de ponto de "
                                     "venda",
                                     "Capacitação da equipe de loja",
                                     "Preços carregados"),
                    "criterio_salida": "Produto na loja conforme o "
                                        "planograma em todas as lojas.",
                    "aprueba": "Operações de loja",
                },
                "temporada": {
                    "nombre": "Temporada",
                    "objetivo": "Vender e reagir rápido ao que acontece.",
                    "entregables": ("Acompanhamento diário de venda",
                                     "Reposição",
                                     "Ajustes de preço e promoção"),
                    "criterio_salida": "Meta de venda e margem atingida.",
                    "aprueba": "Gerência comercial",
                },
                "liquidacion": {
                    "nombre": "Liquidação e encerramento",
                    "objetivo": "Escoar o remanescente e fechar o "
                                "resultado.",
                    "entregables": ("Plano de liquidação", "Resultado da "
                                     "temporada",
                                     "Análise de rupturas e sobras"),
                    "criterio_salida": "Estoque remanescente dentro da "
                                        "meta.",
                    "aprueba": "Gerência comercial",
                },
            },
            "roles": (
                ("Gerência comercial",
                 "Define o sortimento e aprova o plano."),
                ("Compras", "Negocia e garante o abastecimento."),
                ("Logística", "Responde por a mercadoria chegar a tempo."),
                ("Operações de loja", "Executa a implantação na loja."),
                ("Marketing", "Sustenta a campanha da temporada."),
            ),
            "riesgos": (
                ("Mercadoria que chega atrasada",
                 "Atrasos de embarque ou demora na alfândega.",
                 "Margens de tempo no plano de importação e "
                 "acompanhamento do embarque."),
                ("Ruptura de estoque em produto-chave",
                 "Velocidade de venda acima da projetada sem reposição.",
                 "Reposição automática por limite e fornecedor "
                 "alternativo definido."),
                ("Sobra de estoque no encerramento",
                 "Venda abaixo da projetada na metade da temporada.",
                 "Pontos de controle com decisão de promoção "
                 "antecipada."),
                ("Implantação desigual entre lojas",
                 "Auditorias de loja com desvios em relação ao "
                 "planograma.",
                 "Auditoria da implantação nos primeiros dias da "
                 "temporada."),
            ),
            "indicadores": ("Venda vs. meta por categoria",
                             "Margem por categoria", "Rupturas de estoque",
                             "Giro de estoque", "Cumprimento do "
                             "planograma"),
            "normativa": ("Ley 17.250 — relações de consumo e defesa do "
                           "consumidor (Uruguai)",
                           "Normativa de etiquetagem e rotulagem do "
                           "produto",
                           "Regulamentação de promoções e ofertas",
                           "Normativa aduaneira para mercadoria "
                           "importada"),
            "portafolios_sugeridos": ("Temporadas", "Novas lojas",
                                       "E-commerce", "Cadeia de "
                                       "suprimentos"),
        },
        "educacion": {
            "rubro": "Educação e formação",
            "resumen": "O calendário acadêmico é uma restrição rígida: o que "
                       "não está pronto para o início das aulas espera o "
                       "período seguinte.",
            "etapas": {
                "diseno_academico": {
                    "nombre": "Design acadêmico",
                    "objetivo": "Definir a proposta formativa e sua "
                                "justificativa.",
                    "entregables": ("Perfil do egresso", "Plano de "
                                     "estudos", "Justificativa da "
                                     "proposta", "Estimativa de "
                                     "matrícula"),
                    "criterio_salida": "Proposta aprovada pelo órgão "
                                        "acadêmico.",
                    "aprueba": "Conselho / Direção acadêmica",
                },
                "aprobacion_academica": {
                    "nombre": "Aprovação e credenciamento",
                    "objetivo": "Conseguir o reconhecimento oficial, quando "
                                "aplicável.",
                    "entregables": ("Processo de aprovação",
                                     "Documentação de credenciamento",
                                     "Respostas a exigências"),
                    "criterio_salida": "Proposta aprovada ou credenciada "
                                        "pela autoridade educacional.",
                    "aprueba": "Direção acadêmica",
                },
                "preparacion": {
                    "nombre": "Preparação do curso",
                    "objetivo": "Ter docentes, materiais e salas prontos.",
                    "entregables": ("Docentes designados",
                                     "Materiais e bibliografia",
                                     "Salas e plataforma definidas",
                                     "Cronograma do curso"),
                    "criterio_salida": "Tudo pronto antes do início das "
                                        "aulas.",
                    "aprueba": "Coordenação acadêmica",
                },
                "dictado": {
                    "nombre": "Realização do curso",
                    "objetivo": "Ministrar o curso e acompanhar os "
                                "estudantes.",
                    "entregables": ("Registro de frequência",
                                     "Avaliações aplicadas",
                                     "Acompanhamento da evasão"),
                    "criterio_salida": "Curso ministrado por completo "
                                        "conforme o plano.",
                    "aprueba": "Coordenação acadêmica",
                },
                "evaluacion_curso": {
                    "nombre": "Avaliação do curso",
                    "objetivo": "Medir resultados e satisfação.",
                    "entregables": ("Resultados de aprovação",
                                     "Pesquisa com os estudantes",
                                     "Avaliação docente"),
                    "criterio_salida": "Indicadores dentro do esperado.",
                    "aprueba": "Direção acadêmica",
                },
                "cierre_edu": {
                    "nombre": "Encerramento e melhoria",
                    "objetivo": "Encerrar a edição e ajustar a seguinte.",
                    "entregables": ("Atas de notas fechadas",
                                     "Diploma ou certificado emitido",
                                     "Plano de melhoria para a próxima "
                                     "edição"),
                    "criterio_salida": "Atas fechadas e certificados "
                                        "emitidos.",
                    "aprueba": "Secretaria acadêmica / Direção",
                },
            },
            "roles": (
                ("Direção acadêmica",
                 "Aprova a proposta e responde pela qualidade."),
                ("Coordenação acadêmica",
                 "Gerencia a realização do curso."),
                ("Corpo docente", "Ministra e avalia."),
                ("Secretaria acadêmica",
                 "Responde por atas e certificações."),
                ("Direção administrativa",
                 "Aprova orçamento e recursos."),
            ),
            "riesgos": (
                ("Matrícula abaixo do ponto de equilíbrio",
                 "Inscrições lentas perto do fechamento.",
                 "Ponto de decisão com data para abrir ou adiar a "
                 "edição."),
                ("Docente-chave que desiste",
                 "Confirmações de disponibilidade que não chegam.",
                 "Substituto identificado para cada disciplina "
                 "crítica."),
                ("Evasão alta",
                 "Frequência que cai nas primeiras semanas.",
                 "Acompanhamento precoce e contato com quem está "
                 "faltando."),
                ("Aprovação oficial fora do prazo",
                 "Processo com exigências perto do início das aulas.",
                 "Iniciar o trâmite com um período letivo de "
                 "antecedência."),
            ),
            "indicadores": ("Matrícula vs. meta", "Taxa de aprovação",
                             "Evasão", "Satisfação dos estudantes",
                             "Custo por estudante"),
            "normativa": ("Reconhecimento do nível educacional "
                           "correspondente (MEC / ANEP, no Uruguai)",
                           "Normativa de credenciamento de cursos, "
                           "quando aplicável",
                           "Ley 18.331 — dados pessoais de "
                           "estudantes, com menores como categoria "
                           "sensível (Uruguai)",
                           "Regulamento acadêmico da instituição"),
            "portafolios_sugeridos": ("Oferta acadêmica", "Infraestrutura",
                                       "Tecnologia educacional",
                                       "Extensão"),
        },
        "logistica": {
            "rubro": "Logística, transporte e comércio exterior",
            "resumen": "Projetos de rede, depósito e transporte. Os prazos de "
                       "alfândega e de trânsito não dependem da equipe, e é "
                       "preciso planejar com isso.",
            "etapas": {
                "diseno_red": {
                    "nombre": "Design da operação",
                    "objetivo": "Definir como vai fluir a mercadoria.",
                    "entregables": ("Análise de fluxos e volumes",
                                     "Design da rede",
                                     "Modelo de custos logísticos"),
                    "criterio_salida": "A diretoria aprova o design e o "
                                        "investimento.",
                    "aprueba": "Direção de operações",
                },
                "infraestructura": {
                    "nombre": "Infraestrutura e sistemas",
                    "objetivo": "Ter depósito, frota e sistemas prontos.",
                    "entregables": ("Depósito licenciado",
                                     "Frota ou transportadoras "
                                     "contratadas",
                                     "Sistema de gestão de armazém "
                                     "configurado",
                                     "Licenças de transporte"),
                    "criterio_salida": "Infraestrutura licenciada e "
                                        "sistemas testados.",
                    "aprueba": "Operações / Sistemas",
                },
                "puesta_operacion": {
                    "nombre": "Entrada em operação",
                    "objetivo": "Iniciar a operação sem cortar o serviço.",
                    "entregables": ("Plano de migração da operação",
                                     "Capacitação da equipe",
                                     "Operação em paralelo, se "
                                     "substituir outra"),
                    "criterio_salida": "Operação funcionando com os "
                                        "níveis de serviço combinados.",
                    "aprueba": "Direção de operações",
                },
                "estabilizacion": {
                    "nombre": "Estabilização",
                    "objetivo": "Ajustar até que a operação fique "
                                "previsível.",
                    "entregables": ("Indicadores de nível de serviço",
                                     "Registro de ocorrências",
                                     "Ajustes de processo"),
                    "criterio_salida": "Nível de serviço sustentado na "
                                        "meta.",
                    "aprueba": "Direção de operações",
                },
                "cierre_log": {
                    "nombre": "Encerramento",
                    "objetivo": "Transferir para a operação de rotina.",
                    "entregables": ("Procedimentos documentados",
                                     "Transição para a operação",
                                     "Resultado vs. modelo de custos"),
                    "criterio_salida": "Operação aceita como rotina.",
                    "aprueba": "Diretoria",
                },
            },
            "roles": (
                ("Direção de operações",
                 "Aprova o design e responde pelo serviço."),
                ("Chefia de depósito", "Executa a operação diária."),
                ("Despachante aduaneiro",
                 "Responde pelo trâmite de comércio exterior."),
                ("Sistemas",
                 "Configura e integra o sistema de gestão."),
                ("Comercial",
                 "Compromete níveis de serviço com o cliente."),
            ),
            "riesgos": (
                ("Demora na alfândega",
                 "Documentação incompleta ou classificação fiscal "
                 "duvidosa.",
                 "Revisão documental antes do embarque e classificação "
                 "confirmada."),
                ("Corte de serviço na migração",
                 "Migração sem operação em paralelo nem plano de "
                 "contingência.",
                 "Operação em paralelo e critério de reversão "
                 "definido."),
                ("Custo logístico acima do modelo",
                 "Desvios de tarifa de frete ou de ocupação do "
                 "depósito.",
                 "Contratos com tarifa combinada e acompanhamento "
                 "mensal contra o modelo."),
                ("Faltas ou avarias de mercadoria",
                 "Diferenças de inventário recorrentes.",
                 "Inventários cíclicos e controle de acesso ao "
                 "depósito."),
            ),
            "indicadores": ("Entregas no prazo e completas",
                             "Custo logístico sobre a venda",
                             "Acuracidade de inventário",
                             "Tempo de desembaraço aduaneiro",
                             "Ocupação do depósito"),
            "normativa": ("Código Aduaneiro e normativa da Dirección "
                           "Nacional de Aduanas (Uruguai)",
                           "Janela única de comércio exterior (VUCE, "
                           "Uruguai)",
                           "Licenças de transporte de carga do MTOP "
                           "(Uruguai)",
                           "Normativa de mercadorias perigosas, se "
                           "aplicável"),
            "portafolios_sugeridos": ("Rede logística", "Depósitos",
                                       "Transporte", "Comércio exterior"),
        },
        "telecom": {
            "rubro": "Telecomunicações",
            "resumen": "Implantação de rede e serviços. A licença de sítio e "
                       "o espectro definem o cronograma, e são a parte menos "
                       "controlável do projeto.",
            "etapas": {
                "diseno_red_tel": {
                    "nombre": "Design de rede",
                    "objetivo": "Definir cobertura, capacidade e "
                                "tecnologia.",
                    "entregables": ("Estudo de cobertura",
                                     "Dimensionamento de capacidade",
                                     "Seleção de tecnologia",
                                     "Modelo econômico"),
                    "criterio_salida": "A diretoria aprova o design e o "
                                        "investimento.",
                    "aprueba": "Direção técnica",
                },
                "espectro_permisos": {
                    "nombre": "Espectro e licenças",
                    "objetivo": "Garantir espectro e licenças de sítio.",
                    "entregables": ("Autorização de uso de espectro",
                                     "Licenças municipais de sítio",
                                     "Contratos de locação de sítios",
                                     "Estudos de radiação não "
                                     "ionizante"),
                    "criterio_salida": "Licenças concedidas para os "
                                        "sítios da primeira etapa.",
                    "aprueba": "Regulatório",
                },
                "despliegue": {
                    "nombre": "Implantação",
                    "objetivo": "Instalar e colocar os sítios em "
                                "operação.",
                    "entregables": ("Sítios construídos",
                                     "Equipamentos instalados e "
                                     "configurados",
                                     "Enlaces de transmissão "
                                     "operacionais",
                                     "Testes de cobertura"),
                    "criterio_salida": "Sítios em operação com cobertura "
                                        "medida.",
                    "aprueba": "Engenharia de implantação",
                },
                "integracion_serv": {
                    "nombre": "Integração de serviços",
                    "objetivo": "Fazer o serviço funcionar de ponta a "
                                "ponta.",
                    "entregables": ("Integração com o núcleo de rede",
                                     "Testes de serviço",
                                     "Configuração de faturamento e "
                                     "provisionamento"),
                    "criterio_salida": "Serviço testado de ponta a "
                                        "ponta.",
                    "aprueba": "Engenharia",
                },
                "lanzamiento_tel": {
                    "nombre": "Lançamento comercial",
                    "objetivo": "Ir ao mercado com a operação pronta para "
                                "sustentar.",
                    "entregables": ("Plano comercial",
                                     "Capacitação do atendimento ao "
                                     "cliente",
                                     "Monitoramento da qualidade de "
                                     "serviço"),
                    "criterio_salida": "Serviço comercializado com "
                                        "qualidade dentro da meta.",
                    "aprueba": "Direção comercial",
                },
                "cierre_tel": {
                    "nombre": "Transição para a operação",
                    "objetivo": "Fazer com que operações sustente a rede "
                                "sem a equipe do projeto.",
                    "entregables": ("Documentação da rede",
                                     "Transição para operação e "
                                     "manutenção",
                                     "Lições aprendidas"),
                    "criterio_salida": "Operações aceita a transição.",
                    "aprueba": "Direção técnica",
                },
            },
            "roles": (
                ("Direção técnica",
                 "Aprova o design e o investimento."),
                ("Regulatório",
                 "Gerencia espectro e licenças junto ao regulador."),
                ("Engenharia de implantação",
                 "Executa a instalação."),
                ("Operações de rede",
                 "Recebe e sustenta a rede."),
                ("Direção comercial",
                 "Define o lançamento."),
            ),
            "riesgos": (
                ("Licença de sítio negada",
                 "Oposição de vizinhos ou rejeição municipal em "
                 "sítios-chave.",
                 "Sítios alternativos identificados já no design."),
                ("Atraso na atribuição de espectro",
                 "Processo regulatório sem data de resolução.",
                 "Iniciar o trâmite antes de comprometer a data de "
                 "lançamento."),
                ("Equipamentos com prazo de entrega longo",
                 "Prazos do fabricante que não fecham com o plano.",
                 "Pedidos antecipados de equipamentos críticos."),
                ("Qualidade de serviço abaixo do combinado",
                 "Medições de cobertura ou capacidade abaixo do "
                 "design.",
                 "Medir cada sítio antes de habilitar comercialmente."),
            ),
            "indicadores": ("Sítios em operação vs. plano",
                             "Cobertura alcançada",
                             "Qualidade de serviço medida",
                             "Investimento executado vs. orçamento",
                             "Ativações comerciais"),
            "normativa": ("Regulamentação da URSEC — órgão regulador de "
                           "serviços de comunicações do Uruguai",
                           "Autorização de uso de espectro "
                           "radioelétrico",
                           "Normativa municipal de instalação de "
                           "antenas",
                           "Limites de exposição à radiação não "
                           "ionizante"),
            "portafolios_sugeridos": ("Implantação de rede", "Serviços",
                                       "Transformação digital",
                                       "Regulatório"),
        },
    },
}


def _etapa_tr(e: Etapa, ov: dict | None) -> Etapa:
    """Aplica la superposición de traducción a una etapa. `clave` y
    `grupo_pmbok` nunca se tocan: son identificadores, no texto."""
    if not ov:
        return e
    return Etapa(
        e.clave,
        ov.get("nombre", e.nombre),
        e.grupo_pmbok,
        ov.get("objetivo", e.objetivo),
        tuple(ov.get("entregables", e.entregables)),
        ov.get("criterio_salida", e.criterio_salida),
        ov.get("aprueba", e.aprueba),
    )


def _riesgo_tr(r: Riesgo, ov: tuple[str, str, str] | None) -> Riesgo:
    """Aplica la traducción a un riesgo. `area_pmbok` nunca se toca."""
    if not ov:
        return r
    titulo, senal_temprana, mitigacion = ov
    return Riesgo(titulo, r.area_pmbok, senal_temprana, mitigacion)


def _plantilla_tr(p: Plantilla, lang: str) -> Plantilla:
    """Devuelve una vista traducida de la plantilla, sin tocar la constante
    original. `clave` y `areas_criticas` nunca se traducen. Si no hay
    superposición para (lang, p.clave) — o lang no está soportado — se
    devuelve la plantilla en español tal cual, en vez de romper."""
    if lang == "es":
        return p
    ov = _TRAD.get(lang, {}).get(p.clave)
    if ov is None:
        return p

    etapas_ov = ov.get("etapas", {})
    etapas = tuple(_etapa_tr(e, etapas_ov.get(e.clave)) for e in p.etapas)

    roles_ov = ov.get("roles")
    roles = tuple(roles_ov) if roles_ov else p.roles

    riesgos_ov = ov.get("riesgos")
    if riesgos_ov:
        riesgos = tuple(_riesgo_tr(r, rov) for r, rov in zip(p.riesgos, riesgos_ov))
    else:
        riesgos = p.riesgos

    return Plantilla(
        clave=p.clave,
        rubro=ov.get("rubro", p.rubro),
        resumen=ov.get("resumen", p.resumen),
        etapas=etapas,
        roles=roles,
        riesgos=riesgos,
        indicadores=tuple(ov.get("indicadores", p.indicadores)),
        normativa=tuple(ov.get("normativa", p.normativa)),
        portafolios_sugeridos=tuple(
            ov.get("portafolios_sugeridos", p.portafolios_sugeridos)),
        areas_criticas=p.areas_criticas,
        nota=ov.get("nota", p.nota),
    )


# Rótulos fijos de la versión imprimible (como_texto), en los tres idiomas.
_TEXTO_LABELS = {
    "es": {
        "titulo": "Gobernanza de proyectos",
        "etapas": "Etapas",
        "entregables": "Entregables:",
        "puerta": "Puerta de salida:",
        "aprueba": "Aprueba:",
        "roles": "Roles",
        "riesgos": "Riesgos típicos",
        "senal": "señal temprana:",
        "mitigacion": "Mitigación:",
        "indicadores": "Indicadores",
        "normativa": "Normativa de referencia",
        "disclaimer": "Las referencias normativas son orientativas y hay que "
                      "confirmarlas con quien lleva calidad, legales o compliance "
                      "en la empresa. No son asesoramiento legal.",
    },
    "en": {
        "titulo": "Project governance",
        "etapas": "Stages",
        "entregables": "Deliverables:",
        "puerta": "Exit gate:",
        "aprueba": "Approves:",
        "roles": "Roles",
        "riesgos": "Typical risks",
        "senal": "early warning sign:",
        "mitigacion": "Mitigation:",
        "indicadores": "Indicators",
        "normativa": "Reference regulations",
        "disclaimer": "Regulatory references are indicative and specific to "
                      "Uruguay unless noted otherwise, and need to be confirmed "
                      "with whoever handles quality, legal, or compliance at the "
                      "company. This is not legal advice.",
    },
    "pt": {
        "titulo": "Governança de projetos",
        "etapas": "Etapas",
        "entregables": "Entregáveis:",
        "puerta": "Portão de saída:",
        "aprueba": "Aprova:",
        "roles": "Papéis",
        "riesgos": "Riscos típicos",
        "senal": "sinal precoce:",
        "mitigacion": "Mitigação:",
        "indicadores": "Indicadores",
        "normativa": "Normativa de referência",
        "disclaimer": "As referências normativas são orientativas e específicas "
                      "do Uruguai, salvo indicação contrária, e precisam ser "
                      "confirmadas com quem cuida de qualidade, jurídico ou "
                      "compliance na empresa. Isto não é uma consultoria "
                      "jurídica.",
    },
}


def catalogo(lang: str = "es") -> list[Plantilla]:
    return [_plantilla_tr(p, lang) for p in PLANTILLAS.values()]


def obtener(clave: str, lang: str = "es") -> Plantilla:
    if clave not in PLANTILLAS:
        raise ValueError(f"Rubro desconocido: {clave!r}")
    return _plantilla_tr(PLANTILLAS[clave], lang)


def rubros(lang: str = "es") -> list[tuple[str, str]]:
    return [(clave, obtener(clave, lang).rubro) for clave in PLANTILLAS]


def areas_criticas_explicadas(clave: str, lang: str = "es") -> list[dict]:
    """Cruza las áreas críticas del rubro con las definiciones de PMBOK.

    `areas_criticas` no depende del idioma (son claves). El nombre del área
    tiene versión en inglés en pmbok.py (`area_en`) y se usa si está
    disponible; `definicion_tecnica` y `criollo` son contenido de pmbok.py,
    que este módulo no toca, y hoy sólo existen en español para los tres
    idiomas — una limitación pre-existente de pmbok.py, no de esta función.
    """
    p = obtener(clave)
    por_clave = {a["clave"]: a for a in pmbok.AREAS}
    areas = [por_clave[c] for c in p.areas_criticas if c in por_clave]
    if lang == "en":
        areas = [{**a, "area": a.get("area_en") or a["area"]} for a in areas]
    return areas


def checklist(clave: str, lang: str = "es") -> list[dict]:
    """Aplana la plantilla a una lista de puntos verificables por etapa."""
    p = obtener(clave, lang)
    salida = []
    for etapa in p.etapas:
        for entregable in etapa.entregables:
            salida.append({
                "etapa": etapa.nombre,
                "grupo_pmbok": etapa.grupo_pmbok,
                "entregable": entregable,
                "criterio_salida": etapa.criterio_salida,
                "aprueba": etapa.aprueba,
            })
    return salida


def como_texto(clave: str, lang: str = "es") -> str:
    """Versión imprimible, para llevar impresa a la reunión de arranque."""
    p = obtener(clave, lang)
    t = _TEXTO_LABELS.get(lang, _TEXTO_LABELS["es"])
    lineas = [f"# {t['titulo']} — {p.rubro}", "", p.resumen, "",
              f"## {t['etapas']}"]
    for i, e in enumerate(p.etapas, 1):
        lineas += ["", f"### {i}. {e.nombre}", f"*{e.objetivo}*", "",
                   t["entregables"]]
        lineas += [f"- {x}" for x in e.entregables]
        lineas += ["", f"**{t['puerta']}** {e.criterio_salida}",
                   f"**{t['aprueba']}** {e.aprueba}"]
    lineas += ["", f"## {t['roles']}"] + [f"- **{r}**: {q}" for r, q in p.roles]
    lineas += ["", f"## {t['riesgos']}"]
    for r in p.riesgos:
        lineas.append(f"- **{r.titulo}** — {t['senal']} {r.senal_temprana} "
                      f"{t['mitigacion']} {r.mitigacion}")
    lineas += ["", f"## {t['indicadores']}"] + [f"- {i}" for i in p.indicadores]
    lineas += ["", f"## {t['normativa']}"] + [f"- {n}" for n in p.normativa]
    lineas += ["", f"> {t['disclaimer']}"]
    return "\n".join(lineas)



# --------------------------------------------------------------- persistencia


def aplicada(empresa_id: int) -> dict | None:
    """Qué plantilla adoptó esta empresa, si adoptó alguna."""
    version = db.obtener_version_actual(empresa_id, ENTIDAD, "rubro")
    if not version:
        return None
    clave = version["contenido"]
    return {"clave": clave, "plantilla": PLANTILLAS.get(clave), "version": version}


def adoptar(empresa_id: int, clave: str, validado_por_nombre: str = "",
            validado_por_cargo: str = "") -> int:
    """Deja registrado qué gobernanza adoptó la empresa, con quién la validó.

    Queda versionado igual que las definiciones: se puede ver quién la aprobó y
    cuándo, y cambiarla más adelante sin perder la historia.
    """
    obtener(clave)                       # valida que exista antes de guardar
    return db.guardar_version(
        empresa_id, ENTIDAD, "rubro", clave,
        estado="validado" if validado_por_nombre else "borrador",
        recomendado_por="plantilla",
        validado_por_nombre=validado_por_nombre or None,
        validado_por_cargo=validado_por_cargo or None,
    )
