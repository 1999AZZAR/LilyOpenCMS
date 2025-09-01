#!/usr/bin/env python3
"""
Database Health Checker for LilyOpenCMS

This module provides comprehensive database health checking capabilities to ensure
the database structure matches the models.py definitions and maintains data integrity.

Features:
- Database connectivity verification
- Table existence and structure validation
- Foreign key relationship checks
- Index verification
- Data integrity checks
- Performance monitoring
- Detailed reporting with recommendations
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

# Add the parent directory to the path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy.schema import Table
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Numeric, Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import models
from models import db, User, News, Image, Category, YouTubeVideo, ShareLog, SocialMedia
from models import ContactDetail, TeamMember, BrandIdentity, UserSubscription
from models import Comment, Rating, CommentLike, CommentReport
from models import NavigationLink, RootSEO, AdCampaign, Ad, AdPlacement, AdStats
from models import PrivacyPolicy, MediaGuideline, VisiMisi, Penyangkalan, PedomanHak
from models import Album, AlbumChapter, Permission, CustomRole, UserActivity, UserRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CheckSeverity(Enum):
    """Severity levels for database health checks."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    """Result of a database health check."""
    name: str
    severity: CheckSeverity
    status: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


class DatabaseHealthChecker:
    """Comprehensive database health checker for LilyOpenCMS."""
    
    def __init__(self, database_url: str = None):
        """Initialize the database health checker.
        
        Args:
            database_url: Database URL. If None, uses the default from the app.
        """
        self.database_url = database_url or "sqlite:///instance/LilyOpenCms.db"
        self.engine: Optional[Engine] = None
        self.inspector: Optional[Any] = None
        self.metadata: Optional[MetaData] = None
        self.results: List[CheckResult] = []
        
        # Expected tables from models.py
        self.expected_tables = {
            'user', 'permission', 'custom_role', 'role_permission', 'user_activity',
            'privacy_policy', 'media_guideline', 'visi_misi', 'penyangkalan', 'pedoman_hak',
            'image', 'category', 'news', 'album', 'album_chapter', 'youtube_video',
            'share_log', 'social_media', 'contact_detail', 'team_member', 'brand_identity',
            'user_subscriptions', 'comment', 'rating', 'comment_like', 'comment_report',
            'navigation_link', 'root_seo', 'ad_campaign', 'ad', 'ad_placement', 'ad_stats'
        }
        
        # Critical tables that must exist
        self.critical_tables = {'user', 'news', 'category', 'image'}
        
        # Expected foreign key relationships
        self.expected_foreign_keys = {
            'news': ['user_id', 'category_id', 'image_id'],
            'album': ['user_id', 'category_id', 'cover_image_id'],
            'album_chapter': ['album_id', 'news_id'],
            'comment': ['user_id', 'parent_id'],
            'rating': ['user_id'],
            'comment_like': ['user_id', 'comment_id'],
            'comment_report': ['user_id', 'comment_id'],
            'image': ['user_id'],
            'youtube_video': ['user_id'],
            'share_log': ['news_id'],
            'social_media': ['created_by', 'updated_by'],
            'navigation_link': ['user_id'],
            'root_seo': ['created_by', 'updated_by'],
            'ad_campaign': ['created_by', 'updated_by'],
            'ad': ['campaign_id', 'created_by', 'updated_by'],
            'ad_placement': ['ad_id', 'created_by', 'updated_by'],
            'ad_stats': ['ad_id'],
            'user_subscriptions': ['user_id'],
            'user_activity': ['user_id'],
            'user': ['custom_role_id']
        }
    
    def connect(self) -> bool:
        """Establish database connection and verify connectivity.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.engine = create_engine(self.database_url, echo=False)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.inspector = inspect(self.engine)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            
            result = CheckResult(
                name="Database Connection",
                severity=CheckSeverity.INFO,
                status=True,
                message="Database connection established successfully",
                details={"database_url": self.database_url}
            )
            self.results.append(result)
            return True
            
        except Exception as e:
            result = CheckResult(
                name="Database Connection",
                severity=CheckSeverity.CRITICAL,
                status=False,
                message=f"Failed to connect to database: {str(e)}",
                details={"database_url": self.database_url, "error": str(e)},
                recommendations=[
                    "Verify database URL is correct",
                    "Check if database file exists (for SQLite)",
                    "Verify database server is running (for PostgreSQL/MySQL)",
                    "Check database credentials and permissions"
                ]
            )
            self.results.append(result)
            return False
    
    def check_table_existence(self) -> None:
        """Check if all expected tables exist in the database."""
        if not self.inspector:
            return
        
        existing_tables = set(self.inspector.get_table_names())
        missing_tables = self.expected_tables - existing_tables
        critical_missing = missing_tables & self.critical_tables
        
        if critical_missing:
            result = CheckResult(
                name="Critical Tables Missing",
                severity=CheckSeverity.CRITICAL,
                status=False,
                message=f"Critical tables missing: {', '.join(critical_missing)}",
                details={"missing_tables": list(critical_missing)},
                recommendations=[
                    "Run database migrations: flask db upgrade",
                    "Check if migrations are up to date",
                    "Verify models.py is properly imported"
                ]
            )
            self.results.append(result)
        
        if missing_tables - critical_missing:
            result = CheckResult(
                name="Non-Critical Tables Missing",
                severity=CheckSeverity.WARNING,
                status=False,
                message=f"Some tables missing: {', '.join(missing_tables - critical_missing)}",
                details={"missing_tables": list(missing_tables - critical_missing)},
                recommendations=[
                    "Run database migrations: flask db upgrade",
                    "Check if new models need to be migrated"
                ]
            )
            self.results.append(result)
        
        if not missing_tables:
            result = CheckResult(
                name="Table Existence",
                severity=CheckSeverity.INFO,
                status=True,
                message="All expected tables exist",
                details={"total_tables": len(existing_tables)}
            )
            self.results.append(result)
    
    def check_table_structure(self) -> None:
        """Check if table structures match the expected schema."""
        if not self.inspector:
            return
        
        for table_name in self.expected_tables:
            if not self.inspector.has_table(table_name):
                continue
            
            # Get actual columns
            actual_columns = {col['name']: col for col in self.inspector.get_columns(table_name)}
            
            # Get expected columns from model
            expected_columns = self._get_expected_columns(table_name)
            
            if expected_columns:
                missing_columns = set(expected_columns.keys()) - set(actual_columns.keys())
                extra_columns = set(actual_columns.keys()) - set(expected_columns.keys())
                
                if missing_columns:
                    result = CheckResult(
                        name=f"Table Structure - {table_name}",
                        severity=CheckSeverity.ERROR,
                        status=False,
                        message=f"Missing columns in {table_name}: {', '.join(missing_columns)}",
                        details={
                            "table": table_name,
                            "missing_columns": list(missing_columns),
                            "expected_columns": list(expected_columns.keys())
                        },
                        recommendations=[
                            "Run database migrations: flask db upgrade",
                            "Check if model definition matches database schema"
                        ]
                    )
                    self.results.append(result)
                
                if extra_columns:
                    result = CheckResult(
                        name=f"Table Structure - {table_name}",
                        severity=CheckSeverity.WARNING,
                        status=True,
                        message=f"Extra columns in {table_name}: {', '.join(extra_columns)}",
                        details={
                            "table": table_name,
                            "extra_columns": list(extra_columns)
                        }
                    )
                    self.results.append(result)
    
    def check_foreign_keys(self) -> None:
        """Check foreign key relationships."""
        if not self.inspector:
            return
        
        for table_name, expected_fks in self.expected_foreign_keys.items():
            if not self.inspector.has_table(table_name):
                continue
            
            actual_fks = self.inspector.get_foreign_keys(table_name)
            actual_fk_columns = {fk['constrained_columns'][0] for fk in actual_fks}
            missing_fks = set(expected_fks) - actual_fk_columns
            
            if missing_fks:
                result = CheckResult(
                    name=f"Foreign Keys - {table_name}",
                    severity=CheckSeverity.ERROR,
                    status=False,
                    message=f"Missing foreign keys in {table_name}: {', '.join(missing_fks)}",
                    details={
                        "table": table_name,
                        "missing_foreign_keys": list(missing_fks),
                        "expected_foreign_keys": expected_fks
                    },
                    recommendations=[
                        "Run database migrations: flask db upgrade",
                        "Check model relationships in models.py"
                    ]
                )
                self.results.append(result)
    
    def check_indexes(self) -> None:
        """Check if important indexes exist."""
        if not self.inspector:
            return
        
        # Check for indexes on commonly queried columns
        important_indexes = {
            'user': ['username', 'email'],
            'news': ['date', 'is_visible', 'is_main_news', 'is_premium'],
            'album': ['is_visible', 'is_premium', 'created_at'],
            'comment': ['content_type', 'content_id', 'is_approved'],
            'rating': ['content_type', 'content_id'],
            'image': ['is_visible'],
            'ad': ['is_active', 'ad_type']
        }
        
        for table_name, expected_index_columns in important_indexes.items():
            if not self.inspector.has_table(table_name):
                continue
            
            table_indexes = self.inspector.get_indexes(table_name)
            existing_index_columns = set()
            
            for index in table_indexes:
                existing_index_columns.update(index['column_names'])
            
            missing_indexes = set(expected_index_columns) - existing_index_columns
            
            if missing_indexes:
                result = CheckResult(
                    name=f"Indexes - {table_name}",
                    severity=CheckSeverity.WARNING,
                    status=False,
                    message=f"Missing indexes in {table_name}: {', '.join(missing_indexes)}",
                    details={
                        "table": table_name,
                        "missing_indexes": list(missing_indexes)
                    },
                    recommendations=[
                        "Consider adding indexes for better performance",
                        "Check if indexes are defined in models.py"
                    ]
                )
                self.results.append(result)
    
    def check_data_integrity(self) -> None:
        """Check for data integrity issues."""
        if not self.engine:
            return
        
        try:
            with self.engine.connect() as conn:
                # Check for orphaned records
                orphaned_checks = [
                    ("news", "user", "user_id"),
                    ("news", "category", "category_id"),
                    ("album", "user", "user_id"),
                    ("album", "category", "category_id"),
                    ("comment", "user", "user_id"),
                    ("rating", "user", "user_id"),
                    ("image", "user", "user_id")
                ]
                
                for child_table, parent_table, fk_column in orphaned_checks:
                    if not (self.inspector.has_table(child_table) and self.inspector.has_table(parent_table)):
                        continue
                    
                    query = text(f"""
                        SELECT COUNT(*) as count 
                        FROM {child_table} c 
                        LEFT JOIN {parent_table} p ON c.{fk_column} = p.id 
                        WHERE p.id IS NULL AND c.{fk_column} IS NOT NULL
                    """)
                    
                    result = conn.execute(query).fetchone()
                    orphaned_count = result[0] if result else 0
                    
                    if orphaned_count > 0:
                        check_result = CheckResult(
                            name=f"Data Integrity - {child_table}",
                            severity=CheckSeverity.ERROR,
                            status=False,
                            message=f"Found {orphaned_count} orphaned records in {child_table}",
                            details={
                                "table": child_table,
                                "orphaned_count": orphaned_count,
                                "foreign_key": fk_column
                            },
                            recommendations=[
                                f"Clean up orphaned records in {child_table}",
                                "Check foreign key constraints"
                            ]
                        )
                        self.results.append(check_result)
        
        except Exception as e:
            result = CheckResult(
                name="Data Integrity Check",
                severity=CheckSeverity.WARNING,
                status=False,
                message=f"Could not perform data integrity checks: {str(e)}",
                details={"error": str(e)}
            )
            self.results.append(result)
    
    def check_performance(self) -> None:
        """Check database performance metrics."""
        if not self.engine:
            return
        
        try:
            with self.engine.connect() as conn:
                # Get table sizes
                if self.database_url.startswith('sqlite'):
                    # For SQLite, get row counts for each table
                    performance_data = {}
                    tables = ['user', 'news', 'album', 'comment', 'rating', 'image']
                    
                    for table in tables:
                        try:
                            count_query = text(f"SELECT COUNT(*) FROM {table}")
                            count_result = conn.execute(count_query).scalar()
                            performance_data[table] = count_result
                        except Exception as e:
                            performance_data[table] = f"Error: {str(e)}"
                else:
                    # For PostgreSQL/MySQL, get actual row counts
                    query = text("""
                        SELECT 'user' as table_name, COUNT(*) as count FROM user
                        UNION ALL
                        SELECT 'news', COUNT(*) FROM news
                        UNION ALL
                        SELECT 'album', COUNT(*) FROM album
                        UNION ALL
                        SELECT 'comment', COUNT(*) FROM comment
                        UNION ALL
                        SELECT 'rating', COUNT(*) FROM rating
                        UNION ALL
                        SELECT 'image', COUNT(*) FROM image
                    """)
                    
                    result = conn.execute(query).fetchall()
                    
                    performance_data = {}
                    for row in result:
                        if hasattr(row, '_mapping'):
                            table_name = row._mapping['table_name']
                            count = row._mapping['count']
                        else:
                            table_name = row[0]
                            count = row[1]
                        performance_data[table_name] = count
                
                result = CheckResult(
                    name="Database Performance",
                    severity=CheckSeverity.INFO,
                    status=True,
                    message="Database performance metrics collected",
                    details={"table_counts": performance_data}
                )
                self.results.append(result)
        
        except Exception as e:
            result = CheckResult(
                name="Database Performance",
                severity=CheckSeverity.WARNING,
                status=False,
                message=f"Could not collect performance metrics: {str(e)}",
                details={"error": str(e)}
            )
            self.results.append(result)
    
    def _get_expected_columns(self, table_name: str) -> Dict[str, Any]:
        """Get expected columns for a table based on models.py."""
        # This is a simplified version - in a real implementation,
        # you would parse the actual model definitions
        expected_columns = {
            'user': {
                'id': {'type': 'INTEGER', 'primary_key': True},
                'username': {'type': 'VARCHAR(50)', 'unique': True},
                'password_hash': {'type': 'VARCHAR(255)'},
                'role': {'type': 'VARCHAR(50)'},
                'is_active': {'type': 'BOOLEAN'},
                'email': {'type': 'VARCHAR(255)'},
                'created_at': {'type': 'DATETIME'},
                'updated_at': {'type': 'DATETIME'}
            },
            'news': {
                'id': {'type': 'INTEGER', 'primary_key': True},
                'title': {'type': 'VARCHAR(200)'},
                'content': {'type': 'TEXT'},
                'date': {'type': 'DATETIME'},
                'user_id': {'type': 'INTEGER'},
                'category_id': {'type': 'INTEGER'},
                'is_visible': {'type': 'BOOLEAN'},
                'created_at': {'type': 'DATETIME'},
                'updated_at': {'type': 'DATETIME'}
            },
            'category': {
                'id': {'type': 'INTEGER', 'primary_key': True},
                'name': {'type': 'VARCHAR(50)', 'unique': True}
            },
            'image': {
                'id': {'type': 'INTEGER', 'primary_key': True},
                'filename': {'type': 'VARCHAR(100)'},
                'filepath': {'type': 'VARCHAR(255)'},
                'is_visible': {'type': 'BOOLEAN'},
                'user_id': {'type': 'INTEGER'},
                'created_at': {'type': 'DATETIME'},
                'updated_at': {'type': 'DATETIME'}
            }
        }
        
        return expected_columns.get(table_name, {})
    
    def run_all_checks(self) -> List[CheckResult]:
        """Run all database health checks.
        
        Returns:
            List[CheckResult]: List of check results
        """
        self.results = []
        
        # Run checks in order of importance
        if not self.connect():
            return self.results
        
        self.check_table_existence()
        self.check_table_structure()
        self.check_foreign_keys()
        self.check_indexes()
        self.check_data_integrity()
        self.check_performance()
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all check results.
        
        Returns:
            Dict containing summary statistics
        """
        if not self.results:
            return {"error": "No checks have been run"}
        
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r.status)
        failed_checks = total_checks - passed_checks
        
        severity_counts = {}
        for severity in CheckSeverity:
            severity_counts[severity.value] = sum(
                1 for r in self.results if r.severity == severity
            )
        
        critical_issues = [
            r for r in self.results 
            if r.severity == CheckSeverity.CRITICAL and not r.status
        ]
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "success_rate": (passed_checks / total_checks) * 100 if total_checks > 0 else 0,
            "severity_counts": severity_counts,
            "critical_issues": len(critical_issues),
            "overall_status": "HEALTHY" if not critical_issues else "UNHEALTHY"
        }
    
    def generate_report(self, output_format: str = "text") -> str:
        """Generate a detailed report of all check results.
        
        Args:
            output_format: "text", "json", or "html"
            
        Returns:
            str: Formatted report
        """
        summary = self.get_summary()
        
        if output_format == "json":
            return json.dumps({
                "summary": summary,
                "results": [
                    {
                        "name": r.name,
                        "severity": r.severity.value,
                        "status": r.status,
                        "message": r.message,
                        "details": r.details,
                        "recommendations": r.recommendations
                    }
                    for r in self.results
                ]
            }, indent=2)
        
        elif output_format == "html":
            return self._generate_html_report(summary)
        
        else:  # text format
            return self._generate_text_report(summary)
    
    def _generate_text_report(self, summary: Dict[str, Any]) -> str:
        """Generate a text report."""
        report = []
        report.append("=" * 60)
        report.append("DATABASE HEALTH CHECK REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Database: {self.database_url}")
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Total Checks: {summary['total_checks']}")
        report.append(f"  Passed: {summary['passed_checks']}")
        report.append(f"  Failed: {summary['failed_checks']}")
        report.append(f"  Success Rate: {summary['success_rate']:.1f}%")
        report.append(f"  Overall Status: {summary['overall_status']}")
        report.append("")
        
        # Results by severity
        for severity in [CheckSeverity.CRITICAL, CheckSeverity.ERROR, CheckSeverity.WARNING, CheckSeverity.INFO]:
            severity_results = [r for r in self.results if r.severity == severity]
            if severity_results:
                report.append(f"{severity.value.upper()} ISSUES:")
                for result in severity_results:
                    status_icon = "✓" if result.status else "✗"
                    report.append(f"  {status_icon} {result.name}: {result.message}")
                    if result.recommendations:
                        for rec in result.recommendations:
                            report.append(f"    → {rec}")
                report.append("")
        
        return "\n".join(report)
    
    def _generate_html_report(self, summary: Dict[str, Any]) -> str:
        """Generate an HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Health Check Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .critical {{ background-color: #ffe6e6; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .error {{ background-color: #fff2e6; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .warning {{ background-color: #fffbe6; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .info {{ background-color: #e6f3ff; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .status-ok {{ color: green; font-weight: bold; }}
                .status-fail {{ color: red; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Database Health Check Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Database: {self.database_url}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Checks:</strong> {summary['total_checks']}</p>
                <p><strong>Passed:</strong> {summary['passed_checks']}</p>
                <p><strong>Failed:</strong> {summary['failed_checks']}</p>
                <p><strong>Success Rate:</strong> {summary['success_rate']:.1f}%</p>
                <p><strong>Overall Status:</strong> <span class="status-{'ok' if summary['overall_status'] == 'HEALTHY' else 'fail'}">{summary['overall_status']}</span></p>
            </div>
        """
        
        for severity in [CheckSeverity.CRITICAL, CheckSeverity.ERROR, CheckSeverity.WARNING, CheckSeverity.INFO]:
            severity_results = [r for r in self.results if r.severity == severity]
            if severity_results:
                html += f'<h2>{severity.value.title()} Issues</h2>'
                for result in severity_results:
                    status_class = "status-ok" if result.status else "status-fail"
                    status_icon = "✓" if result.status else "✗"
                    html += f"""
                    <div class="{severity.value}">
                        <h3>{status_icon} {result.name}</h3>
                        <p class="{status_class}">{result.message}</p>
                    """
                    if result.recommendations:
                        html += "<ul>"
                        for rec in result.recommendations:
                            html += f"<li>{rec}</li>"
                        html += "</ul>"
                    html += "</div>"
        
        html += """
        </body>
        </html>
        """
        return html


def main():
    """Main function to run database health checks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Health Checker for LilyOpenCMS")
    parser.add_argument("--database-url", help="Database URL to check")
    parser.add_argument("--format", choices=["text", "json", "html"], default="text", 
                       help="Output format")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--quick", action="store_true", help="Run quick checks only")
    
    args = parser.parse_args()
    
    # Initialize checker
    checker = DatabaseHealthChecker(args.database_url)
    
    # Run checks
    results = checker.run_all_checks()
    
    # Generate report
    report = checker.generate_report(args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)
    
    # Exit with appropriate code
    summary = checker.get_summary()
    if summary.get("critical_issues", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main() 