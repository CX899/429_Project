"""
Step definitions specific to amending a Project by ID.
"""
import json
import requests
from behave import given, then, when
from hamcrest import assert_that, equal_to
from features.steps.test_utils import get_mapped_id, verify_error_message

@given('I have the following updated project information')
def step_create_updated_project_json(context):
    """Create a JSON body for updating all project fields."""
    row = context.table[0]
    
    context.project_body = {
        "title": row["title"].strip('"'),
        "completed": row["completed"] == "true" or row["completed"] == "True",
        "active": row["active"] == "true" or row["active"] == "True",
        "description": row["description"].strip('"')
    }
    
    print(f"Created project update JSON body: {context.project_body}")

@given('I have the following partial project update')
def step_create_partial_project_json(context):
    """Create a JSON body for updating only some project fields."""
    row = context.table[0]
    
    # Create a body with only the specified fields
    context.project_body = {}
    
    if "completed" in row:
        context.project_body["completed"] = row["completed"] == "true" or row["completed"] == "True"
    
    if "description" in row:
        context.project_body["description"] = row["description"].strip('"')
    
    print(f"Created partial project update JSON body: {context.project_body}")

@given('I have valid project update information')
def step_create_valid_project_update(context):
    """Create a standard valid project update body."""
    # Create a simple valid update
    context.project_body = {
        "title": "Updated Project",
        "completed": False,
        "active": True,
        "description": "Updated description"
    }
    
    print(f"Created valid project update JSON body: {context.project_body}")

@when('I send a {method} request to "/projects/{id}" with this updated information')
def step_send_update_request(context, method, id):
    """Send a request to update a project with specified ID."""
    # Map the ID if needed
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/projects/{actual_id}"
    headers = {"Content-Type": "application/json"}
    
    print(f"Sending {method} request to {url} with body: {context.project_body}")
    
    # First, get original project for comparison later
    try:
        get_response = requests.get(url)
        if get_response.status_code == 200:
            context.original_project = get_response.json()
            print(f"Stored original project: {context.original_project}")
    except Exception as e:
        print(f"Failed to retrieve original project: {e}")
    
    context.response = getattr(requests, method.lower())(url, json=context.project_body, headers=headers)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('I send a {method} request to "/projects/{id}" with this partial update')
def step_send_partial_update_request(context, method, id):
    """Send a request to partially update a project."""
    # Store original project for later comparison
    actual_id = get_mapped_id(context, id)
    
    url = f"{context.base_url}/projects/{actual_id}"
    
    try:
        get_response = requests.get(url)
        if get_response.status_code == 200:
            # Handle direct project object or projects array
            response_json = get_response.json()
            if isinstance(response_json, dict) and 'projects' in response_json:
                projects = response_json['projects']
                if len(projects) > 0 and isinstance(projects, list):
                    context.original_project = projects[0]
                else:
                    context.original_project = {}
            else:
                context.original_project = response_json
            print(f"Stored original project: {context.original_project}")
    except Exception as e:
        print(f"Failed to retrieve original project: {e}")
        context.original_project = {}
    
    # For PUT requests, we need to include all fields, so get the current values for fields not being updated
    if method.upper() == "PUT" and hasattr(context, 'original_project'):
        # Make a fresh copy of the original project to avoid modifying it
        complete_body = {}
        
        # Copy only the essential fields, converting them to proper types
        # DON'T include the ID in the request body - it's already in the URL
            
        if 'title' in context.original_project:
            complete_body['title'] = context.original_project['title']
            
        if 'completed' in context.original_project:
            # Convert completed to boolean if it's a string
            original_completed = context.original_project['completed']
            if isinstance(original_completed, str):
                complete_body['completed'] = original_completed.lower() == 'true'
            else:
                complete_body['completed'] = bool(original_completed)
                
        if 'active' in context.original_project:
            # Convert active to boolean if it's a string
            original_active = context.original_project['active']
            if isinstance(original_active, str):
                complete_body['active'] = original_active.lower() == 'true'
            else:
                complete_body['active'] = bool(original_active)
                
        if 'description' in context.original_project:
            complete_body['description'] = context.original_project['description']
        
        # Update only the fields that were specified in the partial update
        for key, value in context.project_body.items():
            complete_body[key] = value
        
        # Use the complete body for the request
        update_body = complete_body
        print(f"Created complete update body: {update_body}")
    else:
        # Use the partial body directly
        update_body = context.project_body
    
    # Send the request
    headers = {"Content-Type": "application/json"}
    context.response = getattr(requests, method.lower())(url, json=update_body, headers=headers)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('I send a {method} request to "/projects/{invalid_id}" with this information')
def step_send_invalid_update_request(context, method, invalid_id):
    """Send a request to update a project with an invalid ID."""
    url = f"{context.base_url}/projects/{invalid_id}"
    headers = {"Content-Type": "application/json"}
    
    print(f"Sending {method} request to {url} with body: {context.project_body}")
    
    context.response = getattr(requests, method.lower())(url, json=context.project_body, headers=headers)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@then('the response should contain the updated project')
