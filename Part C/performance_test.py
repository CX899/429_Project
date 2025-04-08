import time
import csv
import random
import psutil
import requests
import os
import sys
from datetime import datetime
from faker import Faker

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__)) # More robust way to get script dir
tests_dir = os.path.join(script_dir, 'tests')
utils_dir = os.path.join(tests_dir, 'utils')
if tests_dir not in sys.path: sys.path.insert(0, tests_dir)
if utils_dir not in sys.path: sys.path.insert(0, utils_dir)
if script_dir not in sys.path: sys.path.insert(0, script_dir)

# Import API utilities
try:
    from tests.utils.api_client import get, post, put, delete
    from tests.utils.config import BASE_URL
except ImportError as e:
    print(f"Import Error: {e}")
    # Try importing directly if running from the script's directory maybe?
    try:
        from utils.api_client import get, post, put, delete
        from utils.config import BASE_URL
        print("Warning: Imported utils directly, assuming script run location.")
    except ImportError:
        print("Could not find API utilities. Ensure 'tests/utils' is accessible.")
        sys.exit(1)
except Exception as e:
    print(f"Unexpected error during import: {e}")
    sys.exit(1)


# Configuration
script_directory = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR_NAME = "performance_test_logs"
SUMMARY_DIR_NAME = "summary"
LOGS_DIR_PATH = os.path.join(script_directory, LOGS_DIR_NAME)
SUMMARY_DIR_PATH = os.path.join(LOGS_DIR_PATH, SUMMARY_DIR_NAME)
NUM_OBJECTS_STEPS = [100,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,13000,14000,15000,16000,17000,18000,19000,20000]

# Globals
fake = Faker()
created_ids = {"todos": [], "categories": [], "projects": []}
last_non_zero_cpu_smoothed = None
ZERO_THRESHOLD = 0.01  # Values below this are treated as zero for smoothing
script_start_time = time.time() # Initialize script start time

# Helper Functions

def generate_random_data(object_type):
    if object_type == "todos":
        return {"title": fake.sentence(nb_words=4), "description": fake.text(max_nb_chars=50), "doneStatus": random.choice([True, False])}
    elif object_type == "categories":
        return {"title": fake.word().capitalize(), "description": fake.sentence(nb_words=6)}
    elif object_type == "projects":
        return {"title": fake.company(), "description": fake.catch_phrase(), "active": random.choice([True, False]), "completed": random.choice([True, False])}
    return {}

def get_system_metrics():
    cpu_percent = None
    memory_usage_percent = None
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except Exception as e:
        print(f"Warning: Couldn't get CPU metrics: {e}")
    try:
        memory_info = psutil.virtual_memory()
        memory_usage_percent = memory_info.percent
    except Exception as e:
        print(f"Warning: Couldn't get memory metrics: {e}")
    return cpu_percent, memory_usage_percent

def measure_operation(operation_func, endpoint, *args, **kwargs):
    duration = None
    cpu_before, mem_before = None, None
    cpu_after, mem_after = None, None
    response = None
    error_message = None
    status_code = None
    start_time = None

    try:
        cpu_before, mem_before = get_system_metrics()
        start_time = time.perf_counter()
        response = operation_func(endpoint, *args, **kwargs)
        status_code = response.status_code
        # Check for common success codes (200 OK, 201 Created)
        if status_code not in [200, 201]:
             # Try to get more info from response body for errors
            try:
                 error_detail = response.json()
            except: # noqa E722
                 error_detail = response.text
            raise requests.exceptions.HTTPError(f"HTTP Error {status_code}: {error_detail}", response=response)
        # response.raise_for_status() # This might be too broad if non-2xx codes are sometimes expected but not errors for the test logic itself
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        # Ensure status_code is captured even if response object exists in exception
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
        else:
             status_code = "N/A" # Or some other indicator for connection errors etc.
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        status_code = "N/A"
    finally:
        end_time = time.perf_counter()
        cpu_after, mem_after = get_system_metrics()
        if start_time is not None:
            duration = end_time - start_time

    return duration, cpu_before, mem_before, cpu_after, mem_after, status_code, error_message, response

