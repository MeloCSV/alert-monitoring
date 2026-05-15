# Configuración de la Service Account `get-scheduled-alert`

## 1. Aplicar el RBAC en cada cluster

Conectarse a cada cluster y aplicar el manifiesto:

```bash
kubectl apply -f rbac-get-scheduled-alert.yaml
```

Esto crea el `ClusterRole` con permisos de lectura sobre `PrometheusRules` y el `ClusterRoleBinding` que lo asocia a la SA `get-scheduled-alert` del namespace `prometheus`.

## 2. Obtener el token de la Service Account

Ejecutar en **cada cluster** el siguiente comando para generar un token:

```bash
kubectl create token get-scheduled-alert \
  --namespace prometheus \
  --duration 8760h   # 1 año; ajustar según política del cluster
```

Guardar el token de cada cluster; se necesitará en el paso siguiente.

## 3. Obtener la URL del API server de cada cluster

```bash
kubectl cluster-info
```

La URL es la que aparece como `Kubernetes control plane is running at https://...`

## 4. (Opcional) Obtener el CA certificate del cluster

Si el cluster usa SSL verificado:

```bash
kubectl get secret \
  $(kubectl get serviceaccount get-scheduled-alert -n prometheus -o jsonpath='{.secrets[0].name}') \
  -n prometheus \
  -o jsonpath='{.data.ca\.crt}' | base64 -d
```

> En clusters Kubernetes >= 1.24 no hay secret automático; usar el CA del kubeconfig:
> ```bash
> kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d
> ```

## 5. Configurar la variable de entorno `K8S_CLUSTERS`

La aplicación lee la variable de entorno `K8S_CLUSTERS` con el siguiente formato JSON:

```json
[
  {
    "name": "cluster-1",
    "host": "https://<API_SERVER_CLUSTER_1>",
    "token": "<TOKEN_CLUSTER_1>",
    "ca_cert": "<CA_CERT_CLUSTER_1_EN_PEM>",
    "verify_ssl": true
  },
  {
    "name": "cluster-2",
    "host": "https://<API_SERVER_CLUSTER_2>",
    "token": "<TOKEN_CLUSTER_2>",
    "ca_cert": "<CA_CERT_CLUSTER_2_EN_PEM>",
    "verify_ssl": true
  }
]
```

> Si no quieres verificar SSL (entornos internos): `"verify_ssl": false` y omitir `ca_cert`.

Ejemplo de cómo exportarla en local:

```bash
export K8S_CLUSTERS='[{"name":"ocp","host":"https://api.cluster1.example.com:6443","token":"eyJhbGc...","verify_ssl":false},{"name":"utils","host":"https://api.cluster2.example.com:6443","token":"eyJhbGc...","verify_ssl":false}]'
```

En los entornos desplegados (dev, itg, pre, pro) esta variable se inyecta a través del sistema de secretos del entorno (Vault, Kubernetes Secret, etc.).

## 6. Verificar que funciona

Arrancar la aplicación y llamar al endpoint de sincronización:

```bash
curl -X POST http://localhost:8080/alerts/sync
```

En los logs debe aparecer:
```
INFO  Recogiendo PrometheusRules del cluster cluster-1
INFO  Recogiendo PrometheusRules del cluster cluster-2
```
