# Firewallo Web UI

A modern Bootstrap-based web interface for the Firewallo firewall management system.

## Overview

The Firewallo Web UI provides a user-friendly interface for managing your firewall system, including:

- **Dashboard**: System overview with real-time statistics
- **Plugin Management**: Install, configure, and manage firewall plugins
- **Firewall Rules**: View and manage firewall rules
- **System Monitoring**: CPU, memory, disk, and network monitoring
- **Activity Logs**: Recent system activity and security events
- **User Authentication**: Secure login system

## Features

### 🎨 Modern UI
- Bootstrap 5 responsive design
- Dark/light theme support
- Mobile-friendly interface
- Real-time data updates

### 📊 Dashboard
- System health monitoring
- Resource usage graphs
- Recent activity timeline
- Quick action buttons

### 🔌 Plugin Management
- Browse available plugins
- Install from file, URL, or Git repository
- Enable/disable plugins
- Plugin configuration interface

### 🔒 Security
- JWT-based authentication
- Session management
- CSRF protection
- Secure API endpoints

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd firewallo-ui
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Development Mode

1. **Start the FastAPI development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the web interface:**
   - Open your browser and navigate to: `http://localhost:8000`
   - You'll be redirected to the dashboard

3. **API Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Production Mode

1. **Install a production ASGI server (if not already installed):**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn:**
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Docker (Alternative)

1. **Build the Docker image:**
   ```bash
   docker build -t firewallo-ui .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 firewallo-ui
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root to configure the application:

```env
# Application settings
SECRET_KEY=your-secret-key-here
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database settings (if using MongoDB)
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=firewallo

# Authentication settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Plugin settings
PLUGIN_DIRECTORY=./plugins
AUTO_LOAD_PLUGINS=true
```

### Static Files

Static files (CSS, JavaScript, images) are served from the `app/static/` directory:
- CSS files: `app/static/css/`
- JavaScript files: `app/static/js/`
- Images: `app/static/img/`

### Templates

HTML templates are located in the `app/templates/` directory and use Jinja2 templating.

## Usage

### First Time Setup

1. **Access the login page** at `http://localhost:8000/login`
2. **Default credentials** (in development):
   - Username: `admin@firewallo.local`
   - Password: `admin` (should be changed in production)

### Navigation

- **Dashboard**: Overview of system status and recent activity
- **Plugins**: Manage installed plugins and install new ones
- **Rules**: View and configure firewall rules
- **Logs**: View system logs and activity
- **Settings**: Configure system settings and user preferences

### Plugin Management

1. Navigate to the **Plugins** page
2. **Install new plugins** using one of three methods:
   - Upload a ZIP file
   - Install from a URL
   - Clone from a Git repository
3. **Enable/disable plugins** using the toggle switches
4. **Configure plugins** by clicking the gear icon

### API Usage

The web UI is built on top of a REST API. You can interact with the API directly:

```bash
# Get system statistics
curl http://localhost:8000/api/system/stats

# List plugins
curl http://localhost:8000/api/plugins/

# Get recent activity
curl http://localhost:8000/api/system/activity/recent
```

## Development

### Project Structure

```
firewallo-ui/
├── app/
│   ├── api/
│   │   └── routes/          # API route handlers
│   ├── core/               # Core application configuration
│   ├── plugins/            # Plugin system
│   ├── static/             # Static files (CSS, JS, images)
│   ├── templates/          # Jinja2 HTML templates
│   └── main.py            # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
└── README.md              # This file
```

### Adding New Pages

1. **Create a new template** in `app/templates/`
2. **Add a route handler** in `app/api/routes/gui.py`
3. **Add navigation links** in `app/templates/base.html`
4. **Add API endpoints** if needed in appropriate route files

### Customizing Styles

1. **Edit** `app/static/css/custom.css` for custom styles
2. **Add new CSS files** and include them in the base template
3. **Use Bootstrap utility classes** for quick styling

### Adding JavaScript Functionality

1. **Add code to** `app/static/js/common.js` for shared functionality
2. **Create page-specific JS files** and include them in templates
3. **Use the global API client** (`window.api`) for making requests

## Troubleshooting

### Common Issues

1. **Port 8000 already in use:**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

2. **Module not found errors:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Static files not loading:**
   - Check that the `app/static/` directory exists
   - Verify file permissions
   - Check browser console for 404 errors

4. **Database connection errors:**
   - Verify MongoDB is running (if using MongoDB)
   - Check database configuration in `.env`

5. **Plugin loading errors:**
   - Check plugin directory permissions
   - Verify plugin manifest files
   - Check application logs

### Logging

Logs are written to the console by default. For production, configure proper logging:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Performance

For better performance in production:
- Use a production ASGI server (Gunicorn with Uvicorn workers)
- Configure reverse proxy (Nginx)
- Enable static file caching
- Use a production database
- Enable gzip compression

## Security Considerations

- Change default credentials immediately
- Use strong secret keys
- Enable HTTPS in production
- Regularly update dependencies
- Implement rate limiting for API endpoints
- Use secure session cookies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Include your license information here]

## Support

For support and questions:
- Check the API documentation at `/docs`
- Review the application logs
- Create an issue in the project repository

---

**Note**: This is a development interface. For production use, ensure proper security measures are in place, including authentication, authorization, and secure communication protocols.