def cleanup_all_created_objects():
    print("\nCleaning up...")
    total_deleted = 0
    ids_to_delete = {k: list(v) for k, v in created_ids.items()}

    for obj_type, ids in ids_to_delete.items():
        print(f"Cleaning {len(ids)} {obj_type}...")
        endpoint_base = f"/{obj_type}"
        deleted_count_type = 0
        failed_count_type = 0

        # Iterate backwards or on a copy if removing while iterating
        for obj_id in reversed(ids): # Iterate backwards to safely remove
            try:
                # Add a small delay if needed, e.g., time.sleep(0.01)
                _duration, _cpu_b, _mem_b, _cpu_a, _mem_a, status, error, _resp = measure_operation(
                    delete, f"{endpoint_base}/{obj_id}")

                if error is None and status == 200:
                    total_deleted += 1
                    deleted_count_type += 1
                    try:
                        created_ids[obj_type].remove(obj_id)
                    except ValueError:
                        pass
                else:
                     failed_count_type += 1
                     print(f"  Warning: Failed to delete {obj_type} {obj_id}. Status: {status}, Error: {error}")

            except Exception as e:
                failed_count_type += 1
                print(f"  Warning: Error during measured deletion of {obj_type} {obj_id}: {e}")

        print(f"Finished cleaning {obj_type}. Success: {deleted_count_type}, Failed: {failed_count_type}")

    remaining_count = sum(len(v) for v in created_ids.values())
    print(f"Cleanup complete. Total attempted deletions tracked: {total_deleted}. Estimated remaining (if cleanup failed): {remaining_count}")


def write_results_to_csv(filepath, data_list, custom_fieldnames=None):
    if not data_list:
        print(f"  No results to write for {os.path.basename(filepath)}.")
        return

    default_fieldnames = [
        "timestamp",
        "sample_time_sec", # Renamed from transaction_time_sec
        "object_type",
        "operation",
        "target_population_step",
        "population_at_operation",
        "population_after_operation",
        "duration_sec",
        "cpu_percent_before",
        "cpu_percent_after",
        "cpu_percent_smoothed",
        "memory_percent_before",
        "memory_percent_after",
        "status_code",
        "error"
    ]

    fieldnames = custom_fieldnames if custom_fieldnames else default_fieldnames

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data_list)
        # print(f"  Results saved to {filepath}") # Reduce noise, print summary location later
    except IOError as e:
        print(f"  Error writing to {filepath}: {e}")
    except Exception as e:
        print(f"  Error writing CSV {filepath}: {e}")


