import time
import csv
import random
import psutil
import requests
import os
import sys
from datetime import datetime
from faker import Faker
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
tests_dir = os.path.join(script_dir, 'tests')
utils_dir = os.path.join(tests_dir, 'utils')
if tests_dir not in sys.path: sys.path.insert(0, tests_dir)
if utils_dir not in sys.path: sys.path.insert(0, utils_dir)
if script_dir not in sys.path: sys.path.insert(0, script_dir)

try:
    from tests.utils.api_client import get, post, put, delete
    from tests.utils.config import BASE_URL
except ImportError as e:
    print(f"Import Error: {e}")
    try:
        from utils.api_client import get, post, put, delete
        from utils.config import BASE_URL
        print("Imported directly")
    except ImportError:
        print("Utils missing")
        sys.exit(1)
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

script_directory = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR_NAME = "performance_test_logs"
SUMMARY_DIR_NAME = "summary"
PLOTS_DIR_NAME = "plots"
LOGS_DIR_PATH = os.path.join(script_directory, LOGS_DIR_NAME)
SUMMARY_DIR_PATH = os.path.join(LOGS_DIR_PATH, SUMMARY_DIR_NAME)
PLOTS_DIR_PATH = os.path.join(LOGS_DIR_PATH, PLOTS_DIR_NAME)
# Define population steps
NUM_OBJECTS_STEPS = [100,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,13000,14000,15000,16000,17000,18000,19000,20000]
OBJECT_TYPES = ["todos", "categories", "projects"]

fake = Faker()
created_ids = {obj_type: [] for obj_type in OBJECT_TYPES}
last_non_zero_cpu_smoothed = None
ZERO_THRESHOLD = 0.01 # CPU smoothing threshold
script_start_time = time.time()
population_duration = 0
cleanup_duration = 0

def generate_random_data(object_type):
    """Generates fake data dictionary."""
    if object_type == "todos":
        return {"title": fake.sentence(nb_words=4), "description": fake.text(max_nb_chars=50), "doneStatus": random.choice([True, False])}
    elif object_type == "categories":
        return {"title": fake.word().capitalize(), "description": fake.sentence(nb_words=6)}
    elif object_type == "projects":
        return {"title": fake.company(), "description": fake.catch_phrase(), "active": random.choice([True, False]), "completed": random.choice([True, False])}
    return {}

def get_system_metrics():
    """Gets CPU and memory usage."""
    cpu_percent = None
    memory_usage_percent = None
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1) # Non-blocking interval
    except Exception:
        pass # Ignore CPU metric error
    try:
        memory_info = psutil.virtual_memory()
        memory_usage_percent = memory_info.percent
    except Exception:
        pass # Ignore Memory metric error
    return cpu_percent, memory_usage_percent

def measure_operation(operation_func, endpoint, *args, **kwargs):
    """Measures duration and resources for API call."""
    duration = None
    # Use consistent variable names
    cpu_b, mem_b = None, None
    cpu_a, mem_a = None, None
    response = None
    error_message = None
    status_code = None
    start_time = None

    try:
        # Assign to consistent names
        cpu_b, mem_b = get_system_metrics()
        start_time = time.perf_counter()
        response = operation_func(endpoint, *args, **kwargs)
        status_code = response.status_code
        # Check for client/server errors
        if status_code >= 400:
            try:
                 error_detail = response.json()
                 # Extract common error messages
                 if isinstance(error_detail, dict) and 'errorMessages' in error_detail:
                     error_message = "; ".join(error_detail['errorMessages'])
                 elif isinstance(error_detail, dict) and 'message' in error_detail:
                     error_message = error_detail['message']
                 else:
                     error_message = str(error_detail) # Fallback
            except ValueError: # Not JSON
                 error_message = response.text[:200] # Limit length
            except Exception as json_e:
                 error_message = f"Error parsing response: {str(json_e)}"

            # Raise HTTPError for standard handling
            http_error = requests.exceptions.HTTPError(f"HTTP Error {status_code}: {error_message}", response=response)
            http_error.message = error_message # Store extracted message
            raise http_error

    except requests.exceptions.HTTPError as e:
        error_message = getattr(e, 'message', str(e)) # Use extracted message
        status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else "N/A HttpError"
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        status_code = "N/A ConnError"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        status_code = "N/A CodeError"
    finally:
        # Always execute
        end_time = time.perf_counter()
        # Assign to consistent names
        cpu_a, mem_a = get_system_metrics()
        if start_time is not None: # Calculate duration if possible
            duration = end_time - start_time

    # Return consistent names
    return duration, cpu_b, mem_b, cpu_a, mem_a, status_code, error_message, response

