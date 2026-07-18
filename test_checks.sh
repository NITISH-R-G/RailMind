export DEMO_MODE=true
export MONGODB_URI="mongodb://localhost:27017/railmind"
export REDIS_URL="redis://localhost:6379"
PYTHONPATH=. python3 -m pytest backend/tests/ -v
