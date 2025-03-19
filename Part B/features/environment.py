"""
Environment configuration for Behave tests.
"""
import requests
import json
import sys
from time import sleep

def before_all(context):
    """Run before all tests to check if the API is running."""
    # Base URL of the API
    context.base_url = "http://localhost:4567"
    
    # Check if the API is running
    try:
        response = requests.get(f"{context.base_url}/todos", timeout=5)
        print(f"Connected to API at {context.base_url}")
        print(f"API Response Status: {response.status_code}")
    except (requests.ConnectionError, requests.Timeout) as e:
        print(f"ERROR: Could not connect to API at {context.base_url}")
        print(f"Please ensure the API service is running before executing tests.")
        sys.exit(1)  # Exit with error code - this will make the tests fail

def before_scenario(context, scenario):
    """Run before each scenario to reset the system state."""
    # Store original states to restore later
    context.original_state = {}
    
    # Capture the original state of all entities
    try:
        # Get all todos
        todos_response = requests.get(f"{context.base_url}/todos")
        if todos_response.status_code == 200:
            todos = todos_response.json()
            if isinstance(todos, dict) and 'todos' in todos:
                todos = todos['todos']
            context.original_state['todos'] = todos
        
        # Get all categories
        categories_response = requests.get(f"{context.base_url}/categories")
        if categories_response.status_code == 200:
            categories = categories_response.json()
            if isinstance(categories, dict) and 'categories' in categories:
                categories = categories['categories']
            context.original_state['categories'] = categories
        
        # Get all projects
        projects_response = requests.get(f"{context.base_url}/projects")
        if projects_response.status_code == 200:
            projects = projects_response.json()
            if isinstance(projects, dict) and 'projects' in projects:
                projects = projects['projects']
            context.original_state['projects'] = projects
            
        # Capture relationships
        context.original_state['relationships'] = {}
        # We'll store them when needed for specific tests
        
        print(f"Captured original state: {len(context.original_state.get('todos', []))} todos, " 
              f"{len(context.original_state.get('categories', []))} categories, "
              f"{len(context.original_state.get('projects', []))} projects")
    
    except Exception as e:
        print(f"Warning: Failed to capture original system state: {e}")
        context.original_state = {'todos': [], 'categories': [], 'projects': []}
    
    # Initialize test data tracking
    context.test_data = {
        'todos': [],
        'categories': [],
        'projects': [],
        'relationships': []  # Will store tuples like ('todos', 'categories', todo_id, category_id)
    }
    
    context.response = None  # Store API responses
    
    # Print scenario information for debugging
    print(f"\nExecuting scenario: {scenario.name}")

def after_scenario(context, scenario):
    """Run after each scenario to restore the system to its original state."""
    print("\nRestoring system to original state...")
    
    # 1. First, clean up relationships created during tests
    for rel_type, entity1, entity2, id1, id2 in context.test_data.get('relationships', []):
        try:
            # The endpoint format varies based on relationship type
            if rel_type == 'category_todos':
                # Delete relationship between category and todo
                url = f"{context.base_url}/categories/{id1}/todos/{id2}"
                response = requests.delete(url)
                print(f"Deleted {entity1}-{entity2} relationship: {id1}-{id2}, status: {response.status_code}")
            elif rel_type == 'category_projects':
                # Delete relationship between category and project
                url = f"{context.base_url}/categories/{id1}/projects/{id2}"
                response = requests.delete(url)
                print(f"Deleted {entity1}-{entity2} relationship: {id1}-{id2}, status: {response.status_code}")
            elif rel_type == 'project_tasks':
                # Delete relationship between project and todo (tasks)
                url = f"{context.base_url}/projects/{id1}/tasks/{id2}"
                response = requests.delete(url)
                print(f"Deleted {entity1}-{entity2} relationship: {id1}-{id2}, status: {response.status_code}")
            elif rel_type == 'todo_tasksof':
                # Delete relationship between todo and project (tasksof)
                url = f"{context.base_url}/todos/{id1}/tasksof/{id2}"
                response = requests.delete(url)
                print(f"Deleted {entity1}-{entity2} relationship: {id1}-{id2}, status: {response.status_code}")
        except Exception as e:
            print(f"Warning: Failed to delete relationship {entity1}-{entity2} {id1}-{id2}: {e}")
    
    # 2. Delete test entities in reverse order of dependency
    # First todos
    for todo_id in context.test_data.get('todos', []):
        try:
            response = requests.delete(f"{context.base_url}/todos/{todo_id}")
            print(f"Deleted test todo with ID: {todo_id}, status: {response.status_code}")
        except Exception as e:
            print(f"Warning: Failed to delete test todo {todo_id}: {e}")
    
    # Then projects
    for project_id in context.test_data.get('projects', []):
        try:
            response = requests.delete(f"{context.base_url}/projects/{project_id}")
            print(f"Deleted test project with ID: {project_id}, status: {response.status_code}")
        except Exception as e:
            print(f"Warning: Failed to delete test project {project_id}: {e}")
    
    # Finally categories
    for category_id in context.test_data.get('categories', []):
        try:
            response = requests.delete(f"{context.base_url}/categories/{category_id}")
            print(f"Deleted test category with ID: {category_id}, status: {response.status_code}")
        except Exception as e:
            print(f"Warning: Failed to delete test category {category_id}: {e}")
    
    # 3. Check that original entities still exist and restore if needed
    # Give the API a moment to process deletions
    sleep(0.5)
    
    # Restore todos if needed
    _check_and_restore_entities(context, 'todos')
    
    # Restore categories if needed
    _check_and_restore_entities(context, 'categories')
    
    # Restore projects if needed
    _check_and_restore_entities(context, 'projects')
    
    # 4. Check original relationships (would be implemented for specific tests)
    # This is complex and depends on the specific test case
    
    print("System restoration complete")

def _check_and_restore_entities(context, entity_type):
    """Helper function to check if original entities exist and restore them if needed."""
    # Get current entities
    response = requests.get(f"{context.base_url}/{entity_type}")
    if response.status_code != 200:
        print(f"Warning: Failed to get current {entity_type}, status: {response.status_code}")
        return
    
    current_entities = response.json()
    if isinstance(current_entities, dict) and entity_type in current_entities:
        current_entities = current_entities[entity_type]
    
    current_ids = [entity.get('id') for entity in current_entities if entity.get('id')]
    
    # Check original entities
    for original_entity in context.original_state.get(entity_type, []):
        original_id = original_entity.get('id')
        if original_id and original_id not in current_ids:
            print(f"Original {entity_type[:-1]} {original_id} is missing, attempting to restore")
            
            # Create a copy of the entity data without the ID
            entity_data = {k: v for k, v in original_entity.items() if k != 'id'}
            
            # Try to restore with the original ID
            try:
                restore_url = f"{context.base_url}/{entity_type}/{original_id}"
                restore_response = requests.post(restore_url, json=entity_data)
                if restore_response.status_code in [200, 201]:
                    print(f"Restored original {entity_type[:-1]} {original_id}")
                else:
                    print(f"Failed to restore {entity_type[:-1]} {original_id}, status: {restore_response.status_code}")
            except Exception as e:
                print(f"Error restoring {entity_type[:-1]} {original_id}: {e}")