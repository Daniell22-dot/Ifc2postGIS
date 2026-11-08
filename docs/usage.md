# Usage

This document covers installation, running the converter, and common
options.

## Installation

The converter is managed with Poetry. From the repository root:

    poetry install

This creates a virtual environment and installs all dependencies,
including IfcOpenShell, psycopg2, Click, Rich, and Shapely.

To enter the environment:

    poetry shell

## Database preparation

The target database must have the PostGIS extension enabled. Run once
against the database as a superuser:

    CREATE EXTENSION IF NOT EXISTS postgis;

Verify the installation:

    SELECT PostGIS_Version();

## Running the converter

Minimal invocation:

    ifc2postgis --input model.ifc --db-url "postgresql://user:pass@localhost:5432/bim_db"

The command prints progress information and exits with status zero on
success.

## Options

| Option   | Short | Default   | Description                                              |
|----------|-------|-----------|----------------------------------------------------------|
| --input  | -i    | none      | Path to the IFC file. Required.                          |
| --db-url | -d    | none      | PostgreSQL connection string. Required.                  |
| --srid   | -s    | 4326      | SRID for geometry columns. Use 0 for local coordinates.  |
| --schema |       | public    | Target schema for generated tables.                      |
| --drop   |       | enabled   | Drop existing tables before writing.                     |
| --no-drop|       |           | Keep existing tables and append new rows.                |

## Coordinate systems

If the IFC model has not been georeferenced, pass --srid 0. This tells
PostGIS to treat the coordinates as plain Cartesian values without a
projection. Spatial functions that depend on a geographic coordinate
system will not behave as expected in this mode, but storage and
visualization in QGIS or similar tools work correctly.

If the model has been georeferenced with IfcMapConversion or an
equivalent mechanism, and the coordinates are already in a projected
system, pass the matching EPSG code. For example, a model in UTM Zone
33N uses --srid 32633.

## Example workflow

Load a model into a fresh schema:

    ifc2postgis \
        --input building.ifc \
        --db-url "postgresql://postgres:secret@localhost:5432/bim" \
        --schema project_alpha \
        --srid 0

Inspect the result:

    psql "postgresql://postgres:secret@localhost:5432/bim" \
        -c "SELECT name, COUNT(*) FROM project_alpha.ifc_space GROUP BY name;"

## Troubleshooting

Symptom: "geometry type MULTIPOINT has no Z dimension".

Cause: The SRID was passed as a string or the PostGIS version is older
than 2.0.

Fix: Confirm the geometry column definition includes GeometryZ, and
verify the PostGIS version with SELECT PostGIS_Version().

Symptom: all geom columns are null.

Cause: The IFC elements have no body representation, or create_shape
failed for every element.

Fix: Open the file in an IFC viewer and confirm the elements have
geometry. Check the conversion log for the first failure message.

Symptom: parent_global_id columns are all null.

Cause: The file uses IfcRelContainedInSpatialStructure rather than
IfcRelAggregates to link elements to their parents.

Fix: This is a known limitation. The next revision of parser.py will
traverse both relationship types.