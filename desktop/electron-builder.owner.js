// © 2026 Martín Viera. Todos los derechos reservados.
//
// Configuración de electron-builder para la **Owner Edition**: el mismo
// instalador de escritorio, con identidad propia para que el dueño pueda
// tener las dos versiones instaladas en la misma PC sin que una pise a la
// otra.
//
// Qué la hace "owner" NO está acá: es `packaging/marcar_build_owner.py`, que
// pone `ES_OWNER_BUILD = True` en mvpm/edicion.py ANTES de que Cython compile
// el motor, así que la constante queda adentro del .pyd. Este archivo sólo
// cambia el envoltorio (AppId, nombre, accesos directos); si alguien corriera
// este config sin ese paso, saldría un instalador con nombre de owner y
// candado de cliente — por eso el workflow los ata en el mismo job.
//
// Se parte del `build` de package.json en vez de repetirlo: cuando se pasa
// `--config`, electron-builder IGNORA el bloque `build` de package.json, así
// que sin este spread la edición del dueño se quedaría sin `extraResources`
// (el motor y la UI de React) y produciría un instalador vacío que arranca y
// no encuentra el motor. Lo cubre `tests/test_instalador_escritorio.py`.
const base = require('./package.json').build;

module.exports = {
  ...base,
  appId: 'com.mvprojectmanagement.desktop.owner',
  productName: 'MV Project Management Owner',
  artifactName: 'MVProjectManagement-Owner-Setup-${version}.${ext}',
  nsis: {
    ...base.nsis,
    shortcutName: 'MV Project Management Owner',
    uninstallDisplayName: 'MV Project Management Owner',
  },
};
