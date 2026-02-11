"""
Lightweight logging system for MicroPython.
Provides configurable log levels for debugging and production use.
"""


class LogLevel:
    """Log level constants."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    NONE = 4  # Disable all logging


class Logger:
    """
    Simple logger with configurable global and per-module levels.

    Usage:
        from logger import Logger, LogLevel

        log = Logger("MyModule")
        log.info("Starting...")
        log.debug("Debug details")

        # Change global level
        Logger.set_level(LogLevel.DEBUG)

        # Set module-specific level (overrides global)
        Logger.set_module_level("WiFiManager", LogLevel.DEBUG)
        Logger.set_module_level("WebServer", LogLevel.ERROR)
    """

    _level = LogLevel.INFO  # Default global level
    _module_levels = {}  # Module-specific levels: {module_name: level}
    _level_names = ['DEBUG', 'INFO', 'WARN', 'ERROR']
    _hooks = []  # list of callable(level, module, msg)

    def __init__(self, module_name: str):
        """
        Create a logger for a specific module.

        Args:
            module_name: Name to prefix log messages with.
        """
        self._module = module_name

    @classmethod
    def set_level(cls, level: int) -> None:
        """
        Set the global logging level.

        Args:
            level: LogLevel constant (DEBUG, INFO, WARNING, ERROR, NONE).
        """
        cls._level = level

    @classmethod
    def get_level(cls) -> int:
        """Get the current global logging level."""
        return cls._level

    @classmethod
    def set_module_level(cls, module_name: str, level: int) -> None:
        """
        Set logging level for a specific module.

        Module-level settings override the global level for that module.

        Args:
            module_name: Name of the module (as passed to Logger constructor).
            level: LogLevel constant. Use None to remove module-specific level.
        """
        if level is None:
            cls._module_levels.pop(module_name, None)
        else:
            cls._module_levels[module_name] = level

    @classmethod
    def get_module_level(cls, module_name: str) -> int:
        """
        Get the effective logging level for a module.

        Args:
            module_name: Name of the module.

        Returns:
            Module-specific level if set, otherwise global level.
        """
        return cls._module_levels.get(module_name, cls._level)

    @classmethod
    def clear_module_levels(cls) -> None:
        """Remove all module-specific level settings."""
        cls._module_levels.clear()

    @classmethod
    def add_hook(cls, hook) -> None:
        """
        Register a log hook callback.

        Hook signature: hook(level: int, module: str, msg: str)

        Args:
            hook: Callable to receive log messages.
        """
        if hook not in cls._hooks:
            cls._hooks.append(hook)

    @classmethod
    def remove_hook(cls, hook) -> None:
        """
        Remove a log hook callback.

        Args:
            hook: Previously registered hook to remove.
        """
        if hook in cls._hooks:
            cls._hooks.remove(hook)

    def _get_effective_level(self) -> int:
        """Get the effective level for this logger instance."""
        return Logger._module_levels.get(self._module, Logger._level)

    def _log(self, level: int, msg: str) -> None:
        """Internal logging method."""
        if level >= self._get_effective_level():
            prefix = Logger._level_names[level] if level < len(Logger._level_names) else '?'
            print(f"[{prefix}] {self._module}: {msg}")
            for hook in Logger._hooks:
                try:
                    hook(level, self._module, msg)
                except Exception:
                    pass

    def debug(self, msg: str) -> None:
        """Log a debug message (verbose, for development)."""
        self._log(LogLevel.DEBUG, msg)

    def info(self, msg: str) -> None:
        """Log an info message (normal operation)."""
        self._log(LogLevel.INFO, msg)

    def warning(self, msg: str) -> None:
        """Log a warning message (potential issues)."""
        self._log(LogLevel.WARNING, msg)

    def error(self, msg: str) -> None:
        """Log an error message (failures)."""
        self._log(LogLevel.ERROR, msg)
