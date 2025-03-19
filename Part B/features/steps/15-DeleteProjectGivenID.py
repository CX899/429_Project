"""
Step definitions specific to deleting a Project by ID.
"""
import json
import requests
from behave import then
from hamcrest import assert_that, is_not, is_in
from features.steps.test_utils import get_mapped_id

@then('the response should not contain a project with ID {id}')
def step_verify_project_deleted(context, id):
    """Verify that the specified project ID does not exist in the response."""
    actual_id = get_mapped_id(context, id)
    
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    # Handle both direct array and wrapped in 'projects' field
    projects = []
    if isinstance(context.response_data, dict) and 'projects' in context.response_data:
        projects = context.response_data['projects']
    else:
        projects = context.response_data
    
    # Verify the project with the specified ID is not in the response
    project_ids = [str(project.get('id')) for project in projects]
    assert_that(str(actual_id), is_not(is_in(project_ids)))
    
    print(f"Verified project with ID {actual_id} is not in the response")

@then('the response should contain projects with IDs {id_list}')
def step_verify_remaining_projects(context, id_list):
    """Verify that projects with the specified IDs exist in the response."""
    # Parse the ID list (format like "1 and 3" or "1, 2, and 3")
    id_parts = id_list.replace(' and ', ', ').replace(',', '').split()
    expected_ids = [get_mapped_id(context, id_part) for id_part in id_parts]
    
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    # Handle both direct array and wrapped in 'projects' field
    projects = []
    if isinstance(context.response_data, dict) and 'projects' in context.response_data:
        projects = context.response_data['projects']
    else:
        projects = context.response_data
    
    # Extract project IDs from the response
    project_ids = [str(project.get('id')) for project in projects]
    
    # Verify all expected IDs are in the response
    for expected_id in expected_ids:
        assert str(expected_id) in project_ids, f"Expected project with ID {expected_id} is missing from the response"
        print(f"Verified project with ID {expected_id} is in the response")
    
    print(f"Verified all expected projects are in the response")