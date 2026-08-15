// MV Project Management -> Microsoft Fabric (Dataflow Gen2)
// © 2026 Martín Viera. Todos los derechos reservados.
//
// Pegar en: Fabric -> Dataflow Gen2 -> Obtener datos -> Consulta en blanco ->
// Editor avanzado. Devuelve una tabla de navegación con las 6 tablas del
// portafolio; expandí la columna "Data" o hacé clic en la tabla que quieras.
//
// Requiere un gateway de datos local: la API corre en 127.0.0.1 de la máquina
// del cliente y Fabric es un servicio en la nube, así que sin gateway no hay
// forma de que llegue. Está explicado en el README de esta carpeta.
let
    // Cambiar sólo si la API se levantó en otro host o puerto.
    BaseUrl = "http://127.0.0.1:8600",

    // Clave de API. Vacía cuando el gateway corre en la MISMA máquina que la
    // API (el caso normal): api/main.py deja pasar loopback sin clave. Si la
    // API está en otra máquina hay que levantarla con MVPM_API_KEY y poner esa
    // misma clave acá.
    ClaveApi = "",

    Tablas = {"proyectos", "tareas", "equipo", "salud", "backlog_priorizado", "politicas"},

    Encabezados = if ClaveApi = "" then [] else [#"X-API-Key" = ClaveApi],

    // RelativePath en vez de pegar la URL entera a mano: con la URL completa,
    // Power Query no puede validar el origen y la actualización programada
    // falla con "no se puede determinar el origen de datos". Con RelativePath
    // el origen es BaseUrl y el refresh anda.
    Traer = (nombre as text) as table =>
        let
            Respuesta = Web.Contents(BaseUrl, [
                RelativePath = "api/" & nombre,
                Headers = Encabezados
            ]),
            Contenido = Json.Document(Respuesta),
            Tabla = Table.FromRecords(Contenido)
        in
            Tabla,

    Navegacion = Table.FromList(Tablas, Splitter.SplitByNothing(), {"Name"}),
    ConDatos = Table.AddColumn(Navegacion, "Data", each Traer([Name]), type table)
in
    ConDatos
