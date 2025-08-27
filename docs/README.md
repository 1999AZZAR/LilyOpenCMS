# 📚 Documentation Index

Welcome to the LilyOpenCMS documentation! This directory contains comprehensive guides and documentation for all aspects of the system.

## 🚀 Quick Start

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment guide for DirectAdmin hosting and other environments
- **[Contact Details Guide](CONTACT_DETAILS_GUIDE.md)** - How to manage contact information in the footer
- **[Development Roadmap](TODO.md)** - Current development status and progress tracking

## 📖 Core Documentation

### System Documentation
- **[API Documentation](api.md)** - Complete API reference with endpoints and examples
- **[Admin UI Guide](admin_ui.md)** - Comprehensive admin interface documentation
- **[Sitemap Documentation](SITEMAP_DOCUMENTATION.md)** - Complete sitemap system guide
- **[Card Design System](CARD_DESIGN_SYSTEM.md)** - Complete card design system with 4 distinct designs
- **[Card Design Troubleshooting](CARD_DESIGN_TROUBLESHOOTING.md)** - Troubleshooting guide for card design issues
- **[Ads Injection System – Comprehensive](ADS_INJECTION_COMPREHENSIVE.md)** - Ads injection architecture and roadmap
- **[Comment & Rating System – Comprehensive](COMMENT_RATING_COMPREHENSIVE.md)** - Complete comment and rating system documentation

### Performance & Optimization
- **[Performance & Optimizations – Comprehensive](PERFORMANCE_OPTIMIZATIONS_COMPREHENSIVE.md)** - Complete guide, quick start, advanced topics, and dashboards




### System Implementation
- **[Performance & Optimizations – Comprehensive](PERFORMANCE_OPTIMIZATIONS_COMPREHENSIVE.md)** - Unified performance implementation and results
- **[Premium Content & Subscription – Comprehensive](PREMIUM_SYSTEM_COMPREHENSIVE.md)** - Premium content and subscription system
- **[Subscription System Status](SUBSCRIPTION_SYSTEM_STATUS.md)** - Subscription feature status
- **[Weighted Rating System](WEIGHTED_RATING_SYSTEM.md)** - Advanced rating system with weighted calculations

### Testing & Quality Assurance
- **[Comprehensive Endpoint Testing](test/test_comprehensive_endpoints.py)** - Full endpoint testing with 95% success rate
- **[Test Summary](test/test_summary.md)** - Detailed testing results and system status

### Development
- **[Development Roadmap](TODO.md)** - Current development status and future plans

## 🔧 Configuration Guides

### Redis Configuration
The system uses a text-based configuration for Redis settings:

- **Configuration File**: `config/redis_config.txt`
- **Deployment Script**: `config/deploy_redis_config.py`
- **Test Script**: `test/test_redis_connection.py`
- **Config Reader**: `routes/utils/config_reader.py`

### Environment Setup
- **Environment Variables**: See root README.md for complete `.env` configuration
- **Database Setup**: Alembic migrations and seeding scripts
- **Performance Setup**: Redis installation and optimization

## 🛠️ Troubleshooting

### Common Issues
1. **Redis Connection Errors**: Check `DEPLOYMENT_GUIDE.md` for Redis setup
2. **Database Issues**: Run `flask db upgrade` to apply migrations
3. **Performance Issues**: Review `PERFORMANCE_OPTIMIZATIONS_COMPREHENSIVE.md`
4. **Deployment Issues**: Follow `DEPLOYMENT_GUIDE.md` step by step
5. **Comment & Rating Issues**: Check `COMMENT_RATING_COMPREHENSIVE.md` for troubleshooting
6. **Asset Optimization Issues**: Review `PERFORMANCE_OPTIMIZATIONS_COMPREHENSIVE.md` for optimization problems
7. **Card Design Issues**: Check `CARD_DESIGN_TROUBLESHOOTING.md` for card design system problems
8. **Authentication Issues**: Run comprehensive endpoint tests with `python test/test_comprehensive_endpoints.py`
9. **Template Path Issues**: Check `test/test_summary.md` for template path verification

### Getting Help
- Check the relevant documentation above
- Review the main [README.md](../README.md) in the root directory
- Check application logs for specific error messages
- Use the test scripts to diagnose issues

## 📝 Contributing to Documentation

When adding new documentation:

1. **Place files in this directory** (`docs/`)
2. **Update this index** to include new files
3. **Follow the naming convention**: Use descriptive names with `.md` extension
4. **Include cross-references** to related documentation
5. **Keep documentation up to date** with code changes

## 📋 Documentation Standards

- Use clear, descriptive titles
- Include code examples where helpful
- Provide step-by-step instructions for complex processes
- Include troubleshooting sections for common issues
- Keep documentation concise but comprehensive
- Use consistent formatting and structure

## 🎯 System Features Overview

### Core Features
- **User Management**: Role-based access control (SUPERUSER, ADMIN, GENERAL)
- **Content Management**: News, albums, chapters, images, videos
- **Card Design System**: 4 distinct card designs (classic, modern, minimal, featured)
- **SEO Optimization**: Comprehensive SEO with structured data
- **Performance**: Redis caching, database optimization, asset compression
- **Comments & Ratings**: Nested comments, 5-star ratings, moderation
- **Subscription System**: Premium content with ad-free experience
- **Analytics**: Real-time performance monitoring and analytics
- **Comprehensive Testing**: 95% endpoint success rate with full authentication testing

### Admin Features
- **Dashboard**: Performance monitoring, analytics, and system health
- **Content Management**: News, albums, images, videos, categories
- **User Management**: User roles, permissions, and activity tracking
- **SEO Management**: Page-specific and root SEO settings
- **Brand Management**: Logo, tagline, and brand identity
- **Settings**: Contact details, social media, navigation, policies

### Performance Features
- **Caching**: Redis-based intelligent caching with invalidation
- **Database Optimization**: Connection pooling, query optimization, indexing
- **Asset Optimization**: CSS/JS minification, gzip compression, versioning
- **SSR Optimization**: Template caching and rendering optimization
- **Monitoring**: Real-time performance metrics and alerts

---

**Need help?** Start with the [Deployment Guide](DEPLOYMENT_GUIDE.md) for setup instructions, or check the [API Documentation](api.md) for technical details. 