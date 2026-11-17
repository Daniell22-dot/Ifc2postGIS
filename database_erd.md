# Database ER Diagram: ifc2postGIS PostgreSQL Schema

## Overview
Database for ifc2postgis CLI tool converting IFC building models to PostGIS.
Database: `ifc` on PostgreSQL port `5433`
ERD reflects topological hierarchy: Site → Building → Storey → Space

---

## Entity-Relationship Diagram (Text Format)

```
+------------------+     1:m     +------------------+     1:m     +------------------+     1:m     +------------------+
|     ifc_site     |-------------|    ifc_building  |-------------|   ifc_storey   |-------------|    ifc_space   |
+------------------+             +------------------+             +------------------+             +------------------+
| id SERIAL PK     |             | id SERIAL PK     |             | id SERIAL PK     |             | id SERIAL PK   |
| global_id TEXT   |             | global_id TEXT   |             | global_id TEXT   |             | global_id TEXT |
| UNIQUE NOT NULL  |             | UNIQUE NOT NULL  |             | UNIQUE NOT NULL  |             | UNIQUE NOT NULL|
| name TEXT        |             | name TEXT        |             | name TEXT        |             | name TEXT      |
| geom geometry(Z) |             | geom geometry(Z) |             | elevation DOUBLE |             | long_name TEXT |
| (srid from env)  |             | site_global_id   |             | building_global_id|             | storey_global_id|
+------------------+             | TEXT FK→ifc_site |             | TEXT FK→ifc_building|           | geom geometry(Z)|
                                    +------------------+             +------------------+
                                    | site_global_id   |                                  ^
                                    | FK→ifc_site.id   |                                  |
+------------------+                     | (references ifc_building.global_id)                           |
|     ifc_site     |     1:m      +--------------------------------------------------------------+
+------------------+

Key:
- PK = Primary Key
- FK = Foreign Key
- 1:m = One-to-Many relationship
- geometry(Z) = 3D geometry with Z coordinates
- SRID from .env: localhost:5433, database 'ifc'
```

---

## SQL Schema: CREATE TABLE Statements

Run these in your PostgreSQL port 5433, database `ifc`:

```sql
-- 1. ifc_site table (top level)
CREATE TABLE IF NOT EXISTS ifc_site (
    id SERIAL PRIMARY KEY,
    global_id TEXT UNIQUE NOT NULL,
    name TEXT,
    geom geometry(GeometryZ, 4326)  -- SRID from .env or 0 for local coords
);

-- 2. ifc_building table (linked to site)
CREATE TABLE IF NOT EXISTS ifc_building (
    id SERIAL PRIMARY KEY,
    global_id TEXT UNIQUE NOT NULL,
    name TEXT,
    site_global_id TEXT REFERENCES ifc_site(global_id),
    geom geometry(GeometryZ, 4326)
);

-- 3. ifc_storey table (linked to building)
CREATE TABLE IF NOT EXISTS ifc_storey (
    id SERIAL PRIMARY KEY,
    global_id TEXT UNIQUE NOT NULL,
    name TEXT,
    elevation DOUBLE PRECISION,      -- floor height relative to origin
    building_global_id TEXT REFERENCES ifc_building(global_id),
    geom geometry(GeometryZ, 4326)
);

-- 4. ifc_space table (linked to storey - the rooms)
CREATE TABLE IF NOT EXISTS ifc_space (
    id SERIAL PRIMARY KEY,
    global_id TEXT UNIQUE NOT NULL,
    name TEXT,
    long_name TEXT,                  -- optional additional name
    storey_global_id TEXT REFERENCES ifc_storey(global_id),
    geom geometry(GeometryZ, 4326)
);
```

---

## Relationship Logic (CLI Tool Flow)

```
IFC File
  │
  ├── IfcSite  ──────► stored in ifc_site (1 row)
  │
  ├── IfcBuilding ────► stored in ifc_building (1 row)
  │   └── FK: site_global_id → ifc_site.global_id
  │
  ├── IfcBuildingStorey  ─► stored in ifc_storey (3 rows for SOE.ifc)
  │   └── FK: building_global_id → ifc_building.global_id
  │   └── FK: elevation (e.g., 0.0, 3.5, 7.0)
  │
  └── IfcSpace  ────────► stored in ifc_space (105 rows for SOE.ifc)
      └── FK: storey_global_id → ifc_storey.global_id
      └── Geometry: MULTIPOINT Z WKT in world coordinates
```

