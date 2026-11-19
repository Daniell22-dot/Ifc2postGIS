"""
Command line interface for ifc2postgis.

This module defines the Click command that the user invokes from the
shell. It validates input, reads database connection options, and
delegates the actual conversion work to the parser module.
"""

import sys

import click

from .parser import process_ifc
from .database import validate_schema, validate_srid


@click.command()
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to the input IFC file.",
)
@click.option(
    "--db-url",
    "-d",
    required=True,
    help="PostGIS connection string, for example "
    "postgresql://user:pass@host:5432/dbname.",
)
@click.option(
    "--srid",
    "-s",
    default=4326,
    type=int,
    show_default=True,
    help="Spatial Reference System Identifier for the output geometries. "
    "Use 0 for local Cartesian coordinates.",
)
@click.option(
    "--schema",
    default="public",
    show_default=True,
    help="Target database schema for the generated tables.",
)
@click.option(
    "--drop/--no-drop",
    default=False,
    show_default=True,
    help="Drop existing tables before writing new data. "
    "Defaults to False to prevent accidental data loss. "
    "Use with caution -- all existing data in the schema will be removed.",
)
def main(input, db_url, srid, schema, drop):
    """
    Convert an IFC building model into a PostGIS database.

    The converter extracts sites, buildings, storeys, and spaces from the
    input file, preserves their 3D geometry, and writes them into four
    related tables.
    """
    # Security: Validate schema and SRID before proceeding
    try:
        schema = validate_schema(schema)
        srid = validate_srid(srid)
    except ValueError as exc:
        click.echo(f"Invalid input: {exc}", err=True)
        sys.exit(1)

    click.echo("Input file: {0}".format(input))
    click.echo("Target schema: {0}".format(schema))
    click.echo("SRID: {0}".format(srid))
    click.echo("Drop existing tables: {0}".format(drop))

    try:
        if drop:
            click.echo(
                "WARNING: Dropping existing tables - all data will be lost!",
                err=True,
            )

        process_ifc(
            file_path=input,
            db_url=db_url,
            srid=srid,
            schema=schema,
            drop_tables=drop,
        )
    except Exception as exc:
        click.echo("Conversion failed: {0}".format(exc), err=True)
        sys.exit(1)

    click.echo("Conversion finished successfully.")


if __name__ == "__main__":
    main()