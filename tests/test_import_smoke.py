"""Smoke test de importación/compilación del paquete auto_reddit.

Objetivo: detectar roturas gruesas (sintaxis, import circular, dependencias
faltantes) en cualquier módulo del paquete, sin acoplarse a ninguna API interna.

Estrategia:
- Recorre todos los sub-módulos bajo ``auto_reddit`` con ``pkgutil.walk_packages``.
- Importa cada uno vía ``importlib.import_module``.
- Un fallo de import → el test falla con el nombre del módulo roto como parámetro.

Por qué es pragmático:
- Cero acoplamiento a contratos o lógica interna.
- Se auto-actualiza al añadir nuevos módulos (no hay lista manual).
- Coste de mantenimiento casi nulo: solo falla si algo se rompe de verdad.

Limitaciones conocidas:
- No detecta errores en tiempo de ejecución ni lógica incorrecta.
- ``config/settings.py`` instancia ``Settings()`` al importarse; las variables de
  entorno dummy del conftest raíz garantizan que no falle en ausencia de `.env`.
"""

from __future__ import annotations

import importlib
import pkgutil

import auto_reddit

# ---------------------------------------------------------------------------
# Colección de módulos — se ejecuta una sola vez al cargarse el fichero
# ---------------------------------------------------------------------------

_ALL_MODULE_NAMES: list[str] = [
    module_info.name
    for module_info in pkgutil.walk_packages(
        path=auto_reddit.__path__,
        prefix=auto_reddit.__name__ + ".",
        onerror=None,
    )
]


# ---------------------------------------------------------------------------
# Test parametrizado: un caso por módulo
# ---------------------------------------------------------------------------


def pytest_generate_tests(metafunc):
    """Parametriza ``module_name`` dinámicamente con todos los módulos encontrados."""
    if "module_name" in metafunc.fixturenames:
        metafunc.parametrize("module_name", _ALL_MODULE_NAMES, ids=_ALL_MODULE_NAMES)


class TestImportSmoke:
    """Cada módulo del paquete debe poder importarse sin errores."""

    def test_module_imports_cleanly(self, module_name: str) -> None:
        """Importar ``module_name`` no debe lanzar ninguna excepción.

        Detecta: SyntaxError, ImportError, ModuleNotFoundError, errores de
        inicialización de módulo (e.g. Settings() fallando por vars faltantes).
        """
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"El módulo '{module_name}' falló al importarse: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
