#!/usr/bin/env bash
# Vuelve a desplegar la última versión de `develop` en una instancia ya
# creada con bootstrap.sh (no crea nada nuevo en AWS, solo actualiza).
# Uso: ./deploy/redeploy.sh <ip-o-host> [usuario-ssh] [ruta-a-la-llave.pem]
set -euo pipefail

HOST="${1:?Uso: redeploy.sh <ip> [usuario=ec2-user] [clave.pem]}"
USUARIO="${2:-ec2-user}"
CLAVE="${3:-}"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new)
if [ -n "$CLAVE" ]; then
  SSH_OPTS+=(-i "$CLAVE")
fi

ssh "${SSH_OPTS[@]}" "$USUARIO@$HOST" "sudo bash -c '
  set -euo pipefail
  cd /opt/aml-app
  git fetch origin develop
  git reset --hard origin/develop
  /opt/aml-app/.venv-app/bin/pip install -r /opt/aml-app/app/requirements.txt
  systemctl restart aml-app.service
'"

echo "Redeploy listo en $HOST"
