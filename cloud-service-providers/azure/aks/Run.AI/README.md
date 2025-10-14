# Run.AI on AKS



## Create name space
```
kubectl create namespace runai-backend
```

## Create ingress controller

```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace nginx-ingress --create-namespace
    --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=healthz
```
### Using the Azure Portal:
- Sign in to the Azure portal.
- In the search box at the top, type "Load balancer" and select Load balancers from the search results.
- Select your specific load balancer: from the list.
- In the load balancer's settings menu, under Settings, select Health probes.
- Select the existing health probe: you want to modify, or select + Add to create a new one.
- In the "Add health probe" or "Edit health probe" pane, locate the Path field. This is where you can view or change the URI used for the health probe request.
- Enter or modify the desired URI: /healthz.
- Select Add or Save: to apply the changes.

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

## Login

- https://<prefix>.<region>.cloudapp.azure.com
- default user is: test@run.ai and default password is Abcd!234
- ![](./images/login.jpg)

- ![](./images/install.jpg)

# Reference

https://run-ai-docs.nvidia.com/self-hosted/getting-started/installation/cp-system-requirements
https://docs.azure.cn/en-us/aks/app-routing-configuration
https://learn.microsoft.com/en-us/azure/aks/app-routing?tabs=without-osm#enable-web-application-routing-via-the-azure-cli
https://learn.microsoft.com/en-us/troubleshoot/azure/azure-kubernetes/load-bal-ingress-c/create-unmanaged-ingress-controller?tabs=azure-cli


