"""
IFC parsing and geometry extraction.

This module opens the IFC file with IfcOpenShell, walks the spatial
hierarchy, extracts geometry for each element in world coordinates, and
hands the results to the database module for insertion.
"""

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element

from .database import (
    connect,
    create_schema,
    insert_site,
    insert_building,
    insert_storey,
    insert_space,
)


def build_geometry_settings():
    """
    Return an IfcOpenShell geometry settings object configured to emit
    world coordinates. Using world coordinates means each vertex is
    already placed relative to the IFC project origin, so no additional
    transformation is required before insertion into PostGIS.
    """
    settings = ifcopenshell.geom.settings()
    # The string form works across IfcOpenShell versions. Some releases
    # also expose a constant named USE_WORLD_COORDS.
    settings.set("use-world-coords", True)
    return settings


def element_to_wkt(element, settings):
    """
    Convert one IFC element into a WKT string representing its geometry.

    Returns a MULTIPOINT Z WKT built from the element's vertices, or None
    if the element has no geometry representation. Storing vertices as a
    point cloud is a pragmatic baseline; a later version can reconstruct
    surfaces or solids from the face index buffer.
    """
    if not getattr(element, "Representation", None):
        return None

    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
    except Exception:
        return None

    verts = shape.geometry.verts
    if not verts:
        return None

    points = []
    # The vertex buffer is a flat list of x, y, z triples.
    for i in range(0, len(verts), 3):
        points.append("({0} {1} {2})".format(verts[i], verts[i + 1], verts[i + 2]))

    return "MULTIPOINT Z ({0})".format(", ".join(points))


def find_parent_global_id(element):
    """
    Return the GlobalId of the element that aggregates the given element,
    or None if no aggregating parent exists.
    """
    try:
        parent = ifcopenshell.util.element.get_aggregate(element)
    except Exception:
        parent = None

    if parent is not None and getattr(parent, "GlobalId", None):
        return parent.GlobalId
    return None


def process_ifc(file_path, db_url, srid, schema, drop_tables):
    """
    Read the IFC file, extract the spatial hierarchy, and write rows to
    PostGIS.

    Parameters:
        file_path: path to the input IFC file.
        db_url: PostgreSQL connection string.
        srid: integer SRID for the geometry columns.
        schema: target schema name.
        drop_tables: if True, drop and recreate the tables first.
    """
    ifc_file = ifcopenshell.open(file_path)
    settings = build_geometry_settings()
    conn = connect(db_url)

    try:
        create_schema(conn, schema=schema, srid=srid, drop=drop_tables)

        # Sites are top level elements.
        for site in ifc_file.by_type("IfcSite"):
            if not getattr(site, "GlobalId", None):
                continue
            insert_site(
                conn,
                schema=schema,
                srid=srid,
                global_id=site.GlobalId,
                name=site.Name or "",
                wkt=element_to_wkt(site, settings),
            )

        # Buildings reference their parent site through aggregation.
        for building in ifc_file.by_type("IfcBuilding"):
            if not getattr(building, "GlobalId", None):
                continue
            insert_building(
                conn,
                schema=schema,
                srid=srid,
                global_id=building.GlobalId,
                name=building.Name or "",
                site_global_id=find_parent_global_id(building),
                wkt=element_to_wkt(building, settings),
            )

        # Storeys reference their parent building through aggregation.
        for storey in ifc_file.by_type("IfcBuildingStorey"):
            if not getattr(storey, "GlobalId", None):
                continue
            elevation = getattr(storey, "Elevation", None)
            elevation_value = float(elevation) if elevation is not None else None
            insert_storey(
                conn,
                schema=schema,
                srid=srid,
                global_id=storey.GlobalId,
                name=storey.Name or "",
                elevation=elevation_value,
                building_global_id=find_parent_global_id(storey),
                wkt=element_to_wkt(storey, settings),
            )

        # Spaces reference their parent storey through aggregation.
        for space in ifc_file.by_type("IfcSpace"):
            if not getattr(space, "GlobalId", None):
                continue
            insert_space(
                conn,
                schema=schema,
                srid=srid,
                global_id=space.GlobalId,
                name=space.Name or "",
                long_name=getattr(space, "LongName", "") or "",
                storey_global_id=find_parent_global_id(space),
                wkt=element_to_wkt(space, settings),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()