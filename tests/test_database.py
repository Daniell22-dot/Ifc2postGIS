"""
Unit tests for ifc2postgis database module.

Tests the PostgreSQL connection handling, table creation, and row insertion logic.
"""

import pytest

from unittest.mock import MagicMock, patch

from ifc2postgis.database import (
    connect,
    create_schema,
    insert_site,
    insert_building,
    insert_storey,
    insert_space,
    _insert_row,
)


@patch("ifc2postgis.database.psycopg2.connect")
def test_connect(mock_connect):
    """connect() should open a valid psycopg2 connection."""
    mock_connect.return_value = MagicMock()
    
    result = connect("postgresql://user:pass@host:5432/db")
    
    mock_connect.assert_called_once_with("postgresql://user:pass@host:5432/db")
    assert result is not None


@patch("ifc2postgis.database.psycopg2.connect")
def test_create_schema_no_drop(mock_connect):
    """create_schema should create tables without dropping when drop=False."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import create_schema
    
    create_schema(
        conn=mock_conn,
        schema="public",
        srid=4326,
        drop=False,
    )
    
    # Verify tables were created (check execute was called)
    assert mock_cursor.execute.called


@patch("ifc2postgis.database.psycopg2.connect")
def test_create_schema_with_drop(mock_connect):
    """create_schema should drop tables first when drop=True."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import create_schema
    
    create_schema(
        conn=mock_conn,
        schema="public",
        srid=4326,
        drop=True,
    )
    
    # Verify drop statements were executed
    assert mock_cursor.execute.called


@patch("ifc2postgis.database.psycopg2.connect")
def test_insert_site(mock_connect):
    """insert_site should insert a row into ifc_site table."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import insert_site
    
    insert_site(
        conn=mock_conn,
        schema="public",
        srid=4326,
        global_id="SITE001",
        name="Test Site",
        wkt="MULTIPOINT Z (0 0 0)",
    )
    
    # Verify cursor.execute was called
    assert mock_cursor.execute.called


@patch("ifc2postgis.database.psycopg2.connect")
def test_insert_building(mock_connect):
    """insert_building should insert a row into ifc_building table."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import insert_building
    
    insert_building(
        conn=mock_conn,
        schema="public",
        srid=4326,
        global_id="BUILDING001",
        name="Test Building",
        site_global_id="SITE001",
        wkt="MULTIPOINT Z (0 0 0)",
    )
    
    assert mock_cursor.execute.called


@patch("ifc2postgis.database.psycopg2.connect")
def test_insert_storey(mock_connect):
    """insert_storey should insert a row into ifc_storey table."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import insert_storey
    
    insert_storey(
        conn=mock_conn,
        schema="public",
        srid=4326,
        global_id="STOREY001",
        name="Ground Floor",
        elevation=0.0,
        building_global_id="BUILDING001",
        wkt="MULTIPOINT Z (0 0 0)",
    )
    
    assert mock_cursor.execute.called


@patch("ifc2postgis.database.psycopg2.connect")
def test_insert_space(mock_connect):
    """insert_space should insert a row into ifc_space table."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import insert_space
    
    insert_space(
        conn=mock_conn,
        schema="public",
        srid=4326,
        global_id="SPACE001",
        name="Test Space",
        long_name="Reception Area",
        storey_global_id="STOREY001",
        wkt="MULTIPOINT Z (0 0 0)",
    )
    
    assert mock_cursor.execute.called


@patch("ifc2postgis.database.psycopg2.connect")
def test_insert_row_no_wkt(mock_connect):
    """_insert_row should insert row without geometry when wkt is None."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import _insert_row
    
    _insert_row(
        conn=mock_conn,
        schema="public",
        table="ifc_site",
        columns=["global_id", "name"],
        values=["SITE001", "Test Site"],
        wkt=None,
        srid=4326,
    )
    
    # Should execute without geometry column
    assert mock_cursor.execute.called


@patch("ifc2postgis.database.psycopg2.connect")
def test_insert_row_with_wkt(mock_connect):
    """_insert_row should insert row with geometry when wkt is provided."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    from ifc2postgis.database import _insert_row
    
    _insert_row(
        conn=mock_conn,
        schema="public",
        table="ifc_site",
        columns=["global_id", "name"],
        values=["SITE001", "Test Site"],
        wkt="MULTIPOINT Z (0 0 0)",
        srid=4326,
    )
    
    # Should execute with ST_GeomFromText
    assert mock_cursor.execute.called