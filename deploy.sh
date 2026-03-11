#!/bin/bash
# 龙虾学校部署脚本 — 在服务器上执行
set -e

APP_DIR=/opt/clawschool
DATA_DIR=$APP_DIR/data

# 创建目录
mkdir -p $APP_DIR $DATA_DIR

# 解压代码（假设 tar 已上传到 /tmp/clawschool.tar.gz）
cd $APP_DIR
tar xzf /tmp/clawschool.tar.gz --strip-components=0 2>/dev/null || true

# 安装 Python 依赖
pip3 install -r $APP_DIR/requirements.txt --quiet 2>/dev/null || pip install -r $APP_DIR/requirements.txt --quiet

# 创建 systemd service
cat > /etc/systemd/system/clawschool.service << 'EOF'
[Unit]
Description=ClawSchool Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/clawschool
Environment=CLAWSCHOOL_DATA_DIR=/opt/clawschool/data
Environment=CLAWSCHOOL_DOMAIN=school.teamolab.com
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 3210
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 配置 nginx
cat > /etc/nginx/sites-available/clawschool << 'NGINX'
server {
    listen 80;
    server_name school.teamolab.com;

    location / {
        proxy_pass http://127.0.0.1:3210;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/clawschool /etc/nginx/sites-enabled/clawschool 2>/dev/null || true

# 重载服务
systemctl daemon-reload
systemctl enable clawschool
systemctl restart clawschool
nginx -t && systemctl reload nginx

echo "部署完成！服务运行在 http://school.teamolab.com/"
systemctl status clawschool --no-pager -l
