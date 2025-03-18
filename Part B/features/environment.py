import requests
import json
import time
from .utils import make_request, reset_system_state

BASE_URL = "http://localhost:4567"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def check_api_health(context):
    """Check if the API service is running and healthy"""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(f"{context.base_url}/health")
            if response.status_code == 200:
                return True
            else:
                print(f"API health check failed (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.ConnectionError:
            print(f"Could not connect to API (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
    return False

def setup_test_data(context):
    """Setup initial test data if needed"""
    # Example todos
    initial_todos = [
        {
            "title": "Initial Todo 1",
            "doneStatus": False,
            "description": "First todo for testing"
        },
        {
            "title": "Initial Todo 2",
            "doneStatus": True,
            "description": "Second todo for testing"
        }
    ]

    # Example categories
    initial_categories = [
        {
            "title": "Initial Category 1",
            "description": "First category for testing"
        },
        {
            "title": "Initial Category 2",
            "description": "Second category for testing"
        }
    ]

    # Example projects
    initial_projects = [
        {
            "title": "Initial Project 1",
            "completed": False,
            "active": True,
            "description": "First project for testing"
        },
        {
            "title": "Initial Project 2",
            "completed": True,
            "active": False,
            "description": "Second project for testing"
        }
    ]

    try:
        # Create initial todos
        for todo in initial_todos:
            make_request(context, "POST", "/todos", todo)

        # Create initial categories
        for category in initial_categories:
            make_request(context, "POST", "/categories", category)

        # Create initial projects
        for project in initial_projects:
            make_request(context, "POST", "/projects", project)

    except Exception as e:
        print(f"Failed to setup test data: {str(e)}")
        raise

def before_all(context):
    """Setup before all scenarios"""
    context.base_url = BASE_URL
    context.headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Check if API is available
    if not check_api_health(context):
        raise Exception("API service is not available. Please ensure the service is running.")

    # Store initial state configuration
    context.config.setup_data = True
    context.config.cleanup_needed = True

def before_feature(context, feature):
    """Setup before each feature"""
    # Reset system state before each feature
    if context.config.cleanup_needed:
        reset_system_state(context)
        if context.config.setup_data:
            setup_test_data(context)

def before_scenario(context, scenario):
    """Setup before each scenario"""
    # Initialize scenario-specific variables
    context.response = None
    context.request_data = None
    context.error_message = None

    # Reset system state if needed
    if "no_reset" not in scenario.tags:  # Allow scenarios to opt-out of reset
        reset_system_state(context)
        if context.config.setup_data:
            setup_test_data(context)

def after_scenario(context, scenario):
    """Cleanup after each scenario"""
    # Cleanup any scenario-specific resources
    if hasattr(context, 'created_resources'):
        for resource in context.created_resources:
            try:
                make_request(context, "DELETE", resource)
            except:
                print(f"Failed to cleanup resource: {resource}")

def after_feature(context, feature):
    """Cleanup after each feature"""
    if context.config.cleanup_needed:
        reset_system_state(context)

def after_all(context):
    """Cleanup after all scenarios"""
    try:
        # Final cleanup
        reset_system_state(context)
        print("Test suite completed - system reset to initial state")
    except:
        print("Warning: Failed to reset system to initial state after all tests")

def before_tag(context, tag):
    """Handle specific tags"""
    if tag == "no_reset":
        context.config.cleanup_needed = False
    elif tag == "require_setup":
        context.config.setup_data = True

def after_tag(context, tag):
    """Cleanup after tagged scenarios"""
    if tag == "no_reset":
        context.config.cleanup_needed = True
    elif tag == "require_setup":
        context.config.setup_data = False
