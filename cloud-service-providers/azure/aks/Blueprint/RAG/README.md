# Get Started With NVIDIA RAG Blueprint (v2.0)

This document suppliment [official instructions](https://github.com/NVIDIA-AI-Blueprints/rag/blob/main/docs/quickstart.md#deploy-with-helm-chart) with 3 enhancements.

- explain how to upgrade nv-ingest version to latest version
- explain how to use time slice to save 4 GPUs
- explain how to use this Blueprint in WSL2 environment

## Architecture
![](diagram.jpg)
## Create 2 GPU nodepools

- frontend - 2x nodes, 4x GPUs (aks-gpunp2h100-03571910-vmss000002, aks-gpunp2h100-03571910-vmss000003)
- backend - 1X node, 1x GPUs (aks-gpunp1h100-34045329-vmss000002)time-slicing to 6

![](gpunodepool.jpg)

## 

### Export NGC API Key

```
export NGC_API_KEY="your_ngc_api_key"
export NVIDIA_API_KEY="nvapi-*"
```

### Verify that you have a default storage class available in the cluster for PVC provisioning. 

```
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.26/deploy/local-path-storage.yaml
kubectl get pods -n local-path-storage
kubectl get storageclass
```

### If the local path storage class is not set as default, it can be made default by using the following command.

```
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

### Add NVIDIA Helm Repositories

```
helm repo add nvidia-nim https://helm.ngc.nvidia.com/nim/nvidia/ --username='$oauthtoken' --password=$NGC_API_KEY
helm repo add nim https://helm.ngc.nvidia.com/nim/ --username='$oauthtoken' --password=$NGC_API_KEY
helm repo add nemo-microservices https://helm.ngc.nvidia.com/nvidia/nemo-microservices --username='$oauthtoken' --password=$NGC_API_KEY
helm repo add baidu-nim https://helm.ngc.nvidia.com/nim/baidu --username='$oauthtoken' --password=$NGC_API_KEY
```

### Update Helm Repositories

```
helm repo update
```

```
git clone https://github.com/NVIDIA-AI-Blueprints/rag.git
cd deploy/helm/
```

### Update Dependencies for RAG Server

```
helm dependency update rag-server/charts/ingestor-server
helm dependency update rag-server
```
### Update nv-ingest version (Optional)

Current nv-ingest version is 25.3.0.  You can upgrade to 25.4.2 with the following steps.
update rag-server/values.yaml, change nv-ingest version from 25.3.0 to 25.4.2 (line 181)

### Assign pods to proper nodepool

#### for backend
```
rm -rf ingestor-server
tar -xvf ingestor-server-v2.0.0.tgz
rm ingestor-server-v2.0.0.tgz
```
 - rag-server/charts/ingestor-server/charts/nv-ingest/charts/milvus/values.yaml
 - rag-server/charts/ingestor-server/charts/nv-ingest/charts/nvidia-nim-paddleocr/values.yaml
 - rag-server/charts/ingestor-server/charts/nv-ingest/charts/nvidia-nim-nemoretriever-page-elements-v2/values.yaml
 - rag-server/charts/ingestor-server/charts/nv-ingest/charts/nvidia-nim-nemoretriever-graphic-elements-v1/values.yaml
 - rag-server/charts/ingestor-server/charts/nv-ingest/charts/nvidia-nim-nemoretriever-table-structure-v1/values.yaml

```
# change 
# nodeSelector: {}  # likely best to set this to `nvidia.com/gpu.present: "true"` depending on cluster setup
# into
# nodeSelector:
#   nvidia.com/gpu.sharing-strategy: "time-slicing"
```
#### for frontend
```
tar -xvf nvidia-nim-llama-32-nv-embedqa-1b-v2-1.5.0.tgz
rm nvidia-nim-llama-32-nv-embedqa-1b-v2-1.5.0.tgz
tar -xvf text-reranking-nim-1.3.0.tgz
rm text-reranking-nim-1.3.0.tgz
```
- rag-server/charts/nvidia-nim-llama-32-nv-embedqa-1b-v2/values.yaml
- rag-server/charts/text-reranking-nim/values.yaml
```
# change 
# nodeSelector: {}  # likely best to set this to `nvidia.com/gpu.present: "true"` depending on cluster setup
# into
# nodeSelector:
#   kubernetes.io/hostname: "aks-gpunp2h100-03571910-vmss000002"
``` 
```
tar -xvf nim-llm-1.3.0.tgz
rm nim-llm-1.3.0.tgz
```
- rag-server/charts/nim-llm/values.yaml
```
# change 
# nodeSelector: {}  # likely best to set this to `nvidia.com/gpu.present: "true"` depending on cluster setup
# into
# nodeSelector:
#   kubernetes.io/hostname: "aks-gpunp2h100-03571910-vmss000003"
```

### Create a namespace for the deployment:

```
kubectl create namespace rag
```

### Deploying End to End RAG Server + Ingestor Server (NV-Ingest)

```
helm install rag -n rag rag-server/ \
--set imagePullSecret.password=$NVIDIA_API_KEY \
--set ngcApiSecret.password=$NVIDIA_API_KEY
```
![](./pods.jpg)
### Port forwarding for UI
```
kubectl port-forward -n rag service/rag-frontend 3000:3000 --address 0.0.0.0
```
![](GUI.jpg)

### Enabling Observability with the chart 

To enable tracing and view the Zipkin or Grafana UI, follow these steps:

#### Enable OpenTelemetry Collector, Zipkin and Prometheus stack

- Update the values.yaml file to enable the OpenTelemetry Collector and Zipkin:

```
env:
# ... existing code ...
APP_TRACING_ENABLED: "True"

# ... existing code ...
serviceMonitor:
enabled: true
opentelemetry-collector:
enabled: true
# ... existing code ...

zipkin:
enabled: true
kube-prometheus-stack:
enabled: true
```
- Deploy the Changes:
Redeploy the Helm chart to apply these changes:
```
helm uninstall rag -n rag
helm install rag -n rag rag-server/ \
--set imagePullSecret.password=$NVIDIA_API_KEY \
--set ngcApiSecret.password=$NVIDIA_API_KEY
```
#### Port-Forwarding to Access UIs
- Zipkin UI:
Run the following command to port-forward the Zipkin service to your local machine:
```
kubectl port-forward -n rag service/rag-zipkin 9411:9411 --address 0.0.0.0
```
- Grafana UI:
run the following command to port-forward the Grafana service:
```
kubectl port-forward -n rag service/rag-grafana 3000:80 --address 0.0.0.0
```
Access the Grafana UI at http://localhost:3000 using the default credentials (admin/admin).
#### Creating a Dashboard in Grafana
- Upload JSON to Grafana:

Navigate to the Grafana UI at http://localhost:3000.
Log in with the default credentials (admin/admin).
Go to the "Dashboards" section and click on "Import".
Upload the JSON file located in the deploy/config directory.

- Configure the Dashboard:

After uploading, select the data source that the dashboard will use. Ensure that the data source is correctly configured to pull metrics from your Prometheus instance.

- Save and View:

Once the dashboard is configured, save it and start viewing your metrics and traces.

### WSL2
if you wsl,  find the ip of your wsl, then hit https://"ip of your wsl":3000 from your windows browser
```
josephw@JosephDesktop:~$ ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
172.19.164.145
```
### Set up work pod for batch ingestion

Detail instructions  can be forund in [NeMo Retriever Extraction](../../NemoRetrieverExtraction/README.md)