def cleanup_all_created_objects():
    """Deletes all objects created during test."""
    global cleanup_duration
    cleanup_start = time.time()
    print("Cleanup starting")
    total_deleted = 0
    # Copy dictionary for safe iteration
    ids_to_delete = {k: list(v) for k, v in created_ids.items()}

    for obj_type, ids in ids_to_delete.items():
        if not ids:
            # print(f"Cleanup skip {obj_type}: no ids")
            continue

        print(f"Cleaning {len(ids)} {obj_type}")
        endpoint_base = f"/{obj_type}"
        deleted_count_type = 0
        failed_count_type = 0

        # Delete in reverse
        for obj_id in reversed(ids):
            try:
                response = delete(f"{endpoint_base}/{obj_id}")
                if response.status_code == 200:
                    total_deleted += 1
                    deleted_count_type += 1
                    try:
                        created_ids[obj_type].remove(obj_id) # Remove from original dict
                    except ValueError:
                        # print(f"Warn: ID {obj_id} {obj_type} not found remove")
                        pass # Ignore if missing
                elif response.status_code == 404:
                     failed_count_type += 1
                     # print(f"Delete fail {obj_id} {obj_type}: 404 Not Found")
                     try: # Assume gone if 404
                         created_ids[obj_type].remove(obj_id)
                     except ValueError:
                         pass
                else:
                     failed_count_type += 1
                     # error_detail = response.text[:100]
                     # print(f"Delete fail {obj_id} {obj_type}: Status {response.status_code}")
            except requests.exceptions.Timeout:
                failed_count_type += 1
                # print(f"Delete timeout {obj_id} {obj_type}")
            except requests.exceptions.RequestException as e:
                failed_count_type += 1
                # print(f"Delete error {obj_id} {obj_type}: {e}")
            except Exception as e:
                failed_count_type += 1
                # print(f"Delete error {obj_id} {obj_type}: {e}")

        # print(f"Cleanup done {obj_type}: {deleted_count_type} deleted, {failed_count_type} failed")

    remaining_count = sum(len(v) for v in created_ids.values())
    print(f"Cleanup finished. Total deleted: {total_deleted}")
    if remaining_count > 0:
        print(f"Warn: {remaining_count} objects remain")
        # for obj_type, ids in created_ids.items():
        #     if ids:
        #         print(f"  {obj_type}: {len(ids)} remain")
    else:
        print("All objects removed")

    cleanup_end = time.time()
    cleanup_duration = cleanup_end - cleanup_start
    print(f"Cleanup duration: {cleanup_duration:.2f} sec")

def write_results_to_csv(filepath, data_list, custom_fieldnames=None):
    """Writes list of dicts to CSV file."""
    if not data_list:
        # print(f"Warn: No data for {filepath}")
        return

    # Default CSV columns
    default_fieldnames = [
        "timestamp", "sample_time_sec", "object_type", "operation",
        "target_population_step", "population_at_operation", "population_after_operation",
        "duration_sec", "cpu_percent_before", "cpu_percent_after", "cpu_percent_smoothed",
        "memory_percent_before", "memory_percent_after", "status_code", "error"
    ]

    fieldnames = custom_fieldnames if custom_fieldnames else default_fieldnames

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True) # Ensure dir exists
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Ignore extra dict keys
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data_list)
        # print(f"Wrote {len(data_list)} rows to {filepath}")
    except IOError as e:
        print(f"Error writing CSV {filepath}: {e}")
    except Exception as e:
        print(f"Unexpected CSV error {filepath}: {e}")

