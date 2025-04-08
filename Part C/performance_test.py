# performance_test.py

import time
import csv
import random
import psutil
import requests
import os
import sys
from datetime import datetime
from faker import Faker

script_dir = os.path.dirname(__file__)
tests_dir = os.path.join(script_dir, 'tests')
utils_dir = os.path.join(tests_dir, 'utils')

if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)
if utils_dir not in sys.path:
    sys.path.insert(0, utils_dir)
if script_dir not in sys.path:
     sys.path.insert(0, script_dir)


try:
    from utils.api_client import get, post, put, delete
    from utils.config import BASE_URL
except ImportError as e:
    print(f"Error importing API client or config: {e}")
    print("Please ensure performance_test.py is in the project root directory",
          "and the utils directory exists under tests.")
    sys.exit(1)


# --- Configuration ---
script_directory = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = os.path.join(script_directory, "performance_results.csv")

# Define the number of objects to test at different stages
NUM_OBJECTS_STEPS = [10, 50, 100, 200, 500]

# Number of random operations (Create/Update/Delete) to perform at each step size
OPERATIONS_PER_STEP = 10 # Perform 10 operations per object type per step

# --- Globals ---
fake = Faker()
created_ids = {"todos": [], "categories": [], "projects": []}
results_data = [] # Store results before writing to CSV

# --- Helper Functions ---
def generate_random_data(object_type):
    """Generates random data dictionary for a given object type."""
    if object_type == "todos":
        return {
            "title": fake.sentence(nb_words=4),
            "description": fake.text(max_nb_chars=50),
            "doneStatus": random.choice([True, False])
        }
    elif object_type == "categories":
        return {
            "title": fake.word().capitalize(),
            "description": fake.sentence(nb_words=6)
        }
    elif object_type == "projects":
        return {
            "title": fake.company(),
            "description": fake.catch_phrase(),
            "active": random.choice([True, False]),
            "completed": random.choice([True, False])
        }
    else:
        return {}

def get_system_metrics():
    """Gets current CPU and Available Memory percentage."""
    cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking snapshot
    memory_info = psutil.virtual_memory()
    # Using available memory percentage might be more insightful than free
    # memory_available_percent = memory_info.available * 100 / memory_info.total
    memory_usage_percent = memory_info.percent # Overall system memory usage
    return cpu_percent, memory_usage_percent

def measure_operation(operation_func, endpoint, *args, **kwargs):
    """
    Measures the time taken for an API operation and captures system metrics.
    Returns: (duration, cpu_usage, memory_usage, status_code, error) tuple.
             error is None on success, or exception message on failure.
    """
    start_time = time.perf_counter()
    cpu_before, mem_before = get_system_metrics() # Metrics just before the call
    response = None
    error_message = None
    status_code = None

    try:
        response = operation_func(endpoint, *args, **kwargs)
        status_code = response.status_code
        # Raise HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if response is not None:
            status_code = response.status_code
        else:
            # Network error, etc. - no status code available
             status_code = "N/A" # Or some other indicator
    except Exception as e: # Catch other potential errors
        error_message = f"Unexpected error: {str(e)}"
        status_code = "Error"

    end_time = time.perf_counter()
    duration = end_time - start_time
    # Capture metrics again *after* if needed, or just use 'before' values
    # cpu_after, mem_after = get_system_metrics()

    return duration, cpu_before, mem_before, status_code, error_message, response


def cleanup_all_created_objects():
    """Deletes all objects created during the test run."""
    print("\n--- Starting Cleanup ---")
    total_deleted = 0
    for obj_type, ids in created_ids.items():
        print(f"Cleaning up {len(ids)} {obj_type}...")
        endpoint_base = f"/{obj_type}"
        for obj_id in ids:
            try:
                delete(f"{endpoint_base}/{obj_id}")
                total_deleted += 1
                # Optional: add a small delay if needed
                # time.sleep(0.01)
            except requests.exceptions.RequestException as e:
                print(f"  Warning: Failed to delete {obj_type} {obj_id}: {e}")
        print(f"Finished cleaning {obj_type}.")
    print(f"--- Cleanup Complete ({total_deleted} objects deleted) ---")


# --- Main Performance Test Logic ---

