import importlib.resources
import logging
import os
import pathlib
from collections.abc import Callable

import platformdirs

log = logging.getLogger(__name__)


def _get_file(reader: Callable[..., bytes], target: pathlib.Path) -> pathlib.Path:
    file_obj = open(target, 'wb')
    fd = file_obj.fileno()
    _ = os.write(fd, reader())
    os.close(fd)
    del reader
    return pathlib.Path(target)


def _get_target_path(archive_name: str, resource_name: str) -> pathlib.Path:
    target_path = _get_cache_dir() / f'{archive_name}-tmp' / resource_name
    os.makedirs(target_path.parent, exist_ok=True)
    return target_path


def _get_cache_dir() -> pathlib.Path:
    if os.environ.get('PYTHON_EGG_CACHE'):
        return pathlib.Path(os.environ['PYTHON_EGG_CACHE'])
    return pathlib.Path(platformdirs.user_cache_dir('Python-Eggs'))


def resource_filename(package: str, resource_name: str) -> str:
    """Returns a file system path for the specified .egg plugin resource."""
    log.warning(f'Getting resource for {resource_name} in package {package}')
    target_path = _get_target_path(package, resource_name)

    fp = importlib.resources.files(package)
    reader = fp.joinpath(resource_name).read_bytes
    usable_path = _get_file(reader, target_path)
    return usable_path.as_posix()