# Main Test Logic
def run_performance_experiments():
    global last_non_zero_cpu_smoothed
    last_non_zero_cpu_smoothed = None
    # Dictionary to hold summary results, separated by object type and operation
    all_results_summary = {
        "todos": {"CREATE": [], "UPDATE": [], "DELETE": []},
        "categories": {"CREATE": [], "UPDATE": [], "DELETE": []},
        "projects": {"CREATE": [], "UPDATE": [], "DELETE": []}
    }
    system_performance_data = []

    print("Starting API Performance Test")
    print(f"Target steps: {NUM_OBJECTS_STEPS}")
    print("Operations per step/type: 1 CREATE, 1 UPDATE, 1 DELETE") # Updated description
    print(f"Results will be saved in: {LOGS_DIR_PATH}")
    print(f"Summary results will be saved in: {SUMMARY_DIR_PATH}")

    try:
        os.makedirs(LOGS_DIR_PATH, exist_ok=True)
        os.makedirs(SUMMARY_DIR_PATH, exist_ok=True)
        print(f"Log directories checked/created: {LOGS_DIR_PATH}, {SUMMARY_DIR_PATH}")
    except OSError as e:
        print(f"Error creating log directories: {e}")
        sys.exit(1)

    try:
        response = get("/")
        if response.status_code != 200:
             raise requests.exceptions.RequestException(f"API status check failed: {response.status_code}")
        print(f"API connection to {BASE_URL} is working.")
    except requests.exceptions.RequestException as e:
        print(f"Error: Can't connect to API at {BASE_URL}. ({e})")
        sys.exit(1)

    current_object_count = {"todos": 0, "categories": 0, "projects": 0}
    global created_ids
    created_ids = {"todos": [], "categories": [], "projects": []}

    for target_count in NUM_OBJECTS_STEPS:
        print(f"\n===== Testing Population Target: {target_count} =====")
        step_dir = os.path.join(LOGS_DIR_PATH, f"step_{target_count}")
        try:
            os.makedirs(step_dir, exist_ok=True)
            # print(f"Directory for step {target_count}: {step_dir}") # Less verbose
        except OSError as e:
            print(f"Error creating step directory {step_dir}: {e}")
            continue # Skip this step if dir creation fails

        # 1. Populate Phase
        start_populate_time = time.time()
        print(f"Populating objects to reach ~{target_count} per type...")
        objects_to_populate = {
            "todos": target_count - current_object_count["todos"],
            "categories": target_count - current_object_count["categories"],
            "projects": target_count - current_object_count["projects"]
        }

        total_added_this_step = 0
        for obj_type, num_to_add in objects_to_populate.items():
             if num_to_add <= 0:
                print(f"  Skipping population for {obj_type} (already at or above target).")
                continue

             print(f"  Attempting to add {num_to_add} {obj_type}...")
             endpoint = f"/{obj_type}"
             headers = {"Content-Type": "application/json"}
             added_count = 0
             failed_count = 0

             for i in range(num_to_add):
                 data = generate_random_data(obj_type)
                 try:
                     # Use basic post here, not full measure_operation for speed
                     response = post(endpoint, data=data, headers=headers)
                     if response.status_code == 201:
                         try:
                             obj_id = response.json().get("id")
                             if obj_id:
                                 created_ids[obj_type].append(str(obj_id))
                                 current_object_count[obj_type] += 1
                                 added_count += 1
                             else:
                                 print(f"  Warning: Created {obj_type} but no ID returned. Response: {response.text}")
                                 failed_count += 1
                         except (ValueError, AttributeError, KeyError) as json_err:
                             print(f"  Warning: Created {obj_type} but couldn't parse ID from response. Status: {response.status_code}, Error: {json_err}, Response: {response.text[:100]}...")
                             failed_count += 1
                     else:
                         # Log specific failures during population phase if needed
                         # print(f"  Warning: Failed to create {obj_type}. Status: {response.status_code}, Response: {response.text[:100]}")
                         failed_count += 1
                 except requests.exceptions.RequestException as e:
                     # print(f"  Warning: Request failed for {obj_type}: {e}")
                     failed_count += 1
                 except Exception as e:
                     # print(f"  Warning: Error during creation of {obj_type}: {e}")
                     failed_count += 1

                 # time.sleep(0.01)

             print(f"  Finished adding {obj_type}. Added: {added_count}, Failed/Skipped: {failed_count}")
             total_added_this_step += added_count

        end_populate_time = time.time()
        print(f"Population phase took {end_populate_time - start_populate_time:.2f} seconds (attempted adding {sum(v for v in objects_to_populate.values() if v > 0)}, successful: {total_added_this_step} objects)")
        print(f"Current counts: Todos={current_object_count['todos']}, Categories={current_object_count['categories']}, Projects={current_object_count['projects']}")


        # 2. Measurement Phase
        print(f"Performing measurement operations (CREATE, UPDATE, DELETE) per type...")
        operations_sequence = ["CREATE", "UPDATE", "DELETE"] # Define the fixed sequence

        for obj_type in ["todos", "categories", "projects"]:
            step_type_results = []
            endpoint_base = f"/{obj_type}"
            ids_list_for_step = list(created_ids[obj_type])
            headers = {"Content-Type": "application/json"}
            ops_performed_this_type = 0

            print(f" Testing {obj_type} at population {current_object_count[obj_type]}...")

            for operation_type in operations_sequence:
                pop_at_op_start = current_object_count[obj_type]
                current_timestamp = datetime.now().isoformat()
                current_sample_time = round(time.time() - script_start_time, 4) # Calculate elapsed time

                result_row = {
                    "timestamp": current_timestamp,
                    "sample_time_sec": current_sample_time,
                    "object_type": obj_type,
                    "operation": operation_type,
                    "target_population_step": target_count,
                    "population_at_operation": pop_at_op_start,
                    "population_after_operation": None,
                    "duration_sec": None,
                    "cpu_percent_before": None,
                    "cpu_percent_after": None,
                    "cpu_percent_smoothed": None,
                    "memory_percent_before": None,
                    "memory_percent_after": None,
                    "status_code": None,
                    "error": None
                }

                duration, cpu_b_actual, mem_b, cpu_a_actual, mem_a, status, error, response = None, None, None, None, None, None, None, None
                op_successful = False

                if operation_type == "CREATE":
                    data = generate_random_data(obj_type)
                    duration, cpu_b_actual, mem_b, cpu_a_actual, mem_a, status, error, response = measure_operation(
                        post, endpoint_base, data=data, headers=headers)
                    if error is None and status == 201:
                        try:
                            new_id = response.json().get("id")
                            if new_id:
                                new_id_str = str(new_id)
                                created_ids[obj_type].append(new_id_str)
                                ids_list_for_step.append(new_id_str)
                                current_object_count[obj_type] += 1
                                op_successful = True
                            else:
                                result_row["error"] = "CREATE succeeded (201) but no ID returned"
                        except Exception as parse_err:
                            result_row["error"] = f"CREATE succeeded (201) but failed to parse ID: {parse_err}"

                elif operation_type == "UPDATE":
                    if not ids_list_for_step:
                        result_row["error"] = "Skipped UPDATE: No objects available to update"
                        result_row["status_code"] = "SKIPPED"
                    else:
                        # Choose a random ID from the *current* list for this step
                        obj_id_to_update = random.choice(ids_list_for_step)
                        update_data = generate_random_data(obj_type)
                        endpoint = f"{endpoint_base}/{obj_id_to_update}"
                        duration, cpu_b_actual, mem_b, cpu_a_actual, mem_a, status, error, _ = measure_operation(
                            put, endpoint, data=update_data, headers=headers)
                        if error is None and status == 200:
                            op_successful = True
                        # Note: UPDATE does not change object count

                elif operation_type == "DELETE":
                    if not ids_list_for_step:
                        result_row["error"] = "Skipped DELETE: No objects available to delete"
                        result_row["status_code"] = "SKIPPED"
                    else:
                        # Choose a random ID from the *current* list for this step
                        obj_id_to_delete = random.choice(ids_list_for_step)
                        endpoint = f"{endpoint_base}/{obj_id_to_delete}"
                        duration, cpu_b_actual, mem_b, cpu_a_actual, mem_a, status, error, _ = measure_operation(
                            delete, endpoint)
                        if error is None and status == 200:
                           try:
                               ids_list_for_step.remove(obj_id_to_delete) # Remove from local list
                               created_ids[obj_type].remove(obj_id_to_delete) # Remove from global list
                               current_object_count[obj_type] -= 1
                               op_successful = True
                           except ValueError:
                               print(f"  Warning: DELETE successful but ID {obj_id_to_delete} not found in lists.")
                               result_row["error"] = f"DELETE successful (200) but ID {obj_id_to_delete} missing from tracking list"
                               current_object_count[obj_type] -= 1
                               op_successful = True # Mark as successful API-wise

                pop_after_op = current_object_count[obj_type]
                total_objects_after_op = sum(current_object_count.values()) # Recalculate total across all types

                cpu_smoothed = None
                if cpu_a_actual is not None: # Process CPU smoothing even if operation failed network-wise
                    if cpu_a_actual >= ZERO_THRESHOLD:
                        cpu_smoothed = cpu_a_actual
                        last_non_zero_cpu_smoothed = cpu_smoothed
                    elif last_non_zero_cpu_smoothed is not None:
                         # Use last known good value if current is zero/near-zero
                         cpu_smoothed = last_non_zero_cpu_smoothed
                    # else: cpu_smoothed remains None if we never got a non-zero reading

                op_duration = round(duration, 4) if duration is not None else None

                result_row["duration_sec"] = op_duration
                result_row["cpu_percent_before"] = round(cpu_b_actual, 2) if cpu_b_actual is not None else None
                result_row["memory_percent_before"] = round(mem_b, 2) if mem_b is not None else None
                result_row["cpu_percent_after"] = round(cpu_a_actual, 2) if cpu_a_actual is not None else None
                result_row["memory_percent_after"] = round(mem_a, 2) if mem_a is not None else None
                result_row["cpu_percent_smoothed"] = round(cpu_smoothed, 2) if cpu_smoothed is not None else None
                result_row["population_after_operation"] = pop_after_op
                result_row["status_code"] = status if status else result_row["status_code"] # Update status if measure_op provided one
                if error and not result_row["error"]: # Only add measure_op error if no specific error was set
                    result_row["error"] = str(error)

                step_type_results.append(result_row)
                ops_performed_this_type += 1

                # Add data to the correct summary list IF the operation was attempted (not skipped)
                if result_row["status_code"] != "SKIPPED":
                    if operation_type in all_results_summary[obj_type]:
                        all_results_summary[obj_type][operation_type].append(result_row)
                    else:
                         print(f"Warning: Unexpected operation type '{operation_type}' encountered for summary.")

                    # Add data for system performance summary after every measured operation
                    system_record = {
                        "timestamp": current_timestamp,
                        "sample_time_sec": current_sample_time,
                        "total_objects": total_objects_after_op, # Total across all types
                        "cpu_percent_after": result_row["cpu_percent_after"],
                        "cpu_percent_smoothed": result_row["cpu_percent_smoothed"],
                        "memory_percent_after": result_row["memory_percent_after"]
                    }
                    system_performance_data.append(system_record)
                else:
                    print(f"  Skipped {operation_type} for {obj_type} due to: {result_row['error']}")



            csv_filename = f"{obj_type}.csv"
            csv_filepath = os.path.join(step_dir, csv_filename)
            write_results_to_csv(csv_filepath, step_type_results) # Uses default fieldnames including sample_time_sec
            print(f" Completed {ops_performed_this_type} operations ({', '.join(operations_sequence)}) for {obj_type}. Results logged.")

        print(f"----- Finished tests for population target {target_count} -----")

    # Write Specific Summary Files after all steps are completed
    print("\nWriting summary files...")
    for obj_type, operations in all_results_summary.items():
        for op_type, results in operations.items():
            if results: # Only write if there's data
                summary_filename = f"{obj_type}_{op_type}_summary.csv"
                summary_filepath = os.path.join(SUMMARY_DIR_PATH, summary_filename)
                write_results_to_csv(summary_filepath, results) # Uses default fieldnames

    # Write System Performance Summary
    if system_performance_data:
        system_summary_filepath = os.path.join(SUMMARY_DIR_PATH, "system_performance_summary.csv")
        system_fieldnames = ["timestamp", "sample_time_sec", "total_objects", "cpu_percent_after", "cpu_percent_smoothed", "memory_percent_after"]
        write_results_to_csv(system_summary_filepath, system_performance_data, custom_fieldnames=system_fieldnames)

    print(f"Summary files written to: {SUMMARY_DIR_PATH}")


# Script Execution
if __name__ == "__main__":
    try:
        run_performance_experiments()
    except KeyboardInterrupt:
        print("\nTest interrupted by user. Running cleanup...")
    except Exception as e:
        print(f"\nAn unexpected error occurred during the test run: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nInitiating final cleanup...")
        cleanup_start_time = time.time()
        cleanup_all_created_objects()
        cleanup_end_time = time.time()
        print(f"Cleanup process took {cleanup_end_time - cleanup_start_time:.2f} seconds")

    end_run_time = time.time()
    total_duration = end_run_time - script_start_time
    print(f"\nTotal execution time: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
    print("Performance Test Complete")