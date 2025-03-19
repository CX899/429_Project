"""
Environment configuration for Behave tests.
"""
import requests
import json

def before_all(context):
    # Base URL of the API
    context.base_url = "http://localhost:4567"
    
    # Store API responses during test execution
    context.response = None
    
    # Store ToDo data for sharing between steps
    context.todos = []
    
    # Print API information (helps confirm we're talking to the right API)
    try:
        response = requests.get(f"{context.base_url}/todos")
        print(f"Connected to API at {context.base_url}")
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            # If we get a successful response, try to print some info about it
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"Found {len(data)} todos in the system")
                elif isinstance(data, dict) and 'todos' in data:
                    print(f"Found {len(data['todos'])} todos in the system")
                else:
                    print("API returned JSON but not in expected format")
            except json.JSONDecodeError:
                print("API response is not JSON")
                print(f"First 100 chars of response: {response.text[:100]}...")
    except requests.RequestException as e:
        print(f"Warning: Could not connect to API: {e}")
        print("Tests may fail if the API is not running")

def before_scenario(context, scenario):
    # Reset response for each scenario
    context.response = None
    
    # Print scenario information for debugging
    print(f"\nExecuting scenario: {scenario.name}")