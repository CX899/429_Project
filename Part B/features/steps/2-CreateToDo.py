import json
import requests
import random
import string
from behave import given, then
from hamcrest import assert_that, equal_to, is_not, contains_string, has_key, has_length, greater_than

@given('the user has a valid JSON body for a new ToDo with')
def step_create_valid_todo_json(context):
    row = context.table[0]
    
    context.todo_body = {
        "title": row["title"].strip('"'),
        "doneStatus": row["doneStatus"] == "true" or row["doneStatus"] == "True",
        "description": row["description"].strip('"')
    }
    
    print(f"Created valid ToDo JSON body: {context.todo_body}")

@given('the user has a valid JSON body for a new ToDo without an "id" field')
def step_create_valid_todo_json_without_id(context):
    step_create_valid_todo_json(context)

@given('the user has an invalid JSON body for a new ToDo with "{issue}"')
def step_create_invalid_todo_json(context, issue):
    if issue == "missing required fields":
        context.todo_body = {
            "doneStatus": False,
            "description": "This ToDo is missing the required title field"
        }
    elif issue == "title is null":
        context.todo_body = {
            "title": None,
            "doneStatus": False,
            "description": "This ToDo has a null title"
        }
    elif issue == "doneStatus is not a boolean value":
        context.todo_body = {
            "title": "Invalid ToDo",
            "doneStatus": "not-a-boolean",
            "description": "This ToDo has an invalid doneStatus value"
        }
    else:
        context.todo_body = {}
    
    print(f"Created invalid ToDo JSON body for issue '{issue}': {context.todo_body}")

@then('the response JSON should contain a new ToDo with the specified title, doneStatus, and description')
def step_verify_todo_values(context):
    assert context.response_data is not None, "Response data is not valid JSON"
    
    assert_that(context.response_data, has_key("title"))
    assert_that(context.response_data, has_key("doneStatus"))
    assert_that(context.response_data, has_key("description"))
    
    request_done_status = str(context.todo_body["doneStatus"]).lower()
    response_done_status = str(context.response_data["doneStatus"]).lower()
    
    assert_that(context.response_data["title"], equal_to(context.todo_body["title"]))
    assert_that(response_done_status, equal_to(request_done_status))
    assert_that(context.response_data["description"], equal_to(context.todo_body["description"]))
    
    print("Verified response contains todo with expected values")
    
    todo_id = context.response_data.get("id")
    if todo_id:
        context.test_data["todos"].append(todo_id)
        print(f"Added todo ID {todo_id} to test data for cleanup")

@then('the response JSON should contain a unique "id"')
def step_verify_unique_id(context):
    assert context.response_data is not None, "Response data is not valid JSON"
    
    assert_that(context.response_data, has_key("id"))
    assert_that(context.response_data["id"], is_not(None))
    assert_that(len(str(context.response_data["id"])), greater_than(0))
    
    print(f"Verified response contains unique ID: {context.response_data['id']}")

@then('the response JSON should contain a newly generated "id" that does not match any existing ToDo')
def step_verify_new_id(context):
    step_verify_unique_id(context)
    
    url = context.base_url + "/todos"
    response = requests.get(url)
    
    try:
        response_data = response.json()
        if isinstance(response_data, dict) and 'todos' in response_data:
            todos = response_data['todos']
        else:
            todos = response_data
        
        existing_ids = [todo["id"] for todo in todos if todo["id"] != context.response_data["id"]]
        
        assert context.response_data["id"] not in existing_ids, "New ID matches an existing todo ID"
        
        print(f"Verified ID {context.response_data['id']} is unique among {len(existing_ids)} existing todos")
    except (json.JSONDecodeError, KeyError) as e:
        assert False, f"Failed to verify unique ID: {e}"