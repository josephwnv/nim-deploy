# Run.AI on AKS



## Create name space
```
kubectl create namespace runai-backend
```

## Create ingress controller

```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace nginx-ingress --create-namespace --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=healthz
```
### For Azure Local
```
    az network public-ip create \
      --resource-group <resource-group-name> \
      --name <public-ip-name> \
      --allocation-method Static \
      --sku Standard \
      --zone 1 # Optional: For zonal redundancy
      
kubectl edit svc -n nginx-ingress    nginx-ingress-ingress-nginx-controller
...
    metadata:
      name: my-app-service
      annotations:
        service.beta.kubernetes.io/azure-load-balancer-resource-group: <resource-group-name> # If Public IP is in a different resource group
        service.beta.kubernetes.io/azure-load-balancer-public-ip: <public-ip-name> # Name of the pre-existing Public IP

spec:
  allocateLoadBalancerNodePorts: true
  clusterIP: 10.111.66.236
  clusterIPs:
  - 10.111.66.236
  externalIPs:
  - 192.168.10.202
  externalTrafficPolicy: Cluster
  internalTrafficPolicy: Cluster
...
```
# Find the public IP
```
kubectl get svc -A

```
# Find the public IP name 
az network public-ip list -g mc_<resource group>_<cluster name>_<region> --query "[?ipAddress=='<public ip of load balancer>'].name" -o tsv

# Add DNS Label
```
az network public-ip update --dns-name <prefix> -g mc_<resource group>_<cluster name>_<region> -n <public ip name> --allocation-method Static
az network public-ip show   --resource-group mc_<resource group>_<cluster name>_<region>   --name <public ip name>
```
## Create a Cert

```
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes -keyout <prefix>.<region>.cloudapp.azure.com.key -out <prefix>.<region>.cloudapp.azure.com.crt -subj "/CN=<prefix>.<region>.cloudapp.azure.com" -addext "subjectAltName=DNS:<prefix>.<region>.cloudapp.azure.com,DNS:*.<prefix>.<region>.cloudapp.azure.com,IP:<public ip of load balancer>" 
```

## Create a K8 secret for TLS
```
kubectl create secret tls runai-backend-tls -n runai-backend --cert=<prefix>.<region>.cloudapp.azure.com.crt --key=<prefix>.<region>.cloudapp.azure.com.key

cat <prefix>.<region>.cloudapp.azure.com.crt <prefix>.<region>.cloudapp.azure.com.key > <prefix>.<region>.cloudapp.azure.com.pem
kubectl -n runai create secret generic runai-ca-cert --from-file=runai-ca.pem=<ca_bundle_path>
kubectl label secret runai-ca-cert -n runai run.ai/cluster-wide=true run.ai/name=runai-ca-cert --overwrite
```




##

kubectl create secret docker-registry runai-reg-creds  \
--docker-server=https://runai.jfrog.io \
--docker-username=self-hosted-image-puller-prod \
--docker-password=<TOKEN> \
--docker-email=support@run.ai \
--namespace=runai-backend

## Install the Control Plane
```
helm repo add runai-backend https://runai.jfrog.io/artifactory/cp-charts-prod
helm repo update
helm upgrade -i runai-backend -n runai-backend runai-backend/control-plane --set global.domain=<prefix>.<region>.cloudapp.azure.com
```
## install Prometheus
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
    -n monitoring --create-namespace --set grafana.enabled=false
