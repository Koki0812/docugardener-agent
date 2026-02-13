#!/bin/bash
# DocuGardener Agent — Entrypoint
# Runs Streamlit dashboard on port $PORT (default 8080)

set -e

echo "DocuGardener Agent starting..."
echo "   Dashboard: port ${PORT:-8080}"

# Start Streamlit in foreground
exec streamlit run app.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
