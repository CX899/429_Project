import json
import requests
from behave import given, when, then
from hamcrest import assert_that, equal_to, has_key
from features.steps.test_utils import get_mapped_id

@given('I have the following updated category data')
def step_setup_updated_category_data(context):
    row = context.table[0]
    
    context.category_body = {
        "title": row["title"].strip('"'),
        "description": row["description"].strip('"')
    }
    
    print(f"Created updated Category JSON body: {context.category_body}")

@given('I have the following partial category data')
def step_setup_partial_category_data(context):
    # This step is no longer needed with the simplified approach in the feature file
    # We'll reuse the regular updated category data step
    step_setup_updated_category_data(context)
    
    # Get the current category data using existing utility for consistent handling
    url = f"{context.base_url}/categories/{actual_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            current_category = response.json()
            # Create a body with all existing fields
            context.category_body = {
                "title": current_category.get("title", ""),
                "description": current_category.get("description", "")
            }
            # Update only the specified field
            context.category_body[field_name] = field_value
            
            print(f"Created partial update Category JSON body: {context.category_body}")
        except json.JSONDecodeError:
            print("Failed to parse current category data")
            context.category_body = {field_name: field_value}
    else:
        print(f"Failed to get current category data: {response.status_code}")
        context.category_body = {field_name: field_value}

@when('I send a {method} request to "{endpoint}" with the updated data')
def step_send_request_with_method(context, method, endpoint):
    # Use the same ID mapping approach as in common_steps.py
    if '/categories/' in endpoint:
        parts = endpoint.split('/')
        if len(parts) >= 3 and parts[2]:
            requested_id = parts[2]
            if hasattr(context, 'id_mapping') and requested_id in context.id_mapping:
                actual_id = context.id_mapping[requested_id]
                endpoint = f"/categories/{actual_id}"
                print(f"Mapped endpoint from {'/'.join(parts)} to {endpoint}")
    
    url = context.base_url + endpoint
    headers = {"Content-Type": "application/json"}
    
    print(f"Sending {method} request to {url} with body: {context.category_body}")
    
    context.response = getattr(requests, method.lower())(url, json=context.category_body, headers=headers)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
        print("Response is not valid JSON")

@when('I send a {method} request to "{endpoint}" with the partial data')
def step_send_request_with_partial_data(context, method, endpoint):
    step_send_request_with_method(context, method, endpoint)

@then('the response JSON should include the following updated category')
def step_verify_updated_category(context):
    # Ensure we have response data
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    row = context.table[0]
    requested_id = row['id']
    actual_id = get_mapped_id(context, requested_id)
    expected_title = row['title'].strip('"')
    expected_description = row['description'].strip('"')
    
    # Check if response is a direct category object
    if isinstance(context.response_data, dict) and 'id' in context.response_data:
        category = context.response_data
        assert_that(str(category.get('id')), equal_to(str(actual_id)))
        assert_that(category.get('title'), equal_to(expected_title))
        assert_that(category.get('description'), equal_to(expected_description))
        print(f"Verified updated category in response: {category}")
    else:
        # If response doesn't contain the full category, verify by making a GET request
        url = f"{context.base_url}/categories/{actual_id}"
        response = requests.get(url)
        
        assert response.status_code == 200, f"Failed to get updated category with ID {actual_id}"
        
        try:
            category = response.json()
            assert_that(str(category.get('id')), equal_to(str(actual_id)))
            assert_that(category.get('title'), equal_to(expected_title))
            assert_that(category.get('description'), equal_to(expected_description))
            print(f"Verified updated category with GET request: {category}")
        except (json.JSONDecodeError, AssertionError) as e:
            assert False, f"Failed to verify category update: {e}"
    
    print(f"Verified category with ID {actual_id} was updated with correct values")

@then('the response should include an error message indicating invalid ID format')
def step_verify_invalid_id_error(context):
    # Leveraging common step implementations for error checking
    assert context.response.status_code == 404, \
        f"Expected 404 status code, got {context.response.status_code}"
    
    # Use a similar approach to the common_steps.py error message checking
    try:
        if not hasattr(context, 'response_data'):
            context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
    
    error_phrases = ["invalid", "could not find", "not found", "no such"]
    
    if context.response_data is None:
        # Check text response
        found = any(phrase in context.response.text.lower() for phrase in error_phrases)
        assert found, f"Response does not contain an error message about invalid ID: {context.response.text}"
        print(f"Verified error message in response text: {context.response.text[:100]}...")
    else:
        # Check structured JSON response
        if isinstance(context.response_data, dict) and 'errorMessages' in context.response_data:
            error_messages = context.response_data['errorMessages']
            assert len(error_messages) > 0, "No error messages found in response"
            
            # Look for relevant error phrases
            found = False
            for message in error_messages:
                if any(phrase in message.lower() for phrase in error_phrases):
                    found = True
                    break
            
            assert found, f"Error messages don't indicate invalid ID: {error_messages}"
            print(f"Found error messages: {error_messages}")
        elif 'error' in context.response_data:
            error_message = context.response_data['error']
            found = any(phrase in str(error_message).lower() for phrase in error_phrases)
            assert found, f"Error message doesn't indicate invalid ID: {error_message}"
            print(f"Found error message: {error_message}")
        else:
            # Check the entire response
            response_text = json.dumps(context.response_data)
            found = any(phrase in response_text.lower() for phrase in error_phrases)
            assert found, f"Response does not contain error message about invalid ID: {response_text}"
            print(f"Verified error message in response JSON: {response_text[:100]}...")