```
## Login

- https://<prefix>.<region>.cloudapp.azure.com
- default user is: test@run.ai and default password is Abcd!234
- ![](./images/login.jpg)

- ![](./images/install.jpg)


```
# Follow GUI instruction
helm repo add runai https://runai.jfrog.io/artifactory/api/helm/run-ai-charts --force-update
helm repo update
helm upgrade -i runai-cluster runai/runai-cluster -n runai \
--set controlPlane.url=runai.eastus.cloudapp.azure.com \
--set controlPlane.clientSecret=EeTimRDekBO7CuILYpvlVcNANtCJHQox \
--set cluster.uid=349e9937-2250-4fce-8726-f562bc44fefd \
--set global.customCA.enabled=true \  ## <-------------------
--set cluster.url=https://runai.eastus.cloudapp.azure.com --version="2.23.10" --create-namespace
```
##  To Add remote cluster

- Create ingress controller
- install Prometheus
- Create a Cert
- Create a K8 secret for TLS

```
# At remode AKS
kubectl -n runai create secret generic runai-ca-cert --from-file=runai-ca.pem=<ca_bundle_path of control plan cluster>
kubectl label secret runai-ca-cert -n runai run.ai/cluster-wide=true run.ai/name=runai-ca-cert --overwrite
# using Creating Cert
kubectl create secret tls runai-cluster-domain-tls-secret -n runai \    
  --cert /path/to/fullchain.pem  \ # Replace /path/to/fullchain.pem with the actual path to your TLS certificate    
  --key /path/to/private.pem # Replace /path/to/private.pem with the actual path to your private key
