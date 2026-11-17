# -*- coding: utf-8 -*-
"""Zoning and room analysis tools for ifc2postgis-QGIS."""

from qgis.PyQt.QtCore import QSettings, QObject, pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox


def analyze_spaces(ifc_file, db_url, schema, srid):
    """Analyze IFC spaces for room classification.
    
    This function extracts IfcSpace elements from an IFC file and classifies
    them by room type relevant to educational/BIM facilities: Laboratory,
    Office, Corridor, Men, Ladies, and Other.
    
    Parameters:
        ifc_file: Path to the IFC file
        db_url: PostgreSQL connection URL
        schema: Database schema name
        srid: Spatial Reference System Identifier
        
    Returns:
        Dictionary with space list and room type statistics
    """
    import ifcopenshell
    import ifcopenshell.util.element
    
    try:
        ifc = ifcopenshell.open(ifc_file)
    except Exception as e:
        QMessageBox.critical(None, u"Error", u"Cannot open IFC file: {0}".format(str(e)))
        return None
    
    # Collect space data
    spaces = []
    for space in ifc.by_type("IfcSpace"):
        space_data = {
            "global_id": space.GlobalId if hasattr(space, "GlobalId") else None,
            "name": space.Name if hasattr(space, "Name") else None,
            "long_name": getattr(space, "LongName", None),
        }
        spaces.append(space_data)
    
    # Room classification for educational facilities
    # Based on SOE.ifc model naming patterns: Laboratory, Office, Corridor, Men, Ladies
    room_stats = {
        "total_spaces": len(spaces),
        "by_type": {"Laboratory": 0, "Office": 0, "Corridor": 0, "Men": 0, "Ladies": 0, "Other": 0},
    }
    
    for space in spaces:
        name = (space.get("name") or "").lower()
        long_name = (space.get("long_name") or "").lower()
        combined = name + " " + long_name
        
        if 'laborator' in combined:
            room_stats["by_type"]["Laboratory"] += 1
        elif 'office' in combined:
            room_stats["by_type"]["Office"] += 1
        elif 'corrid' in combined:
            room_stats["by_type"]["Corridor"] += 1
        elif 'men' in combined:
            room_stats["by_type"]["Men"] += 1
        elif 'ladies' in combined:
            room_stats["by_type"]["Ladies"] += 1
        else:
            room_stats["by_type"]["Other"] += 1
    
    return {
        "spaces": spaces,
        "room_stats": room_stats,
    }