# --- Main Test Logic ---
def run_performance_experiments():
    """Runs population, measurement, saving."""
    global last_non_zero_cpu_smoothed, population_duration, created_ids
    last_non_zero_cpu_smoothed = None # Reset smoothing
    population_duration = 0 # Reset timer

    # Result storage
    all_results_summary = {
        obj_type: {"CREATE": [], "UPDATE": [], "DELETE": []} for obj_type in OBJECT_TYPES
    }
    system_performance_data = [] # Overall metrics

    print("Starting test")
    print(f"Steps: {NUM_OBJECTS_STEPS}")
    print(f"Types: {OBJECT_TYPES}")
    print(f"Logs: {LOGS_DIR_PATH}/step_*/")
    print(f"Summaries: {SUMMARY_DIR_PATH}/<type>/")
    print(f"Plots: {PLOTS_DIR_PATH}/")

    # Directory Setup
    try:
        os.makedirs(LOGS_DIR_PATH, exist_ok=True)
        os.makedirs(SUMMARY_DIR_PATH, exist_ok=True)
        os.makedirs(PLOTS_DIR_PATH, exist_ok=True)
        for obj_type in OBJECT_TYPES:
            os.makedirs(os.path.join(SUMMARY_DIR_PATH, obj_type), exist_ok=True)
            os.makedirs(os.path.join(PLOTS_DIR_PATH, obj_type), exist_ok=True)
        print("Directories created")
    except OSError as e:
        print(f"Error creating dirs: {e}")
        sys.exit(1)

    # API Check
    try:
        print(f"Checking API: {BASE_URL}")
        response = get("/") # Simple GET
        if response.status_code != 200:
             details = response.text[:100] if response.text else ""
             raise requests.exceptions.RequestException(
                 f"API check fail: {response.status_code}. {details}"
             )
        print(f"API responsive: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Fatal: API error {BASE_URL}")
        print(f"Error: {e}")
        sys.exit(1)

    # Initialization
    current_object_count = {obj_type: 0 for obj_type in OBJECT_TYPES}
    created_ids = {obj_type: [] for obj_type in OBJECT_TYPES} # Clear IDs

    # Main Test Loop (Steps)
    for target_count in NUM_OBJECTS_STEPS:
        step_start_time = time.time()
        print(f"Starting Step: {target_count}")
        step_dir = os.path.join(LOGS_DIR_PATH, f"step_{target_count}")
        try:
            os.makedirs(step_dir, exist_ok=True)
        except OSError as e:
            print(f"Warn: Skip step {target_count}, dir error: {e}")
            continue

        # Population Phase
        step_populate_start_time = time.time()
        print(f"Populating objects")
        objects_to_populate = {
             obj_type: max(0, target_count - current_object_count[obj_type])
             for obj_type in OBJECT_TYPES
        }

        total_added_this_step = 0
        any_population_errors = False
        for obj_type, num_to_add in objects_to_populate.items():
             if num_to_add <= 0:
                continue

             print(f"Adding {num_to_add} {obj_type}")
             endpoint = f"/{obj_type}"
             headers = {"Content-Type": "application/json", "Accept": "application/json"}
             added_count = 0
             failed_count = 0

             for i in range(num_to_add):
                 data = generate_random_data(obj_type)
                 try:
                     response = post(endpoint, data=data, headers=headers)
                     if response.status_code == 201:
                         try:
                             response_json = response.json()
                             obj_id = response_json.get("id")
                             if obj_id is not None:
                                 created_ids[obj_type].append(str(obj_id)) # Store as string
                                 current_object_count[obj_type] += 1
                                 added_count += 1
                             else:
                                 print(f"Warn: Create {obj_type} ok, no id")
                                 failed_count += 1; any_population_errors = True
                         except (ValueError, AttributeError, KeyError) as json_err:
                             print(f"Warn: Create {obj_type} ok, parse fail: {json_err}")
                             failed_count += 1; any_population_errors = True
                     else:
                         print(f"Warn: Create {obj_type} fail: {response.status_code}")
                         failed_count += 1; any_population_errors = True
                 except requests.exceptions.Timeout:
                      print(f"Warn: Create {obj_type} timeout")
                      failed_count += 1; any_population_errors = True
                 except requests.exceptions.RequestException as e:
                     print(f"Warn: Create {obj_type} fail: {e}")
                     failed_count += 1; any_population_errors = True
                 except Exception as e:
                     print(f"Warn: Create {obj_type} fail: {e}")
                     failed_count += 1; any_population_errors = True

             print(f"Added {obj_type}: {added_count} ok, {failed_count} fail")
             total_added_this_step += added_count

        step_populate_end_time = time.time()
        step_pop_duration = step_populate_end_time - step_populate_start_time
        population_duration += step_pop_duration
        print(f"Population done: {step_pop_duration:.2f} sec")
        if any_population_errors:
             print("Warn: Population errors occurred")
        print(f"Counts: {current_object_count}")


        # Measurement Phase
        print(f"Measuring operations")
        operations_sequence = ["CREATE", "UPDATE", "DELETE"]

        for obj_type in OBJECT_TYPES:
            step_type_results = [] # Step specific results
            endpoint_base = f"/{obj_type}"
            # Use copy of IDs for ops in this step
            ids_list_for_step_ops = list(created_ids[obj_type])
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            ops_performed_this_type = 0

            for operation_type in operations_sequence:
                pop_at_op_start = current_object_count[obj_type] # Count before op
                current_timestamp = datetime.now().isoformat()
                current_sample_time = round(time.time() - script_start_time, 4)

                # Result dictionary
                result_row = {
                    "timestamp": current_timestamp, "sample_time_sec": current_sample_time,
                    "object_type": obj_type, "operation": operation_type,
                    "target_population_step": target_count, "population_at_operation": pop_at_op_start,
                    "population_after_operation": None, "duration_sec": None,
                    "cpu_percent_before": None, "cpu_percent_after": None, "cpu_percent_smoothed": None,
                    "memory_percent_before": None, "memory_percent_after": None,
                    "status_code": None, "error": None
                }

                # Variables for measure_operation results
                duration, cpu_b, mem_b, cpu_a, mem_a, status, error_msg, response = None, None, None, None, None, None, None, None
                op_successful_api = False # Track API success
                ids_list_modified = False # Track count changes

                # Perform Operation
                if operation_type == "CREATE":
                    data = generate_random_data(obj_type)
                    duration, cpu_b, mem_b, cpu_a, mem_a, status, error_msg, response = measure_operation(
                        post, endpoint_base, data=data, headers=headers)

                    if error_msg is None and status == 201: # Success
                        op_successful_api = True
                        try:
                            new_id = response.json().get("id")
                            if new_id is not None:
                                new_id_str = str(new_id)
                                created_ids[obj_type].append(new_id_str) # Add to master
                                ids_list_for_step_ops.append(new_id_str) # Add to step list
                                current_object_count[obj_type] += 1
                                ids_list_modified = True
                            else:
                                result_row["error"] = "CREATE ok no id"
                        except Exception as parse_err:
                             result_row["error"] = f"CREATE ok parse fail: {parse_err}"

                elif operation_type == "UPDATE":
                    if not ids_list_for_step_ops:
                        result_row["error"] = "Skip UPDATE no objects"
                        result_row["status_code"] = "SKIPPED"
                    else:
                        obj_id_to_update = random.choice(ids_list_for_step_ops) # Random existing ID
                        update_data = generate_random_data(obj_type)
                        endpoint = f"{endpoint_base}/{obj_id_to_update}"
                        duration, cpu_b, mem_b, cpu_a, mem_a, status, error_msg, _ = measure_operation(
                            put, endpoint, data=update_data, headers=headers)
                        if error_msg is None and status == 200:
                            op_successful_api = True

                elif operation_type == "DELETE":
                    if not ids_list_for_step_ops:
                        result_row["error"] = "Skip DELETE no objects"
                        result_row["status_code"] = "SKIPPED"
                    else:
                        obj_id_to_delete = random.choice(ids_list_for_step_ops) # Random existing ID
                        endpoint = f"{endpoint_base}/{obj_id_to_delete}"
                        duration, cpu_b, mem_b, cpu_a, mem_a, status, error_msg, _ = measure_operation(
                            delete, endpoint)

                        if error_msg is None and status == 200: # Success
                           op_successful_api = True
                           try:
                               if obj_id_to_delete in created_ids[obj_type]: # Remove from lists
                                   created_ids[obj_type].remove(obj_id_to_delete)
                               if obj_id_to_delete in ids_list_for_step_ops:
                                   ids_list_for_step_ops.remove(obj_id_to_delete)

                               current_object_count[obj_type] -= 1 # Decrement count
                               ids_list_modified = True
                           except ValueError:
                               # print(f"Warn: ID {obj_id_to_delete} {obj_type} missing on DELETE")
                               current_object_count[obj_type] = max(0, current_object_count[obj_type] - 1)
                               ids_list_modified = True
                        elif status == 404:
                            result_row["error"] = f"DELETE 404 id {obj_id_to_delete}"
                            if obj_id_to_delete in created_ids[obj_type]: created_ids[obj_type].remove(obj_id_to_delete)
                            if obj_id_to_delete in ids_list_for_step_ops: ids_list_for_step_ops.remove(obj_id_to_delete)


                # Post-Operation Recording
                pop_after_op = current_object_count[obj_type] # Count after op
                total_objects_after_op = sum(current_object_count.values()) # Total count after

                # Smoothed CPU
                cpu_smoothed = None
                if cpu_a is not None:
                    if cpu_a >= ZERO_THRESHOLD:
                        cpu_smoothed = cpu_a
                        last_non_zero_cpu_smoothed = cpu_smoothed # Update last good value
                    elif last_non_zero_cpu_smoothed is not None:
                         cpu_smoothed = last_non_zero_cpu_smoothed # Use last good value
                    # else: remains None

                op_duration = round(duration, 4) if duration is not None else None # Round duration

                # Update result row
                result_row.update({
                    "duration_sec": op_duration,
                    "cpu_percent_before": round(cpu_b, 2) if cpu_b is not None else None,
                    "memory_percent_before": round(mem_b, 2) if mem_b is not None else None,
                    "cpu_percent_after": round(cpu_a, 2) if cpu_a is not None else None,
                    "memory_percent_after": round(mem_a, 2) if mem_a is not None else None,
                    "cpu_percent_smoothed": round(cpu_smoothed, 2) if cpu_smoothed is not None else None,
                    "population_after_operation": pop_after_op,
                    "status_code": status if result_row["status_code"] != "SKIPPED" else "SKIPPED",
                })
                if error_msg and not result_row["error"]: # Record error if not set
                    result_row["error"] = str(error_msg)

                step_type_results.append(result_row) # Add row to step results
                ops_performed_this_type += 1

                # Store for overall summary and system data if not skipped
                if result_row["status_code"] != "SKIPPED":
                    if operation_type in all_results_summary[obj_type]:
                        all_results_summary[obj_type][operation_type].append(result_row)
                    else:
                         print(f"Warn: Bad op type {operation_type}")

                    # System record uses 'after' metrics
                    system_record = {
                        "timestamp": current_timestamp, "sample_time_sec": current_sample_time,
                        "total_objects": total_objects_after_op,
                        "cpu_percent_after": result_row["cpu_percent_after"],
                        "cpu_percent_smoothed": result_row["cpu_percent_smoothed"],
                        "memory_percent_after": result_row["memory_percent_after"]
                    }
                    system_performance_data.append(system_record)

            # End of Operations Loop (one type)
            # print(f"Measured {ops_performed_this_type} ops for {obj_type}")
            if step_type_results: # Save step results
                step_filename = f"{obj_type}_step_{target_count}_results.csv"
                step_filepath = os.path.join(step_dir, step_filename)
                # print(f"Saving step results {obj_type} to {step_filepath}")
                write_results_to_csv(step_filepath, step_type_results)
            # else:
            #     print(f"Warn: No step results {obj_type} step {target_count}")

        # End of Object Type Loop (one step)
        step_end_time = time.time()
        # print(f"Measurement done step {target_count} in {step_end_time - step_populate_end_time:.2f} sec")
        print(f"Step {target_count} done in {step_end_time - step_start_time:.2f} sec")


    # Post-Loop: Write Summaries and Plots
    print("Writing summaries")
    for obj_type, operations in all_results_summary.items():
        obj_type_dir = os.path.join(SUMMARY_DIR_PATH, obj_type)
        consolidated_results_for_type = [] # All results for this type

        # Write per-operation summary
        for op_type, results in operations.items():
            if results:
                summary_filename = f"{obj_type}_{op_type}_summary.csv"
                summary_filepath = os.path.join(obj_type_dir, summary_filename)
                # print(f"Writing {op_type} summary {obj_type} ({len(results)}) to {summary_filepath}")
                write_results_to_csv(summary_filepath, results)
                consolidated_results_for_type.extend(results) # Add to consolidated
            # else:
            #     print(f"No results for {obj_type} {op_type}")

        # Write consolidated summary (all ops for type)
        if consolidated_results_for_type:
            consolidated_results_for_type.sort(key=lambda x: x.get('sample_time_sec', 0)) # Sort by time
            consolidated_filename = f"{obj_type}_all_ops_summary.csv" # Name change
            consolidated_filepath = os.path.join(obj_type_dir, consolidated_filename)
            # print(f"Writing consolidated {obj_type} ({len(consolidated_results_for_type)}) to {consolidated_filepath}")
            write_results_to_csv(consolidated_filepath, consolidated_results_for_type)

    # Write system performance summary
    if system_performance_data:
        system_summary_filepath = os.path.join(SUMMARY_DIR_PATH, "system_performance_summary.csv")
        system_fieldnames = ["timestamp", "sample_time_sec", "total_objects", "cpu_percent_after", "cpu_percent_smoothed", "memory_percent_after"]
        print(f"Writing system summary ({len(system_performance_data)})")
        write_results_to_csv(system_summary_filepath, system_performance_data, custom_fieldnames=system_fieldnames)
    else:
        print("No system data recorded")

    print("Finished writing summaries")

    # Generate Plots
    print("Generating plots")
    # System-wide plots
    generate_performance_plots(system_performance_data)
    # Object-specific plots
    generate_object_specific_plots(OBJECT_TYPES, SUMMARY_DIR_PATH, PLOTS_DIR_PATH)
    print("Finished generating plots")


