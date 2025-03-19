"""
Step definitions specific to retrieving a Project by ID.
"""
import json
from behave import then
from hamcrest import assert_that, equal_to
from features.steps.test_utils import get_mapped_id, verify_error_message

@then('the response JSON should contain a project with the following details')
def step_verify_project_details(context):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    row = context.table[0]
    expected_id = get_mapped_id(context, row['id'])
    expected_title = row['title'].strip('"')
    expected_completed = row['completed'].lower()
    expected_active = row['active'].lower()
    expected_description = row['description'].strip('"')
    
    project = None
    if isinstance(context.response_data, dict) and 'projects' in context.response_data:
        projects = context.response_data['projects']
        if len(projects) > 0:
            project = next((p for p in projects if str(p.get('id')) == str(expected_id)), projects[0])
    else:
        project = context.response_data
    
    assert project is not None, f"No project found in response"
    
    assert_that(str(project.get('id')), equal_to(str(expected_id)))
    assert_that(project.get('title'), equal_to(expected_title))
    assert_that(str(project.get('completed')).lower(), equal_to(expected_completed))
    assert_that(str(project.get('active')).lower(), equal_to(expected_active))
    assert_that(project.get('description'), equal_to(expected_description))
    
    print(f"Verified project with ID {expected_id} has expected details")

@then('the response should contain a "Not Found" message')
def step_verify_not_found_message(context):
    error_phrases = ["not found", "could not find", "does not exist"]
    
    has_error = False
    
    if hasattr(context, 'response_data') and context.response_data:
        if isinstance(context.response_data, dict):
            if 'errorMessages' in context.response_data:
                error_messages = context.response_data['errorMessages']
                error_text = ' '.join(error_messages)
                for phrase in error_phrases:
                    if phrase.lower() in error_text.lower():
                        has_error = True
                        print(f"Found error phrase '{phrase}' in errorMessages")
                        break
            elif 'error' in context.response_data:
                error_text = str(context.response_data['error']).lower()
                for phrase in error_phrases:
                    if phrase.lower() in error_text:
                        has_error = True
                        print(f"Found error phrase '{phrase}' in error field")
                        break
            else:
                response_text = json.dumps(context.response_data).lower()
                for phrase in error_phrases:
                    if phrase.lower() in response_text:
                        has_error = True
                        print(f"Found error phrase '{phrase}' in response JSON")
                        break
    else:
        response_text = context.response.text.lower()
        for phrase in error_phrases:
            if phrase.lower() in response_text:
                has_error = True
                print(f"Found error phrase '{phrase}' in response text")
                break
    
    assert has_error, "No 'Not Found' message found in response"
    print("Verified response contains 'Not Found' message")

@then('the response should contain an error message about invalid ID format')
def step_verify_invalid_id_message(context):
    """Verify that the response contains an invalid ID format error message."""
    error_phrases = ["invalid", "format", "id", "not valid", "malformed"]
    
    has_error = False
    
    if hasattr(context, 'response_data') and context.response_data:
        if isinstance(context.response_data, dict):
            if 'errorMessages' in context.response_data:
                error_messages = context.response_data['errorMessages']
                error_text = ' '.join(error_messages)
                for phrase in error_phrases:
                    if phrase.lower() in error_text.lower():
                        has_error = True
                        print(f"Found error phrase '{phrase}' in errorMessages")
                        break
            elif 'error' in context.response_data:
                error_text = str(context.response_data['error']).lower()
                for phrase in error_phrases:
                    if phrase.lower() in error_text:
                        has_error = True
                        print(f"Found error phrase '{phrase}' in error field")
                        break
            else:
                response_text = json.dumps(context.response_data).lower()
                for phrase in error_phrases:
                    if phrase.lower() in response_text:
                        has_error = True
                        print(f"Found error phrase '{phrase}' in response JSON")
                        break
    else:
        response_text = context.response.text.lower()
        for phrase in error_phrases:
            if phrase.lower() in response_text:
                has_error = True
                print(f"Found error phrase '{phrase}' in response text")
                break
    
    assert has_error, "No invalid ID format error message found in response"
    print("Verified response contains invalid ID format error message")

@then('the response should contain an error message mentioning "{message}"')
def step_verify_specific_error_message(context, message):
    """Verify that the response contains a specific error message."""
    assert verify_error_message(context, [message]), f"Error message not found mentioning: {message}"
    print(f"Verified response contains error message mentioning: {message}")