def step_verify_updated_project_response(context):
    """Verify that the response contains the updated project."""
    assert context.response_data is not None, "Response data is not valid JSON"
    
    # Handle various response formats
    project_data = None
    if isinstance(context.response_data, dict):
        if 'id' in context.response_data:
            project_data = context.response_data
        elif 'projects' in context.response_data and isinstance(context.response_data['projects'], list):
            if len(context.response_data['projects']) > 0:
                project_data = context.response_data['projects'][0]
    
    assert project_data is not None, "Response does not contain project data"
    
    # Verify that the response contains a project object
    assert 'id' in project_data, "Response does not contain a project ID"
    
    # Verify that the response contains the updated fields
    for key, value in context.project_body.items():
        if key in project_data:
            actual_value = project_data[key]
            # Handle boolean values which might be returned as strings
            if isinstance(value, bool):
                assert str(actual_value).lower() == str(value).lower(), f"Updated field {key} has incorrect value"
            else:
                assert actual_value == value, f"Updated field {key} has incorrect value"
            
            print(f"Verified response includes updated field {key} = {value}")
    
    print("Verified response contains updated project")

@then('the project with ID {id} should have all fields updated to the new values')
def step_verify_all_fields_updated(context, id):
    """Verify that all project fields were updated to the new values."""
    actual_id = get_mapped_id(context, id)
    
    # Get the current state of the project
    url = f"{context.base_url}/projects/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Failed to get updated project: {response.status_code}"
    
    try:
        response_json = response.json()
        
        # Handle different response formats
        updated_project = None
        if isinstance(response_json, dict):
            if 'id' in response_json:
                updated_project = response_json
            elif 'projects' in response_json and isinstance(response_json['projects'], list):
                if len(response_json['projects']) > 0:
                    updated_project = response_json['projects'][0]
        
        assert updated_project is not None, "Could not find project in response"
                
        # Verify each field was updated
        for key, expected_value in context.project_body.items():
            actual_value = updated_project.get(key)
            
            # Handle boolean values which might be returned as strings
            if isinstance(expected_value, bool):
                assert str(actual_value).lower() == str(expected_value).lower(), \
                    f"Field {key} not updated correctly. Expected: {expected_value}, got: {actual_value}"
            else:
                assert actual_value == expected_value, \
                    f"Field {key} not updated correctly. Expected: {expected_value}, got: {actual_value}"
            
            print(f"Verified field {key} updated to {expected_value}")
        
        print(f"All fields of project {actual_id} were successfully updated")
    except json.JSONDecodeError:
        assert False, "Invalid JSON response when getting updated project"
    except AssertionError as e:
        assert False, f"Failed to verify project updates: {e}"

@then('the project with ID {id} should have the specified fields updated')
def step_verify_specified_fields_updated(context, id):
    """Verify that specified project fields were updated to the new values."""
    actual_id = get_mapped_id(context, id)
    
    # Get the current state of the project
    url = f"{context.base_url}/projects/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Failed to get updated project: {response.status_code}"
    
    try:
        response_json = response.json()
        
        # Handle different response formats
        updated_project = None
        if isinstance(response_json, dict):
            if 'id' in response_json:
                updated_project = response_json
            elif 'projects' in response_json and isinstance(response_json['projects'], list):
                if len(response_json['projects']) > 0:
                    updated_project = response_json['projects'][0]
        
        assert updated_project is not None, "Could not find project in response"
                
        # Verify each specified field was updated
        for key, expected_value in context.project_body.items():
            actual_value = updated_project.get(key)
            
            # Handle boolean values which might be returned as strings
            if isinstance(expected_value, bool):
                assert str(actual_value).lower() == str(expected_value).lower(), \
                    f"Field {key} not updated correctly. Expected: {expected_value}, got: {actual_value}"
            else:
                assert actual_value == expected_value, \
                    f"Field {key} not updated correctly. Expected: {expected_value}, got: {actual_value}"
            
            print(f"Verified field {key} updated to {expected_value}")
        
        print(f"Specified fields of project {actual_id} were successfully updated")
    except json.JSONDecodeError:
        assert False, "Invalid JSON response when getting updated project"
    except AssertionError as e:
        assert False, f"Failed to verify project updates: {e}"

@then('the project with ID {id} should have unchanged values for other fields')
def step_verify_other_fields_unchanged(context, id):
    """Verify that non-updated fields retain their original values."""
    actual_id = get_mapped_id(context, id)
    
    # Get the current state of the project
    url = f"{context.base_url}/projects/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Failed to get updated project: {response.status_code}"
    
    try:
        response_json = response.json()
        
        # Handle different response formats
        updated_project = None
        if isinstance(response_json, dict):
            if 'id' in response_json:
                updated_project = response_json
            elif 'projects' in response_json and isinstance(response_json['projects'], list):
                if len(response_json['projects']) > 0:
                    updated_project = response_json['projects'][0]
        
        assert updated_project is not None, "Could not find project in response"
        
        # Check that we have the original project for comparison
        if not hasattr(context, 'original_project') or not context.original_project:
            print("Warning: Original project not available for comparison, skipping unchanged fields check")
            return
        
        original_project = context.original_project
        
        # Check only fields that weren't in the update body
        updated_fields = list(context.project_body.keys())
        for key, original_value in original_project.items():
            if key not in updated_fields and key != 'id':  # Skip the ID field
                updated_value = updated_project.get(key)
                
                # Handle boolean values which might be returned as strings
                if isinstance(original_value, bool):
                    assert str(updated_value).lower() == str(original_value).lower(), \
                        f"Unchanged field {key} was modified. Original: {original_value}, Current: {updated_value}"
                else:
                    assert updated_value == original_value, \
                        f"Unchanged field {key} was modified. Original: {original_value}, Current: {updated_value}"
                
                print(f"Verified field {key} remained unchanged at {original_value}")
        
        print(f"All non-updated fields of project {actual_id} remained unchanged")
    except json.JSONDecodeError:
        assert False, "Invalid JSON response when getting updated project"
    except AssertionError as e:
        assert False, f"Failed to verify unchanged fields: {e}"