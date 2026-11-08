# ifc2postgis

A command-line tool that converts IFC building models into a PostGIS database. It extracts the spatial hierarchy (site, building, storey, space) and preserves 3D geometry as native PostGIS geometry columns.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![IfcOpenShell](https://img.shields.io/badge/IfcOpenShell-0.9.0-green?logo=opensourceinitiative&logoColor=white)
![Shell](https://img.shields.io/badge/Shell-PowerShell-5391FE?logo=powershell&logoColor=white)
![BIM](https://img.shields.io/badge/BIM-IFC-orange)

## Overview

This tool reads an IFC file using IfcOpenShell, traverses the `IfcSite` -> `IfcBuilding` -> `IfcBuildingStorey` -> `IfcSpace` hierarchy, and writes each element into a dedicated PostGIS table. Geometry is extracted in world coordinates and inserted as 3D geometries, making the output immediately usable for spatial queries and GIS visualization.

## Requirements

- Python 3.13 or later
- PostgreSQL with PostGIS extension enabled
- IfcOpenShell (installed via Poetry)

## Installation

Clone the repository and install dependencies with Poetry:

```shell
git clone https://github.com/Daniell22-dot/Ifc2postGIS.git
cd ifc2postgis
poetry install
```

Activate the virtual environment:

```shell
poetry shell
```

## Usage

Run the converter by providing an input IFC file and a PostGIS connection string:

```shell
ifc2postgis --input model.ifc --db-url "postgresql://user:password@localhost:5432/bim_db" --srid 0
```

### Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--input` | `-i` | Path to the input IFC file (required) |
| `--db-url` | `-d` | PostGIS connection string (required) |
| `--srid` | `-s` | Spatial Reference System Identifier (default: 4326) |

Set `--srid 0` for local Cartesian coordinates typical of un-georeferenced IFC models. Use a valid EPSG code (e.g., `32633` for UTM Zone 33N) if the model has been georeferenced.

## Database Schema

The tool creates four tables with foreign key relationships:

- `ifc_site` — Site-level geometry and metadata
- `ifc_building` — Buildings linked to sites
- `ifc_storey` — Building storeys with elevation values
- `ifc_space` — Spaces linked to storeys

Each table includes `global_id` (IFC GlobalId), `name`, a 3D geometry column, and a foreign key to its parent element.

## License

MIT