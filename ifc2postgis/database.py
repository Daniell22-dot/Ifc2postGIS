"""
PostGIS connection handling and table management.

This module owns all SQL. It creates the four target tables, defines the
3D geometry columns, and provides one insert helper per table. Each
helper accepts a WKT string and lets PostGIS construct the geometry with
the correct SRID.
"""

import psycopg2
from psycopg2 import sql


def connect(db_url):
    """
    Open a connection to the target PostgreSQL database.

    The db_url is a standard libpq connection string such as
    postgresql://user:password@host:port/dbname.
    """
    return psycopg2.connect(db_url)


def create_schema(conn, schema, srid, drop):
    """
    Create the four output tables.

    If drop is True, existing tables are removed first. The schema name
    is quoted with sql.Identifier so it is safe to use in the statement.
    """
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