def run_performance_experiments():
    """Runs the performance tests for different object counts."""
    global results_data

    print("Starting API Performance Test...")
    print(f"Target steps (object counts): {NUM_OBJECTS_STEPS}")
    print(f"Operations per step per type: {OPERATIONS_PER_STEP}")
    print(f"Results will be saved to: {CSV_FILENAME}")

    # --- Check API Availability ---
    try:
        response = get("/")
        if response.status_code != 200:
            print(f"Error: API at {BASE_URL} is not responding correctly (Status: {response.status_code}). Exiting.")
            sys.exit(1)
        print(f"API connection to {BASE_URL} successful.")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to API at {BASE_URL}. Is it running? Details: {e}")
        sys.exit(1)


    current_object_count = {"todos": 0, "categories": 0, "projects": 0}

    for target_count in NUM_OBJECTS_STEPS:
        print(f"\n--- Testing with Target Object Count: {target_count} (per type) ---")

        # 1. Populate Phase: Create objects to reach the target count
        print("Populating objects...")
        objects_to_populate = {"todos": target_count - current_object_count["todos"],
                               "categories": target_count - current_object_count["categories"],
                               "projects": target_count - current_object_count["projects"]}

        for obj_type, num_to_add in objects_to_populate.items():
            if num_to_add <= 0:
                continue
            print(f"  Adding {num_to_add} {obj_type}...")
            endpoint = f"/{obj_type}"
            headers = {"Content-Type": "application/json"}
            added_count = 0
            for _ in range(num_to_add):
                data = generate_random_data(obj_type)
                # Measure the creation during population phase as well?
                # For simplicity now, we focus measurement on the next phase.
                try:
                    response = post(endpoint, data=data, headers=headers)
                    if response.status_code == 201:
                        obj_id = response.json().get("id")
                        if obj_id:
                            created_ids[obj_type].append(obj_id)
                            current_object_count[obj_type] += 1
                            added_count +=1
                    else:
                         print(f"  Warning: Failed to create {obj_type}. Status: {response.status_code}, Response: {response.text[:100]}")
                except requests.exceptions.RequestException as e:
                    print(f"  Warning: Request failed during population for {obj_type}: {e}")
            print(f"  Actually added {added_count} {obj_type}.")

        print(f"Current object counts: Todos={current_object_count['todos']}, Categories={current_object_count['categories']}, Projects={current_object_count['projects']}")

        # 2. Measurement Phase: Perform random CRUD operations
        print(f"Performing {OPERATIONS_PER_STEP} random operations per type...")
        total_ops_this_step = 0

        for obj_type in ["todos", "categories", "projects"]:
            endpoint_base = f"/{obj_type}"
            ids_list = created_ids[obj_type]
            headers = {"Content-Type": "application/json"}

            for i in range(OPERATIONS_PER_STEP):
                operation_type = random.choice(["CREATE", "UPDATE", "DELETE"])
                result_row = {
                    "timestamp": datetime.now().isoformat(),
                    "target_population": target_count,
                    "current_population": current_object_count[obj_type],
                    "object_type": obj_type,
                    "operation": operation_type,
                    "duration_sec": None,
                    "cpu_percent": None,
                    "memory_percent": None,
                    "status_code": None,
                    "error": None
                }

                duration, cpu, mem, status, error, response = None, None, None, None, None, None

                if operation_type == "CREATE":
                    data = generate_random_data(obj_type)
                    duration, cpu, mem, status, error, response = measure_operation(
                        post, endpoint_base, data=data, headers=headers
                    )
                    if error is None and response and status == 201:
                        new_id = response.json().get("id")
                        if new_id:
                            ids_list.append(new_id) # Add to our tracked list
                            current_object_count[obj_type] += 1


                elif operation_type == "UPDATE":
                    if not ids_list: # Can't update if nothing exists
                         result_row["error"] = "No objects available to update"
                         result_row["status_code"] = "Skipped"
                    else:
                        obj_id_to_update = random.choice(ids_list)
                        update_data = generate_random_data(obj_type) # Generate fresh data for update
                        endpoint = f"{endpoint_base}/{obj_id_to_update}"
                        duration, cpu, mem, status, error, _ = measure_operation(
                            put, endpoint, data=update_data, headers=headers
                        )

                elif operation_type == "DELETE":
                    if not ids_list: # Can't delete if nothing exists
                        result_row["error"] = "No objects available to delete"
                        result_row["status_code"] = "Skipped"
                    else:
                        obj_id_to_delete = random.choice(ids_list)
                        endpoint = f"{endpoint_base}/{obj_id_to_delete}"
                        duration, cpu, mem, status, error, _ = measure_operation(
                            delete, endpoint
                        )
                        if error is None and status == 200:
                           try:
                               ids_list.remove(obj_id_to_delete) # Remove from tracked list
                               current_object_count[obj_type] -= 1
                           except ValueError:
                               # Should not happen if logic is correct, but good to handle
                               print(f"  Warning: Tried to remove ID {obj_id_to_delete} ({obj_type}) but it wasn't in the list.")


                # Record results
                result_row["duration_sec"] = duration
                result_row["cpu_percent"] = cpu
                result_row["memory_percent"] = mem
                result_row["status_code"] = status
                if error and not result_row["error"]: # Don't overwrite specific errors like 'Skipped'
                    result_row["error"] = error

                results_data.append(result_row)
                total_ops_this_step += 1
                # Optional: Print progress within the step
                # print(f"    {obj_type} Op {i+1}/{OPERATIONS_PER_STEP}: {operation_type} -> Status={status}, Duration={duration:.4f}s")

        print(f"Finished {total_ops_this_step} measurement operations for step {target_count}.")


    # --- Write Results to CSV ---
    print(f"\n--- Writing {len(results_data)} results to {CSV_FILENAME} ---")
    if not results_data:
        print("No results to write.")
        return

    fieldnames = results_data[0].keys() # Get headers from the first result dict
    try:
        with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results_data)
        print("Results successfully written.")
    except IOError as e:
        print(f"Error writing results to CSV file: {e}")

# --- Script Execution ---
if __name__ == "__main__":
    try:
        run_performance_experiments()
    except Exception as e:
        print(f"\n--- An unexpected error occurred during the test run: {e} ---")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure cleanup happens even if the main loop fails
        cleanup_all_created_objects()
    print("\nPerformance Test Script Finished.")