import json
import requests
from behave import when, then
from hamcrest import assert_that, is_not, is_in
from features.steps.test_utils import get_mapped_id

@when('I send a {method} request to "{endpoint}"')
def step_send_request_with_method(context, method, endpoint):
    # Check if we need to map an ID in the endpoint
    if '/categories/' in endpoint:
        parts = endpoint.split('/')
        if len(parts) >= 3 and parts[2]:
            requested_id = parts[2]
            actual_id = get_mapped_id(context, requested_id)
            endpoint = f"/categories/{actual_id}"
            print(f"Mapped endpoint from {'/'.join(parts)} to {endpoint}")
    
    url = context.base_url + endpoint
    
    print(f"Sending {method} request to {url}")
    
    context.response = getattr(requests, method.lower())(url)
    
    print(f"Response status: {context.response.status_code}")
    print(f"Response content: {context.response.text[:200]}...")
    
    try:
        context.response_data = context.response.json()
        print(f"Response data: {json.dumps(context.response_data)[:200]}...")
    except json.JSONDecodeError:
        context.response_data = None
        print(f"Response is not JSON or is empty: {context.response.text[:200]}...")

@then('the response should not include a category with id "{id}"')
def step_verify_category_deleted(context, id):
    actual_id = get_mapped_id(context, id)
    
    # First verify the category no longer exists as a direct lookup
    verify_url = f"{context.base_url}/categories/{actual_id}"
    verify_response = requests.get(verify_url)
    
    assert verify_response.status_code == 404, f"Category with ID {actual_id} still exists"
    print(f"Verified category with ID {actual_id} no longer exists")
    
    # Get all categories to ensure it's not in the list
    all_categories_response = requests.get(f"{context.base_url}/categories")
    assert all_categories_response.status_code == 200, "Failed to get all categories"
    
    try:
        categories_data = all_categories_response.json()
        if isinstance(categories_data, dict) and 'categories' in categories_data:
            categories = categories_data['categories']
        else:
            categories = categories_data
            
        # Verify the deleted category is not in the list
        category_ids = [str(category.get('id')) for category in categories]
        assert_that(str(actual_id), is_not(is_in(category_ids)))
        
        print(f"Verified category with ID {actual_id} is not in the list of categories")
    except (json.JSONDecodeError, AssertionError) as e:
        assert False, f"Failed to verify category deletion: {e}"

@then('the response should include an error message indicating category not found')
def step_verify_not_found_error(context):
    assert context.response.status_code == 404, \
        f"Expected 404 status code, got {context.response.status_code}"
    
    try:
        if not hasattr(context, 'response_data'):
            context.response_data = context.response.json()
    except json.JSONDecodeError:
        context.response_data = None
    
    if context.response_data is None:
        assert "not found" in context.response.text.lower() or \
               "could not find" in context.response.text.lower(), \
            f"Response does not contain a not found error message"
        print(f"Verified not found error message in response text: {context.response.text[:100]}...")
    else:
        if isinstance(context.response_data, dict) and 'errorMessages' in context.response_data:
            error_messages = context.response_data['errorMessages']
            assert len(error_messages) > 0, "No error messages found in response"
            
            error_phrases = ["not found", "could not find", "doesn't exist", "does not exist"]
            found = False
            for message in error_messages:
                if any(phrase in message.lower() for phrase in error_phrases):
                    found = True
                    break
            
            assert found, f"Error messages don't indicate category not found: {error_messages}"
            print(f"Found error messages: {error_messages}")
        elif 'error' in context.response_data:
            error_message = context.response_data['error']
            error_phrases = ["not found", "could not find", "doesn't exist", "does not exist"]
            found = any(phrase in str(error_message).lower() for phrase in error_phrases)
            assert found, f"Error message doesn't indicate category not found: {error_message}"
            print(f"Found error message: {error_message}")
        else:
            response_text = json.dumps(context.response_data)
            error_phrases = ["not found", "could not find", "doesn't exist", "does not exist"]
            found = any(phrase in response_text.lower() for phrase in error_phrases)
            assert found, f"Response does not contain category not found error: {response_text}"
            print(f"Verified error message in response JSON: {response_text[:100]}...")