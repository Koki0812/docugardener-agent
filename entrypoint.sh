#!/bin/bash
# DocuGardener Agent — Entrypoint
# Runs Flask webhook (port 8081) + Streamlit dashboard (port $PORT)
# Both processes share the same container.

set -e

echo "🌿 DocuGardener Agent starting..."
echo "   Dashboard: port ${PORT:-8080}"
echo "   Webhook:   port 8081"

# Start Flask webhook in background
python webhook.py &
WEBHOOK_PID=$!
echo "   Webhook PID: $WEBHOOK_PID"

# Start Streamlit in foreground
exec streamlit run app.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
