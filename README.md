# Firewallo

> **Extensible Network Management Platform**

Firewallo is a comprehensive, plugin-based network management platform that provides unified control over VPNs, firewalls, monitoring systems, and network services through a modern REST API and extensible architecture.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-green.svg)
![Docker](https://img.shields.io/badge/docker-supported-blue.svg)

## 🌟 Key Features

- **🔌 Plugin-Based Architecture** - Extensible framework supporting VPN, firewall, monitoring, and network management plugins
- **🔒 Enterprise Security** - JWT authentication, RBAC, and secure API endpoints
- **🌐 Multi-Protocol Support** - WireGuard, OpenVPN, IPSec, and custom VPN solutions via plugins
- **📊 Unified Management** - Single API for diverse network technologies and services
- **🔄 Hot-Reload Plugins** - Install and configure plugins without application restarts
- **💾 Flexible Storage** - Support for both LiteDB (JSON) and MongoDB backends
- **🚀 Production Ready** - Docker support, monitoring, and enterprise-grade features

## 🏗️ Architecture

Firewallo follows a clean, modular architecture designed for scalability and extensibility:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   Mobile App    │    │  External API   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      FastAPI Server       │
                    │    (REST API Gateway)     │
                    └─────────────┬─────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
    ┌───────▼───────┐    ┌────────▼────────┐    ┌──────▼──────┐
    │ VPN Plugins   │    │ Firewall        │    │ Monitoring  │
    │ • WireGuard   │    │ Plugins         │    │ Plugins     │
    │ • OpenVPN     │    │ • iptables      │    │ • Prometheus│
    │ • IPSec       │    │ • nftables      │    │ • Grafana   │
    └───────────────┘    └─────────────────┘    └─────────────┘
```

### Core Components

- **API Layer** - FastAPI-based REST endpoints with automatic documentation
- **Plugin System** - Hot-loadable modules for different network technologies
- **Authentication** - JWT-based security with role-based access control
- **Database Layer** - Abstracted storage supporting multiple backends
- **Service Layer** - Business logic for network operations

## 🚀 Quick Start

### Docker Deployment (Recommended)

1. **Download the docker-compose file:**
   ```bash
   curl -o docker-compose.yaml https://raw.githubusercontent.com/your-repo/firewallo-ui/main/docker-compose.yaml
   ```

2. **Create environment configuration:**
   ```bash
   cat > .env << EOF
   CORS_LIST=["*"]
   DATABASE_TYPE=litedb
   EOF
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - API Documentation: http://localhost:11822/docs
   - Health Check: http://localhost:11822/api/health

### Local Development

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd firewallo-ui
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_LIST` | `["*"]` | CORS allowed origins (JSON array) |
| `DATABASE_TYPE` | `litedb` | Database backend (`litedb` or `mongodb`) |
| `MONGO_URI` | - | MongoDB connection string (if using MongoDB) |
| `MONGO_DB_NAME` | `firewallo` | MongoDB database name |
| `SECRET_KEY` | Auto-generated | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiration |

### Default Credentials

- **Username**: `admin`
- **Password**: `admin`
- **Email**: `admin@firewallo.io`

⚠️ **Change default credentials immediately in production!**

## 🔌 Plugin System

Firewallo's power comes from its extensible plugin architecture. Plugins are organized by category:

### Plugin Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **VPN** | VPN server/client management | WireGuard, OpenVPN, IPSec |
| **Firewall** | Firewall rule management | iptables, nftables, pfSense |
| **Monitoring** | System/network monitoring | Prometheus, Grafana, Zabbix |
| **Network** | Network service management | DNS, DHCP, Load Balancers |
| **Security** | Security tools | IDS, IPS, Vulnerability scanners |

### Installing Plugins

```bash
# Install from Git repository
curl -X POST "http://localhost:8000/api/plugins/install" \
  -H "Content-Type: application/json" \
  -d '{"source": "https://github.com/developer/openvpn-plugin.git"}'

# Install from package registry
curl -X POST "http://localhost:8000/api/plugins/install" \
  -H "Content-Type: application/json" \
  -d '{"source": "registry://prometheus-monitoring:latest"}'

# Enable a plugin
curl -X PUT "http://localhost:8000/api/plugins/openvpn/enable"
```

## 📚 API Documentation

Firewallo provides a comprehensive REST API with automatic documentation:

- **Swagger UI**: `/docs` - Interactive API documentation
- **ReDoc**: `/redoc` - Alternative API documentation
- **OpenAPI Spec**: `/openapi.json` - Machine-readable API specification

### Core API Endpoints

#### Authentication
```http
POST /api/auth/login       # User login
POST /api/auth/register    # User registration
POST /api/auth/refresh     # Token refresh
```

#### Plugin Management
```http
GET    /api/plugins/              # List plugins
POST   /api/plugins/install       # Install plugin
PUT    /api/plugins/{id}/enable   # Enable plugin
DELETE /api/plugins/{id}          # Uninstall plugin
```

#### System Management
```http
GET /api/system/health    # System health check
GET /api/system/stats     # System statistics
GET /api/system/logs      # System logs
```

### Example API Usage

```bash
# Authenticate
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Create WireGuard VPN server (requires WireGuard plugin)
curl -X POST "http://localhost:8000/api/vpn/wireguard/servers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "wg0",
    "listen_port": 51820,
    "address": "10.0.0.1/24"
  }'

