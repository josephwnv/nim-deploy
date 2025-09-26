# Enable RDMA in AKS
https://github.com/Azure/aks-rdma-infiniband/tree/main/tests

## Create AKS 

AKS currently doesn't support multi-interface pods when using the Azure CNI plugin for the cluster, you can use Bring your own CNI in AKS, this will allow you to install all your own “master” CNI and then configure Multus to add additional interfaces to your pods - [Bring your own Container Network Interface (CNI) plugin with Azure Kubernetes Service (AKS) - Azure Kubernetes Service | Microsoft Learn](https://learn.microsoft.com/en-us/azure/aks/use-byo-cni?tabs=azure-cli)

https://docs.tigera.io/calico/latest/getting-started/kubernetes/managed-public-cloud/aks

az aks create --name jwu-byocni --resource-group jwu-nvaie --ssh-key-value ~/.ssh/id_rsa.pub --enable-node-public-ip --location westus2 --network-plugin none
--pod-cidr 192.168.0.0/16 ??

az aks create --resource-group jwu-nvaie --name jwu-byocni --location westus2 --ssh-key-value ~/.ssh/id_rsa.pub --os-sku Ubuntu --enable-oidc-issuer --enable-workload-identity --enable-managed-identity 
        

## The virtual network for the AKS cluster must allow outbound internet connectivity.

## install CNI

kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.30.3/manifests/operator-crds.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.30.3/manifests/tigera-operator.yaml


```
kubectl create -f - <<EOF
kind: Installation
apiVersion: operator.tigera.io/v1
metadata:
  name: default
spec:
  kubernetesProvider: AKS
  cni:
    type: Calico
  calicoNetwork:
    bgp: Disabled
    ipPools:
     - cidr: 192.168.0.0/16
       encapsulation: VXLAN
---

# This section configures the Calico API server.
# For more information, see: https://docs.tigera.io/calico/latest/reference/installation/api#operator.tigera.io/v1.APIServer
apiVersion: operator.tigera.io/v1
kind: APIServer
metadata:
   name: default
spec: {}

---

# Configures the Calico Goldmane flow aggregator.
apiVersion: operator.tigera.io/v1
kind: Goldmane
metadata:
  name: default

---

# Configures the Calico Whisker observability UI.
apiVersion: operator.tigera.io/v1
kind: Whisker
metadata:
  name: default
EOF

watch kubectl get pods -n calico-system
```
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.30.3/manifests/custom-resources.yaml




~/netop-tools/install$ ./ins-calico.sh

iptables v1.8.7 (nf_tables): Couldn't load match `tcp':No such file or directory

Try `iptables -h' or 'iptables --help' for more information.

## Create GPU nodepool

az feature show --namespace Microsoft.ContainerService --name AKSInfinibandSupport
az feature register --name AKSInfinibandSupport --namespace Microsoft.ContainerService

|                           | CENTRAL US | EAST US | EAST US 2 | NORTH CENTRAL US | SOUTH CENTRAL US | WEST US | WEST US 2 | WEST US 3 |
|---------------------------|------------|---------|-----------|------------------|------------------|---------|-----------|-----------|
| Standard_ND96amsr_A100_v4 |            |         |     X     |                  |        X         |         |           |           |
| Standard_ND96asr_v4       |            |   X     |           |                  |        X         |         |     X     |           |
| Standard_ND96isr_H100_v5  |       X    |   X     |     X     |                  |                  |     X   |           |           |
| Standard_ND96isr_H200_v5  |            |         |     X     |         X        |                  |         |           |       X   |

az aks nodepool add --resource-group jwu-nvaie --cluster-name jwu-byocni --name gpunp --node-count 2 --skip-gpu-driver-install --node-vm-size Standard_NC40ads_H100_v5 --node-osdisk-size 512 --max-pods 110 --enable-node-public-ip --node-osdisk-type Managed --ssh-key-value ~/.ssh/id_rsa.pub

## Install GPU operator

```
helm install --create-namespace --namespace nvidia-gpu-operator nvidia/gpu-operator  --set driver.rdma.enabled=true  --wait --generate-name
```

## Clone netop-tools

```
git clone https://github.com/Mellanox/netop-tools
cd netop-tools
source NETOP_ROOT_DIR.sh
cp config/examples/global_ops_user.cfg.hostdev_rdma_sriov global_ops_user.cfg
```
## label worker

```
cd ./netop-tools/ops
./labelworker.sh {nodename}
```
## pull chart
```
cd ../install
./ins-netop-chart.sh
./ins-network-operator.sh
```
or if network operation exists
```
cd ../upgrade
./upgrade-network-operator.sh
```

## edit global_ops_user.cfg
open ssh port to login
```
ssh -i ~/.ssh/id_rsa azureuser@<public ip of gpu node>
lspci
ls -la /sys/class/net/ |grep -i d5f6:00:02.0
```

## mk-config.sh only for update

```
$NETOP_ROOT_DIR/ops/mk-config.sh
```
##
```
cd uc
kubectl apply -f NicClusterPolicy.yaml
```

##

```
cd $NETOP_ROOT_DIR/uc
$NETOP_ROOT_DIR/ops/mk-app.sh test1 default
$NETOP_ROOT_DIR/ops/mk-app.sh test2 default
```