def generate_performance_plots(system_data):
    """Generates system-wide plots."""
    print("Generating system plots")
    if not system_data:
        print("Warn: No system data for plots")
        return

    try:
        df_system = pd.DataFrame(system_data)
        df_system = df_system.dropna(subset=[ # Drop NA rows
            'sample_time_sec', 'total_objects',
            'cpu_percent_smoothed', 'memory_percent_after'
        ])

        if df_system.empty:
             print("Warn: System data empty after NA clean")
             return

        # Plot 1: CPU vs Time (Line)
        plt.figure(figsize=(12, 6))
        plt.plot(df_system['sample_time_sec'], df_system['cpu_percent_smoothed'], marker='.', linestyle='-', label='CPU % (Smoothed)')
        plt.title('System CPU Usage vs Time')
        plt.xlabel('Sample Time (sec)')
        plt.ylabel('CPU Usage (%)')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plot_path = os.path.join(PLOTS_DIR_PATH, 'system_cpu_vs_time.png')
        plt.savefig(plot_path); plt.close()
        # print(f"Saved: {plot_path}")

        # Plot 2: Memory vs Time (Line)
        plt.figure(figsize=(12, 6))
        plt.plot(df_system['sample_time_sec'], df_system['memory_percent_after'], marker='.', linestyle='-', label='Memory %', color='orange')
        plt.title('System Memory Usage vs Time')
        plt.xlabel('Sample Time (sec)')
        plt.ylabel('Memory Usage (%)')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plot_path = os.path.join(PLOTS_DIR_PATH, 'system_memory_vs_time.png')
        plt.savefig(plot_path); plt.close()
        # print(f"Saved: {plot_path}")

        # Sort by objects for next plots
        df_system_sorted = df_system.sort_values(by='total_objects').copy()

        # Plot 3: CPU vs Total Objects (Line)
        plt.figure(figsize=(12, 6))
        plt.plot(df_system_sorted['total_objects'], df_system_sorted['cpu_percent_smoothed'], marker='.', linestyle='-', alpha=0.7, label='CPU % (Smoothed)')
        # Optional trend line
        try:
            if df_system_sorted['total_objects'].nunique() > 1:
                coeffs_cpu = np.polyfit(df_system_sorted['total_objects'], df_system_sorted['cpu_percent_smoothed'], 1)
                poly_cpu = np.poly1d(coeffs_cpu)
                x_trend = np.linspace(df_system_sorted['total_objects'].min(), df_system_sorted['total_objects'].max(), 100)
                plt.plot(x_trend, poly_cpu(x_trend), "r--", linewidth=1.5, label=f'Trend')
            # else:
            #     print("Skip CPU trend: not enough unique counts")
        except Exception as e:
            print(f"Warn: CPU trend error: {e}")

        plt.title('System CPU Usage vs Total Objects')
        plt.xlabel('Total Objects')
        plt.ylabel('CPU Usage (%)')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plot_path = os.path.join(PLOTS_DIR_PATH, 'system_cpu_vs_objects.png')
        plt.savefig(plot_path); plt.close()
        # print(f"Saved: {plot_path}")

        # Plot 4: Memory vs Total Objects (Line)
        plt.figure(figsize=(12, 6))
        plt.plot(df_system_sorted['total_objects'], df_system_sorted['memory_percent_after'], marker='.', linestyle='-', alpha=0.7, label='Memory %', color='orange')
        # Optional trend line
        try:
             if df_system_sorted['total_objects'].nunique() > 1:
                coeffs_mem = np.polyfit(df_system_sorted['total_objects'], df_system_sorted['memory_percent_after'], 1)
                poly_mem = np.poly1d(coeffs_mem)
                x_trend = np.linspace(df_system_sorted['total_objects'].min(), df_system_sorted['total_objects'].max(), 100)
                plt.plot(x_trend, poly_mem(x_trend), "r--", linewidth=1.5, label=f'Trend')
             # else:
             #     print("Skip Mem trend: not enough unique counts")
        except Exception as e:
            print(f"Warn: Mem trend error: {e}")

        plt.title('System Memory Usage vs Total Objects')
        plt.xlabel('Total Objects')
        plt.ylabel('Memory Usage (%)')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plot_path = os.path.join(PLOTS_DIR_PATH, 'system_memory_vs_objects.png')
        plt.savefig(plot_path); plt.close()
        # print(f"Saved: {plot_path}")

    except Exception as e:
        print(f"Error generating system plots: {e}")
        # import traceback; traceback.print_exc()


