import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to, is_not, has_key, has_length, greater_than

@given('I have the following category data')
def step_create_valid_category_json(context):
    row = context.table[0]
    
    context.category_body = {
        "title": row["title"].strip('"'),
        "description": row["description"].strip('"')
    }
    
    print(f"Created valid Category JSON body: {context.category_body}")

@given('I have incomplete category data missing "{missing_field}"')
def step_create_incomplete_category_json(context, missing_field):
    missing_field = missing_field.strip('"')
    
    if missing_field == "title":
        context.category_body = {
            "description": "This category is missing the required title field"
        }
    else:
        context.category_body = {}
    
    print(f"Created incomplete Category JSON body missing '{missing_field}': {context.category_body}")

@then('the response JSON should include a newly created category with the provided data')
def step_verify_category_values(context):
    assert context.response_data is not None, "Response data is not valid JSON"
    
    assert_that(context.response_data, has_key("title"))
    assert_that(context.response_data, has_key("description"))
    
    assert_that(context.response_data["title"], equal_to(context.category_body["title"]))
    assert_that(context.response_data["description"], equal_to(context.category_body["description"]))
    
    print("Verified response contains category with expected values")
    
    category_id = context.response_data.get("id")
    if category_id:
        context.test_data["categories"].append(category_id)
        print(f"Added category ID {category_id} to test data for cleanup")

@then('the category should have a system-generated unique ID')
def step_verify_unique_category_id(context):
    assert context.response_data is not None, "Response data is not valid JSON"
    
    assert_that(context.response_data, has_key("id"))
    assert_that(context.response_data["id"], is_not(None))
    assert_that(len(str(context.response_data["id"])), greater_than(0))
    
    print(f"Verified response contains unique ID: {context.response_data['id']}")
    
    url = context.base_url + "/categories"
    response = requests.get(url)
    
    try:
        response_data = response.json()
        if isinstance(response_data, dict) and 'categories' in response_data:
            categories = response_data['categories']
        else:
            categories = response_data
        
        existing_ids = [str(category["id"]) for category in categories if str(category["id"]) != str(context.response_data["id"])]
        
        assert str(context.response_data["id"]) not in existing_ids, "New ID matches an existing category ID"
        
        print(f"Verified ID {context.response_data['id']} is unique among {len(existing_ids)} existing categories")
    except (json.JSONDecodeError, KeyError) as e:
        assert False, f"Failed to verify unique ID: {e}"