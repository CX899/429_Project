import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to
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
    step_setup_updated_category_data(context)

@then('the response JSON should include the following updated category')
def step_verify_updated_category(context):
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
    
    if isinstance(context.response_data, dict) and 'id' in context.response_data:
        category = context.response_data
        assert_that(str(category.get('id')), equal_to(str(actual_id)))
        assert_that(category.get('title'), equal_to(expected_title))
        assert_that(category.get('description'), equal_to(expected_description))
        print(f"Verified updated category in response: {category}")
    else:
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