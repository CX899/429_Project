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
    
    if not hasattr(context, 'id_mapping'):
        context.id_mapping = {}
    
    # Merge with existing mappings
    for req_id, actual_id in id_mapping.items():
        context.id_mapping[req_id] = actual_id
        
    return id_mapping

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
    
    for req_id, actual_id in id_mapping.items():
        context.id_mapping[req_id] = actual_id
    
    return id_mapping

def get_mapped_id(context, requested_id):
    """
    Get the actual ID mapped from the requested ID.
    """
    if hasattr(context, 'id_mapping') and requested_id in context.id_mapping:
        return context.id_mapping[requested_id]
    return requested_id

def verify_entity_exists(context, entity_type, id):
    """
    Verify that an entity with the specified ID exists.
    
    Args:
        context: The behave context
        entity_type: The type of entity ('todos' or 'categories')
        id: The ID to check
    
    Returns:
        The entity data if it exists
    
    Raises:
        AssertionError: If the entity does not exist
    """
    actual_id = get_mapped_id(context, id)
    url = f"{context.base_url}/{entity_type}/{actual_id}"
    response = requests.get(url)
    
    assert response.status_code == 200, f"{entity_type.capitalize()[:-1]} with ID {actual_id} does not exist"
    
    try:
        entity_data = response.json()
        print(f"Verified {entity_type[:-1]} with ID {actual_id} exists")
        return entity_data
    except json.JSONDecodeError:
        assert False, f"Invalid JSON response when getting {entity_type[:-1]} {actual_id}"

def verify_todo_exists(context, id):
    """
    Verify that a todo with the specified ID exists.
    """
    return verify_entity_exists(context, 'todos', id)

def verify_category_exists(context, id):
    """
    Verify that a category with the specified ID exists.
    """
    return verify_entity_exists(context, 'categories', id)

def parse_entity_from_response(response_data, entity_type, id=None):
    """
    Parse entity data from a response, handling different response formats.
    
    Args:
        response_data: The parsed JSON response data
        entity_type: The type of entity ('todos' or 'categories')
        id: Optional ID to find a specific entity
    
    Returns:
        The parsed entity data
    """
    if isinstance(response_data, list) and len(response_data) > 0:
        if id is not None:
            return next((e for e in response_data if str(e.get('id')) == str(id)), response_data[0])
        return response_data[0]
    elif isinstance(response_data, dict) and 'id' in response_data:
        return response_data
    elif isinstance(response_data, dict) and entity_type in response_data:
        entities = response_data[entity_type]
        if id is not None and len(entities) > 0:
            return next((e for e in entities if str(e.get('id')) == str(id)), None)
        elif len(entities) > 0:
            return entities[0]
    return None

def parse_todo_from_response(response_data, id=None):
    """
    Parse todo data from a response, handling different response formats.
    """
    return parse_entity_from_response(response_data, 'todos', id)

def parse_category_from_response(response_data, id=None):
    """
    Parse category data from a response, handling different response formats.
    """
    return parse_entity_from_response(response_data, 'categories', id)

def map_endpoint_id(context, endpoint):
    """
    Map the ID in an endpoint to the actual ID if needed.
    
    Args:
        context: The behave context
        endpoint: The endpoint URL
    
    Returns:
        The mapped endpoint
    """
    entity_types = ['todos', 'categories', 'projects']
    
    for entity_type in entity_types:
        if f'/{entity_type}/' in endpoint:
            parts = endpoint.split('/')
            if len(parts) >= 3 and parts[2]:
                requested_id = parts[2]
                if hasattr(context, 'id_mapping') and requested_id in context.id_mapping:
                    actual_id = context.id_mapping[requested_id]
                    mapped_endpoint = f"/{entity_type}/{actual_id}"
                    if len(parts) > 3:
                        mapped_endpoint += '/' + '/'.join(parts[3:])
                    print(f"Mapped endpoint from {endpoint} to {mapped_endpoint}")
                    return mapped_endpoint
    
    return endpoint

def verify_error_message(context, expected_phrases):
    """
    Verify that the response contains an error message with the expected phrases.
    
    Args:
        context: The behave context
        expected_phrases: A list of phrases to look for in the error message
    
    Returns:
        True if the error message was found, False otherwise
    """
    try:
        if not hasattr(context, 'response_data'):
            try:
                context.response_data = context.response.json()
            except json.JSONDecodeError:
                context.response_data = None
    except Exception:
        context.response_data = None
    
    if context.response_data is None:
        for phrase in expected_phrases:
            if phrase.lower() in context.response.text.lower():
                print(f"Verified error message in text response contains: {phrase}")
                return True
        return False
    else:
        if 'errorMessages' in context.response_data and isinstance(context.response_data['errorMessages'], list):
            error_messages = context.response_data['errorMessages']
            for error in error_messages:
                for phrase in expected_phrases:
                    if phrase.lower() in error.lower():
                        print(f"Verified error message contains: {phrase}")
                        return True
        elif 'error' in context.response_data:
            error_text = str(context.response_data['error']).lower()
            for phrase in expected_phrases:
                if phrase.lower() in error_text:
                    print(f"Verified error message contains: {phrase}")
                    return True
        else:
            response_text = json.dumps(context.response_data).lower()
            for phrase in expected_phrases:
                if phrase.lower() in response_text:
                    print(f"Verified error message in response contains: {phrase}")
                    return True
        return False