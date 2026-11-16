# -*- coding: utf-8 -*-
"""Dialog for ifc2postgis-QGIS plugin."""

import sys
import os

# Add the parent project directory to path so we can import ifc2postgis
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                  QLineEdit, QPushButton, QComboBox, QgsCoordinateReferenceSystem,
                                  QgsProject, QgsMessageBox, QgsWkbTypes)

from ifc2postgis import process_ifc
from .zoning import analyze_spaces


class Ifc2postgisDialog(QDialog):
    """Dialog for configuring and running IFC to PostGIS conversion."""

    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.setWindowTitle(u"IFC to PostGIS Conversion")
        self.resize(500, 500)
        self.setupUi()
        
    def setupUi(self):
        layout = QVBoxLayout(self)
        
        # IFC File selection
        self.ifc_file_label = QLabel(u"IFC File:")
        self.ifc_file_input = QLineEdit()
        self.ifc_file_button = QPushButton(u"Browse...")
        self.ifc_file_button.clicked.connect(self.select_ifc_file)
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.ifc_file_label)
        file_layout.addWidget(self.ifc_file_input)
        file_layout.addWidget(self.ifc_file_button)
        layout.addLayout(file_layout)
        
        # Database URL
        self.db_url_label = QLabel(u"PostgreSQL Connection URL:")
        self.db_url_input = QLineEdit()
        self.db_url_input.setPlaceholderText(u"postgresql://user:pass@host:5432/dbname")
        
        layout.addWidget(self.db_url_label)
        layout.addWidget(self.db_url_input)
        
        # Schema
        self.schema_label = QLabel(u"Schema:")
        self.schema_input = QLineEdit(u"public")
        
        schema_layout = QHBoxLayout()
        schema_layout.addWidget(self.schema_label)
        schema_layout.addWidget(self.schema_input)
        layout.addLayout(schema_layout)
        
        # SRID
        self.srid_label = QLabel(u"SRID:")
        self.srid_input = QLineEdit(u"4326")
        self.srid_input.setPlaceholderText(u"e.g., 4326 or 0")
        
        srid_layout = QHBoxLayout()
        srid_layout.addWidget(self.srid_label)
        srid_layout.addWidget(self.srid_input)
        layout.addLayout(srid_layout)
        
        # Drop existing tables
        self.drop_checkbox = QCheckBox(u"Drop existing tables")
        self.drop_checkbox.setChecked(False)
        
        layout.addWidget(self.drop_checkbox)
        
        # Zoning analysis checkbox
        self.zoning_checkbox = QCheckBox(u"Run zoning analysis on spaces")
        self.zoning_checkbox.setChecked(True)
        layout.addWidget(self.zoning_checkbox)
        
        # Run button
        self.run_button = QPushButton(u"Convert IFC")
        self.run_button.clicked.connect(self.run_conversion)
        self.run_button.setDefault(True)
        
        layout.addWidget(self.run_button)
        
        # Status/output area
        self.status_label = QLabel(u"")
        self.status_label.setAlignment(Qt.AlignTop)
        layout.addWidget(self.status_label)
        
        # Zoning results area (initially hidden)
        self.zoning_label = QLabel(u"Zoning Analysis:")
        self.zoning_text = QLabel(u"")
        self.zoning_text.setAlignment(Qt.AlignTop)
        self.zoning_text.setVisible(False)
        layout.addWidget(self.zoning_label)
        layout.addWidget(self.zoning_text)
        
        self.setLayout(layout)
        
    def select_ifc_file(self):
        """Open file dialog to select IFC file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, u"Select IFC File", u"", u"IFC Files (*.ifc *.ifc.zip)")
        if file_path:
            self.ifc_file_input.setText(file_path)
            
    def run_conversion(self):
        """Run the IFC to PostGIS conversion."""
        ifc_file = self.ifc_file_input.text().strip()
        db_url = self.db_url_input.text().strip()
        schema = self.schema_input.text().strip() or u"public"
        srid_text = self.srid_input.text().strip()
        
        if not ifc_file:
            QgsMessageBox.critical(self, u"Error", u"Please select an IFC file.")
            return
            
        if not db_url:
            QgsMessageBox.critical(self, u"Error", u"Please enter a PostgreSQL connection URL.")
            return
            
        try:
            srid = int(srid_text)
        except ValueError:
            QgsMessageBox.critical(self, u"Error", u"SRID must be a valid integer.")
            return
            
        self.status_label.setText(u"Converting IFC model...")
        QgsApplication.processEvents()
        
        try:
            process_ifc(
                file_path=ifc_file,
                db_url=db_url,
                srid=srid,
                schema=schema,
                drop_tables=self.drop_checkbox.isChecked()
            )
            self.status_label.setText(u"Conversion completed successfully!")
            QgsMessageBox.information(self, u"Success", u"IFC model converted to PostGIS successfully.")
            
            # Load layers into QGIS
            self.load_into_qgis()
            
            # Run zoning analysis if checked
            if self.zoning_checkbox.isChecked():
                self.run_zoning_analysis(ifc_file, db_url, schema, srid)
                
        except Exception as e:
            self.status_label.setText(u"Conversion failed: {0}".format(str(e)))
            QgsMessageBox.critical(self, u"Error", u"Conversion failed: {0}".format(str(e)))
            
    def run_zoning_analysis(self, ifc_file, db_url, schema, srid):
        """Run zoning analysis on spaces."""
        self.status_label.setText(u"Running zoning analysis...")
        QgsApplication.processEvents()
        
        try:
            results = analyze_spaces(ifc_file, db_url, schema, srid)
            if results:
                stats = results["zoning_stats"]
                total = stats["total_spaces"]
                lines = [
                    u"Zoning Analysis Results:",
                    u"---------------------",
                    u"Total spaces analyzed: {0}".format(total),
                    u"",
                    u"By usage type:",
                    u"  Residential: {0}".format(stats["by_usage"]["residential"]),
                    u"  Commercial: {0}".format(stats["by_usage"]["commercial"]),
                    u"  Industrial: {0}".format(stats["by_usage"]["industrial"]),
                    u"  Other: {0}".format(stats["by_usage"]["other"]),
                    u"",
                    u"Total spaces: {0}".format(total),
                ]
                self.zoning_text.setText("\n".join(lines))
                self.zoning_text.setVisible(True)
        except Exception as e:
            self.iface.messageBar().pushWarning(u"Zoning Analysis", u"Analysis completed with warnings: {0}".format(str(e)))
            self.zoning_text.setVisible(True)
            self.zoning_text.setText(u"Zoning analysis completed with warnings.")
            
    def load_into_qgis(self):
        """Load the converted tables into QGIS map canvas."""
        try:
            schema = self.schema_input.text().strip() or u"public"
            # Add the space, storey, building, and site tables as layers
            tables = [u"ifc_site", u"ifc_building", u"ifc_storey", u"ifc_space"]
            
            for table in tables:
                layer = self.iface.addVectorLayer(
                    u"postgresql://{}.{}".format(schema, table),
                    u"{}_{}".format(schema, table),
                    u"postgres"
                )
                if layer:
                    QgsProject.instance().addMapLayer(layer)
        except Exception as e:
            self.iface.messageBar().pushWarning(u"Warning", u"Could not load all layers: {0}".format(str(e)))