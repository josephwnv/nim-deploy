#!/bin/bash

# Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# AzureML Workspace and corresponding container registry related information
subscription_id="b7d41fc8-d35d-41db-92ed-1f7f1d32d4d9"
resource_group="jwu-ml"
workspace="azlocaltest3"
location="southcentralus" # eg: "southcentralus", "westeurope" etc.

# Azure keyvault creation related information
ngc_api_key="aWg5NnYzZGdtZDRobHEwdGE2MTBtM21nc246NWNiYjBmNzYtODk3My00NDJkLTg1MzItY2Y5YTAxZTE1MjI4"
keyvault_name="azlocaltkeyvault00f63518"
email_address="josephw@nvidia.com"

# Container related information
 # NOTE: Verify that your AML workspace can access this ACR
acr_registry_name="4ee8ee60d20244b3846c9e6326751f9f"
image_name="llama32nvembedqa1bv2"
ngc_container="nvcr.io/nim/nvidia/llama-3.2-nv-embedqa-1b-v2:1.9.0"
#ngc_container="nvcr.io/nvidia/nemo-microservices/llama-3.2-nemoretriever-1b-vlm-embed-v1:1.7.0"

# Endpoint related information
#endpoint_name="llama38bnimendpointaml1"
endpoint_name="llama32nvembedqaendpointaml1"

# Deployment related information
#deployment_name="llama3-8b-nim-deployment-aml-1"
deployment_name="llama32-nv-embedqa-dep-aml-1"
#instance_type="Standard_NC40ads_H100_v5"
#instance_type="h100instancetypename"
instance_type="myinstancetypename"
