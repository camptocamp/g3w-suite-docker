#!/bin/bash
# Entrypoint script fro deploy production
# ---------------------------------------

# Gis3W Sign
figlet -t "G3W-SUITE Docker by Gis3w"

# Start XVfb
if [[  -f /tmp/.X99-lock ]]; then
  rm /tmp/.X99-lock
fi
Xvfb :99 -screen 0 640x480x24 -nolisten tcp &
export DISPLAY=:99
export QGIS_SERVER_PARALLEL_RENDERING=1

# Start
cd /code/g3w-admin

# Setup once
/code/ci_scripts/setup_suite.sh

if [ ! -f /shared-volume/gunicorn.conf.py ]; then
  cat > /shared-volume/gunicorn.conf.py << EOF
import os
limit_request_fields = 0
error_logfile        = '-'
log_level            = 'info'
timeout              = os.getenv('G3WSUITE_GUNICORN_TIMEOUT', 120)
workers              = os.getenv('G3WSUITE_GUNICORN_NUM_WORKERS', 8)
max_requests         = os.getenv('G3WSUITE_GUNICORN_MAX_REQUESTS', 200)
bind                 = '0.0.0.0:8000'
reload               = False # os.path.ismount('/code')
EOF
fi

# Start Django server
gunicorn base.wsgi:application -c /shared-volume/gunicorn.conf.py
