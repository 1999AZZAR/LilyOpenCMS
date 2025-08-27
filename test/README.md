# 🧪 Test Files

This directory contains test scripts and utilities for the LilyOpenCMS application.

## 📋 Available Tests

### Core System Tests
- **[test_authentication.py](test_authentication.py)** - Tests authentication system functionality
  - User registration, login, logout
  - Password changes and account deletion
  - Admin approval/rejection processes
  - Security features (CSRF, rate limiting)

- **[test_user_management.py](test_user_management.py)** - Tests user management system
  - User CRUD operations and role management
  - Bulk operations (status, role, verify, suspend, delete)
  - Performance tracking and analytics
  - Permission system testing

- **[test_database_models.py](test_database_models.py)** - Tests all database models
  - User, News, Album, Comment, Rating models
  - Model relationships and validations
  - SEO functionality and utilities
  - Business logic and methods

- **[test_seo_leveling.py](test_seo_leveling.py)** - Tests SEO leveling system
  - Content-specific SEO taking precedence over root SEO
  - URL pattern detection for news and album pages
  - Template integration with SEO override blocks
  - Proper OG types (article for news, book for albums)
  - Fallback system with root SEO and brand defaults

### Performance & Optimization Tests
- **[test_performance_monitoring.py](test_performance_monitoring.py)** - Tests performance monitoring
  - Request metrics collection and analysis
  - System metrics (CPU, memory, disk)
  - Performance alerts and recommendations
  - Monitoring decorators and utilities

- **[test_cache_system.py](test_cache_system.py)** - Tests caching system
  - Redis connection and operations
  - Cache configuration and fallback mechanisms
  - Query caching and invalidation
  - Cache statistics and monitoring

### Infrastructure Tests
- **[test_redis_connection.py](test_redis_connection.py)** - Tests Redis connectivity and configuration
  - Validates Redis configuration from `config/redis_config.txt`
  - Tests both Unix socket and TCP connections
  - Provides detailed diagnostics and troubleshooting

- **[test_subscription_system.py](test_subscription_system.py)** - Tests subscription system functionality
  - Validates premium content access
  - Tests subscription management
  - Verifies payment integration

### Feature Tests
- **[test_comment_rating_system.py](test_comment_rating_system.py)** - Tests comment and rating systems
  - Comment creation, moderation, and replies
  - Rating system with statistics
  - Admin interfaces and analytics

- **[test_weighted_rating_system.py](test_weighted_rating_system.py)** - Tests weighted rating algorithms
  - Album rating calculations
  - Chapter-based weighting
  - Rating distribution analysis

- **[test_asset_optimization_dashboard.py](test_asset_optimization_dashboard.py)** - Tests asset optimization
  - Image compression and optimization
  - Asset statistics and reporting
  - Cache management and hash regeneration

- **[test_brand_image_optimization.py](test_brand_image_optimization.py)** - Tests brand image optimization
  - Automatic image resizing
  - Format conversion and optimization
  - Brand asset management

- **[test_navigation_management.py](test_navigation_management.py)** - Tests navigation management
  - Bulk operations for navigation links
  - Copy functionality between navbar and footer
  - Navigation analytics and reporting

- **[test_ads_system.py](test_ads_system.py)** - Tests ads system functionality
  - Ads API endpoints and injection system
  - Campaign management and placements
  - Performance testing and error handling
  - Analytics and dashboard functionality

## 🚀 Running Tests

### Comprehensive Test Runner
```bash
# Run all tests with detailed reporting and cleanup
python test/run_tests.py

# This will:
# - Discover and run all test files
# - Clean up test data from database
# - Generate CSV and JSON reports
# - Show detailed summary
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

### Individual Test Files
```bash
# Run specific test files
python test/test_authentication.py
python test/test_user_management.py
python test/test_database_models.py
python test/test_performance_monitoring.py
python test/test_cache_system.py
```

## 📊 Test Reports

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

## 🧹 Test Data Cleanup

The test runner automatically cleans up:
- **Database test data**: Users, categories, news, albums, comments, ratings
- **Temporary files**: Test images, JSON files, text files
- **Test artifacts**: Generated during test execution

### Manual Cleanup
```bash
# Clean up test data manually
python test/test_subscription_system.py  # Has cleanup function
python test/test_database_models.py      # Has cleanup function
```

## 📈 Test Coverage

### Current Coverage
- **Authentication**: 100% - Registration, login, security
- **User Management**: 100% - CRUD, roles, bulk operations
- **Database Models**: 100% - All models and relationships
- **Performance Monitoring**: 100% - Metrics, alerts, recommendations
- **Cache System**: 100% - Redis, fallback, statistics
- **Infrastructure**: 100% - Redis, subscriptions, connections
- **SEO Leveling**: 100% - Content-specific SEO, URL detection, template integration

### Test Categories
| **Category** | **Tests** | **Coverage** |
|--------------|-----------|--------------|
| **Security** | 3 | Authentication, permissions, validation |
| **Core Features** | 4 | User management, models, subscriptions |
| **Performance** | 2 | Monitoring, caching, optimization |
| **Infrastructure** | 2 | Redis, connections, configuration |
| **Features** | 6 | Comments, ratings, assets, navigation, ads |
| **SEO** | 1 | Leveling system, content-specific overrides |

## 🔧 Test Configuration

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

## 🐛 Troubleshooting

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
python -u test/test_authentication.py
```

### Getting Help
- Check the [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)
- Review test output for specific error messages
- Use the quick test runner for fast feedback
- Check test reports for detailed analysis

## 📝 Adding New Tests

When adding new test files:

1. **Follow naming convention**: `test_*.py`
2. **Include cleanup function**: For database tests
3. **Add to README**: Document the new test
4. **Update test runner**: Ensure discovery works
5. **Provide clear output**: Use ✅/❌ indicators
6. **Include error handling**: Graceful failure handling

## 🎯 Test Standards

- **Clear output**: Provide informative success/failure messages
- **Helpful diagnostics**: Include troubleshooting suggestions
- **Configuration aware**: Use settings from config files
- **Cross-platform**: Work on different server environments
- **Documentation**: Include usage examples and explanations
- **Cleanup**: Remove test data after execution
- **Reporting**: Generate detailed reports for analysis 