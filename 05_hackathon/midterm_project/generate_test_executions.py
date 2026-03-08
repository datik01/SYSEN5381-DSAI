import urllib.request
import json
import os
from datetime import datetime

# We will test against the live Posit Connect API deployment
API_BASE_URL = "https://connect.systems-apps.com/content/10263075-06b8-43f3-8dee-a938591f37f2"

def save_json(filename, data):
    """Saves dictionary data to a formatted JSON file."""
    os.makedirs("test_executions", exist_ok=True)
    filepath = os.path.join("test_executions", filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Saved test execution output to: {filepath}")

def make_request(url, method="GET", payload=None):
    req = urllib.request.Request(url, method=method)
    if payload:
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(payload).encode('utf-8')
        req.data = data
    
    with urllib.request.urlopen(req) as response:
        return response.status, json.loads(response.read().decode())

def run_tests():
    print(f"Starting test executions against Live API: {API_BASE_URL}\n")
    
    # Test 1: Fetch Live Congestion Data
    print("Running Test 1: Fetching /congestion/current...")
    try:
        status, data = make_request(f"{API_BASE_URL}/congestion/current")
        
        # Save output
        save_json("test_execution_1_current_congestion.json", {
            "test_timestamp": datetime.now().isoformat(),
            "endpoint": "/congestion/current",
            "status_code": status,
            "data": data
        })
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        
    # Test 2: Fetch Historical Congestion Data (3 days)
    print("\nRunning Test 2: Fetching /congestion/history?days=3...")
    try:
        status, data = make_request(f"{API_BASE_URL}/congestion/history?days=3")
        
        # Save output (limiting to first 50 records so the file isn't massive)
        save_json("test_execution_2_historical_data.json", {
            "test_timestamp": datetime.now().isoformat(),
            "endpoint": "/congestion/history?days=3",
            "status_code": status,
            "total_records_returned": len(data),
            "data_sample_first_50": data[:50]
        })
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        
    # Test 3: Generate AI Insight Summary (7 days)
    print("\nRunning Test 3: Fetching /congestion/summarize (POST)...")
    try:
        payload = {"days_back": 7}
        status, data = make_request(f"{API_BASE_URL}/congestion/summarize", method="POST", payload=payload)
        
        # Save output
        save_json("test_execution_3_ai_summary.json", {
            "test_timestamp": datetime.now().isoformat(),
            "endpoint": "/congestion/summarize",
            "request_payload": payload,
            "status_code": status,
            "response": data
        })
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

if __name__ == "__main__":
    run_tests()
    print("\n🎉 All test executions generated successfully!")
