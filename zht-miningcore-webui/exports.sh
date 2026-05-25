mkdir -p /home/umbrel/.miningcore
chown -R 1000:1000 /home/umbrel/.miningcore

cat > /home/umbrel/.miningcore/nginx-webui.conf << 'NGINXEOF'
server {
    listen 8080;

    # Block support / donate page
    location ~* ^/(support|donate|supportme|support-me|throne|tip) {
        return 404;
    }

    location / {
        proxy_pass http://web:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Accept-Encoding "";

        # WebSocket / SignalR support for Blazor Server
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        # Replace Retro Mike branding with ZHT
        sub_filter_once off;
        sub_filter_types text/html;
        sub_filter 'Retro Mike' 'ZHT';
        sub_filter 'RetroMike' 'ZHT';
    }
}
NGINXEOF
