#!/bin/bash

# Configure the system for better performance
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=60' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=2' >> /etc/sysctl.conf

# Start PostgreSQL with optimized settings
docker-entrypoint.sh postgres -c shared_buffers=2GB -c effective_cache_size=6GB -c maintenance_work_mem=512MB -c work_mem=256MB &

# Wait for PostgreSQL to start
sleep 10

# Start Ollama
ollama serve 

# Configure Python for better performance
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=random
export PYTHONOPTIMIZE=2

# Activate the virtual environment and start the Flask application
source /app/venv/bin/activate
python -X faulthandler /app/app5.py &

# Keep the container running
tail -f /dev/null
