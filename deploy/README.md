# Desplegar la app (Hito 3) en AWS Lightsail

Por qué Lightsail y no App Runner/ECS: Streamlit depende de una conexión
WebSocket persistente para cada interacción, y el proxy de App Runner no
soporta de forma confiable el *upgrade* a WebSocket (ver discusión en la
comunidad de Streamlit). Una instancia Lightsail es una VM real: no hay
proxy gestionado de por medio, y la facturación es plana mensual (no por
request), así que una URL pública sin login no puede generar una
sorpresa en la factura.

Todo lo de acá es un paso **operativo manual**, no algo que un PR
"contenga": crear infraestructura real en una cuenta de AWS no se
automatiza en CI.

## 0. Antes de empezar

- Un profile de AWS CLI ya configurado localmente (`~/.aws/credentials`),
  con permisos sobre Lightsail. En los comandos de abajo, agregar
  `--profile <tu-perfil>` a cada uno (o exportar `AWS_PROFILE=<tu-perfil>`
  una vez y omitirlo en el resto).
- El repo es público: no hace falta ninguna credencial de GitHub para
  que la instancia lo clone.

## 1. Crear la instancia

Elegir una zona de disponibilidad y el bundle (tamaño) más chico que
tenga **al menos 1 GB de RAM** (el bundle de 512 MB se queda corto:
Streamlit + pandas + scikit-learn ya importados usan 150-250 MB solo de
overhead). Los IDs de bundle cambian con el tiempo, confirmar los
disponibles:

```bash
aws lightsail get-bundles --query "bundles[?ramSizeInGb>=\`1\`] | [0:5]"
aws lightsail get-blueprints --query "blueprints[?blueprintId=='amazon_linux_2023']"
```

Crear la instancia (reemplazar `<bundle-id>` por el elegido arriba, y la
zona si hace falta):

```bash
aws lightsail create-instances \
  --instance-names aml-sst-app \
  --availability-zone us-east-1a \
  --blueprint-id amazon_linux_2023 \
  --bundle-id <bundle-id> \
  --user-data file://deploy/bootstrap.sh
```

Esperar a que esté `running`:

```bash
aws lightsail get-instance --instance-name aml-sst-app --query "instance.state.name"
```

## 2. Abrir el puerto 80 al público

```bash
aws lightsail put-instance-public-ports \
  --instance-name aml-sst-app \
  --port-infos fromPort=80,toPort=80,protocol=TCP
```

## 3. IP estática (para que la URL no cambie si se reinicia la instancia)

```bash
aws lightsail allocate-static-ip --static-ip-name aml-sst-ip
aws lightsail attach-static-ip --static-ip-name aml-sst-ip --instance-name aml-sst-app
aws lightsail get-static-ip --static-ip-name aml-sst-ip --query "staticIp.ipAddress"
```

La URL final es `http://<esa-ip>/`. Sin TLS/dominio por defecto (nadie
pidió uno); si aparece un dominio más adelante, agregar Caddy como proxy
es un paso aparte, no bloquea esto.

**Importante:** `bootstrap.sh` tarda uno o dos minutos en terminar de
instalar y levantar el servicio después de que la instancia pasa a
`running`. Si la URL no responde todavía, esperar y reintentar antes de
asumir que algo falló.

## 4. Verificar

```bash
curl -I http://<esa-ip>/
```
Debería responder `200 OK`. Probar también desde un navegador en otra
red (no solo desde la misma conexión), para confirmar que es accesible
públicamente.

Si no responde, revisar el log de arranque (`user-data`) por SSH:
```bash
aws lightsail download-default-key-pair --query "privateKeyBase64" --output text | base64 -d > aml-sst-key.pem
chmod 600 aml-sst-key.pem
ssh -i aml-sst-key.pem ec2-user@<esa-ip> "sudo journalctl -u aml-app.service -n 50"
```

## 5. Redesplegar después de mergear cambios nuevos a `develop`

```bash
./deploy/redeploy.sh <esa-ip> ec2-user aml-sst-key.pem
```

## 6. Apagar todo (después de que se evalúe el hito, para no seguir pagando)

```bash
aws lightsail delete-instance --instance-name aml-sst-app
aws lightsail release-static-ip --static-ip-name aml-sst-ip
```
