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
script_dir = os.path.dirname(__file__)
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
    sys.exit(1)

# Configuration
script_directory = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR_NAME = "performance_test_logs"
SUMMARY_DIR_NAME = "summary"
LOGS_DIR_PATH = os.path.join(script_directory, LOGS_DIR_NAME)
SUMMARY_DIR_PATH = os.path.join(LOGS_DIR_PATH, SUMMARY_DIR_NAME)
NUM_OBJECTS_STEPS = [10, 50, 75, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 2000, 3000,
                     4000, 5000, 6000, 7000, 8000, 9000, 10000]
OPERATIONS_PER_STEP = 10

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
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        status_code = response.status_code if response is not None else None
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
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

        for obj_id in ids:
            try:
                delete(f"{endpoint_base}/{obj_id}")
                total_deleted += 1
                deleted_count_type += 1
                try:
                    created_ids[obj_type].remove(obj_id)
                except ValueError:
                    pass
            except requests.exceptions.RequestException as e:
                failed_count_type += 1
                print(f"  Warning: Failed to delete {obj_type} {obj_id}: {e}")
            except Exception as e:
                failed_count_type += 1
                print(f"  Warning: Error deleting {obj_type} {obj_id}: {e}")

        print(f"Finished cleaning {obj_type}. Success: {deleted_count_type}, Failed: {failed_count_type}")

    remaining_count = sum(len(v) for v in created_ids.values())
    print(f"Cleanup complete. Deleted: {total_deleted}. Remaining: {remaining_count}")


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
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data_list)
        print(f"  Results saved to {filepath}")
    except IOError as e:
        print(f"  Error writing to {filepath}: {e}")
    except Exception as e:
        print(f"  Error with CSV {filepath}: {e}")


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
    print(f"Operations per step/type: {OPERATIONS_PER_STEP}")
    print(f"Results will be saved in: {LOGS_DIR_PATH}")
    print(f"Summary results will be saved in: {SUMMARY_DIR_PATH}")

    try:
        os.makedirs(LOGS_DIR_PATH, exist_ok=True)
        os.makedirs(SUMMARY_DIR_PATH, exist_ok=True)
        print(f"Log directories created: {LOGS_DIR_PATH}, {SUMMARY_DIR_PATH}")
    except OSError as e:
        print(f"Error creating log directories: {e}")
        sys.exit(1)

    try:
        response = get("/")
        response.raise_for_status()
        print(f"API connection to {BASE_URL} is working.")
    except requests.exceptions.RequestException as e:
        print(f"Error: Can't connect to API at {BASE_URL}. ({e})")
        sys.exit(1)

    current_object_count = {"todos": 0, "categories": 0, "projects": 0}

    for target_count in NUM_OBJECTS_STEPS:
        print(f"\nTesting Population Target: {target_count}")
        step_dir = os.path.join(LOGS_DIR_PATH, f"step_{target_count}")
        try:
            os.makedirs(step_dir, exist_ok=True)
            print(f"Created directory for step {target_count}")
        except OSError as e:
            print(f"Error creating step directory: {e}")
            continue

        # 1. Populate Phase
        start_populate_time = time.time()
        print("Populating objects...")
        objects_to_populate = {
            "todos": target_count-current_object_count["todos"],
            "categories": target_count-current_object_count["categories"],
            "projects": target_count-current_object_count["projects"]
        }

        total_added_this_step = 0
        for obj_type, num_to_add in objects_to_populate.items():
             if num_to_add <= 0:
                continue

             print(f"  Adding {num_to_add} {obj_type}...")
             endpoint = f"/{obj_type}"
             headers = {"Content-Type": "application/json"}
             added_count = 0

             for i in range(num_to_add):
                 data = generate_random_data(obj_type)
                 try:
                     response = post(endpoint, data=data, headers=headers)
                     if response.status_code == 201:
                         obj_id = response.json().get("id")
                         created_ids[obj_type].append(str(obj_id))
                         current_object_count[obj_type] += 1
                         added_count += 1
                     else:
                         print(f"  Warning: Failed to create {obj_type}. Status: {response.status_code}")
                 except requests.exceptions.RequestException as e:
                     print(f"  Warning: Request failed for {obj_type}: {e}")
                 except Exception as e:
                     print(f"  Warning: Error during creation of {obj_type}: {e}")

             print(f"  Added {added_count}/{num_to_add} {obj_type}")
             total_added_this_step += added_count

        end_populate_time = time.time()
        print(f"Population phase took {end_populate_time - start_populate_time:.2f} seconds (added {total_added_this_step} objects)")
        print(f"Current counts: Todos={current_object_count['todos']}, Categories={current_object_count['categories']}, Projects={current_object_count['projects']}")


        # 2. Measurement Phase
        print(f"Performing {OPERATIONS_PER_STEP} operations per type...")
        for obj_type in ["todos", "categories", "projects"]:
            step_type_results = []
            endpoint_base = f"/{obj_type}"
            ids_list = list(created_ids[obj_type])
            headers = {"Content-Type": "application/json"}
            ops_performed_this_type = 0

            print(f" Testing {obj_type} at population {current_object_count[obj_type]} (target {target_count})...")

            for i in range(OPERATIONS_PER_STEP):
                # Corrected operation names to match summary dictionary keys
                operation_type = random.choice(["CREATE", "UPDATE", "DELETE"])
                pop_at_op_start = current_object_count[obj_type]
                current_timestamp = datetime.now().isoformat()
                current_sample_time = round(time.time() - script_start_time, 4) # Calculate elapsed time

                result_row = {
                    "timestamp": current_timestamp,
                    "sample_time_sec": current_sample_time, # Add the sample time
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

                if operation_type == "CREATE":
                    data = generate_random_data(obj_type)
                    duration, cpu_b_actual, mem_b, cpu_a_actual, mem_a, status, error, response = measure_operation(
                        post, endpoint_base, data=data, headers=headers)
                    if error is None and status == 201:
                        new_id = response.json().get("id")
                        if new_id:
                            created_ids[obj_type].append(str(new_id))
                            ids_list.append(str(new_id))
                            current_object_count[obj_type] += 1
                elif operation_type == "UPDATE": # Changed PUT to UPDATE to match key
                    if not ids_list:
                        result_row["error"] = "No objects to update"
                        result_row["status_code"] = "Skipped"
                    else:
                        obj_id_to_update = random.choice(ids_list)
                        update_data = generate_random_data(obj_type)
                        endpoint = f"{endpoint_base}/{obj_id_to_update}"
                        duration, cpu_b_actual, mem_b, cpu_a_actual, mem_a, status, error, _ = measure_operation(
                            put, endpoint, data=update_data, headers=headers)
                elif operation_type == "DELETE":
                    if not ids_list:
                        result_row["error"] = "No objects to delete"
                        result_row["status_code"] = "Skipped"
                    else:
                        obj_id_to_delete = random.choice(ids_list)
                        endpoint = f"{endpoint_base}/{obj_id_to_delete}"
                        duration, cpu_b_actual, mem_b, cpu_a_actual, mem_a, status, error, _ = measure_operation(
                            delete, endpoint)
                        if error is None and status == 200:
                           try:
                               ids_list.remove(obj_id_to_delete)
                               created_ids[obj_type].remove(obj_id_to_delete)
                               current_object_count[obj_type] -= 1
                           except ValueError:
                               print(f"  Warning: Couldn't find ID {obj_id_to_delete} to remove.")

                pop_after_op = current_object_count[obj_type]
                total_objects_after_op = sum(current_object_count.values())

                cpu_smoothed = None
                if cpu_a_actual is not None and cpu_a_actual >= ZERO_THRESHOLD:
                    cpu_smoothed = cpu_a_actual
                    last_non_zero_cpu_smoothed = cpu_smoothed
                else:
                    cpu_smoothed = last_non_zero_cpu_smoothed

                op_duration = round(duration, 4) if duration is not None else None

                result_row["duration_sec"] = op_duration
                # sample_time_sec is already set above
                result_row["cpu_percent_before"] = round(cpu_b_actual, 2) if cpu_b_actual is not None else None
                result_row["memory_percent_before"] = round(mem_b, 2) if mem_b is not None else None
                result_row["cpu_percent_after"] = round(cpu_a_actual, 2) if cpu_a_actual is not None else None
                result_row["memory_percent_after"] = round(mem_a, 2) if mem_a is not None else None
                result_row["cpu_percent_smoothed"] = round(cpu_smoothed, 2) if cpu_smoothed is not None else None
                result_row["population_after_operation"] = pop_after_op
                result_row["status_code"] = status
                if error and not result_row["error"]:
                    result_row["error"] = str(error)

                step_type_results.append(result_row)
                ops_performed_this_type += 1

                # Add data to the correct summary list
                if operation_type in all_results_summary[obj_type]:
                    all_results_summary[obj_type][operation_type].append(result_row)
                else:
                     print(f"Warning: Unexpected operation type '{operation_type}' for summary.")


                # Add data for system performance summary
                system_record = {
                    "timestamp": current_timestamp,
                    "sample_time_sec": current_sample_time, # Add sample time here too
                    "total_objects": total_objects_after_op,
                    "cpu_percent_after": result_row["cpu_percent_after"],
                    "cpu_percent_smoothed": result_row["cpu_percent_smoothed"],
                    "memory_percent_after": result_row["memory_percent_after"]
                }
                system_performance_data.append(system_record)


            csv_filename = f"{obj_type}.csv"
            csv_filepath = os.path.join(step_dir, csv_filename)
            # Use default fieldnames which now include sample_time_sec
            write_results_to_csv(csv_filepath, step_type_results)
            print(f" Completed {ops_performed_this_type} operations for {obj_type}")

        print(f"Finished tests for population target {target_count}")

    # Write Specific Summary Files after all steps are completed
    print("\nWriting summary files...")
    for obj_type, operations in all_results_summary.items():
        for op_type, results in operations.items():
            summary_filename = f"{obj_type}_{op_type}_summary.csv"
            summary_filepath = os.path.join(SUMMARY_DIR_PATH, summary_filename)
            # Use default fieldnames for these summaries as well
            write_results_to_csv(summary_filepath, results)

    # Write System Performance Summary
    system_summary_filepath = os.path.join(SUMMARY_DIR_PATH, "system_performance_summary.csv")
    # Update system fieldnames to include sample_time_sec
    system_fieldnames = ["timestamp", "sample_time_sec", "total_objects", "cpu_percent_after", "cpu_percent_smoothed", "memory_percent_after"]
    write_results_to_csv(system_summary_filepath, system_performance_data, custom_fieldnames=system_fieldnames)

    print("Summary files written.")


# Script Execution
if __name__ == "__main__":
    # script_start_time is already initialized globally
    try:
        run_performance_experiments()
    except KeyboardInterrupt:
        print("\nTest interrupted by user. Running cleanup...")
    except Exception as e:
        print(f"\nError during run: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nStarting cleanup...")
        cleanup_start_time = time.time()
        cleanup_all_created_objects()
        cleanup_end_time = time.time()
        print(f"Cleanup took {cleanup_end_time - cleanup_start_time:.2f} seconds")

    end_run_time = time.time()
    total_duration = end_run_time - script_start_time
    print(f"\nTotal execution time: {total_duration:.2f} seconds")
    print("Performance Test Complete")