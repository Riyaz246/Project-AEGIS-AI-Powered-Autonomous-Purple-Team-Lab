import requests
import json
from elasticsearch import Elasticsearch

# --- CONFIGURATION ---
# 1. Your Windows Laptop IP (Where Ollama is running)
# UPDATE THIS IP to match your Windows Host IP if it changes
OLLAMA_IP = "YOUR WINDOWS IP" 
OLLAMA_URL = f"http://{OLLAMA_IP}:11434/api/generate"

# 2. Your Kali SIEM IP
ES_URL = "http://localhost:9200"

# --- THE LOGIC ---
def get_threat_data():
    es = Elasticsearch(ES_URL)
    # The "Nuclear" Query (Find nanodump anywhere)
    query = {
        "query": {
            "query_string": {
                "query": "*nanodump*"
            }
        }
    }
    # Get the most recent hit
    response = es.search(index="winlogbeat-*", body=query, size=1)
    
    if len(response['hits']['hits']) > 0:
        return response['hits']['hits'][0]['_source']
    else:
        return None

def analyze_with_ai(log_data):
    print(f"[*] Sending alert to AI Brain at {OLLAMA_IP}...")
    
    # Extract key details to save token space
    try:
        command = log_data['winlog']['event_data']['CommandLine']
        user = log_data['winlog']['event_data']['User']
        host = log_data['host']['name']
    except KeyError:
        command = "Unknown"
        user = "Unknown"
        host = "Unknown"

    # The Prompt for the AI
    prompt = f"""
    You are a Senior Security Analyst. Analyze this detection log:
    
    THREAT DETECTED: Credential Dumping
    HOST: {host}
    USER: {user}
    COMMAND EXECUTED: {command}
    
    Task:
    1. Explain what this command does.
    2. Assess the severity (Low/Medium/High/Critical).
    3. Recommend 3 immediate remediation steps for the SOC team.
    
    Format the output as a formal Incident Report.
    """
    
    # Send to Ollama
    payload = {
        "model": "llama3", # Change to "tinyllama" if using the smaller model
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        return response.json()['response']
    except requests.exceptions.ConnectionError:
        return "[!] Error: Could not connect to Ollama on Windows. Is 'ollama serve' running? Did you set OLLAMA_HOST=0.0.0.0?"

# --- EXECUTION ---
print("[-] Querying SIEM for threats...")
log = get_threat_data()

if log:
    print("[+] Threat Found! Analyzing...")
    report = analyze_with_ai(log)
    print("\n" + "="*60)
    print("      AI-GENERATED INCIDENT REPORT")
    print("="*60)
    print(report)
    print("="*60)
else:
    print("[-] No 'nanodump' threats found in the database.")
