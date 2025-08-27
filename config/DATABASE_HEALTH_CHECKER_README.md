# Database Health Checker for LilyOpenCMS

## Overview

The Database Health Checker is a comprehensive system designed to ensure the database structure matches the models.py definitions and maintains data integrity. It provides robust checking mechanisms for database availability, integrity, and performance.

## Features

### 🔍 Comprehensive Checks
- **Database Connectivity**: Verifies database connection and availability
- **Table Existence**: Ensures all expected tables from models.py exist
- **Schema Validation**: Checks column types and constraints match models
- **Foreign Key Integrity**: Verifies foreign key relationships are intact
- **Index Verification**: Checks important indexes for performance
- **Data Integrity**: Detects orphaned records and constraint violations
- **Performance Monitoring**: Collects database performance metrics

### 📊 Detailed Reporting
- **Multiple Formats**: Text, JSON, and HTML reports
- **Severity Levels**: INFO, WARNING, ERROR, CRITICAL
- **Actionable Recommendations**: Specific steps to fix issues
- **Summary Statistics**: Success rates and overall health status

### 🛠️ Integration
- **Startup Checks**: Automatic health checks on application startup
- **Health Endpoint**: Enhanced `/health` endpoint with detailed database status
- **CLI Tool**: Standalone command-line interface for manual checks

## Usage

### Command Line Interface

```bash
# Basic health check
python config/check_db.py

# Detailed JSON report
python config/check_db.py --format json

# Save HTML report
python config/check_db.py --output report.html --format html

# Check specific database
python config/check_db.py --database-url sqlite:///test.db

# Verbose output
python config/check_db.py --verbose
```

### Programmatic Usage

```python
from config.database_health_checker import DatabaseHealthChecker

# Initialize checker
checker = DatabaseHealthChecker("sqlite:///instance/LilyOpenCms.db")

# Run all checks
results = checker.run_all_checks()

# Get summary
summary = checker.get_summary()
print(f"Success rate: {summary['success_rate']:.1f}%")

# Generate report
report = checker.generate_report("text")
print(report)
```

### Health Endpoint

```bash
# Basic health check
curl http://localhost:5000/health

# Detailed health check
curl http://localhost:5000/health?detailed=true
```

## Expected Database Structure

The health checker expects the following tables based on models.py:

### Core Tables (Critical)
- `user` - User accounts and authentication
- `news` - News articles and content
- `category` - Content categories
- `image` - Image uploads and media

### Content Tables
- `album` - Content albums/chapters
- `album_chapter` - Individual chapters within albums
- `youtube_video` - YouTube video links
- `share_log` - Social media sharing tracking

### User Interaction Tables
- `comment` - User comments on content
- `rating` - User ratings on content
- `comment_like` - Comment likes/dislikes
- `comment_report` - Comment moderation reports

### Business Tables
- `contact_detail` - Contact information
- `team_member` - Team member profiles
- `brand_identity` - Brand configuration
- `user_subscriptions` - User subscription data

### SEO and Navigation Tables
- `root_seo` - SEO settings for root pages
- `navigation_link` - Navigation menu items

### Advertising Tables
- `ad_campaign` - Advertising campaigns
- `ad` - Individual advertisements
- `ad_placement` - Ad placement rules
- `ad_stats` - Advertisement statistics

### Policy Tables
- `privacy_policy` - Privacy policy content
- `media_guideline` - Media guidelines
- `visi_misi` - Vision and mission
- `penyangkalan` - Disclaimers
- `pedoman_hak` - Rights guidelines

### Authentication and Permissions Tables
- `permission` - System permissions
- `custom_role` - Custom user roles
- `role_permission` - Role-permission mappings
- `user_activity` - User activity logging

## Check Types

### 1. Connection Check
- **Purpose**: Verify database connectivity
- **Severity**: CRITICAL
- **Failure Impact**: Application cannot start

### 2. Table Existence Check
- **Purpose**: Ensure all expected tables exist
- **Severity**: CRITICAL for core tables, WARNING for others
- **Failure Impact**: Missing functionality

### 3. Schema Validation Check
- **Purpose**: Verify column types and constraints
- **Severity**: ERROR
- **Failure Impact**: Data corruption risk

### 4. Foreign Key Check
- **Purpose**: Ensure referential integrity
- **Severity**: ERROR
- **Failure Impact**: Data inconsistency

