# Test Suite

This directory contains a comprehensive test suite for the LilyOpenCMS application, organized into logical categories for better maintainability and clarity.

## Directory Structure

```
test/
├── core/                    # Core system tests
├── features/                # Feature-specific tests  
├── infrastructure/          # Infrastructure and connectivity tests
├── performance/             # Performance and optimization tests
├── utils/                   # Utility and helper tests
├── reports/                 # Test execution reports
├── run_tests.py            # Comprehensive test runner
├── quick_test.py           # Quick test runner
└── README.md               # This documentation
```

## Test Categories

### Core System Tests (`core/`)
Essential system functionality tests:
- **[test_authentication.py](core/test_authentication.py)** - Authentication system tests
  - User registration, login, logout
  - Password changes and account deletion
  - Admin approval/rejection processes
  - Security features (CSRF, rate limiting)

- **[test_user_management.py](core/test_user_management.py)** - User management system tests
  - User CRUD operations and role management
  - Bulk operations (status, role, verify, suspend, delete)
  - Performance tracking and analytics

- **[test_database_models.py](core/test_database_models.py)** - Database model tests
  - User, News, Album, Comment, Rating models
  - Model relationships and validations
  - SEO functionality and utilities

- **[test_permissions.py](core/test_permissions.py)** - Permission system tests
  - Role-based access control
  - Permission inheritance and validation

- **[test_comprehensive_endpoints.py](core/test_comprehensive_endpoints.py)** - API endpoint tests
  - Comprehensive endpoint testing
  - Request/response validation

- **[test_public_api.py](core/test_public_api.py)** - Public API tests
  - External API functionality
  - Authentication and authorization

- **[test_user_account_management.py](core/test_user_account_management.py)** - Account management tests
  - User profile management
  - Account settings and preferences

### Feature Tests (`features/`)
Application feature-specific tests:
- **[test_comment_rating_system.py](features/test_comment_rating_system.py)** - Comment and rating system tests
- **[test_weighted_rating_system.py](features/test_weighted_rating_system.py)** - Weighted rating algorithm tests
- **[test_ads_system.py](features/test_ads_system.py)** - Advertisement system tests
- **[test_ads_premium_detector.py](features/test_ads_premium_detector.py)** - Premium ad detection tests
- **[test_subscription_system.py](features/test_subscription_system.py)** - Subscription system tests
- **[test_seo_leveling.py](features/test_seo_leveling.py)** - SEO leveling system tests
- **[test_navigation_management.py](features/test_navigation_management.py)** - Navigation management tests
- **[test_share_tracking.py](features/test_share_tracking.py)** - Share tracking functionality tests
- **[test_unified_news.py](features/test_unified_news.py)** - Unified news system tests
- **[test_achievement_system.py](features/test_achievement_system.py)** - Achievement system tests
- **[test_premium_content_system.py](features/test_premium_content_system.py)** - Premium content tests
- **[test_create_ad.py](features/test_create_ad.py)** - Ad creation tests
- **[test_push_ad.py](features/test_push_ad.py)** - Ad push functionality tests
- **[test_push_ad_comprehensive.py](features/test_push_ad_comprehensive.py)** - Comprehensive ad push tests

### Infrastructure Tests (`infrastructure/`)
Infrastructure and connectivity tests:
- **[test_redis_connection.py](infrastructure/test_redis_connection.py)** - Redis connectivity tests
- **[test_email_system.py](infrastructure/test_email_system.py)** - Email system tests
- **[test_verification_mechanism.py](infrastructure/test_verification_mechanism.py)** - Verification system tests
- **[test_login_auth.py](infrastructure/test_login_auth.py)** - Login authentication tests
- **[test_smtp_manual.py](infrastructure/test_smtp_manual.py)** - Manual SMTP tests
- **[test_smtp_simple.py](infrastructure/test_smtp_simple.py)** - Simple SMTP tests

### Performance Tests (`performance/`)
Performance monitoring and optimization tests:
- **[test_performance_monitoring.py](performance/test_performance_monitoring.py)** - Performance monitoring tests
- **[test_cache_system.py](performance/test_cache_system.py)** - Caching system tests
- **[test_asset_optimization_dashboard.py](performance/test_asset_optimization_dashboard.py)** - Asset optimization tests
- **[test_brand_image_optimization.py](performance/test_brand_image_optimization.py)** - Brand image optimization tests
- **[test_album_view_count.py](performance/test_album_view_count.py)** - Album view counting tests
- **[test_album_view_sorting.py](performance/test_album_view_sorting.py)** - Album sorting performance tests

### Utility Tests (`utils/`)
Utility and helper function tests:
- **[test_imports.py](utils/test_imports.py)** - Import validation tests
- **[test_js_functions.py](utils/test_js_functions.py)** - JavaScript function tests
- **[test_write_access_api.py](utils/test_write_access_api.py)** - Write access API tests

