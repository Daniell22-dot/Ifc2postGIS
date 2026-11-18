"""
ifc2postgis-QGIS
QGIS plugin for converting IFC building models to PostGIS database.
Provides a GUI interface using PyQT for non-developers.
"""
__version__ = "0.1.0"


def classFactory(iface):
    """Required function that creates a plugin instance.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    :return: Instance of the plugin class.
    :rtype: Ifc2postgisQgisPlugin
    """
    from .plugin import Ifc2postgisQgisPlugin
    return Ifc2postgisQgisPlugin(iface)