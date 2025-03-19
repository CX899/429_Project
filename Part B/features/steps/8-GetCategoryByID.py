"""
Step definitions specific to retrieving categories by ID.
"""
import json
from behave import then
from hamcrest import assert_that, equal_to
from features.steps.test_utils import get_mapped_id

@then('the response should contain the category with ID "{id}"')
def step_verify_category_id(context, id):
    actual_id = get_mapped_id(context, id)
    
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    if isinstance(context.response_data, dict) and 'id' in context.response_data:
        # Direct category object response
        category = context.response_data
        assert_that(str(category.get('id')), equal_to(str(actual_id)))
        print(f"Found category with ID {actual_id}")
    elif isinstance(context.response_data, dict) and 'categories' in context.response_data:
        # List of categories in a wrapper
        categories = context.response_data['categories']
        if len(categories) == 1:
            assert_that(str(categories[0].get('id')), equal_to(str(actual_id)))
            print(f"Found category with ID {actual_id}")
        else:
            # Try to find the category with matching ID
            matching_category = next((c for c in categories if str(c.get('id')) == str(actual_id)), None)
            assert matching_category is not None, f"Category with ID {actual_id} not found in response"
            print(f"Found category with ID {actual_id} among {len(categories)} categories")
    else:
        # If it's a direct list
        categories = context.response_data if isinstance(context.response_data, list) else []
        matching_category = next((c for c in categories if str(c.get('id')) == str(actual_id)), None)
        assert matching_category is not None, f"Category with ID {actual_id} not found in response"
        print(f"Found category with ID {actual_id} among {len(categories)} categories")