### 5. Index Check
- **Purpose**: Verify performance indexes
- **Severity**: WARNING
- **Failure Impact**: Poor performance

### 6. Data Integrity Check
- **Purpose**: Detect orphaned records
- **Severity**: ERROR
- **Failure Impact**: Data corruption

### 7. Performance Check
- **Purpose**: Collect performance metrics
- **Severity**: INFO
- **Failure Impact**: Monitoring gaps

## Configuration

### Environment Variables

```bash
# Enable health checks on startup
RUN_DB_HEALTH_CHECK=true

# Database URL (if different from default)
DATABASE_URI=sqlite:///instance/LilyOpenCms.db
```

### Application Configuration

```python
# In main.py
app.config["RUN_DB_HEALTH_CHECK"] = True  # Enable startup checks
```

## Troubleshooting

### Common Issues

#### 1. Missing Tables
**Symptoms**: Critical tables missing error
**Solution**: 
```bash
flask db upgrade
```

#### 2. Schema Mismatch
**Symptoms**: Column type errors
**Solution**:
```bash
flask db migrate -m "Fix schema mismatch"
flask db upgrade
```

#### 3. Foreign Key Issues
**Symptoms**: Orphaned records detected
**Solution**:
```python
# Clean up orphaned records
from models import db, News, User
orphaned_news = News.query.filter(~News.user_id.in_(User.query.with_entities(User.id))).all()
for news in orphaned_news:
    db.session.delete(news)
db.session.commit()
```

#### 4. Performance Issues
**Symptoms**: Missing indexes warning
**Solution**:
```python
# Add indexes in models.py
class News(db.Model):
    __table_args__ = (
        db.Index('idx_news_date', 'date'),
        db.Index('idx_news_visible', 'is_visible'),
    )
```

### Debug Mode

Enable verbose logging for detailed debugging:

```bash
python config/check_db.py --verbose
```

## Integration with CI/CD

### Pre-deployment Check

```bash
#!/bin/bash
# pre_deploy.sh

echo "Running database health checks..."
python config/check_db.py --format json --output health_report.json

if [ $? -ne 0 ]; then
    echo "❌ Database health check failed"
    cat health_report.json
    exit 1
fi

echo "✅ Database health check passed"
```

### Automated Monitoring

```python
# monitor_db.py
import schedule
import time
from config.database_health_checker import DatabaseHealthChecker

def check_database_health():
    checker = DatabaseHealthChecker()
    results = checker.run_all_checks()
    summary = checker.get_summary()
    
    if summary.get("critical_issues", 0) > 0:
        # Send alert
        send_alert(f"Database has {summary['critical_issues']} critical issues")
    
    # Log results
    log_health_check(summary)

# Run every hour
schedule.every().hour.do(check_database_health)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Performance Considerations

### Quick Checks
For frequent monitoring, use quick checks that skip performance metrics:

```python
# Skip performance checks for faster execution
checker = DatabaseHealthChecker()
checker.run_quick_checks()  # Only connection and critical table checks
```

### Caching
The health checker caches results for 5 minutes to avoid repeated expensive checks:

```python
# Results are cached automatically
checker = DatabaseHealthChecker()
results1 = checker.run_all_checks()  # Full check
results2 = checker.run_all_checks()  # Cached results
```

## Security Considerations

### Database Credentials
- Never log database credentials in health check reports
- Use environment variables for sensitive configuration
- Implement proper access controls for health check endpoints

### Information Disclosure
- Health check reports may contain sensitive information
- Restrict access to detailed health reports in production
- Sanitize error messages before logging

## Contributing

### Adding New Checks

1. Extend the `DatabaseHealthChecker` class
2. Add your check method
3. Update the `run_all_checks()` method
4. Add expected data to the constructor
5. Update documentation

Example:
```python
def check_custom_table(self) -> None:
    """Check custom table structure."""
    if not self.inspector.has_table('custom_table'):
        result = CheckResult(
            name="Custom Table Missing",
            severity=CheckSeverity.ERROR,
            status=False,
            message="Custom table does not exist",
            recommendations=["Create custom table migration"]
        )
        self.results.append(result)
```

### Testing

```bash
# Run tests
python -m pytest test/test_database_health_checker.py

# Test with different databases
python config/check_db.py --database-url sqlite:///test.db
python config/check_db.py --database-url postgresql://user:pass@localhost/test
```

## License

This database health checker is part of the LilyOpenCMS project and follows the same license terms. 