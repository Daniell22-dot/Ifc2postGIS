# -*- coding: utf-8 -*-
"""Main plugin class for ifc2postgis-QGIS."""

import os

from qgis.PyQt.QtWidgets import QAction


class Ifc2postgisQgisPlugin:
    """QGIS plugin that provides a GUI for ifc2postgis conversion tool."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to the plugin
                      which provides the hook by which you can manipulate the QGIS
                      application at runtime.
        :type iface: QgisInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []

    def initGui(self):
        """Create the menu entry and toolbar icon for the plugin."""
        self.action = QAction(
            u"&IFC to PostGIS",
            self.iface.mainWindow(),
            triggered=self.run,
            parent=self.iface.mainWindow(),
        )
        self.action.setObjectName(u"ifc2postgisAction")
        self.iface.addPluginToMenu(u"&BIM Tools", self.action)
        self.iface.addToolBarIcon(self.action)
        self.actions.append(self.action)

    def unload(self):
        """Removes the plugin menu item and toolbar icon from QGIS."""
        for action in self.actions:
            self.iface.removePluginMenu(u"&BIM Tools", action)
            self.iface.removeToolBarIcon(action)
        self.actions = []

    def run(self):
        """Run the plugin's main dialog."""
        from .dialog import Ifc2postgisDialog

        dlg = Ifc2postgisDialog(self.iface)
        dlg.show()
        dlg.raise_()
