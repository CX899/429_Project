import requests
import json

def setup_test_todos(context, test_todos):
    id_mapping = {}
    
    response = requests.get(f"{context.base_url}/todos")
    existing_todos = []
    
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, dict) and 'todos' in data:
                existing_todos = data['todos']
            else:
                existing_todos = data
            print(f"Found {len(existing_todos)} existing todos")
        except json.JSONDecodeError:
            print("Error parsing existing todos response")
            existing_todos = []
    
    for todo in test_todos:
        requested_id = str(todo.get('id', '')).strip()
        title = todo.get('title', '').strip('"')
        done_status = todo.get('doneStatus', 'false').lower() == 'true'
        description = todo.get('description', '').strip('"')
        
        matching_todo = next(
            (t for t in existing_todos if 
             t.get('title') == title and 
             str(t.get('doneStatus')).lower() == str(done_status).lower() and
             t.get('description') == description),
            None
        )
        
        if matching_todo:
            actual_id = matching_todo.get('id')
            id_mapping[requested_id] = actual_id
            print(f"Using existing todo with ID {actual_id} for requested ID {requested_id}")
            
            if actual_id not in context.test_data['todos']:
                context.test_data['todos'].append(actual_id)
        else:
            todo_data = {
                'title': title,
                'doneStatus': done_status,
                'description': description
            }
            
            create_response = requests.post(f"{context.base_url}/todos", json=todo_data)
            
            if create_response.status_code in [200, 201]:
                try:
                    created_todo = create_response.json()
                    actual_id = created_todo.get('id')
                    id_mapping[requested_id] = actual_id
                    
                    context.test_data['todos'].append(actual_id)
                    print(f"Created new todo with ID {actual_id} for requested ID {requested_id}")
                except json.JSONDecodeError:
                    print(f"Failed to parse response when creating todo: {create_response.text}")
            else:
                print(f"Failed to create todo: {create_response.status_code} - {create_response.text}")
    
    context.id_mapping = id_mapping
    return id_mapping

def get_mapped_id(context, requested_id):
    if hasattr(context, 'id_mapping') and requested_id in context.id_mapping:
        return context.id_mapping[requested_id]
    return requested_id

def verify_todo_exists(context, id):
    actual_id = get_mapped_id(context, id)
    url = f"{context.base_url}/todos/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Todo with ID {actual_id} does not exist"
    
    try:
        todo_data = response.json()
        print(f"Verified todo with ID {actual_id} exists")
        return todo_data
    except json.JSONDecodeError:
        assert False, f"Invalid JSON response when getting todo {actual_id}"
        
def parse_todo_from_response(response_data, id=None):
    if isinstance(response_data, list) and len(response_data) > 0:
        if id is not None:
            return next((t for t in response_data if str(t.get('id')) == str(id)), response_data[0])
        return response_data[0]
    elif isinstance(response_data, dict) and 'id' in response_data:
        return response_data
    elif isinstance(response_data, dict) and 'todos' in response_data:
        todos = response_data['todos']
        if id is not None and len(todos) > 0:
            return next((t for t in todos if str(t.get('id')) == str(id)), None)
        elif len(todos) > 0:
            return todos[0]
    return None