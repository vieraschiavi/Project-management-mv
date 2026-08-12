# Deja el .exe recién compilado en INSTALADOR/ y lo commitea.
#
# Corre en el runner de Windows, al final de build_windows.yml y de
# build_windows_owner.yml. Es lo que hace que el instalador se pueda bajar
# directo del repositorio, sin entrar a Actions ni buscar un artefacto.
#
# Se borra lo que había antes en la subcarpeta: interesa el instalador VIGENTE,
# no una pila de versiones. El historial de git igual las conserva todas —ver la
# nota de tamaño en INSTALADOR/README.md— así que dejarlas también en el árbol
# sería pagar dos veces por lo mismo.
#
# El push se hace con GITHUB_TOKEN, que NO dispara workflows: por eso este
# commit no vuelve a lanzar el build que lo generó. Sin esa garantía de GitHub,
# esto sería un bucle infinito.

param(
    [Parameter(Mandatory = $true)][string]$Subcarpeta,   # CLIENTE u OWNER
    [Parameter(Mandatory = $true)][string]$Origen        # packaging/Output/*.exe
)

$ErrorActionPreference = "Stop"

$exe = Get-ChildItem -Path $Origen -Filter *.exe | Select-Object -First 1
if (-not $exe) {
    Write-Error "No se encontró ningún .exe en $Origen"
    exit 1
}

$destino = Join-Path "INSTALADOR" $Subcarpeta
New-Item -ItemType Directory -Force -Path $destino | Out-Null
Get-ChildItem -Path $destino -Filter *.exe | Remove-Item -Force
Copy-Item $exe.FullName -Destination $destino

$mb = [math]::Round($exe.Length / 1MB, 1)
Write-Host "Instalador copiado: $destino\$($exe.Name) ($mb MB)"

# GitHub RECHAZA cualquier archivo de 100 MiB o más, y no hay forma de forzarlo:
# el push muere del lado del servidor después de subir el archivo entero. El
# instalador de cliente viene rondando los 98 MiB, así que el margen es de un par
# de MB. Se corta acá, con el tamaño a la vista, en vez de dejar que falle un
# push de 15 minutos con un error remoto que no dice cuál archivo fue.
$limiteGitHub = 100MB
if ($exe.Length -ge $limiteGitHub) {
    Write-Error @"
$($exe.Name) pesa $mb MB y GitHub rechaza todo archivo de 100 MiB o más.
No se puede commitear en INSTALADOR/: el push va a fallar del lado del servidor.

Opciones, de menor a mayor cambio:
  * Achicar el .exe (revisar qué está metiendo PyInstaller en el bundle).
  * Publicarlo como asset de un Release en vez de versionarlo — misma descarga
    directa, sin el límite de 100 MiB y sin inflar el historial del repo.
Ver la nota de tamaño en INSTALADOR/README.md.
"@
    exit 1
}
if ($exe.Length -ge 50MB) {
    Write-Host "AVISO: $mb MB. GitHub avisa a partir de 50 MiB y corta en 100 MiB."
}

git config user.name  "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add INSTALADOR

# Sin cambios reales no se commitea: evita ensuciar el historial con commits
# vacíos cuando se redispara el build sobre el mismo código.
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "El instalador de $Subcarpeta no cambió: no hay nada que commitear."
    exit 0
}

git commit -m "Instalador $Subcarpeta actualizado ($($exe.Name))"

# El error de stderr de git no puede abortar el script de acá en adelante: hace
# falta poder mirar $LASTEXITCODE y decidir.
$ErrorActionPreference = "Continue"

# --------------------------------------------------- dejar el árbol limpio
#
# `git pull --rebase` se NIEGA a correr con cambios sin commitear:
#
#     error: cannot pull with rebase: You have unstaged changes.
#     error: Please commit or stash them.
#
# y como los reintentos de abajo no limpian nada, los cinco fallaban idénticos y
# el .exe recién compilado se perdía. No es la carrera entre los dos builds
# —para eso están los reintentos— sino el árbol sucio, que ningún reintento
# arregla.
#
# Quién lo ensucia, en los DOS builds: packaging/strip_py_sources.py borra los
# mvpm/*.py después de que Cython los compila, y esos 39 archivos están
# VERSIONADOS. Para git son 39 borrados sin commitear. El build del dueño suma
# uno más: marcar_build_owner.py reescribe mvpm/edicion.py para dejar
# ES_OWNER_BUILD = True adentro del binario.
#
# Los dos builds del merge de #39 murieron acá con el mismo error, cliente y
# dueño, después de compilar el .exe entero.
#
# `git checkout -- .` restaura tanto lo modificado como lo borrado, así que
# cubre los dos casos. Se descarta todo lo demás: a esta altura el .exe ya está
# commiteado, y lo que queda en el árbol es residuo de compilación que no tiene
# que viajar a main.
git checkout -- .

# ---------------------------------------------------------------- el push
#
# Con reintentos, y no por paranoia de red: los dos builds de instalador
# —cliente y dueño— se disparan con el MISMO push a main, corren en paralelo en
# runners distintos y terminan los dos acá, pusheando a la misma rama. El que
# llega segundo se encuentra con que main avanzó entre su `pull --rebase` y su
# `push`, y muere con "cannot lock ref 'refs/heads/main'". Ya pasó: el build de
# cliente entró y el del dueño quedó en rojo con el .exe compilado y tirado.
#
# Un solo `pull --rebase` no alcanza justamente porque la ventana es esa: entre
# el pull y el push. Lo que cierra el caso es reintentar el par completo.

$maxIntentos = 5
for ($intento = 1; $intento -le $maxIntentos; $intento++) {
    git pull --rebase origin main
    if ($LASTEXITCODE -ne 0) {
        # Rebase a medio hacer: se deja el árbol limpio antes de reintentar, si
        # no el próximo pull se encuentra un rebase en curso y falla siempre.
        git rebase --abort 2>&1 | Out-Null
        Write-Host "El rebase falló (intento $intento de $maxIntentos)."
    }
    else {
        git push origin HEAD:main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "INSTALADOR/$Subcarpeta actualizado en main (intento $intento)."
            exit 0
        }
        Write-Host "El push falló (intento $intento de $maxIntentos): main avanzó."
    }
    if ($intento -lt $maxIntentos) {
        $espera = 5 * $intento
        Write-Host "Reintentando en $espera segundos..."
        Start-Sleep -Seconds $espera
    }
}

Write-Error "No se pudo pushear INSTALADOR/$Subcarpeta después de $maxIntentos intentos."
exit 1
