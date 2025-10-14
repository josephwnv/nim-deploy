# Run.AI on AKS

https://run-ai-docs.nvidia.com/self-hosted/getting-started/installation/cp-system-requirements
https://docs.azure.cn/en-us/aks/app-routing-configuration

# --enable-app-routing 
```
az aks approuting enable --resource-group jwu-rdma-test --name jwu-ib-aks-cluster
az aks show --resource-group jwu-rdma-test --name jwu-ib-aks-cluster --query "addonProfiles.approuting.enabled" -o tsv
```
az aks approuting disable --resource-group jwu-rdma-test --name jwu-ib-aks-cluster
# find the public IP
```
kubectl get svc -A
```
# find the public IP name 
az network public-ip list -g mc_jwu-rdma-test_jwu-ib-aks-cluster_eastus --query "[?ipAddress=='4.236.239.253'].name" -o tsv

# Add DNS Label
```
az network public-ip update --dns-name myaksingres -g mc_jwu-rdma-test_jwu-ib-aks-cluster_eastus -n kubernetes-a913470c0fe1a4401bc4d0dc70e2a6f6 --allocation-method Static

az network public-ip show   --resource-group mc_jwu-rdma-test_jwu-ib-aks-cluster_eastus   --name kubernetes-a913470c0fe1a4401bc4d0dc70e2a6f6
```

## Create name space
```
kubectl create namespace runai-backend
```
## Create ingress controller
# ```
# helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
# helm repo update
# helm install nginx-ingress ingress-nginx/ingress-nginx \
#     --namespace nginx-ingress --create-namespace
# ```

## NO Need to Create a Public IP with a DNS label  
# ```
az network public-ip create \
  --resource-group jwu-rdma-test \
  --name jwuRunaiPublicIP \
  --dns-name myaksingress \
  --allocation-method Static \
  --sku Standard
# ```

## Assign Permission

# From Azure portal, Give AKS full control of Public IP

## Create ingress controller

# ```
# az network public-ip show   --resource-group jwu-rdma-test   --name jwuRunaiPublicIP

# 20.169.178.207
# myaksingress.eastus.cloudapp.azure.com
# ```

# ```
# helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
# helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
       --namespace nginx-ingress \
       --set controller.service.loadBalancerIP=13.92.190.19 \
       --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-dns-label-name"=myaksingress \
       --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-resource-group"=mc_jwu-rdma-test_jwu-ib-aks-cluster_eastus
# ```

## Create a Cert

```
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes -keyout myaksingres.eastus.cloudapp.azure.com.key -out myaksingres.eastus.cloudapp.azure.com.crt -subj "/CN=myaksingres.eastus.cloudapp.azure.com" -addext "subjectAltName=DNS:myaksingres.eastus.cloudapp.azure.com,DNS:*.myaksingres.eastus.cloudapp.azure.com,IP:4.236.239.253" 
```

## Create a K8 secret for TLS
  ```
kubectl create secret tls runai-backend-tls -n runai-backend --cert=myaksingres.eastus.cloudapp.azure.com.crt --key=myaksingres.eastus.cloudapp.azure.com.key
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
helm upgrade -i runai-backend -n runai-backend runai-backend/control-plane --set global.domain=myaksingres.eastus.cloudapp.azure.com
```

## Create the Ingress
```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: runai-backend-frontend
  namespace: runai-backend
spec:
  ingressClassName: webapprouting.kubernetes.azure.com
  rules:
  - http:
      paths:
      - backend:
          service:
            name: runai-backend-frontend
            port:
              number: 8080
        path: /
        pathType: Prefix
```

```
kubectl apply -f ingress.yaml -n runai-backend
```