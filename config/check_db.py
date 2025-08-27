#!/usr/bin/env python3
"""
Database Health Check CLI Script

Simple command-line interface to run database health checks.
"""

import sys
import os
import argparse
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_health_checker import DatabaseHealthChecker


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Database Health Checker for LilyOpenCMS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_db.py                           # Run all checks with default database
  python check_db.py --format json             # Output JSON report
  python check_db.py --output report.html --format html  # Save HTML report
  python check_db.py --database-url sqlite:///test.db    # Check specific database
        """
    )
    
    parser.add_argument(
        "--database-url", 
        help="Database URL (default: sqlite:///instance/LilyOpenCms.db)"
    )
    
    parser.add_argument(
        "--format", 
        choices=["text", "json", "html"], 
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--output", 
        help="Output file (default: print to stdout)"
    )
    
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Run quick checks only (skip performance checks)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fix", 
        action="store_true",
        help="Attempt to fix common issues (experimental)"
    )
    
    args = parser.parse_args()
    
    print("🔍 LilyOpenCMS Database Health Checker")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {args.database_url or 'sqlite:///instance/LilyOpenCms.db'}")
    print()
    
    try:
        # Initialize checker
        checker = DatabaseHealthChecker(args.database_url)
        
        # Run checks
        if args.verbose:
            print("Running database health checks...")
        
        results = checker.run_all_checks()
        
        # Generate report
        report = checker.generate_report(args.format)
        
        # Output report
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Report saved to: {args.output}")
        else:
            print(report)
        
        # Get summary
        summary = checker.get_summary()
        
        print()
        print("📊 Summary:")
        print(f"  Total Checks: {summary['total_checks']}")
        print(f"  Passed: {summary['passed_checks']}")
        print(f"  Failed: {summary['failed_checks']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Overall Status: {summary['overall_status']}")
        
        if summary.get("critical_issues", 0) > 0:
            print(f"  ⚠️  Critical Issues: {summary['critical_issues']}")
            print()
            print("🔧 Recommendations:")
            print("  1. Run: flask db upgrade")
            print("  2. Check database migrations")
            print("  3. Verify models.py is up to date")
            print("  4. Check database permissions")
            sys.exit(1)
        else:
            print("  ✅ Database is healthy!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n❌ Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running health checks: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 