```
- From Run.AI GUI --> resouces --> Add cluster. Follow instruction

## Testing

```
kubectl apply -f corednsms.yaml
kubectl --namespace kube-system rollout restart deployment coredns
```

### NCCL-test

```
kubectl apply -f ib-test-A100.yaml
```

### inference workflow

## [Install Knative](https://run-ai-docs.nvidia.com/self-hosted/getting-started/installation/system-requirements#inference)

helm repo add knative-operator https://knative.github.io/operator
# helm install knative-operator --create-namespace --namespace knative-operator knative-operator/knative-operator

kubectl apply -f https://github.com/knative/operator/releases/download/knative-v1.18.0/operator.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.18.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.18.0/serving-core.yaml
kubectl apply -f https://github.com/knative-extensions/net-kourier/releases/download/knative-v1.18.0/kourier.yaml
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
kubectl --namespace kourier-system get service kourier

kubectl patch configmap/config-domain \
      --namespace knative-serving \
      --type merge \
      --patch '{"data":{"k8.ignite.net":""}}'

kubectl patch configmap/config-autoscaler \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"enable-scale-to-zero":"true"}}' && \
kubectl patch configmap/config-features \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"kubernetes.podspec-schedulername":"enabled","kubernetes.podspec-nodeselector": "enabled","kubernetes.podspec-affinity":"enabled","kubernetes.podspec-tolerations":"enabled","kubernetes.podspec-volumes-emptydir":"enabled","kubernetes.podspec-securitycontext":"enabled","kubernetes.containerspec-addcapabilities":"enabled","kubernetes.podspec-persistent-volume-claim":"enabled","kubernetes.podspec-persistent-volume-write":"enabled","multi-container":"enabled","kubernetes.podspec-init-containers":"enabled","kubernetes.podspec-fieldref":"enabled"}}'

## Enabling Host-Based Routing

### Create a DNS Zone for custom Domain
az network dns zone create -g jwu-nvaie -n jwu-netapp2.westus2.cloudapp.azure.com

### Assign Variables
tenantid=$(az account show --subscription "NV-WWFO" --query tenantId --output tsv)
subscriptionid=$(az account show --query id -o tsv)
UserClientId=$(az aks show --name jwu-netapp2 --resource-group jwu-nvaie --query identityProfile.kubeletidentity.clientId -o tsv)
DNSID=$(az network dns zone show --name jwu-netapp2.westus2.cloudapp.azure.com --resource-group jwu-nvaie --query id -o tsv)
### Assign managed identity of cluster’s node pools DNS Zone Contributor rights on to Custom Domain DNS zone.
az role assignment create --assignee $UserClientId --role 'DNS Zone Contributor' --scope $DNSID

### Add the Helm repository
# helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm repo update

### Use Helm to deploy an External DNS
### https://kubernetes-sigs.github.io/external-dns/latest/docs/tutorials/azure/#internal-load-balancer

kubectl create secret generic azure-config-file --namespace "nginx-ingress" --from-file /local/path/to/azure.json
kubectl apply -n nginx-ingress -f external-dns.yaml 

kubectl create secret generic azure-config-file --namespace "default" --from-file /local/path/to/azure.json
helm upgrade --install external-dns external-dns/external-dns --version 1.17.0 --namespace nginx-ingress --set provider=azure --set txtOwnerId=jwu-netapp2 --set policy=sync --set azure.resourceGroup=jwu-nvaie --set azure.tenantId=$tenantid --set azure.subscriptionId=$subscriptionid --set azure.useManagedIdentityExtension=true --set azure.userAssignedIdentityID=$UserClientId

helm install external-dns bitnami/external-dns --namespace nginx-ingress --set provider=azure --set txtOwnerId=jwu-netapp2 --set policy=sync --set azure.resourceGroup=jwu-nvaie --set azure.tenantId=$tenantid --set azure.subscriptionId=$subscriptionid --set azure.useManagedIdentityExtension=true --set azure.userAssignedIdentityID=$UserClientId





openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes -keyout <prefix>.<region>.cloudapp.azure.com.key -out <prefix>.<region>.cloudapp.azure.com.crt -subj "/CN=<prefix>.<region>.cloudapp.azure.com" -addext "subjectAltName=DNS:<prefix>.<region>.cloudapp.azure.com,DNS:*.<prefix>.<region>.cloudapp.azure.com,IP:<public ip of load balancer>" 

kubectl create secret tls runai-cluster-domain-star-tls-secret -n runai \    
  --cert /path/to/fullchain.pem  \ # Replace /path/to/fullchain.pem with the actual path to your TLS certificate    
  --key /path/to/private.pem # Replace /path/to/private.pem with the actual path to your private key

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: runai-cluster-domain-star-ingress
  namespace: runai
spec:
  ingressClassName: nginx
  rules:
  - host: '*.<CLUSTER_URL>'
  tls:
  - hosts:
    - '*.<CLUSTER_URL>'
    secretName: runai-cluster-domain-star-tls-secret

kubectl apply -f <filename>

kubectl patch RunaiConfig runai -n runai --type="merge" \    
    -p '{"spec":{"global":{"subdomainSupport": true}}}' 

kubectl get ksvc -A




invoke_url='http://nim.runai-jwu-test.jwu-netapp2.westus2.cloudapp.azure.com/v1/chat/completions'

authorization_header='Authorization: Bearer $API_KEY_REQUIRED_IF_EXECUTING_OUTSIDE_NGC'
accept_header='Accept: application/json'
content_type_header='Content-Type: application/json'

data=$'{
  "model": "meta/llama-3.1-8b-instruct",
  "messages": [
    {
      "role": "user",
      "content": ""
    }
  ],
  "temperature": 0.2,
  "top_p": 0.7,
  "frequency_penalty": 0,
  "presence_penalty": 0,
  "max_tokens": 1024,
  "stream": true
}'

response=$(curl --silent -i -w "\n%{http_code}" --request POST \
  --url "$invoke_url" \
  --header "$authorization_header" \
  --header "$accept_header" \
  --header "$content_type_header" \
  --data "$data"
)

echo "$response"

# Reference

https://run-ai-docs.nvidia.com/self-hosted/getting-started/installation/cp-system-requirements
https://docs.azure.cn/en-us/aks/app-routing-configuration
https://learn.microsoft.com/en-us/azure/aks/app-routing?tabs=without-osm#enable-web-application-routing-via-the-azure-cli
https://learn.microsoft.com/en-us/troubleshoot/azure/azure-kubernetes/load-bal-ingress-c/create-unmanaged-ingress-controller?tabs=azure-cli