def generate_object_specific_plots(object_types, summary_base_path, plots_base_path):
    """Generates object-specific plots."""
    print("Generating object plots")
    operations = ["CREATE", "UPDATE", "DELETE"]
    colors = {"CREATE": "blue", "UPDATE": "green", "DELETE": "red"}
    duration_unit = "ms" # Y-axis unit
    duration_scale = 1000 # Scale sec to ms

    for obj_type in object_types:
        print(f"Generating plots: {obj_type}")
        obj_summary_dir = os.path.join(summary_base_path, obj_type)
        obj_plot_dir = os.path.join(plots_base_path, obj_type)
        # Use consolidated summary file
        consolidated_filepath = os.path.join(obj_summary_dir, f"{obj_type}_all_ops_summary.csv")

        try:
            os.makedirs(obj_plot_dir, exist_ok=True)
        except OSError as e:
            print(f"Warn: Skip {obj_type}, dir error {obj_plot_dir}: {e}")
            continue # Skip type

        if not os.path.exists(consolidated_filepath):
            print(f"Warn: Skip {obj_type}, no summary file: {consolidated_filepath}")
            continue # Skip type

        try:
            df_ops = pd.read_csv(consolidated_filepath)
            df_ops = df_ops.dropna(subset=[ # Drop NA rows
                'sample_time_sec', 'duration_sec', 'population_at_operation',
                'memory_percent_after', 'cpu_percent_smoothed', 'operation'
            ])
            # Scale duration AFTER dropping NAs
            df_ops['duration_scaled'] = df_ops['duration_sec'] * duration_scale

            if df_ops.empty:
                print(f"Warn: Skip {obj_type}, no valid data in {consolidated_filepath}")
                continue # Skip type

        except FileNotFoundError:
             print(f"Error: File not found {consolidated_filepath}")
             continue
        except Exception as e:
            print(f"Error processing {consolidated_filepath}: {e}")
            continue # Skip type

        # Helper to create line plots
        def create_line_plot(df_data, x_col, y_col, title_suffix, x_label, y_label, filename_suffix):
            """Creates line plot split by operation."""
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.suptitle(f'{obj_type.capitalize()}: {title_suffix}', fontsize=14)
            plot_saved = False

            for op in operations:
                df_filtered = df_data[df_data['operation'] == op].copy()
                if not df_filtered.empty:
                    # Sort by X for line plot
                    df_filtered = df_filtered.sort_values(by=x_col)
                    ax.plot(df_filtered[x_col], df_filtered[y_col], marker='.', linestyle='-',
                            color=colors[op], label=f'{op}', alpha=0.7, markersize=4)

            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend()
            plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout

            plot_filename = f"{obj_type}_{filename_suffix}.png" # Filename
            plot_filepath = os.path.join(obj_plot_dir, plot_filename)
            try:
                plt.savefig(plot_filepath)
                plot_saved = True
            except Exception as e:
                 print(f"Warn: Save fail {plot_filepath}: {e}")
            plt.close(fig) # Free memory
            return plot_saved

        # Generate the 6 plots
        plot_results = []
        plot_results.append(create_line_plot(df_ops, 'sample_time_sec', 'duration_scaled',
                    'Time vs Sample Time', 'Sample Time (sec)', f'Duration ({duration_unit})', '1_duration_vs_time'))
        plot_results.append(create_line_plot(df_ops, 'population_at_operation', 'duration_scaled',
                    'Time vs Object Count', f'{obj_type.capitalize()} Count', f'Duration ({duration_unit})', '2_duration_vs_objects'))
        plot_results.append(create_line_plot(df_ops, 'sample_time_sec', 'memory_percent_after',
                    'Memory vs Sample Time', 'Sample Time (sec)', 'Memory (%)', '3_memory_vs_time'))
        plot_results.append(create_line_plot(df_ops, 'population_at_operation', 'memory_percent_after',
                    'Memory vs Object Count', f'{obj_type.capitalize()} Count', 'Memory (%)', '4_memory_vs_objects'))
        plot_results.append(create_line_plot(df_ops, 'sample_time_sec', 'cpu_percent_smoothed',
                    'CPU vs Sample Time', 'Sample Time (sec)', 'CPU (%)', '5_cpu_vs_time'))
        plot_results.append(create_line_plot(df_ops, 'population_at_operation', 'cpu_percent_smoothed',
                    'CPU vs Object Count', f'{obj_type.capitalize()} Count', 'CPU (%)', '6_cpu_vs_objects'))

        if all(plot_results):
            print(f"Plots saved for {obj_type}")
        else:
            print(f"Plot saving issues for {obj_type}")


