from elasticsearch import Elasticsearch
from datetime import datetime
import json

# 1. Connect to Database
es = Elasticsearch("http://localhost:9200")

# 2. The "Nuclear" Query
# We use query_string with wildcards to find *nanodump* anywhere, anytime.
# This technique bypasses timezone/latency sync issues between the Host and VM.
hunt_query = {
    "query": {
        "query_string": {
            "query": "*nanodump*"
        }
    }
}

print(f"[*] Starting Deep Threat Hunt...")

# 3. Execute Search
# size=10 means "Show me the top 10 matches"
response = es.search(index="winlogbeat-*", body=hunt_query, size=10)

# 4. Analyze Results
hits = response['hits']['hits']
if len(hits) > 0:
    print(f"\n[!!!] CRITICAL ALERT: CREDENTIAL DUMPING DETECTED [!!!]")
    print(f"Found {len(hits)} malicious events in history.")
    
    for hit in hits:
        source = hit['_source']
        # Try to grab the command line safely
        try:
            command = source['winlog']['event_data']['CommandLine']
            host = source['host']['name']
            time = source['@timestamp']
            
            print(f"-"*50)
            print(f"Time:    {time}")
            print(f"Victim:  {host}")
            print(f"Command: {command}")
            print(f"-"*50)
        except KeyError:
            # If the field layout is slightly different, just print the raw log
            print(f"Raw Hit: {source}")
else:
    print("[-] No threats found.")
