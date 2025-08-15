# Architecture Documentation

This directory contains comprehensive documentation about Firewallo's system architecture, design patterns, and database structure.

## 📚 Documentation Contents

### [Clean Architecture](./CLEAN_ARCHITECTURE.md)
Detailed documentation of Firewallo's clean architecture implementation, including:
- Architecture principles and patterns
- Layer separation and responsibilities
- Dependency management
- Code organization best practices

### [Database Architecture](./DATABASE_ARCHITECTURE.md)
Complete database design and structure documentation, covering:
- Database schema organization
- Plugin data storage patterns
- Migration strategies
- Backend support (LiteDB and MongoDB)

## 🏗️ System Overview

Firewallo follows a clean, modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│            API Layer (FastAPI)          │
├─────────────────────────────────────────┤
│          Service Layer (Business)       │
├─────────────────────────────────────────┤
│        Repository Layer (Data)          │
├─────────────────────────────────────────┤
│     Database Layer (LiteDB/MongoDB)     │
└─────────────────────────────────────────┘
```

## 🔑 Key Architectural Principles

1. **Separation of Concerns** - Each layer has a specific responsibility
2. **Dependency Injection** - Loose coupling between components
3. **Plugin Architecture** - Extensible design for adding new functionality
4. **Database Abstraction** - Support for multiple backend storage systems
5. **API-First Design** - RESTful API as the primary interface

## 📊 Architecture Diagrams

The main documentation includes visual representations of:
- Application Architecture
- Base Infrastructure
- Application Manifest
- Remote Management

These diagrams are available in the [main documentation](../INDEX.md#system-architecture-diagrams).

## 🔗 Related Documentation

- [Plugin Framework](../plugins/FRAMEWORK.md) - Plugin system architecture
- [WebUI Implementation](../webui/IMPLEMENTATION.md) - Frontend architecture
- [Testing Guide](../testing/README.md) - Testing architecture and strategies

## 📝 Quick Reference

### Database Structure
```
firewallo/
├── plugins/          # Plugin-specific data
│   ├── vpn/         # VPN plugins data
│   ├── firewall/    # Firewall plugins data
│   ├── monitoring/  # Monitoring plugins data
│   └── network/     # Network plugins data
├── core/            # Core system data
│   ├── system/      # System configuration
│   ├── config/      # Application config
│   └── logs/        # System logs
└── auth/            # Authentication data
    ├── users/       # User accounts
    └── rbac/        # Roles and permissions
```

### API Architecture
- **RESTful Design** - Standard HTTP methods and status codes
- **JWT Authentication** - Secure token-based auth
- **Automatic Documentation** - OpenAPI/Swagger integration
- **CORS Support** - Configurable cross-origin support

## 🚀 Getting Started

1. Review the [Clean Architecture](./CLEAN_ARCHITECTURE.md) documentation to understand the system design
2. Explore the [Database Architecture](./DATABASE_ARCHITECTURE.md) for data storage patterns
3. Check the [main documentation](../INDEX.md) for complete system overview

## 📚 Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [MongoDB Documentation](https://docs.mongodb.com/)