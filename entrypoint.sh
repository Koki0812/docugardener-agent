#!/bin/bash
# DocuGardener Agent — Entrypoint
# Uses nginx to route:
#   /webhook  → Flask (port 8081)
#   /*        → Streamlit (port 8501)
# External port: $PORT (default 8080)

set -e

echo "DocuGardener Agent starting..."
echo "   External port: ${PORT:-8080}"
echo "   Streamlit:     port 8501"
echo "   Webhook:       port 8081"

# Install nginx
apt-get update -qq && apt-get install -y -qq nginx > /dev/null 2>&1
echo "   nginx installed"

# Create nginx config
cat > /etc/nginx/sites-available/default << EOF
server {
    listen ${PORT:-8080};

    # Webhook endpoint -> Flask
    location /webhook {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }

    # Health check for webhook
    location /health {
        proxy_pass http://127.0.0.1:8081;
    }

    # Everything else -> Streamlit
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # Streamlit specific paths
    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

# Start nginx
nginx
echo "   nginx started"

# Start Flask webhook in background
python webhook.py &
WEBHOOK_PID=$!
echo "   Webhook started (PID: $WEBHOOK_PID)"

# Start Streamlit in foreground
exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
