"""Task registry — functions must be registered so workers can look them up by name."""

from typing import Callable

_registry: dict[str, Callable] = {}


def register(name: str = ""):
    """Decorator to register a task function."""
    def wrapper(fn: Callable) -> Callable:
        task_name = name or fn.__name__
        _registry[task_name] = fn
        return fn
    return wrapper


def get_task(name: str) -> Callable | None:
    return _registry.get(name)
