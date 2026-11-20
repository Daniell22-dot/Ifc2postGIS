# -*- coding: utf-8 -*-
"""Zoning and room analysis tools for ifc2postgis-QGIS."""

from collections import Counter

from qgis.PyQt.QtWidgets import QMessageBox


def analyze_spaces(ifc_file, db_url, schema, srid):
    """Analyze IfcSpace elements in any IFC dataset.

    Spaces are grouped by their IFC Name, falling back to LongName and then
    to "Unnamed". No room-type vocabulary is assumed, so the results adapt
    to the vocabulary used by the loaded model.

    Parameters:
        ifc_file: Path to the IFC file
        db_url: PostgreSQL connection URL
        schema: Database schema name
        srid: Spatial Reference System Identifier

    Returns:
        Dictionary with the space list and name-based statistics.
    """
    import ifcopenshell

    try:
        ifc = ifcopenshell.open(ifc_file)
    except Exception as e:
        QMessageBox.critical(None, u"Error", u"Cannot open IFC file: {0}".format(str(e)))
        return None

    spaces = []
    labels = []
    for space in ifc.by_type("IfcSpace"):
        name = getattr(space, "Name", None)
        long_name = getattr(space, "LongName", None)
        label = (name or long_name or u"Unnamed").strip() or u"Unnamed"
        spaces.append(
            {
                "global_id": getattr(space, "GlobalId", None),
                "name": name,
                "long_name": long_name,
            }
        )
        labels.append(label)

    return {
        "spaces": spaces,
        "room_stats": {
            "total_spaces": len(spaces),
            "by_type": dict(Counter(labels)),
        },
    }
