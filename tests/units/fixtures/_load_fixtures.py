import pkgutil
import types
import typing


def get_modules(module: types.ModuleType) -> typing.Iterable[pkgutil.ModuleInfo]:
    """Wrapp pkgutil.walk_packages with predefined magic variables.

    Args:
    ----
        module (ModuleType): Module to be walked through.

    Returns:
    -------
        Iterable[pkgutil.ModuleInfo]: Iterable of pkgutil.ModuleInfo objects.

    """
    return pkgutil.walk_packages(module.__path__, prefix=module.__name__ + ".")


def get_sub_modules(module: types.ModuleType) -> typing.Iterable[str]:
    """Create iterable from modules list.

    Args:
    ----
        module (ModuleType): Module to be inpected

    Returns:
    -------
        Iterable[str]: list of packages" names.

    """
    return [package.name for package in get_modules(module)]