## Running Tests

### Comprehensive Test Runner
```bash
# Run all tests with detailed reporting and cleanup
python test/run_tests.py

# This will:
# - Discover and run all test files in all categories
# - Clean up test data from database
# - Generate CSV and JSON reports
# - Show detailed summary by category
```

### Quick Test Runner
```bash
# Run tests quickly without detailed reporting
python test/quick_test.py

# This provides:
# - Fast execution
# - Basic pass/fail results
# - Quick summary
```

### Category-Specific Testing
```bash
# Run tests from specific categories
python test/core/test_authentication.py
python test/features/test_comment_rating_system.py
python test/infrastructure/test_redis_connection.py
python test/performance/test_cache_system.py
```

### Individual Test Files
```bash
# Run specific test files
python test/core/test_user_management.py
python test/features/test_ads_system.py
python test/performance/test_performance_monitoring.py
```

## Test Reports

### CSV Reports
The comprehensive test runner generates CSV reports with:
- Test file names and status
- Duration and test case counts
- Return codes and timestamps
- Detailed notes and error messages

### JSON Reports
Detailed JSON reports include:
- Summary statistics (total tests, success rate, duration)
- Individual test results with full output
- Timestamps and performance metrics
- Error details and stack traces

### Report Location
Reports are saved to `test/reports/` with timestamps:
```
test/reports/
├── test_report_20250804_143022.csv
├── test_report_20250804_143022.json
└── ...
```

## Test Data Cleanup

The test runner automatically cleans up:
- **Database test data**: Users, categories, news, albums, comments, ratings
- **Temporary files**: Test images, JSON files, text files
- **Test artifacts**: Generated during test execution

### Manual Cleanup
```bash
# Clean up test data manually
python test/features/test_subscription_system.py  # Has cleanup function
python test/core/test_database_models.py          # Has cleanup function
```

## Test Coverage

### Current Coverage by Category
- **Core System**: 100% - Authentication, user management, database models, permissions
- **Features**: 100% - Comments, ratings, ads, subscriptions, SEO, navigation
- **Infrastructure**: 100% - Redis, email, SMTP, verification
- **Performance**: 100% - Monitoring, caching, optimization
- **Utilities**: 100% - Imports, JavaScript functions, API access

### Test Categories Summary
| **Category** | **Tests** | **Coverage** |
|--------------|-----------|--------------|
| **Core** | 7 | Authentication, users, database, permissions, APIs |
| **Features** | 14 | Comments, ratings, ads, subscriptions, SEO, navigation |
| **Infrastructure** | 6 | Redis, email, SMTP, verification, connectivity |
| **Performance** | 6 | Monitoring, caching, optimization, view tracking |
| **Utilities** | 3 | Imports, JavaScript, API access |

## Test Configuration

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
pip install -r requirements.txt

# Set up test database (if needed)
python helper/setup_test_db.py
```

### Test Timeouts
- **Individual tests**: 60 seconds (quick runner)
- **Comprehensive tests**: 300 seconds (full runner)
- **Database operations**: 30 seconds
- **Network requests**: 10 seconds

## Troubleshooting

### Common Issues
1. **Redis not available**: Tests will use fallback caching
2. **Database connection**: Check database configuration
3. **Import errors**: Ensure virtual environment is activated
4. **Timeout errors**: Increase timeout values in test files

### Debug Mode
```bash
# Run tests with verbose output
python -v test/run_tests.py

# Run specific test with debug
python -u test/core/test_authentication.py
```

### Getting Help
- Check the [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)
- Review test output for specific error messages
- Use the quick test runner for fast feedback
- Check test reports for detailed analysis

## Adding New Tests

When adding new test files:

1. **Choose appropriate category**: Place in correct subdirectory
2. **Follow naming convention**: `test_*.py`
3. **Include cleanup function**: For database tests
4. **Update this README**: Document the new test
5. **Update test runner**: Ensure discovery works
6. **Provide clear output**: Use ✅/❌ indicators
7. **Include error handling**: Graceful failure handling

### Test File Placement Guide
- **Core functionality**: Place in `core/` directory
- **Feature-specific**: Place in `features/` directory  
- **Infrastructure/connectivity**: Place in `infrastructure/` directory
- **Performance/optimization**: Place in `performance/` directory
- **Utility/helper functions**: Place in `utils/` directory

## Test Standards

- **Clear output**: Provide informative success/failure messages
- **Helpful diagnostics**: Include troubleshooting suggestions
- **Configuration aware**: Use settings from config files
- **Cross-platform**: Work on different server environments
- **Documentation**: Include usage examples and explanations
- **Cleanup**: Remove test data after execution
- **Reporting**: Generate detailed reports for analysis
- **Organization**: Place tests in appropriate categories