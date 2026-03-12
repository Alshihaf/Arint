# core/__init__.py
from .SilentWatcherSuper import SilentWatcherSuper
from .reflection import AuditLoop
from .memory_router import BrainCore
from .dream import Dreamer
from .cot_executive import CoTExecutive

__all__ = ['SilentWatcherSuper', 'AuditLoop', 'BrainCore', 'Dreamer', 'CoTExecutive']