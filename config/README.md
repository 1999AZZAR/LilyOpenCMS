# ⚙️ Configuration Files

This directory contains all configuration files for the LilyOpenCMS application.

## 📋 Available Configurations

### Redis Configuration
- **[redis_config.txt](redis_config.txt)** - Main Redis configuration file
  - Connection settings (socket/TCP)
  - Timeout configurations
  - Cache settings
  - Environment-specific examples

- **[redis_config.env](redis_config.env)** - Environment-based Redis configuration
  - Alternative to text-based configuration
  - Uses environment variables
  - Backup configuration method

- **[redis.env](redis.env)** - Redis environment configuration
  - Environment variables for Redis setup
  - Alternative configuration method

### Deployment Tools
- **[deploy_redis_config.py](deploy_redis_config.py)** - Interactive Redis configuration setup
  - Supports multiple server types (DirectAdmin, cPanel, VPS)
  - Automatic configuration generation
  - Backup existing configurations

- **[deploy_setup.sh](deploy_setup.sh)** - Deployment setup script
  - Server deployment automation
  - Environment setup

- **[generate_test_data.sh](generate_test_data.sh)** - Test data generation
  - Creates sample data for testing
  - Database seeding

### Redis Setup Scripts
- **[setup_redis.sh](setup_redis.sh)** - Redis installation script
  - Automated Redis installation
  - Configuration setup

- **[start_redis.sh](start_redis.sh)** - Redis startup script
  - Redis service management
  - Process control

- **[redis-performance.conf](redis-performance.conf)** - Redis performance configuration
  - Performance optimization settings
  - Production-ready configuration

## 🔧 Configuration Types

### Text-Based Configuration (`redis_config.txt`)
Primary configuration method using simple key=value format:

```txt
# Connection Type: 'socket' or 'tcp'
CONNECTION_TYPE=socket

# Unix Socket Path
REDIS_SOCKET=/home/username/.redis/redis.sock

# TCP Connection Settings
REDIS_HOST=localhost
REDIS_PORT=6379

# Authentication
REDIS_PASSWORD=

# Timeouts
SOCKET_CONNECT_TIMEOUT=1
SOCKET_TIMEOUT=1
TCP_CONNECT_TIMEOUT=2
TCP_TIMEOUT=2

# Cache Settings
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=lilycms_
```

### Environment-Based Configuration (`redis_config.env`)
Alternative method using environment variables:

```env
# Redis Configuration for DirectAdmin Hosting
REDIS_SOCKET=/home/username/.redis/redis.sock
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=lilycms_
```

## 🚀 Quick Setup

### Automated Configuration
```bash
# Run the deployment script from project root
python config/deploy_redis_config.py

# Choose your server type:
# 1. DirectAdmin hosting
# 2. cPanel hosting
# 3. VPS/Dedicated server
# 4. Custom socket path
# 5. TCP connection
```

### Manual Configuration
```bash
# Edit the configuration file
nano config/redis_config.txt

# Test the configuration
python test/test_redis_connection.py
```

## 🔄 Server Migration

When deploying to a new server:

1. **Copy configuration files**:
   ```bash
   scp config/redis_config.txt user@newserver:/path/to/app/config/
   ```

2. **Update the username** in the config file:
   ```txt
   REDIS_SOCKET=/home/new_username/.redis/redis.sock
   ```

3. **Test the configuration**:
   ```bash
   python test/test_redis_connection.py
   ```

## 🛠️ Troubleshooting

### Configuration Issues
1. **File not found**: Ensure config files are in the `config/` directory
2. **Permission denied**: Check file permissions (should be readable)
3. **Invalid format**: Follow the key=value format exactly
4. **Missing values**: Provide all required configuration values

### Common Server Types
- **DirectAdmin**: `/home/username/.redis/redis.sock`
- **cPanel**: `/home/username/.redis/redis.sock`
- **VPS**: `/var/run/redis/redis.sock`
- **Custom**: Specify your socket path

## 📝 Adding New Configurations

When adding new configuration files:

1. **Place files in this directory** (`config/`)
2. **Update this README** to document new configs
3. **Follow naming convention**: `*_config.*`
4. **Include examples** and documentation
5. **Provide validation** scripts if needed

## 🎯 Configuration Standards

- **Clear documentation**: Include comments and examples
- **Environment-specific**: Provide examples for different server types
- **Validation**: Include validation scripts where possible
- **Backup support**: Support for backing up existing configurations
- **Cross-platform**: Work on different operating systems 