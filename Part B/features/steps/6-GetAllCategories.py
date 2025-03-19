import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to, has_item, contains_string
from features.steps.test_utils import get_mapped_id

def setup_test_categories(context, test_categories):
    """
    Set up test categories and maintain ID mapping.
    """
    id_mapping = {}
    
    response = requests.get(f"{context.base_url}/categories")
    existing_categories = []
    
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, dict) and 'categories' in data:
                existing_categories = data['categories']
            else:
                existing_categories = data
            print(f"Found {len(existing_categories)} existing categories")
        except json.JSONDecodeError:
            print("Error parsing existing categories response")
            existing_categories = []
    
    for category in test_categories:
        requested_id = str(category.get('id', '')).strip()
        title = category.get('title', '').strip('"')
        description = category.get('description', '').strip('"')
        
        matching_category = next(
            (c for c in existing_categories if 
             c.get('title') == title and 
             c.get('description') == description),
            None
        )
        
        if matching_category:
            actual_id = matching_category.get('id')
            id_mapping[requested_id] = actual_id
            print(f"Using existing category with ID {actual_id} for requested ID {requested_id}")
            
            if actual_id not in context.test_data['categories']:
                context.test_data['categories'].append(actual_id)
        else:
            category_data = {
                'title': title,
                'description': description
            }
            
            create_response = requests.post(f"{context.base_url}/categories", json=category_data)
            
            if create_response.status_code in [200, 201]:
                try:
                    created_category = create_response.json()
                    actual_id = created_category.get('id')
                    id_mapping[requested_id] = actual_id
                    
                    context.test_data['categories'].append(actual_id)
                    print(f"Created new category with ID {actual_id} for requested ID {requested_id}")
                except json.JSONDecodeError:
                    print(f"Failed to parse response when creating category: {create_response.text}")
            else:
                print(f"Failed to create category: {create_response.status_code} - {create_response.text}")
    
    if not hasattr(context, 'id_mapping'):
        context.id_mapping = {}
    
    # Merge category mappings with existing mappings
    for req_id, actual_id in id_mapping.items():
        context.id_mapping[req_id] = actual_id
    
    return id_mapping

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

@then('the response contains a list of categories')
def step_verify_categories_list(context):
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'categories' in context.response_data:
        categories = context.response_data['categories']
    else:
        categories = context.response_data
    
    assert isinstance(categories, list), f"Expected a list of categories, but got {type(categories)}"
    
    print(f"Response contains {len(categories)} categories")
    if len(categories) > 0:
        print(f"First category: {categories[0]}")

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