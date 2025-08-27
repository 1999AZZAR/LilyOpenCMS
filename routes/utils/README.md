# 🔧 Routes Utilities

This directory contains utility functions and helpers for the routes package.

## 📋 Available Utilities

### Configuration Management
- **[config_reader.py](config_reader.py)** - Redis configuration reader
  - Reads configuration from text files
  - Validates configuration settings
  - Provides fallback to environment variables
  - Caches configuration for performance

## 🚀 Usage

### Configuration Reader
```python
from routes.utils.config_reader import get_redis_config, validate_redis_config

# Get Redis configuration
config = get_redis_config()

# Validate configuration
is_valid = validate_redis_config()
```

### Direct Import
```python
from routes.utils.config_reader import ConfigReader

# Create reader instance
reader = ConfigReader("config/redis_config.txt")

# Read configuration
config = reader.read_config()

# Print configuration
reader.print_config()

# Validate configuration
is_valid = reader.validate_config()
```

## 📝 Adding New Utilities

When adding new utility files:

1. **Place files in this directory** (`routes/utils/`)
2. **Update this README** to document new utilities
3. **Follow naming convention**: Use descriptive names
4. **Include clear documentation** in the utility file
5. **Provide usage examples** and error handling

## 🎯 Utility Standards

- **Clear documentation**: Include docstrings and comments
- **Error handling**: Provide graceful fallbacks
- **Configuration aware**: Use settings from config files
- **Cross-platform**: Work on different operating systems
- **Performance**: Optimize for speed and memory usage 