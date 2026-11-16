#!/usr/bin/env bash
# User-data de la instancia Lightsail: deja la app de Hito 3 corriendo
# como servicio systemd. Se pasa con --user-data file://deploy/bootstrap.sh
# al crear la instancia (ver deploy/README.md). Idempotente: correrlo de
# nuevo no rompe nada, vuelve a instalar y reinicia el servicio.
set -euo pipefail

REPO_URL="https://github.com/Jerimy2021/Applied-Machine-Learning.git"
REPO_BRANCH="develop"
APP_DIR="/opt/aml-app"
SERVICE_USER="ec2-user"
VENV_DIR="$APP_DIR/.venv-app"

dnf install -y git python3.12 python3.12-pip

if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$REPO_BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$REPO_BRANCH"
else
  git clone --branch "$REPO_BRANCH" --depth 1 "$REPO_URL" "$APP_DIR"
fi

python3.12 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/app/requirements.txt"

chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

# server.port=80 + AmbientCapabilities abajo: streamlit corre como
# SERVICE_USER (no root) pero puede abrir el puerto 80 igual. Así la URL
# final queda en http://<ip>/ sin sufijo de puerto.
cat > /etc/systemd/system/aml-app.service <<EOF
[Unit]
Description=App Streamlit - Analisis Predictivo de Accidentes SST (Hito 3)
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/streamlit run $APP_DIR/app/Inicio.py --server.port=80 --server.address=0.0.0.0 --server.headless=true
Restart=on-failure
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now aml-app.service
