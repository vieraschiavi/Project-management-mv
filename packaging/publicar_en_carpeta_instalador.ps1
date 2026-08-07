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
git pull --rebase origin main
git push origin HEAD:main
Write-Host "INSTALADOR/$Subcarpeta actualizado en main."
