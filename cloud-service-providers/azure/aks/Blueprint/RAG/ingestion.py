# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This script is used to ingest a corpus of documents into a vector database.

Requirements:
```
pip install -r requirements.txt
python3 -c "import nltk; nltk.download('punkt')"
```

Usage:
    python ingestion.py [options]

Options:
    --nv_ingest_host HOST     Host where nv-ingest-ms-runtime is running (default: localhost)
    --nv_ingest_port PORT     REST port for NV Ingest (default: 7670)
    --milvus_uri URI          Milvus URI for external ingestion (default: http://localhost:19530)
    --minio_endpoint ENDPOINT MinIO endpoint for external ingestion (default: localhost:9010)
    --collection_name NAME    Name of the collection (default: bo767_test)
    --folder_path PATH          Path to the data files (default: "/path/to/bo767/corpus/")

Example:
    python ingestion.py --nv_ingest_host localhost --nv_ingest_port 7670 --milvus_uri http://localhost:19530 --minio_endpoint localhost:9010 --collection_name bo767_test --folder_path "/path/to/bo767/corpus/"

"""
import os
import time
import argparse
import PyPDF2
from tqdm import tqdm
from nv_ingest_client.client import Ingestor, NvIngestClient

def parse_args():
    """
    Parse the arguments for the ingestion script.
    """
    parser = argparse.ArgumentParser(
        description='Ingest a corpus of documents into a vector database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='For more information, see the example usage above.'
    )
    parser.add_argument('--nv_ingest_host', type=str, default="localhost",
                        help='Host where nv-ingest-ms-runtime is running')
    parser.add_argument('--nv_ingest_port', type=int, default=7670,
                        help='REST port for NV Ingest')
    parser.add_argument('--milvus_uri', type=str, default="http://localhost:19530",
                        help='Milvus URI for external ingestion')
    parser.add_argument('--minio_endpoint', type=str, default="localhost:9010",
                        help='MinIO endpoint for external ingestion')
    parser.add_argument('--collection_name', type=str, default="bo767_test",
                        help='Name of the collection')
    parser.add_argument('--folder_path', type=str, default="/path/to/bo767/corpus/",
                        help='Path to the data files')
    parser.add_argument('--skip_vdb_upload', action='store_true',
                        help='Skip the vector database upload')
    return parser.parse_args()

# Parse the arguments
args = parse_args()

# Print the configuration
print("\n" + "="*80)
print("PERFORMING INGESTION WITH THE FOLLOWING CONFIGURATION:")
print("="*80)
print(f"NV-Ingest Host:     {args.nv_ingest_host}")
print(f"NV-Ingest Port:     {args.nv_ingest_port}")
print(f"Milvus URI:         {args.milvus_uri}")
print(f"MinIO Endpoint:     {args.minio_endpoint}")
print(f"Collection Name:    {args.collection_name}")
print(f"Folder Path:        {args.folder_path}")
print("-"*80 + "\n")

# Compute the total number of pages of all the pdfs in the folder
print("\nComputing the total number of pages of all the pdfs in the folder...")
total_pages = 0
pdf_count = 0

for file in tqdm(os.listdir(args.folder_path)):
    try:
        if file.endswith(".pdf") or file.endswith(".txt"):
            pdf_count += 1
            pdf_path = os.path.join(args.folder_path, file)
            with open(pdf_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                total_pages += len(reader.pages)
    except Exception as e:
        print(f"Error processing {file}: {e}")

print(f"Total PDF files:            {pdf_count}")
print(f"Total pages in all PDFs:    {total_pages}")

# Server Mode
client = NvIngestClient(
  # host.docker.internal (from inside docker)
  message_client_hostname=args.nv_ingest_host, # Host where nv-ingest-ms-runtime is running
  message_client_port=args.nv_ingest_port # REST port, defaults to 7670
)

# Create the ingestor instance
ingestor = Ingestor(client=client)

# Add the files to the ingestor
ingestor = ingestor.files(os.path.join(args.folder_path, "*"))

# Extract the text, tables, charts, images from the files
ingestor = ingestor.extract(
                extract_text=True,
                extract_tables=True,
                extract_charts=True,
                extract_images=False,
                text_depth="page",
                paddle_output_format="markdown"
            )

# Split the text into chunks
ingestor = ingestor.split(
            tokenizer="intfloat/e5-large-unsupervised",
            chunk_size=512,
            chunk_overlap=150,
            params={"split_source_types": ["PDF", "text"]}
        )

# Embed the chunks
ingestor = ingestor.embed()

# Upload the chunks to the vector database
if not args.skip_vdb_upload:
    print("\nAdding task to upload the chunks to the vector database...")
    ingestor = ingestor.vdb_upload(
            collection_name=args.collection_name,
            milvus_uri=args.milvus_uri,
            minio_endpoint=args.minio_endpoint,
            sparse=False,
            enable_images=False,
            recreate=False,
            dense_dim=2048
        )
else:
    print("\nSkipping vector database upload...")

print("\nStarting ingestion...")
# Ingest the chunks
start = time.time()
# results blob is directly inspectable
results = ingestor.ingest(show_progress=True)
total_ingestion_time = time.time() - start

# Get count of result elements
print("\nCounting the number of result elements...")
result_elements_count = 0
for result in tqdm(results):
    for result_element in result:
        result_elements_count += 1

print("\n" + "="*80)
print("INGESTION PERFORMANCE METRICS:")
print("="*80)
print(f"Total ingestion time:         {total_ingestion_time:.2f} seconds")
print(f"Total pages ingested:         {total_pages}")
print(f"Pages per second:             {total_pages / total_ingestion_time:.2f}")
print(f"Total result files:           {len(results)}")
print(f"Total result elements/chunks: {result_elements_count}")
print("-" * 80)
