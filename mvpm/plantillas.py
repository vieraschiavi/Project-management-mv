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


def catalogo() -> list[Plantilla]:
    return list(PLANTILLAS.values())


def obtener(clave: str) -> Plantilla:
    if clave not in PLANTILLAS:
        raise ValueError(f"Rubro desconocido: {clave!r}")
    return PLANTILLAS[clave]


def rubros() -> list[tuple[str, str]]:
    return [(p.clave, p.rubro) for p in PLANTILLAS.values()]


def areas_criticas_explicadas(clave: str) -> list[dict]:
    """Cruza las áreas críticas del rubro con las definiciones de PMBOK."""
    p = obtener(clave)
    por_clave = {a["clave"]: a for a in pmbok.AREAS}
    return [por_clave[c] for c in p.areas_criticas if c in por_clave]


def checklist(clave: str) -> list[dict]:
    """Aplana la plantilla a una lista de puntos verificables por etapa."""
    p = obtener(clave)
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


def como_texto(clave: str) -> str:
    """Versión imprimible, para llevar impresa a la reunión de arranque."""
    p = obtener(clave)
    lineas = [f"# Gobernanza de proyectos — {p.rubro}", "", p.resumen, "", "## Etapas"]
    for i, e in enumerate(p.etapas, 1):
        lineas += ["", f"### {i}. {e.nombre}", f"*{e.objetivo}*", "", "Entregables:"]
        lineas += [f"- {x}" for x in e.entregables]
        lineas += ["", f"**Puerta de salida:** {e.criterio_salida}",
                   f"**Aprueba:** {e.aprueba}"]
    lineas += ["", "## Roles"] + [f"- **{r}**: {q}" for r, q in p.roles]
    lineas += ["", "## Riesgos típicos"]
    for r in p.riesgos:
        lineas.append(f"- **{r.titulo}** — señal temprana: {r.senal_temprana} "
                      f"Mitigación: {r.mitigacion}")
    lineas += ["", "## Indicadores"] + [f"- {i}" for i in p.indicadores]
    lineas += ["", "## Normativa de referencia"] + [f"- {n}" for n in p.normativa]
    lineas += ["", "> Las referencias normativas son orientativas y hay que "
               "confirmarlas con quien lleva calidad, legales o compliance en la "
               "empresa. No son asesoramiento legal."]
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
