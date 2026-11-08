# Database schema

The converter creates four tables in the target schema. All geometry
columns use the type geometry(GeometryZ, SRID) so they can hold
three-dimensional coordinates. The default SRID is 4326. Pass 0 on the
command line to store unprojected local coordinates.

## Tables

### ifc_site

Stores top level sites.

| Column    | Type                      | Notes                          |
|-----------|---------------------------|--------------------------------|
| id        | SERIAL PRIMARY KEY        | Surrogate key                  |
| global_id | TEXT UNIQUE NOT NULL      | IFC GlobalId                   |
| name      | TEXT                      | Site name                      |
| geom      | geometry(GeometryZ, SRID) | 3D geometry, may be null       |

### ifc_building

Stores buildings and links them to their parent site.

| Column         | Type                      | Notes                          |
|----------------|---------------------------|--------------------------------|
| id             | SERIAL PRIMARY KEY        | Surrogate key                  |
| global_id      | TEXT UNIQUE NOT NULL      | IFC GlobalId                   |
| name           | TEXT                      | Building name                  |
| site_global_id | TEXT                      | GlobalId of parent site        |
| geom           | geometry(GeometryZ, SRID) | 3D geometry, may be null       |

### ifc_storey

Stores building storeys and links them to their parent building.

| Column             | Type                      | Notes                          |
|--------------------|---------------------------|--------------------------------|
| id                 | SERIAL PRIMARY KEY        | Surrogate key                  |
| global_id          | TEXT UNIQUE NOT NULL      | IFC GlobalId                   |
| name               | TEXT                      | Storey name                    |
| elevation          | DOUBLE PRECISION          | Storey elevation in metres     |
| building_global_id | TEXT                      | GlobalId of parent building    |
| geom               | geometry(GeometryZ, SRID) | 3D geometry, may be null       |

### ifc_space

Stores spaces and links them to their parent storey.

| Column           | Type                      | Notes                          |
|------------------|---------------------------|--------------------------------|
| id               | SERIAL PRIMARY KEY        | Surrogate key                  |
| global_id        | TEXT UNIQUE NOT NULL      | IFC GlobalId                   |
| name             | TEXT                      | Space name                     |
| long_name        | TEXT                      | Space long name                |
| storey_global_id | TEXT                      | GlobalId of parent storey      |
| geom             | geometry(GeometryZ, SRID) | 3D geometry, may be null       |

## Relationships

The parent links are stored as text columns that reference the
global_id of the parent table. They are not enforced with FOREIGN KEY
constraints in the current schema, so rows can be inserted in any
order. If referential integrity is required, add the constraints after
loading:

    ALTER TABLE ifc_building
        ADD CONSTRAINT fk_building_site
        FOREIGN KEY (site_global_id)
        REFERENCES ifc_site(global_id)
        ON DELETE SET NULL;

    ALTER TABLE ifc_storey
        ADD CONSTRAINT fk_storey_building
        FOREIGN KEY (building_global_id)
        REFERENCES ifc_building(global_id)
        ON DELETE SET NULL;

    ALTER TABLE ifc_space
        ADD CONSTRAINT fk_space_storey
        FOREIGN KEY (storey_global_id)
        REFERENCES ifc_storey(global_id)
        ON DELETE SET NULL;

## Example queries

Count spaces per storey:

    SELECT s.name, COUNT(sp.id)
    FROM ifc_storey s
    LEFT JOIN ifc_space sp ON sp.storey_global_id = s.global_id
    GROUP BY s.name
    ORDER BY s.name;

List all buildings on a site:

    SELECT b.name
    FROM ifc_building b
    JOIN ifc_site s ON b.site_global_id = s.global_id
    WHERE s.name = 'Main Site';

Compute the bounding box of all space geometry:

    SELECT ST_Extent(geom)
    FROM ifc_space
    WHERE geom IS NOT NULL;