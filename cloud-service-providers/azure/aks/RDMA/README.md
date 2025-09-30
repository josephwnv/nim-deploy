# Enable RDMA in AKS

Due to resource limitation, this RDMA in AKS exercise is tested on Standard_ND96asr_v4 only.  Feel free to report and issue on other instance type.  We will continue testing other instance type when the resource is available.

## [Install AKSInfinibandSupport feature](https://learn.microsoft.com/en-us/azure/aks/use-amd-gpus)


```
az feature show --namespace Microsoft.ContainerService --name AKSInfinibandSupport
az feature register --name AKSInfinibandSupport --namespace Microsoft.ContainerService
```

## Create AKS 

For proper region and VM size, Please check [product availability by region](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/table)
Following is just for reference.  may not up to date.

|                           | CENTRAL US | EAST US | EAST US 2 | NORTH CENTRAL US | SOUTH CENTRAL US | WEST US | WEST US 2 | WEST US 3 |
|---------------------------|------------|---------|-----------|------------------|------------------|---------|-----------|-----------|
| Standard_ND96amsr_A100_v4 |            |         |     X     |                  |        X         |         |           |           |
| Standard_ND96asr_v4       |            |   X     |           |                  |        X         |         |     X     |           |
| Standard_ND96isr_H100_v5  |       X    |   X     |     X     |                  |                  |     X   |           |           |
| Standard_ND96isr_H200_v5  |            |         |     X     |         X        |                  |         |           |       X   |

```
export AZURE_RESOURCE_GROUP="<Your resource group>"
export AZURE_REGION="<You region>"
export NODE_POOL_VM_SIZE="<Your VM Size>"
export CLUSTER_NAME="<Your Cluster Name>"
```

```
az aks create \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --name "${CLUSTER_NAME}" \
        --enable-oidc-issuer \
        --enable-workload-identity \
        --enable-managed-identity \
        --node-count 1 \
        --location "${AZURE_REGION}" \
        --ssh-key-value ~/.ssh/id_rsa.pub \
        --enable-node-public-ip \
        --os-sku Ubuntu
```

## Create GPU node pool 

```
az aks nodepool add --resource-group "${AZURE_RESOURCE_GROUP}" --cluster-name "${CLUSTER_NAME}" --name gpunp --node-count 2 --skip-gpu-driver-install --node-vm-size "${NODE_POOL_VM_SIZE}" --node-osdisk-size 512 --max-pods 110 --enable-node-public-ip --node-osdisk-type Managed
```

## Clone netop-tools

```
git clone https://github.com/Mellanox/netop-tools
cd netop-tools
source NETOP_ROOT_DIR.sh
cp config/examples/global_ops_user.cfg.hostdev_rdma_sriov global_ops_user.cfg
```

## update global_ops_user.cfg

Mainly is to upload NETOP_NETLIST, The following value is for Standard_ND96asr_v4, not sure whether need to modify for other instance type. If not work, please follow Turn on firewall then ssh in work node section to figure out the correct values

```
#
# hostdev_rdma_sriov
#
NFD_ENABLE=false
OFED_ENABLE=true
CREATE_CONFIG_ONLY=0
USECASE="hostdev_rdma_sriov"
MTU_DEFAULT="9000"
NUM_GPUS=8
DEVICE_TYPES=( "connectx-6-ex" )
NETOP_APP_NAMESPACES=( "default" )
NETOP_COMBINED=true
# for maximum E/W RDMA performance each NIC port gets defined as a network
# example device PCI id for connectx-7 = 1021 # interpreted by config as HEX
# devices index, {device PCI id},,VF devices (PCI BDF VFs | netdevice vf expression)
NETOP_NETLIST=( a,,,0101:00:00.0 b,,,0102:00:00.0 c,,,0103:00:00.0 d,,,0104:00:00.0 e,,,0105:00:00.0 f,,,0106:00:00.0 g,,,0107:00:00.0 h,,,0108:00:00.0 )
```

## label worker

```
cd ./netop-tools/ops
./labelworker.sh {nodename}
```

## Install GPU operator

If you never install GPU operator before, Please follow this [link](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html) to get more info.
```
helm install --create-namespace --namespace nvidia-gpu-operator nvidia/gpu-operator  --set driver.rdma.enabled=true  --wait --generate-name
```

## pull chart and install network operator
Don't wait for GPU operator installation complete.  Just continue...
```
cd ../install
./ins-netop-chart.sh
./ins-network-operator.sh
```
Now wait for both operator installation complete. check with ..
```
watch kubectl get pod -A
```

## Create test pod
```
cd $NETOP_ROOT_DIR/uc
$NETOP_ROOT_DIR/ops/mk-app.sh test1 default
$NETOP_ROOT_DIR/ops/mk-app.sh test2 default
cd apps
kubectl apply -f test1.yaml
kubectl apply -f test1.yaml
```

## RDMA test

### NO GPU
```
cd ~/netop-tools/rdmatest
./gdrsrv.sh ib test1 --net net1 --ns default
# from another terminal
./gdrclt.sh ib test2 test1 --net net1 --ns default
```

### WITH GPU
```
cd ~/netop-tools/rdmatest
# manual select GPU
./gdrsrv.sh ib test1 --net net1 --ns default --gpu 0
or
# auto select GPU
./gdrsrv.sh ib test1 --net net1 --ns default --gdr

# from another terminal
cd ~/netop-tools/rdmatest
# manual select GPU
./gdrclt.sh ib test2 test1 --net net1 --ns default -- gpu 0
or
# auto select GPU
./gdrclt.sh ib test2 test1 --net net1 --ns default -- gdr

```

## Fix/Update/patch cluster

if you need to fix global_ops_user.cfg

```
# after fixing global_ops_user.cfg

$NETOP_ROOT_DIR/ops/mk-config.sh
kubectl apply -f NicClusterPolicy.yaml
kubectl apply -f ippool.yaml
kubectl apply -f network.yaml
```

## Turn on firewall then ssh in work node

```
kubectl get node -o wide
ssh -i ~/.ssh/id_rsa azureuser@<public ip of gpu node>
lspci
...
```

## Reference
- https://github.com/Azure/aks-rdma-infiniband/tree/main/tests
