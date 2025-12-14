"""
Sonorium Plugin System

Provides extensibility for Sonorium through directory-based plugins.
Plugins are stored in /config/sonorium/plugins/ to survive addon updates.
"""

from sonorium.plugins.base import BasePlugin
from sonorium.plugins.manager import PluginManager

__all__ = ['BasePlugin', 'PluginManager']
