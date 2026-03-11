# -*- coding: utf-8 -*-
"""
Modul dlya raboty s SQL Server.
Sozdayet tablicy, zapisyvaet parametry i uslovnye oboznacheniya.
"""

import logging
import pyodbc
from typing import List, Dict

logger = logging.getLogger(__name__)

try:
    from .config import get_sql_connection_string, SQL_SERVER_CONFIG
except ImportError:
    def get_sql_connection_string():
        return (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=HOME-PC;"
            "DATABASE=GOST_Database;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=10;"
        ), "ODBC Driver 17 for SQL Server"
    SQL_SERVER_CONFIG = {'server': 'HOME-PC', 'database': 'GOST_Database'}


class GostDatabase:
    """Klass dlya raboty s bazoj dannyh GOST."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self) -> bool:
        try:
            conn_str, driver = get_sql_connection_string()
            logger.info("Connecting to SQL Server (driver: %s)...", driver)
            self.conn = pyodbc.connect(conn_str)
            self.cursor = self.conn.cursor()
            logger.info("Connected OK")
            return True
        except pyodbc.Error as e:
            logger.error("Connection error: %s", str(e))
            return False
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
            logger.info("Disconnected")
    
    def insert_designations(self, designations: List[Dict], 
                            clear_existing: bool = True) -> int:
        """
        Insert designations into ProductDesignations table.
        
        Args:
            designations: list of dicts with keys matching table columns
            clear_existing: if True, delete existing records for this GOST
        Returns:
            number of records inserted
        """
        if not self.conn:
            raise RuntimeError("No DB connection")
        
        if not designations:
            logger.warning("No designations to insert")
            return 0
        
        gost_number = designations[0].get('GOST_Number', '')
        
        # Optionally clear existing
        if clear_existing and gost_number:
            self.cursor.execute(
                "DELETE FROM ProductDesignations WHERE GOST_Number = ?",
                gost_number
            )
            deleted = self.cursor.rowcount
            logger.info("Deleted %d existing records for GOST %s", 
                       deleted, gost_number)
        
        # Insert new records
        sql = """
            INSERT INTO ProductDesignations 
            (GOST_Number, FullDesignation, ThreadSize, 
             MaterialGroup, Coating, SteelGrade,
             ThreadDiameter, ThreadPitch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        count = 0
        for d in designations:
            try:
                self.cursor.execute(sql, (
                    d.get('GOST_Number', ''),
                    d.get('FullDesignation', ''),
                    d.get('ThreadSize', ''),
                    d.get('MaterialGroup', ''),
                    d.get('Coating', ''),
                    d.get('SteelGrade', ''),
                    d.get('ThreadDiameter', 0),
                    d.get('ThreadPitch', ''),
                ))
                count += 1
            except pyodbc.Error as e:
                logger.error("Insert error: %s | Record: %s", 
                           str(e), d.get('FullDesignation', ''))
        
        self.conn.commit()
        logger.info("Inserted %d designations", count)
        return count
    
    def insert_parameters(self, params: List[Dict],
                          clear_existing: bool = True) -> int:
        """
        Insert parameters into ProductParameters table.
        """
        if not self.conn or not params:
            return 0
        
        gost_number = params[0].get('GOST_Number', '')
        
        if clear_existing and gost_number:
            self.cursor.execute(
                "DELETE FROM ProductParameters WHERE GOST_Number = ?",
                gost_number
            )
        
        sql = """
            INSERT INTO ProductParameters
            (GOST_Number, ThreadDiameter, ThreadPitch, PitchType,
             MaterialGroup, Parameter_da_min, Parameter_da_max,
             Parameter_dw_min, Parameter_e_min,
             Parameter_m_max, Parameter_m_min,
             Parameter_m_prime_min, Parameter_S_nom_max,
             Parameter_S_min, TheoreticalMass)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        count = 0
        for p in params:
            try:
                self.cursor.execute(sql, (
                    p.get('GOST_Number', ''),
                    p.get('ThreadDiameter', 0),
                    p.get('ThreadPitch', ''),
                    p.get('PitchType', ''),
                    p.get('MaterialGroup', ''),
                    p.get('Parameter_da_min', None),
                    p.get('Parameter_da_max', None),
                    p.get('Parameter_dw_min', None),
                    p.get('Parameter_e_min', None),
                    p.get('Parameter_m_max', None),
                    p.get('Parameter_m_min', None),
                    p.get('Parameter_m_prime_min', None),
                    p.get('Parameter_S_nom_max', None),
                    p.get('Parameter_S_min', None),
                    p.get('TheoreticalMass', None),
                ))
                count += 1
            except pyodbc.Error as e:
                logger.error("Insert param error: %s", str(e))
        
        self.conn.commit()
        logger.info("Inserted %d parameters", count)
        return count
    
    def get_designation_count(self, gost_number: str = "") -> int:
        """Get count of designations, optionally filtered by GOST."""
        if not self.conn:
            return 0
        if gost_number:
            self.cursor.execute(
                "SELECT COUNT(*) FROM ProductDesignations WHERE GOST_Number = ?",
                gost_number
            )
        else:
            self.cursor.execute("SELECT COUNT(*) FROM ProductDesignations")
        return self.cursor.fetchone()[0]