def analyze_performance_results():
    """Basic textual analysis of results."""
    print("Analysis summary")

    total_duration_overall = time.time() - script_start_time
    pop_dur = max(0, population_duration)
    clean_dur = max(0, cleanup_duration)
    measurement_duration = max(0, total_duration_overall - pop_dur - clean_dur)

    print(f"Overall time: {total_duration_overall:.2f} sec")
    print(f"Population time: {pop_dur:.2f} sec")
    print(f"Measurement time: {measurement_duration:.2f} sec")
    print(f"Cleanup time: {clean_dur:.2f} sec")

    if (pop_dur + clean_dur) > measurement_duration * 1.5 and measurement_duration > 0:
        overhead_percentage = ((pop_dur + clean_dur) / total_duration_overall) * 100 if total_duration_overall > 0 else 0
        print(f"Note: High overhead {overhead_percentage:.1f}%")

    # System Resource Analysis
    print("System resource analysis")
    system_summary_filepath = os.path.join(SUMMARY_DIR_PATH, "system_performance_summary.csv")
    if os.path.exists(system_summary_filepath):
        try:
            df_system = pd.read_csv(system_summary_filepath)
            df_system = df_system.dropna(subset=['total_objects', 'cpu_percent_smoothed', 'memory_percent_after'])

            if not df_system.empty:
                min_objs = df_system['total_objects'].min()
                max_objs = df_system['total_objects'].max()
                print(f"Ops measured: {len(df_system)}")
                print(f"Objects range: {min_objs} to {max_objs}")

                # CPU Analysis
                cpu_start = df_system['cpu_percent_smoothed'].iloc[0] if not df_system.empty else None
                cpu_end = df_system['cpu_percent_smoothed'].iloc[-1] if not df_system.empty else None
                cpu_max = df_system['cpu_percent_smoothed'].max()
                cpu_avg = df_system['cpu_percent_smoothed'].mean()
                print(f"CPU Usage (%):")
                print(f" Start: {cpu_start:.2f}" if cpu_start is not None else " Start: N/A")
                print(f" End:   {cpu_end:.2f}" if cpu_end is not None else " End:   N/A")
                print(f" Avg:   {cpu_avg:.2f}")
                print(f" Max:   {cpu_max:.2f}")

                if cpu_start is not None and cpu_end is not None:
                    increase_threshold = cpu_start * 1.20; decrease_threshold = cpu_start * 0.80
                    if cpu_end > increase_threshold and cpu_start > 0.5:
                         print(" Trend: CPU increased")
                    elif cpu_end < decrease_threshold:
                         print(" Trend: CPU decreased")
                    else:
                         print(" Trend: CPU stable/varied")
                else:
                    print(" Trend: CPU trend N/A")

                # Memory Analysis
                mem_start = df_system['memory_percent_after'].iloc[0] if not df_system.empty else None
                mem_end = df_system['memory_percent_after'].iloc[-1] if not df_system.empty else None
                mem_max = df_system['memory_percent_after'].max()
                mem_avg = df_system['memory_percent_after'].mean()
                print(f"Memory Usage (%):")
                print(f" Start: {mem_start:.2f}" if mem_start is not None else " Start: N/A")
                print(f" End:   {mem_end:.2f}" if mem_end is not None else " End:   N/A")
                print(f" Avg:   {mem_avg:.2f}")
                print(f" Max:   {mem_max:.2f}")

                if mem_start is not None and mem_end is not None:
                     increase_threshold_abs = mem_start + 10; increase_threshold_rel = mem_start * 1.15
                     if mem_end > increase_threshold_abs or (mem_start > 0 and mem_end > increase_threshold_rel):
                         print(" Trend: Memory increased")
                     else:
                         print(" Trend: Memory stable/varied")
                else:
                    print(" Trend: Memory trend N/A")

            else:
                print("No valid system data")
        except FileNotFoundError:
             print("System summary file not found")
        except Exception as e:
            print(f"Error analyzing system file: {e}")
    else:
        print("System summary file not found")

    # Operation Duration Analysis
    print("Operation duration analysis")
    all_ops_data = []
    for obj_type in OBJECT_TYPES:
        consolidated_filepath = os.path.join(SUMMARY_DIR_PATH, obj_type, f"{obj_type}_all_ops_summary.csv")
        if os.path.exists(consolidated_filepath):
            try:
                df_ops = pd.read_csv(consolidated_filepath)
                df_ops = df_ops.dropna(subset=['object_type', 'operation', 'duration_sec', 'population_at_operation', 'target_population_step'])
                if not df_ops.empty:
                    all_ops_data.append(df_ops)
                # else:
                #     print(f"Note: No valid data in {consolidated_filepath}")
            except FileNotFoundError:
                print(f"Warn: File gone {consolidated_filepath}")
            except Exception as e:
                print(f"Error reading {consolidated_filepath}: {e}")
        # else:
        #      print(f"Warn: No summary file {obj_type}")

    if all_ops_data:
        df_all_ops = pd.concat(all_ops_data, ignore_index=True)
        if not df_all_ops.empty:
            avg_durations = df_all_ops.groupby('operation')['duration_sec'].mean() * 1000 # ms
            print("Avg Operation Durations (ms):")
            if not avg_durations.empty:
                for op, avg_dur in avg_durations.items():
                    print(f" {op:<7}: {avg_dur:.2f}")
            else:
                 print(" No duration data")

            # CREATE Trend Example
            create_ops = df_all_ops[df_all_ops['operation'] == 'CREATE'].copy()
            if not create_ops.empty:
                 median_pop = create_ops['population_at_operation'].median()
                 if pd.notna(median_pop) and median_pop > 0:
                     avg_dur_low = create_ops[create_ops['population_at_operation'] <= median_pop]['duration_sec'].mean()
                     avg_dur_high = create_ops[create_ops['population_at_operation'] > median_pop]['duration_sec'].mean()

                     if pd.notna(avg_dur_low) and pd.notna(avg_dur_high):
                         print(f"CREATE Trend (split ~{median_pop:.0f}):")
                         print(f" Low Pop Avg: {avg_dur_low*1000:.2f} ms")
                         print(f" High Pop Avg: {avg_dur_high*1000:.2f} ms")
                         if avg_dur_high > avg_dur_low * 1.15:
                             ratio = (avg_dur_high / avg_dur_low) if avg_dur_low > 0 else float('inf')
                             print(f" Trend: CREATE slows down ({ratio:.1f}x)")
                         else:
                             print(f" Trend: CREATE stable")
                     else:
                          print("CREATE Trend: N/A data")
                 else:
                      print("CREATE Trend: N/A median")
            else:
                 print("No CREATE data for trend")
            # Can add UPDATE/DELETE trends similarly
        else:
             print("No valid operation data found")
    else:
        print("No operation summary files found")

    print("Analysis Complete")


# --- Main Execution ---
if __name__ == "__main__":
    try:
        run_performance_experiments()
        analyze_performance_results()

    except KeyboardInterrupt:
        print("Test Interrupted")
    except SystemExit as e:
        print(f"Test Halted: {e}")
    except Exception as e:
        print(f"Unexpected Error During Test")
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Final cleanup starting")
        try:
            cleanup_all_created_objects()
        except Exception as ce:
             print(f"Error During Cleanup")
             print(f"Error: {type(ce).__name__}: {ce}")

    print("Test Script Finished")
    total_time = time.time() - script_start_time
    print(f"Total script time: {total_time:.2f} sec")