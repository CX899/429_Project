"""
Step definitions specific to retrieving all Projects.
"""
import json
import requests
from behave import given, then
from hamcrest import assert_that, equal_to, has_item, contains_string
from features.steps.test_utils import get_mapped_id

@given('the system contains the following projects')
def step_setup_projects(context):
    """Set up test projects for the scenario."""
    # Extract test projects from the table
    test_projects = []
    for row in context.table:
        test_project = {
            'id': str(row['id']).strip(),
            'title': row['title'].strip('"'),
            'completed': row['completed'].lower() == 'true',
            'active': row['active'].lower() == 'true',
            'description': row['description'].strip('"')
        }
        test_projects.append(test_project)
    
    # Set up test projects by matching or creating them
    id_mapping = {}
    
    # Get existing projects
    response = requests.get(f"{context.base_url}/projects")
    existing_projects = []
    
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, dict) and 'projects' in data:
                existing_projects = data['projects']
            else:
                existing_projects = data
            print(f"Found {len(existing_projects)} existing projects")
        except json.JSONDecodeError:
            print("Error parsing existing projects response")
            existing_projects = []
    
    # For each test project, either use an existing one or create a new one
    for project in test_projects:
        requested_id = str(project.get('id', '')).strip()
        title = project.get('title', '').strip('"')
        completed = project.get('completed', False)
        active = project.get('active', True)
        description = project.get('description', '').strip('"')
        
        # Look for a matching project
        matching_project = next(
            (p for p in existing_projects if 
             p.get('title') == title and 
             str(p.get('completed')).lower() == str(completed).lower() and
             str(p.get('active')).lower() == str(active).lower() and
             p.get('description') == description),
            None
        )
        
        if matching_project:
            # Use existing project
            actual_id = matching_project.get('id')
            id_mapping[requested_id] = actual_id
            print(f"Using existing project with ID {actual_id} for requested ID {requested_id}")
            
            if actual_id not in context.test_data['projects']:
                context.test_data['projects'].append(actual_id)
        else:
            # Create a new project
            project_data = {
                'title': title,
                'completed': completed,
                'active': active,
                'description': description
            }
            
            create_response = requests.post(f"{context.base_url}/projects", json=project_data)
            
            if create_response.status_code in [200, 201]:
                try:
                    created_project = create_response.json()
                    actual_id = created_project.get('id')
                    id_mapping[requested_id] = actual_id
                    
                    context.test_data['projects'].append(actual_id)
                    print(f"Created new project with ID {actual_id} for requested ID {requested_id}")
                except json.JSONDecodeError:
                    print(f"Failed to parse response when creating project: {create_response.text}")
            else:
                print(f"Failed to create project: {create_response.status_code} - {create_response.text}")
    
    if not hasattr(context, 'id_mapping'):
        context.id_mapping = {}
    
    # Merge with existing mappings
    for req_id, actual_id in id_mapping.items():
        context.id_mapping[req_id] = actual_id

@then('the response JSON should include the following projects')
def step_verify_specific_projects(context):
    """Verify that specific projects are included in the response."""
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    # Handle different response formats
    if isinstance(context.response_data, dict) and 'projects' in context.response_data:
        projects = context.response_data['projects']
    else:
        projects = context.response_data
    
    expected_projects = []
    for row in context.table:
        requested_id = row['id']
        actual_id = get_mapped_id(context, requested_id)
        expected_project = {
            'id': actual_id,
            'title': row['title'].strip('"'),
            'completed': row['completed'].lower() == 'true',
            'active': row['active'].lower() == 'true',
            'description': row['description'].strip('"')
        }
        expected_projects.append(expected_project)
    
    # Verify each expected project exists in the response
    for expected in expected_projects:
        found = False
        for actual in projects:
            # Convert boolean values to strings for comparison
            actual_completed = str(actual.get('completed')).lower()
            expected_completed = str(expected['completed']).lower()
            actual_active = str(actual.get('active')).lower()
            expected_active = str(expected['active']).lower()
            
            if (str(actual.get('id')) == str(expected['id']) or 
                (actual.get('title') == expected['title'] and 
                 actual_completed == expected_completed and
                 actual_active == expected_active and
                 actual.get('description') == expected['description'])):
                found = True
                print(f"Found matching project: {actual}")
                break
        
        assert found, f"Expected project with ID {expected['id']} or matching attributes not found"
    
    print(f"Verified all {len(expected_projects)} expected projects")

@then('the response JSON should contain only projects where {filter_key} equals "{filter_value}"')
def step_verify_filtered_projects(context, filter_key, filter_value):
    """Verify that all projects in the response match the specified filter."""
    if not hasattr(context, 'response_data'):
        try:
            context.response_data = context.response.json()
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    
    # Handle different response formats
    if isinstance(context.response_data, dict) and 'projects' in context.response_data:
        projects = context.response_data['projects']
    else:
        projects = context.response_data
    
    # Process the expected value based on its type
    if filter_value.lower() in ['true', 'false']:
        expected_value = filter_value.lower()
    else:
        expected_value = filter_value.strip('"')
    
    print(f"Checking {len(projects)} projects for filter {filter_key}={expected_value}")
    
    if len(projects) > 0:
        for project in projects:
            actual_value = str(project.get(filter_key)).lower() if filter_key in project else None
            assert str(actual_value) == str(expected_value), \
                f"Project does not match filter: expected {filter_key}={expected_value}, got {filter_key}={actual_value}"
            print(f"Verified project matches filter: {project}")