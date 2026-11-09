"""
Unit tests for ifc2postgis CLI module.

Tests the Click command interface and option handling.
"""

import tempfile
import os

import pytest

import click
from click.testing import CliRunner

from ifc2postgis.cli import main


def _create_temp_ifc():
    """Create a minimal temp IFC file for testing."""
    # Create a minimal IFC file using ifcopenshell
    import ifcopenshell
    model = ifcopenshell.file()
    # Just create an empty file - it will be valid enough for CLI validation
    # The CLI checks if the file exists, not its content validity
    tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
    tmp.write(b"")  # Empty file that exists
    tmp.close()
    return tmp.name


def test_cli_default_drop_false():
    """CLI should default --drop to False."""
    runner = CliRunner()
    
    # Create a temp IFC file that exists
    ifc_path = _create_temp_ifc()
    
    try:
        # Test without --drop flag
        result = runner.invoke(main, [
            "--input", ifc_path,
            "--db-url", "postgresql://user:pass@localhost:5432/bim_db",
        ])
        
        # Verify --drop default is False in the output
        assert "Drop existing tables: False" in result.output
    finally:
        os.unlink(ifc_path)


def test_cli_explicit_drop_true():
    """CLI should use --drop when explicitly specified."""
    runner = CliRunner()
    
    # Create a temp IFC file that exists
    ifc_path = _create_temp_ifc()
    
    try:
        # Test with --drop flag
        result = runner.invoke(main, [
            "--input", ifc_path,
            "--db-url", "postgresql://user:pass@localhost:5432/bim_db",
            "--drop",
        ])
        
        # Verify --drop is True
        assert "Drop existing tables: True" in result.output
    finally:
        os.unlink(ifc_path)


def test_cli_warning_on_drop(capsys):
    """CLI should show WARNING when --drop is used."""
    runner = CliRunner()
    
    # Create a temp IFC file that exists
    ifc_path = _create_temp_ifc()
    
    try:
        result = runner.invoke(main, [
            "--input", ifc_path,
            "--db-url", "postgresql://user:pass@localhost:5432/bim_db",
            "--drop",
        ])
        
        # Verify warning message is in output
        assert "WARNING: Dropping existing tables" in result.output
    finally:
        os.unlink(ifc_path)


def test_cli_help():
    """CLI should show help information."""
    runner = CliRunner()
    
    result = runner.invoke(main, ["--help"])
    
    # Verify help contains expected options
    assert "--input" in result.output
    assert "--db-url" in result.output
    assert "--srid" in result.output
    assert "--drop" in result.output or "--no-drop" in result.output


def test_cli_missing_input():
    """CLI should error when --input is missing."""
    runner = CliRunner()
    
    result = runner.invoke(main, [
        "--db-url", "postgresql://user:pass@localhost:5432/bim_db",
    ])
    
    # Should fail due to missing required --input
    assert result.exit_code != 0


def test_cli_missing_db_url():
    """CLI should error when --db-url is missing."""
    runner = CliRunner()
    
    result = runner.invoke(main, [
        "--input", "test.ifc",
    ])
    
    # Should fail due to missing required --db-url
    assert result.exit_code != 0