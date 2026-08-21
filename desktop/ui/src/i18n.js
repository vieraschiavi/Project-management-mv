// © 2026 Martín Viera. Todos los derechos reservados.
/*
 * Traducciones de la interfaz de escritorio (ES/EN/PT).
 *
 * Es un archivo aparte y no un import de `mvpm/i18n.py` porque este bundle
 * corre en el navegador y no puede leer Python. El precio es tener dos
 * diccionarios; el test `tests/test_ui_escritorio.py` exige que los tres
 * idiomas tengan las MISMAS claves acá, igual que
 * `test_i18n_parity_all_languages` lo exige del lado del motor.
 */

const ES = {
  app: 'MV Project Management',

  nav_panorama: 'Panorama',
  nav_proyectos: 'Proyectos',
  nav_salud: 'Salud',
  nav_tareas: 'Tareas',
  nav_backlog: 'Backlog priorizado',
  nav_equipo: 'Equipo',
  nav_politicas: 'Políticas',
  nav_licencia: 'Licencia',

  kpi_proyectos: 'Proyectos',
  kpi_salud: 'Salud del portafolio',
  kpi_riesgo: 'En rojo',
  kpi_tareas: 'Tareas abiertas',
  kpi_vencidas: 'Tareas vencidas',
  kpi_presupuesto: 'Presupuesto ejecutado',

  salud_por_dimension: 'Salud por dimensión',
  salud_por_proyecto: 'Salud por proyecto',
  peor_dimension: 'Dimensión más floja',

  dim_alcance: 'Alcance',
  dim_cronograma: 'Cronograma',
  dim_presupuesto: 'Presupuesto',
  dim_riesgo: 'Riesgo',
  dim_dependencias: 'Dependencias',
  dim_equipo: 'Equipo',

  col_nombre: 'Nombre',
  col_portafolio: 'Portafolio',
  col_sponsor: 'Sponsor',
  col_dueno: 'Responsable',
  col_criticidad: 'Criticidad',
  col_presupuesto: 'Presupuesto',
  col_ejecutado: 'Ejecutado',
  col_indice: 'Índice',
  col_estado: 'Estado',
  col_titulo: 'Tarea',
  col_responsable: 'Responsable',
  col_vencimiento: 'Vence',
  col_prioridad: 'Prioridad',
  col_valor: 'Valor esperado',
  col_impacto: 'Tareas que destraba',
  col_dias: 'Días restantes',
  col_rol: 'Rol',
  col_capacidad: 'Capacidad semanal',
  col_carga: 'Carga actual',
  col_politica: 'Política',
  col_descripcion: 'Descripción',
  col_evidencia: 'Evidencia',
  col_proyecto: 'Proyecto',

  estado_saludable: 'Saludable',
  estado_observacion: 'En observación',
  estado_riesgo: 'En riesgo',

  buscar: 'Buscar…',
  sin_datos: 'Todavía no hay datos cargados.',
  filas: 'filas',
  reintentar: 'Reintentar',
  actualizar: 'Actualizar',

  cargando: 'Levantando el motor…',
  error_conexion: 'No se pudo hablar con el motor',
  error_detalle: 'Detalle técnico',

  lic_titulo: 'Licencia',
  lic_trial: 'Prueba completa',
  lic_dias: 'días restantes',
  lic_activa: 'Licencia activa',
  lic_owner: 'Edición del dueño — sin candado',
  lic_vencida: 'La prueba de 7 días venció',
  lic_vencida_texto: 'Tus datos siguen guardados, no se borró nada. Pegá tu '
    + 'licencia Professional acá abajo y seguís exactamente donde estabas.',
  lic_pegar: 'Pegá tu token de licencia',
  lic_activar: 'Activar',
  lic_activando: 'Activando…',
  lic_quitar: 'Quitar la licencia de esta máquina',
  lic_ok: 'Licencia activada.',
  lic_invalida: 'Ese token no es una licencia válida.',
  lic_no_guardada: 'La licencia es válida pero no se pudo guardar en el disco.',
  lic_plan: 'Plan',
  lic_cupo: 'Consultas de IA por mes',
  lic_ilimitado: 'sin límite',
};

