# ifc2postgis

[![Python](https://img.shields.io/badge/Python-3.13--3.15-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Poetry](https://img.shields.io/badge/Poetry-packaging-3673A6?style=for-the-badge&logo=poetry&logoColor=white)](https://python-poetry.org/) [![IfcOpenShell](https://img.shields.io/badge/IfcOpenShell-%3E%3D0.9-0B7285?style=for-the-badge)](https://ifcopenshell.org/) [![IFC](https://img.shields.io/badge/IFC-ISO%2016739-6A5ACD?style=for-the-badge)](https://www.buildingsmart.org/) [![BIM](https://img.shields.io/badge/BIM-to%20GIS-1F7A8C?style=for-the-badge)](https://www.buildingsmart.org/) [![QGIS](https://img.shields.io/badge/QGIS-3.x-589F10?style=for-the-badge&logo=qgis&logoColor=white)](https://qgis.org/)

## What we are building

`ifc2postgis` converts IFC (Industry Foundation Classes) building models into a
PostGIS database. It reads the IFC spatial hierarchy — site, building, storey
and space — extracts 3D geometry with IfcOpenShell, and writes each level into
four related database tables.

The goal is BIM/GIS interoperability: instead of opening an IFC file in a
specialist BIM viewer, the building becomes ordinary spatial data that can be
queried with SQL, analysed with PostGIS functions, and styled in QGIS.

## What is included

- A Python package (`ifc2postgis`) with parsing, geometry extraction and
  database modules.
- A command line interface (`ifc2postgis`) for scripted conversions.
- A QGIS plugin (`ifc2postgis-qgis`) that exposes the same conversion through a
  GUI and loads the resulting tables into the map canvas.
- A room-analysis helper that classifies `IfcSpace` names for educational
  facilities (Laboratory, Office, Corridor, Men, Ladies, Other).

## Data flow

```mermaid
flowchart LR
    A[IFC file] --> B[IfcOpenShell parser]
    B --> C[WKT MULTIPOINT Z]
    C --> D[PostGIS tables]
    D --> E[SQL queries and QGIS layers]
```

## Database model

Each IFC spatial level is stored in its own table. Parent links are kept as
text columns containing the parent element's `GlobalId`.

```mermaid
erDiagram
    ifc_site {
        serial id PK
        text global_id UK
        text name
        geometry geom
    }
    ifc_building {
        serial id PK
        text global_id UK
        text name
        text site_global_id FK
        geometry geom
    }
    ifc_storey {
        serial id PK
        text global_id UK
        text name
        double elevation
        text building_global_id FK
        geometry geom
    }
    ifc_space {
        serial id PK
        text global_id UK
        text name
        text long_name
        text storey_global_id FK
        geometry geom
    }

    ifc_site ||--o{ ifc_building : "contains"
    ifc_building ||--o{ ifc_storey : "contains"
    ifc_storey ||--o{ ifc_space : "contains"
```

All geometry columns are `geometry(GeometryZ, SRID)`. The default SRID is
`4326`; use `0` for local, unprojected coordinates. The current geometry format
is `MULTIPOINT Z` built from element vertices.

## Requirements

- Python `>=3.13,<3.16`
- PostgreSQL with PostGIS enabled
- `ifcopenshell >=0.9,<0.10`, `psycopg2`, `click`
- QGIS 3.x (3.0–3.99) for the plugin

## Installation

```bash
poetry install
```

Enable PostGIS once in the target database:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

## Command line usage

```bash
ifc2postgis \
    --input SOE.ifc \
    --db-url "postgresql://user:password@localhost:5433/bim" \
    --srid 4326 \
    --schema public
```

| Option    | Short | Default  | Description                                      |
|-----------|-------|----------|--------------------------------------------------|
| `--input` | `-i`  | required | Path to the IFC file.                            |
| `--db-url`| `-d`  | required | PostgreSQL connection string.                    |
| `--srid`  | `-s`  | `4326`   | Output SRID; use `0` for local coordinates.      |
| `--schema`|       | `public` | Target schema for the generated tables.          |
| `--drop`  |       | off      | Drop existing tables before writing.             |

## QGIS plugin

The plugin lives in `ifc2postgis_qgis/ifc2postgis_qgis`. To install it:

1. Copy that folder into
   `<QGIS profile>/python/plugins/ifc2postgis_qgis`.
2. Make the `ifc2postgis` package importable from the QGIS Python environment
   (for example with `pip install .` from this repository).
3. Restart QGIS and enable **ifc2postgis-qgis** in Plugin Manager.

It adds an **IFC to PostGIS** action under the **BIM Tools** menu. The dialog
accepts the IFC file, database URL, schema, SRID and optional table reset, then
loads `ifc_site`, `ifc_building`, `ifc_storey` and `ifc_space` as QGIS layers.

## Known limitations

- Geometry is stored as a vertex point cloud, not as surfaces or solids.
- Parent links are resolved through `IfcRelAggregates`; files that only use
  `IfcRelContainedInSpatialStructure` will have null parent links.
- Foreign key constraints are not created automatically.

## Documentation

- [Architecture](docs/architecture.md)
- [Database schema and queries](docs/schema.md)
- [Usage and troubleshooting](docs/usage.md)
- [Documentation index](docs/index.md)

## Development

```bash
poetry run pytest
poetry run black ifc2postgis tests
poetry run flake8 ifc2postgis tests
```