---

## Connection String (.env) Format

```
# From .env file
postgresql://postgres:postres@localhost:5433/ifc
```

Breakdown:
- **Driver**: `postgresql://`
- **User**: `postgres`
- **Password**: `postres`
- **Host**: `localhost`
- **Port**: `5433` (custom, default PostGIS is 5432)
- **Database**: `ifc`

---

## Topological Integrity Constraints

The CLI tool (`process_ifc` in `parser.py`) enforces:

1. **Hierarchy enforcement**: Spaces → Storeys → Buildings → Sites
   - Each space must have a valid `storey_global_id` referencing `ifc_storey`
   - Each storey must have a valid `building_global_id` referencing `ifc_building`
   - Each building must have a valid `site_global_id` referencing `ifc_site`

2. **ON CONFLICT DO NOTHING**:
   - All 4 `insert_*` functions use: `ON CONFLICT (global_id) DO NOTHING`
   - Prevents duplicate key errors on re-runs

3. **Geometry preservation**:
   - 3D geometries stored as `geometry(GeometryZ, srid)`
   - World coordinates from IfcOpenShell (no additional transformation)
   - Z-values preserved from original IFC model

4. **Foreign key integrity**:
   - Foreign keys reference the parent table's `global_id` (not auto-generated PK)
   - Matches IFC's natural identifier pattern

---

## Example Data Flow (SOE.ifc → PostgreSQL)

```
Step 1: ifc2postgis CLI runs
  input: SOE.ifc
  db_url: postgresql://postgres:postres@localhost:5433/ifc
  srid: 4326 (or 0 from .env)

Step 2: Creates 4 tables if not exist
  → ifc_site (1 row)
  → ifc_building (1 row)
  → ifc_storey (3 rows: Ground, 1st, 2nd floor)
  → ifc_space (105 rows: labs, offices, corridors, etc.)

Step 3: Topological links established
  ifc_building.site_global_id = ifc_site.global_id
  ifc_storey.building_global_id = ifc_building.global_id
  ifc_space.storey_global_id = ifc_storey.global_id

Step 4: Query example (rooms on 2nd floor)
  SELECT s.name, sp.name, st.elevation
  FROM ifc_space sp
  JOIN ifc_storey st ON sp.storey_global_id = st.global_id
  JOIN ifc_building b ON st.building_global_id = b.global_id
  JOIN ifc_site s ON b.site_global_id = s.global_id
  WHERE st.elevation = 7.0;  -- 2nd floor
```

---

## Index Recommendations for Performance

```sql
-- Primary foreign key indexes (auto-created via REFERENCES)
CREATE INDEX IFK_ifc_building_site ON ifc_building(site_global_id);
CREATE INDEX IFK_ifc_storey_building ON ifc_storey(building_global_id);
CREATE INDEX IFK_ifc_space_storey ON ifc_space(storey_global_id);

-- Geometry indexes for spatial queries
CREATE INDEX IFK_ifc_site_geom ON ifc_site USING GIST(geom);
CREATE INDEX IFK_ifc_building_geom ON ifc_building USING GIST(geom);
CREATE INDEX IFK_ifc_storey_geom ON ifc_storey USING GIST(geom);
CREATE INDEX IFK_ifc_space_geom ON ifc_space USING GIST(geom);

-- GlobalId lookups (frequent in CLI operations)
CREATE INDEX IFK_ifc_site_global ON ifc_site(global_id);
CREATE INDEX IFK_ifc_building_global ON ifc_building(global_id);
CREATE INDEX IFK_ifc_storey_global ON ifc_storey(global_id);
CREATE INDEX IFK_ifc_space_global ON ifc_space(global_id);
```

---
*Diagram and schema generated for SOE DEKUT School of Engineering IFC-to-PostGIS pipeline*
*Database port: 5433 (per .env configuration)*
*SRID: 4326 (WGS84) or 0 (local Cartesian, per CLI --srid flag)*