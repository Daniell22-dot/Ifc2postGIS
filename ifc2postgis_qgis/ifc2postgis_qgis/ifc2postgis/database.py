"""
PostGIS connection handling and table management.

This module owns all SQL. It creates the four target tables, defines the
3D geometry columns, and provides one insert helper per table. Each
helper accepts a WKT string and lets PostGIS construct the geometry with
the correct SRID.

Security:
- All SQL uses psycopg2.sql for safe composition (sql.Identifier, sql.Placeholder, sql.Literal)
- SRID is validated to be a positive integer (valid EPSG code)
- Schema name is validated against a whitelist of allowed characters
- Parameterized queries for geometry insertion (ST_GeomFromText %s %s)
- ON CONFLICT DO NOTHING prevents duplicate key issues
"""

import re

import psycopg2
from psycopg2 import sql


def validate_srid(srid):
    """
    Validate that SRID is a positive integer representing a valid EPSG code.

    Parameters:
        srid: integer SRID value to validate

    Returns:
        validated srid integer

    Raises:
        ValueError: if srid is not a positive integer
    """
    if not isinstance(srid, int):
        raise ValueError(f"SRID must be an integer, got {type(srid).__name__}")
    if srid < 0:
        raise ValueError(f"SRID must be a non-negative integer, got {srid}")
    # 0 is allowed for local Cartesian coordinates
    # Valid EPSG codes are 1-999999 approximately
    if srid > 0 and srid > 999999:
        raise ValueError(
            f"SRID {srid} appears unusually large. "
            "Valid EPSG codes typically range from 1-999999. "
            "Use 0 for local Cartesian coordinates."
        )
    return srid


def validate_schema(schema):
    """
    Validate schema name contains only safe characters.

    Only alphanumeric characters and underscores are allowed,
    preventing SQL injection through schema names.

    Parameters:
        schema: schema name string to validate

    Returns:
        validated schema name

    Raises:
        ValueError: if schema contains unsafe characters
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema):
        raise ValueError(
            f"Invalid schema name: '{schema}'. "
            "Schema names must start with a letter or underscore "
            "and contain only alphanumeric characters and underscores."
        )
    return schema


def connect(db_url):
    """
    Open a connection to the target PostgreSQL database.

    The db_url is a standard libpq connection string such as
    postgresql://user:password@host:port/dbname.

    Raises:
        psycopg2.OperationalError: if connection fails
    """
    return psycopg2.connect(db_url)


def create_schema(conn, schema, srid, drop):
    """
    Create the four output tables.

    Security:
    - Schema name is validated before use
    - SRID is validated before use
    - sql.Identifier() is used for safe identifier quoting
    - sql.Literal() is used for safe SRID literal insertion

    If drop is True, existing tables are removed first.
    """
    # Validate inputs security-first
    schema = validate_schema(schema)
    srid = validate_srid(srid)

    cursor = conn.cursor()
    try:
        if drop:
            for table in ("ifc_space", "ifc_storey", "ifc_building", "ifc_site"):
                cursor.execute(
                    sql.SQL("DROP TABLE IF EXISTS {0}.{1} CASCADE").format(
                        sql.Identifier(schema), sql.Identifier(table)
                    )
                )

        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {schema}.ifc_site (
                    id SERIAL PRIMARY KEY,
                    global_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    geom geometry(GeometryZ, {srid})
                )
                """
            ).format(schema=sql.Identifier(schema), srid=sql.Literal(srid))
        )

        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {schema}.ifc_building (
                    id SERIAL PRIMARY KEY,
                    global_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    site_global_id TEXT,
                    geom geometry(GeometryZ, {srid})
                )
                """
            ).format(schema=sql.Identifier(schema), srid=sql.Literal(srid))
        )

        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {schema}.ifc_storey (
                    id SERIAL PRIMARY KEY,
                    global_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    elevation DOUBLE PRECISION,
                    building_global_id TEXT,
                    geom geometry(GeometryZ, {srid})
                )
                """
            ).format(schema=sql.Identifier(schema), srid=sql.Literal(srid))
        )

        cursor.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {schema}.ifc_space (
                    id SERIAL PRIMARY KEY,
                    global_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    long_name TEXT,
                    storey_global_id TEXT,
                    geom geometry(GeometryZ, {srid})
                )
                """
            ).format(schema=sql.Identifier(schema), srid=sql.Literal(srid))
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def _insert_row(conn, schema, table, columns, values, wkt, srid):
    """
    Insert a single row. If wkt is None, the geom column is left NULL.
    """
    cursor = conn.cursor()
    try:
        if wkt is None:
            statement = sql.SQL(
                "INSERT INTO {0}.{1} ({2}) VALUES ({3}) ON CONFLICT (global_id) DO NOTHING"
            ).format(
                sql.Identifier(schema),
                sql.Identifier(table),
                sql.SQL(", ").join(sql.Identifier(c) for c in columns),
                sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            )
            cursor.execute(statement, values)
        else:
            statement = sql.SQL(
                "INSERT INTO {0}.{1} ({2}, geom) VALUES ({3}, ST_GeomFromText(%s, %s)) "
                "ON CONFLICT (global_id) DO NOTHING"
            ).format(
                sql.Identifier(schema),
                sql.Identifier(table),
                sql.SQL(", ").join(sql.Identifier(c) for c in columns),
                sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            )
            cursor.execute(statement, list(values) + [wkt, srid])
    finally:
        cursor.close()


def insert_site(conn, schema, srid, global_id, name, wkt):
    _insert_row(
        conn,
        schema=schema,
        table="ifc_site",
        columns=["global_id", "name"],
        values=[global_id, name],
        wkt=wkt,
        srid=srid,
    )


def insert_building(conn, schema, srid, global_id, name, site_global_id, wkt):
    _insert_row(
        conn,
        schema=schema,
        table="ifc_building",
        columns=["global_id", "name", "site_global_id"],
        values=[global_id, name, site_global_id],
        wkt=wkt,
        srid=srid,
    )


def insert_storey(conn, schema, srid, global_id, name, elevation, building_global_id, wkt):
    _insert_row(
        conn,
        schema=schema,
        table="ifc_storey",
        columns=["global_id", "name", "elevation", "building_global_id"],
        values=[global_id, name, elevation, building_global_id],
        wkt=wkt,
        srid=srid,
    )


def insert_space(conn, schema, srid, global_id, name, long_name, storey_global_id, wkt):
    _insert_row(
        conn,
        schema=schema,
        table="ifc_space",
        columns=["global_id", "name", "long_name", "storey_global_id"],
        values=[global_id, name, long_name, storey_global_id],
        wkt=wkt,
        srid=srid,
    )