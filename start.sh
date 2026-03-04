#!/bin/bash
set -e

echo "=========================================="
echo "  Travel Assistant - Starting Services"
echo "=========================================="

# 创建日志目录
mkdir -p /var/log/supervisor
mkdir -p /var/log/nginx

# 显示环境变量状态（不显示具体值）
echo ""
echo "Environment Variables Status:"
echo "  - LLM_API_KEY: ${LLM_API_KEY:+[SET]}"
echo "  - LLM_MODEL: ${LLM_MODEL:-deepseek-v3-local-II}"
echo "  - LLM_BASE_URL: ${LLM_BASE_URL:+[SET]}"
echo "  - AMAP_API_KEY: ${AMAP_API_KEY:+[SET]}"
echo ""

# 检查必要的环境变量
if [ -z "$LLM_API_KEY" ]; then
    echo "WARNING: LLM_API_KEY is not set!"
fi

if [ -z "$AMAP_API_KEY" ]; then
    echo "WARNING: AMAP_API_KEY is not set!"
fi

echo "Starting Supervisor..."
echo "=========================================="

# 启动 Supervisor（管理 Nginx 和后端服务）
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