const EN = {
  app: 'MV Project Management',

  nav_panorama: 'Overview',
  nav_proyectos: 'Projects',
  nav_salud: 'Health',
  nav_tareas: 'Tasks',
  nav_backlog: 'Prioritised backlog',
  nav_equipo: 'Team',
  nav_politicas: 'Policies',
  nav_licencia: 'Licence',

  kpi_proyectos: 'Projects',
  kpi_salud: 'Portfolio health',
  kpi_riesgo: 'In red',
  kpi_tareas: 'Open tasks',
  kpi_vencidas: 'Overdue tasks',
  kpi_presupuesto: 'Budget spent',

  salud_por_dimension: 'Health by dimension',
  salud_por_proyecto: 'Health by project',
  peor_dimension: 'Weakest dimension',

  dim_alcance: 'Scope',
  dim_cronograma: 'Schedule',
  dim_presupuesto: 'Budget',
  dim_riesgo: 'Risk',
  dim_dependencias: 'Dependencies',
  dim_equipo: 'Team',

  col_nombre: 'Name',
  col_portafolio: 'Portfolio',
  col_sponsor: 'Sponsor',
  col_dueno: 'Owner',
  col_criticidad: 'Criticality',
  col_presupuesto: 'Budget',
  col_ejecutado: 'Spent',
  col_indice: 'Index',
  col_estado: 'Status',
  col_titulo: 'Task',
  col_responsable: 'Assignee',
  col_vencimiento: 'Due',
  col_prioridad: 'Priority',
  col_valor: 'Expected value',
  col_impacto: 'Tasks it unblocks',
  col_dias: 'Days left',
  col_rol: 'Role',
  col_capacidad: 'Weekly capacity',
  col_carga: 'Current load',
  col_politica: 'Policy',
  col_descripcion: 'Description',
  col_evidencia: 'Evidence',
  col_proyecto: 'Project',

  estado_saludable: 'Healthy',
  estado_observacion: 'Watch',
  estado_riesgo: 'At risk',

  buscar: 'Search…',
  sin_datos: 'No data loaded yet.',
  filas: 'rows',
  reintentar: 'Retry',
  actualizar: 'Refresh',

  cargando: 'Starting the engine…',
  error_conexion: 'Could not reach the engine',
  error_detalle: 'Technical detail',

  lic_titulo: 'Licence',
  lic_trial: 'Full trial',
  lic_dias: 'days left',
  lic_activa: 'Licence active',
  lic_owner: 'Owner edition — no lock',
  lic_vencida: 'The 7-day trial has expired',
  lic_vencida_texto: 'Your data is still saved, nothing was deleted. Paste your '
    + 'Professional licence below and you continue exactly where you were.',
  lic_pegar: 'Paste your licence token',
  lic_activar: 'Activate',
  lic_activando: 'Activating…',
  lic_quitar: 'Remove the licence from this machine',
  lic_ok: 'Licence activated.',
  lic_invalida: 'That token is not a valid licence.',
  lic_no_guardada: 'The licence is valid but could not be saved to disk.',
  lic_plan: 'Plan',
  lic_cupo: 'AI queries per month',
  lic_ilimitado: 'unlimited',
};

const PT = {
  app: 'MV Project Management',

  nav_panorama: 'Panorama',
  nav_proyectos: 'Projetos',
  nav_salud: 'Saúde',
  nav_tareas: 'Tarefas',
  nav_backlog: 'Backlog priorizado',
  nav_equipo: 'Equipe',
  nav_politicas: 'Políticas',
  nav_licencia: 'Licença',

  kpi_proyectos: 'Projetos',
  kpi_salud: 'Saúde do portfólio',
  kpi_riesgo: 'Em vermelho',
  kpi_tareas: 'Tarefas abertas',
  kpi_vencidas: 'Tarefas vencidas',
  kpi_presupuesto: 'Orçamento executado',

  salud_por_dimension: 'Saúde por dimensão',
  salud_por_proyecto: 'Saúde por projeto',
  peor_dimension: 'Dimensão mais fraca',

  dim_alcance: 'Escopo',
  dim_cronograma: 'Cronograma',
  dim_presupuesto: 'Orçamento',
  dim_riesgo: 'Risco',
  dim_dependencias: 'Dependências',
  dim_equipo: 'Equipe',

  col_nombre: 'Nome',
  col_portafolio: 'Portfólio',
  col_sponsor: 'Patrocinador',
  col_dueno: 'Responsável',
  col_criticidad: 'Criticidade',
  col_presupuesto: 'Orçamento',
  col_ejecutado: 'Executado',
  col_indice: 'Índice',
  col_estado: 'Situação',
  col_titulo: 'Tarefa',
  col_responsable: 'Responsável',
  col_vencimiento: 'Vence',
  col_prioridad: 'Prioridade',
  col_valor: 'Valor esperado',
  col_impacto: 'Tarefas que destrava',
  col_dias: 'Dias restantes',
  col_rol: 'Função',
  col_capacidad: 'Capacidade semanal',
  col_carga: 'Carga atual',
  col_politica: 'Política',
  col_descripcion: 'Descrição',
  col_evidencia: 'Evidência',
  col_proyecto: 'Projeto',

  estado_saludable: 'Saudável',
  estado_observacion: 'Em observação',
  estado_riesgo: 'Em risco',

  buscar: 'Buscar…',
  sin_datos: 'Ainda não há dados carregados.',
  filas: 'linhas',
  reintentar: 'Tentar de novo',
  actualizar: 'Atualizar',

  cargando: 'Iniciando o motor…',
  error_conexion: 'Não foi possível falar com o motor',
  error_detalle: 'Detalhe técnico',

  lic_titulo: 'Licença',
  lic_trial: 'Teste completo',
  lic_dias: 'dias restantes',
  lic_activa: 'Licença ativa',
  lic_owner: 'Edição do dono — sem cadeado',
  lic_vencida: 'O teste de 7 dias venceu',
  lic_vencida_texto: 'Seus dados continuam salvos, nada foi apagado. Cole sua '
    + 'licença Professional abaixo e você continua exatamente onde estava.',
  lic_pegar: 'Cole seu token de licença',
  lic_activar: 'Ativar',
  lic_activando: 'Ativando…',
  lic_quitar: 'Remover a licença desta máquina',
  lic_ok: 'Licença ativada.',
  lic_invalida: 'Esse token não é uma licença válida.',
  lic_no_guardada: 'A licença é válida mas não pôde ser salva no disco.',
  lic_plan: 'Plano',
  lic_cupo: 'Consultas de IA por mês',
  lic_ilimitado: 'sem limite',
};

export const IDIOMAS = { es: ES, en: EN, pt: PT };

/** Traduce. Si falta la clave en el idioma elegido, cae a español y no al
 *  nombre de la clave: un `nav_panorama` crudo en pantalla es peor que la
 *  palabra correcta en otro idioma. */
export function t(clave, lang = 'es') {
  const dic = IDIOMAS[lang] || ES;
  return dic[clave] !== undefined ? dic[clave] : (ES[clave] !== undefined ? ES[clave] : clave);
}
