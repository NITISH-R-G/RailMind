import re

with open('backend/api/main.py', 'r') as f:
    content = f.read()

# Replace os.getenv calls with settings calls
content = content.replace('os.getenv("ADMIN_USERNAME", "admin")', 'settings.ADMIN_USERNAME')
content = content.replace('os.getenv("ADMIN_PASSWORD")', 'settings.ADMIN_PASSWORD')
content = content.replace('os.getenv("RAILWAYS_API_KEY", "mock_key")', 'settings.RAILWAYS_API_KEY')
content = content.replace('os.getenv("RAILWAYS_API_KEY", "")', 'settings.RAILWAYS_API_KEY')
content = content.replace('os.getenv("RAPIDAPI_KEY", "")', '""') # RAPIDAPI_KEY is not used much
content = content.replace('os.getenv("TWILIO_ACCOUNT_SID", "")', 'settings.TWILIO_ACCOUNT_SID')
content = content.replace('os.getenv("TWILIO_AUTH_TOKEN", "")', 'settings.TWILIO_AUTH_TOKEN')
content = content.replace('os.getenv("MAINTENANCE_PHONE", "+919651058174")', 'settings.MAINTENANCE_PHONE')
content = content.replace('os.getenv("OPERATIONS_PHONE", "+919651058174")', 'settings.OPERATIONS_PHONE')
content = content.replace('os.getenv("STATION_PHONE", "+919651058174")', 'settings.STATION_PHONE')

# Add Prometheus imports and endpoint
prom_imports = """
from prometheus_client import make_asgi_app
from ..config import settings
"""

if "from prometheus_client import make_asgi_app" not in content:
    content = content.replace('from ..services.db_client import db_client', f'from ..services.db_client import db_client{prom_imports}')

prom_route = """
# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
"""

if "# Prometheus metrics endpoint" not in content:
    content = content.replace('app.include_router(router, prefix="/api")', f'{prom_route}\napp.include_router(router, prefix="/api")')

with open('backend/api/main.py', 'w') as f:
    f.write(content)