# List all plugins
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/plugins/"
```

## 🛠️ Development

### Project Structure

```
firewallo-ui/
├── app/
│   ├── main.py              # Application entrypoint
│   ├── api/                 # API routes and handlers
│   │   └── routes/          # Route modules
│   ├── auth/                # Authentication system
│   ├── core/                # Core application logic
│   │   ├── config.py        # Application configuration
│   │   └── startup.py       # Startup tasks
│   ├── db/                  # Database and migrations
│   ├── plugins/             # Plugin system core
│   │   ├── base/            # Base plugin classes
│   │   ├── registry/        # Plugin registry
│   │   └── system/          # System plugins
│   └── users/               # User management
├── docs/                    # Documentation
├── tests/                   # Test suites
├── docker-compose.yaml      # Docker deployment
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

### Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: MongoDB / LiteDB (JSON files)
- **Authentication**: JWT with PyJWT
- **Networking**: WireGuard, OpenVPN (via plugins)
- **Deployment**: Docker, Docker Compose
- **Testing**: pytest, pytest-asyncio

### Running Tests

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test category
pytest tests/test_plugins/
```

### Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `pytest`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Plugin Framework](docs/PLUGIN_FRAMEWORK.md) | Plugin architecture and interfaces |
| [Plugin Development](docs/PLUGIN_DEVELOPMENT.md) | Guide for creating plugins |
| [Plugin Examples](docs/PLUGIN_EXAMPLES.md) | Example plugin implementations |
| [Database Architecture](docs/DATABASE_ARCHITECTURE.md) | Database design and structure |
| [Clean Architecture](docs/CLEAN_ARCHITECTURE.md) | Application architecture principles |
| [Web UI Implementation](docs/WEBUI_IMPLEMENTATION.md) | Web interface details |
| [Testing Guide](docs/TESTS_README.md) | Testing procedures and standards |

## 🔍 Monitoring & Maintenance

### Health Checks

```bash
# Application health
curl http://localhost:8000/api/system/health

# Database connectivity
curl http://localhost:8000/api/system/stats

# Plugin status
curl http://localhost:8000/api/plugins/status
```

### Database Migration

```bash
# Run database migrations
python -m app.db.migration app/db/metadata.json

# Create backup before migration
python -m app.db.migration --backup app/db/metadata.json
```

### Logging

Logs are available through multiple channels:
- **Application logs**: Console output (stdout/stderr)
- **System logs**: `/var/log/firewallo/` (in container)
- **Plugin logs**: Per-plugin log files
- **API access logs**: HTTP request/response logs

## 🐳 Docker Deployment

### Production Deployment

```yaml
# docker-compose.prod.yaml
version: '3.8'
services:
  firewallo:
    image: registry.gitlab.com/pietromb/firewallo-ui:latest
    restart: unless-stopped
    environment:
      - DATABASE_TYPE=mongodb
      - MONGO_URI=mongodb://mongo:27017
      - CORS_LIST=["https://your-domain.com"]
    volumes:
      - firewallo_data:/usr/src/app/data
    ports:
      - "8000:8000"
    depends_on:
      - mongo

  mongo:
    image: mongo:6
    restart: unless-stopped
    volumes:
      - mongo_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=secure_password

volumes:
  firewallo_data:
  mongo_data:
```

### Environment-Specific Configurations

- **Development**: `docker-compose.dev.yaml`
- **Testing**: `docker-compose.test.yaml`
- **Production**: `docker-compose.prod.yaml`

## 🔒 Security

### Security Features

- **JWT Authentication** with configurable expiration
- **Role-Based Access Control (RBAC)**
- **API Rate Limiting** (plugin-configurable)
- **CORS Protection** with configurable origins
- **Input Validation** using Pydantic models
- **Secure Password Hashing** with SHA-256

### Security Best Practices

1. **Change default credentials** immediately
2. **Use HTTPS** in production environments
3. **Configure strict CORS** policies
4. **Regular security updates** for dependencies
5. **Monitor API access** logs for suspicious activity
6. **Use strong JWT secrets** in production

## 🤝 Community & Support

### Getting Help

- **Documentation**: Check the `/docs` folder for detailed guides
- **API Docs**: Visit `/docs` endpoint for interactive API documentation
- **Issues**: Report bugs and request features via the issue tracker
- **Discussions**: Join community discussions for questions and ideas

### Plugin Development Community

- **Plugin Registry**: Browse and share plugins
- **Development Guide**: Follow the plugin development documentation
- **Examples**: Learn from existing plugin implementations
- **Templates**: Use plugin templates for quick development

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** team for the excellent web framework
- **WireGuard** project for the secure VPN technology
- **MongoDB** team for the flexible database solution
- **Docker** team for containerization platform
- **Contributors** who help improve Firewallo

---

<div align="center">

**[Documentation](docs/) • [API Reference](http://localhost:8000/docs) • [Plugin Registry](docs/PLUGIN_EXAMPLES.md) • [Contributing](CONTRIBUTING.md)**

*Built with ❤️ for network administrators and developers*

</div>