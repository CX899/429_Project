import json
import requests
from behave import then
from hamcrest import assert_that, is_not, is_in
from features.steps.test_utils import get_mapped_id

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