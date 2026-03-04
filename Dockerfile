# ==========================================
# 阶段1: 构建前端
# ==========================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 设置 npm 镜像源
RUN npm config set registry https://registry.npmmirror.com/

# 复制 package.json 和 lock 文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci --silent

# 复制前端源码
COPY frontend/ ./

# 设置生产环境 API 地址（使用空值，让前端使用相对路径通过 Nginx 代理）
# 必须在 COPY 之后覆盖 .env 文件
RUN echo "VITE_API_BASE_URL=" > .env.production

# 构建生产版本（Vite 在 production 模式下会优先读取 .env.production）
RUN npm run build

# ==========================================
# 阶段2: 生产运行环境
# ==========================================
FROM python:3.11-slim

# 安装 Nginx 和 Supervisor（使用阿里云源加速）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 复制后端代码
COPY backend/ ./backend/

# 安装 Python 依赖（使用阿里云 PyPI 镜像）
RUN pip install --no-cache-dir -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 从前端构建阶段复制静态文件
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 复制 Supervisor 配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 复制启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 启动命令
CMD ["/start.sh"]
