import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to, has_item, contains_string
from features.steps.test_utils import get_mapped_id, setup_test_categories

@given('the system contains the following categories')
def step_setup_categories(context):
    test_categories = []
    for row in context.table:
        test_category = {
            'id': str(row['id']).strip(),
            'title': row['title'].strip('"'),
            'description': row['description'].strip('"')
        }
        test_categories.append(test_category)
    
    setup_test_categories(context, test_categories)

@given('the user filters categories where "{filter_key}" equals "{filter_value}"')
def step_filter_categories(context, filter_key, filter_value):
    context.filter_key = filter_key
    context.filter_value = filter_value.strip('"')
    print(f"Setting up filter {filter_key}={context.filter_value}")

@then('the response JSON should include the following categories')
def step_verify_specific_categories(context):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'categories' in context.response_data:
        categories = context.response_data['categories']
    else:
        categories = context.response_data
    
    expected_categories = []
    for row in context.table:
        requested_id = row['id']
        actual_id = get_mapped_id(context, requested_id)
        expected_category = {
            'id': actual_id,
            'title': row['title'].strip('"'),
            'description': row['description'].strip('"')
        }
        expected_categories.append(expected_category)
    
    for expected in expected_categories:
        found = False
        for actual in categories:
            if (str(actual.get('id')) == str(expected['id']) or 
                (actual.get('title') == expected['title'] and 
                 actual.get('description') == expected['description'])):
                found = True
                print(f"Found matching category: {actual}")
                break
        
        assert found, f"Expected category with ID {expected['id']} or matching title/description not found"
    
    print(f"Verified all {len(expected_categories)} expected categories")

@then('the response JSON should contain only categories where "{filter_key}" equals "{filter_value}"')
def step_verify_filtered_categories(context, filter_key, filter_value):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'categories' in context.response_data:
        categories = context.response_data['categories']
    else:
        categories = context.response_data
    
    expected_value = filter_value.strip('"')
    
    print(f"Checking {len(categories)} categories for filter {filter_key}={expected_value}")
    
    if len(categories) > 0:
        for category in categories:
            actual_value = category.get(filter_key)
            assert str(actual_value) == str(expected_value), \
                f"Category does not match filter: expected {filter_key}={expected_value}, got {filter_key}={actual_value}"
            print(f"Verified category matches filter: {category}")