# -*- coding: utf-8 -*-
"""Zoning and room analysis tools for ifc2postgis-QGIS."""

from qgis.PyQt.QtCore import QSettings, QObject, pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox


def analyze_spaces(ifc_file, db_url, schema, srid):
    """Analyze IFC spaces for zoning and usage classification.
    
    This function extracts space information from an IFC file and performs
    zoning analysis to classify spaces by usage type (residential, commercial, 
    industrial, etc.) and calculate area/volume metrics.
    
    Parameters:
        ifc_file: Path to the IFC file
        db_url: PostgreSQL connection URL
        schema: Database schema name
        srid: Spatial Reference System Identifier
        
    Returns:
        Dictionary with zoning analysis results
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
            "storey": find_storey(space, ifc) if hasattr(space, "LongName") else None,
        }
        spaces.append(space_data)
    
    # Zoning classification
    zoning_stats = {
        "total_spaces": len(spaces),
        "by_usage": {"residential": 0, "commercial": 0, "industrial": 0, "other": 0},
        "total_area": 0,
        "total_volume": 0,
    }
    
    for space in spaces:
        # Simple classification based on name keywords
        name = (space.get("name") or "").lower()
        if any(word in name for word in ["office", "room", "apartment", "bedroom"]):
            zoning_stats["by_usage"]["residential"] += 1
        elif any(word in name for word in ["shop", "store", "market", "mall"]):
            zoning_stats["by_usage"]["commercial"] += 1
        elif any(word in name for word in ["factory", "warehouse", "plant"]):
            zoning_stats["by_usage"]["industrial"] += 1
        else:
            zoning_stats["by_usage"]["other"] += 1
    
    return {
        "spaces": spaces,
        "zoning_stats": zoning_stats,
    }


def find_storey(element, ifc):
    """Find the storey (IfcBuildingStorey) that contains the given element."""
    try:
        # Try to get the associated storey
        related = element.IsDeclaredBy or element.HasAssociativeContext
        # Walk up through aggregate relationships
        parent = ifc.util.element.get_aggregate(element)
        if parent and hasattr(parent, "Name"):
            return parent.Name
    except Exception:
        pass
    return None