#!/bin/bash
# DocuGardener Agent — Entrypoint
# Uses nginx to route:
#   /webhook  -> Flask (port 8081)
#   /*        -> Streamlit (port 8501)
# External port: $PORT (default 8080)

set -e

echo "DocuGardener Agent starting..."
echo "   External port: ${PORT:-8080}"
echo "   Streamlit:     port 8501"
echo "   Webhook:       port 8081"

# Create nginx config
cat > /etc/nginx/sites-available/default << 'NGINX_CONF'
server {
    listen 8080;

    location /webhook {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8081;
    }

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
NGINX_CONF

# Start nginx
nginx
echo "   nginx started"

# Start Flask webhook in background
python webhook.py &
echo "   Webhook started"

# Start Streamlit (foreground)
exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
