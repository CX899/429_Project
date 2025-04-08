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
    print(f"Import Error")
    try:
        from utils.api_client import get, post, put, delete
        from utils.config import BASE_URL
        print("Imported directly")
    except ImportError:
        print("Utils missing")
        sys.exit(1)
except Exception as e:
    print(f"Import failed")
    sys.exit(1)

script_directory = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR_NAME = "performance_test_logs"
SUMMARY_DIR_NAME = "summary"
PLOTS_DIR_NAME = "plots"
LOGS_DIR_PATH = os.path.join(script_directory, LOGS_DIR_NAME)
SUMMARY_DIR_PATH = os.path.join(LOGS_DIR_PATH, SUMMARY_DIR_NAME)
PLOTS_DIR_PATH = os.path.join(LOGS_DIR_PATH, PLOTS_DIR_NAME)
NUM_OBJECTS_STEPS = [100,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,13000,14000,15000,16000,17000,18000,19000,20000]
OBJECT_TYPES = ["todos", "categories", "projects"]

fake = Faker()
created_ids = {obj_type: [] for obj_type in OBJECT_TYPES}
last_non_zero_cpu_smoothed = None
ZERO_THRESHOLD = 0.01
script_start_time = time.time()
population_duration = 0
cleanup_duration = 0

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
        pass
    try:
        memory_info = psutil.virtual_memory()
        memory_usage_percent = memory_info.percent
    except Exception as e:
        pass
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
        if status_code not in [200, 201]:
            try:
                 error_detail = response.json()
            except:
                 error_detail = response.text
            raise requests.exceptions.HTTPError(f"HTTP Error {status_code}: {error_detail}", response=response)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
        else:
             status_code = "N/A"
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
    global cleanup_duration
    cleanup_start = time.time()
    print("Cleaning...")
    total_deleted = 0
    ids_to_delete = {k: list(v) for k, v in created_ids.items()}

    for obj_type, ids in ids_to_delete.items():
        print(f"Cleaning {obj_type}")
        endpoint_base = f"/{obj_type}"
        deleted_count_type = 0
        failed_count_type = 0

        for obj_id in reversed(ids):
            try:
                response = delete(f"{endpoint_base}/{obj_id}")
                if response.status_code == 200:
                    total_deleted += 1
                    deleted_count_type += 1
                    try:
                        created_ids[obj_type].remove(obj_id)
                    except ValueError:
                        pass
                else:
                     failed_count_type += 1
                     print(f"Delete failed")
            except Exception as e:
                failed_count_type += 1
                print(f"Delete error")

        print(f"Cleaned {obj_type}")

    remaining_count = sum(len(v) for v in created_ids.values())
    print(f"Cleanup done")
    cleanup_end = time.time()
    cleanup_duration = cleanup_end - cleanup_start
    print(f"Cleanup finished")


def write_results_to_csv(filepath, data_list, custom_fieldnames=None):
    if not data_list:
        return

    default_fieldnames = [
        "timestamp",
        "sample_time_sec",
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
    except IOError as e:
        print(f"Write error")
    except Exception as e:
        print(f"CSV error")


def run_performance_experiments():
    global last_non_zero_cpu_smoothed, population_duration
    last_non_zero_cpu_smoothed = None
    population_duration = 0

    all_results_summary = {
        obj_type: {"CREATE": [], "UPDATE": [], "DELETE": []} for obj_type in OBJECT_TYPES
    }
    system_performance_data = []

    print("Starting test")
    print(f"Steps info")
    print("Ops info")
    print(f"Saving results")
    print(f"Plots location")

    try:
        os.makedirs(LOGS_DIR_PATH, exist_ok=True)
        os.makedirs(SUMMARY_DIR_PATH, exist_ok=True)
        os.makedirs(PLOTS_DIR_PATH, exist_ok=True)
        for obj_type in OBJECT_TYPES:
            os.makedirs(os.path.join(SUMMARY_DIR_PATH, obj_type), exist_ok=True)
            os.makedirs(os.path.join(PLOTS_DIR_PATH, obj_type), exist_ok=True)
        print(f"Log/Summary/Plot directories checked/created.")
    except OSError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        response = get("/")
        if response.status_code != 200:
             raise requests.exceptions.RequestException(f"API failed")
        print(f"API working")
    except requests.exceptions.RequestException as e:
        print(f"API error")
        sys.exit(1)

    current_object_count = {obj_type: 0 for obj_type in OBJECT_TYPES}
    global created_ids
    created_ids = {obj_type: [] for obj_type in OBJECT_TYPES}

    for target_count in NUM_OBJECTS_STEPS:
        print(f"Testing target")
        step_dir = os.path.join(LOGS_DIR_PATH, f"step_{target_count}")
        try:
            os.makedirs(step_dir, exist_ok=True)
        except OSError as e:
            print(f"Dir error")
            continue

        step_populate_start_time = time.time()
        print(f"Populating objects")
        objects_to_populate = {
             obj_type: target_count - current_object_count[obj_type] for obj_type in OBJECT_TYPES
        }

        total_added_this_step = 0
        for obj_type, num_to_add in objects_to_populate.items():
             if num_to_add <= 0:
                continue

             endpoint = f"/{obj_type}"
             headers = {"Content-Type": "application/json"}
             added_count = 0
             failed_count = 0

             for i in range(num_to_add):
                 data = generate_random_data(obj_type)
                 try:
                     response = post(endpoint, data=data, headers=headers)
                     if response.status_code == 201:
                         try:
                             obj_id = response.json().get("id")
                             if obj_id:
                                 created_ids[obj_type].append(str(obj_id))
                                 current_object_count[obj_type] += 1
                                 added_count += 1
                             else:
                                 failed_count += 1
                         except (ValueError, AttributeError, KeyError) as json_err:
                             failed_count += 1
                     else:
                         failed_count += 1
                 except requests.exceptions.RequestException as e:
                     failed_count += 1
                 except Exception as e:
                     failed_count += 1

             total_added_this_step += added_count

        step_populate_end_time = time.time()
        step_pop_duration = step_populate_end_time - step_populate_start_time
        population_duration += step_pop_duration
        print(f"Population done")
        print(f"Current counts")


        print(f"Measuring ops")
        operations_sequence = ["CREATE", "UPDATE", "DELETE"]

        for obj_type in OBJECT_TYPES:
            step_type_results = []
            endpoint_base = f"/{obj_type}"
            ids_list_for_step_ops = list(created_ids[obj_type])
            headers = {"Content-Type": "application/json"}
            ops_performed_this_type = 0

            for operation_type in operations_sequence:
                pop_at_op_start = current_object_count[obj_type]
                current_timestamp = datetime.now().isoformat()
                current_sample_time = round(time.time() - script_start_time, 4)

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

                duration, cpu_b, mem_b, cpu_a, mem_a, status, error, response = None, None, None, None, None, None, None, None
                op_successful_api = False
                ids_list_modified = False

                if operation_type == "CREATE":
                    data = generate_random_data(obj_type)
                    duration, cpu_b, mem_b, cpu_a, mem_a, status, error, response = measure_operation(
                        post, endpoint_base, data=data, headers=headers)
                    if error is None and status == 201:
                        op_successful_api = True
                        try:
                            new_id = response.json().get("id")
                            if new_id:
                                new_id_str = str(new_id)
                                created_ids[obj_type].append(new_id_str)
                                ids_list_for_step_ops.append(new_id_str)
                                current_object_count[obj_type] += 1
                                ids_list_modified = True
                            else:
                                result_row["error"] = "CREATE succeeded (201) but no ID returned"
                        except Exception as parse_err:
                             result_row["error"] = f"CREATE succeeded (201) but failed to parse ID: {parse_err}"

                elif operation_type == "UPDATE":
                    if not ids_list_for_step_ops:
                        result_row["error"] = "Skipped UPDATE: No objects available to update"
                        result_row["status_code"] = "SKIPPED"
                    else:
                        obj_id_to_update = random.choice(ids_list_for_step_ops)
                        update_data = generate_random_data(obj_type)
                        endpoint = f"{endpoint_base}/{obj_id_to_update}"
                        duration, cpu_b, mem_b, cpu_a, mem_a, status, error, _ = measure_operation(
                            put, endpoint, data=update_data, headers=headers)
                        if error is None and status == 200:
                            op_successful_api = True

                elif operation_type == "DELETE":
                    if not ids_list_for_step_ops:
                        result_row["error"] = "Skipped DELETE: No objects available to delete"
                        result_row["status_code"] = "SKIPPED"
                    else:
                        obj_id_to_delete = random.choice(ids_list_for_step_ops)
                        endpoint = f"{endpoint_base}/{obj_id_to_delete}"
                        duration, cpu_b, mem_b, cpu_a, mem_a, status, error, _ = measure_operation(
                            delete, endpoint)
                        if error is None and status == 200:
                           op_successful_api = True
                           try:
                               if obj_id_to_delete in created_ids[obj_type]:
                                   created_ids[obj_type].remove(obj_id_to_delete)
                               if obj_id_to_delete in ids_list_for_step_ops:
                                   ids_list_for_step_ops.remove(obj_id_to_delete)

                               current_object_count[obj_type] -= 1
                               ids_list_modified = True
                           except ValueError:
                               print(f"ID gone")
                               current_object_count[obj_type] -= 1
                               ids_list_modified = True


                pop_after_op = current_object_count[obj_type]
                total_objects_after_op = sum(current_object_count.values())

                cpu_smoothed = None
                if cpu_a is not None:
                    if cpu_a >= ZERO_THRESHOLD:
                        cpu_smoothed = cpu_a
                        last_non_zero_cpu_smoothed = cpu_smoothed
                    elif last_non_zero_cpu_smoothed is not None:
                         cpu_smoothed = last_non_zero_cpu_smoothed

                op_duration = round(duration, 4) if duration is not None else None

                result_row.update({
                    "duration_sec": op_duration,
                    "cpu_percent_before": round(cpu_b, 2) if cpu_b is not None else None,
                    "memory_percent_before": round(mem_b, 2) if mem_b is not None else None,
                    "cpu_percent_after": round(cpu_a, 2) if cpu_a is not None else None,
                    "memory_percent_after": round(mem_a, 2) if mem_a is not None else None,
                    "cpu_percent_smoothed": round(cpu_smoothed, 2) if cpu_smoothed is not None else None,
                    "population_after_operation": pop_after_op,
                    "status_code": status if status else result_row["status_code"],
                })
                if error and not result_row["error"]:
                    result_row["error"] = str(error)

                step_type_results.append(result_row)
                ops_performed_this_type += 1

                if result_row["status_code"] != "SKIPPED":
                    if operation_type in all_results_summary[obj_type]:
                        all_results_summary[obj_type][operation_type].append(result_row)
                    else:
                         print(f"Bad op")

                    system_record = {
                        "timestamp": current_timestamp,
                        "sample_time_sec": current_sample_time,
                        "total_objects": total_objects_after_op,
                        "cpu_percent_after": result_row["cpu_percent_after"],
                        "cpu_percent_smoothed": result_row["cpu_percent_smoothed"],
                        "memory_percent_after": result_row["memory_percent_after"]
                    }
                    system_performance_data.append(system_record)

            print(f"Measured ops for {obj_type} in step {target_count}")
            if step_type_results:
                step_filename = f"{obj_type}_step_{target_count}_results.csv"
                step_filepath = os.path.join(step_dir, step_filename)
                print(f"    Saving step results for {obj_type} to {step_filepath}")
                write_results_to_csv(step_filepath, step_type_results)
            else:
                print(f"    No step results to save for {obj_type} in step {target_count}")

        print(f"Step {target_count} done measuring operations.")

    print("Writing summaries")
    for obj_type, operations in all_results_summary.items():
        obj_type_dir = os.path.join(SUMMARY_DIR_PATH, obj_type)
        consolidated_results_for_type = []

        for op_type, results in operations.items():
            if results:
                summary_filename = f"{obj_type}_{op_type}_summary.csv"
                summary_filepath = os.path.join(obj_type_dir, summary_filename)
                write_results_to_csv(summary_filepath, results)

                consolidated_results_for_type.extend(results)

        if consolidated_results_for_type:
            consolidated_results_for_type.sort(key=lambda x: x.get('sample_time_sec', 0))

            consolidated_filename = f"{obj_type}_summary.csv"
            consolidated_filepath = os.path.join(obj_type_dir, consolidated_filename)
            write_results_to_csv(consolidated_filepath, consolidated_results_for_type)

    if system_performance_data:
        system_summary_filepath = os.path.join(SUMMARY_DIR_PATH, "system_performance_summary.csv")
        system_fieldnames = ["timestamp", "sample_time_sec", "total_objects", "cpu_percent_after", "cpu_percent_smoothed", "memory_percent_after"]
        write_results_to_csv(system_summary_filepath, system_performance_data, custom_fieldnames=system_fieldnames)

    print(f"Files done")
    print(f"System done")

    print("Making plots")
    generate_performance_plots(system_performance_data, all_results_summary)
    print(f"System-wide plots saved to: {PLOTS_DIR_PATH}")

    generate_object_specific_plots(OBJECT_TYPES, SUMMARY_DIR_PATH, PLOTS_DIR_PATH)
    print(f"Object-specific plots saved to subfolders within: {PLOTS_DIR_PATH}")


def generate_performance_plots(system_data, operation_data):
    if not system_data:
        print("No data")
        return

    try:
        df_system = pd.DataFrame(system_data)
        df_system = df_system.dropna(subset=['sample_time_sec', 'total_objects', 'cpu_percent_smoothed', 'memory_percent_after'])
        if df_system.empty:
             print("Empty data")
             return

        plt.figure(figsize=(12, 6))
        plt.plot(df_system['sample_time_sec'], df_system['cpu_percent_smoothed'], marker='.', linestyle='-', label='CPU % (Smoothed)')
        plt.title('CPU Usage Over Time')
        plt.xlabel('Sample Time (seconds since start)')
        plt.ylabel('CPU Usage (%)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR_PATH, 'cpu_vs_time.png'))
        plt.close()

        plt.figure(figsize=(12, 6))
        plt.plot(df_system['sample_time_sec'], df_system['memory_percent_after'], marker='.', linestyle='-', label='Memory %', color='orange')
        plt.title('Memory Usage Over Time')
        plt.xlabel('Sample Time (seconds since start)')
        plt.ylabel('Memory Usage (%)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR_PATH, 'memory_vs_time.png'))
        plt.close()

        plt.figure(figsize=(12, 6))
        plt.scatter(df_system['total_objects'], df_system['cpu_percent_smoothed'], marker='.', alpha=0.6, label='CPU % (Smoothed)')
        try:
            coeffs_cpu = np.polyfit(df_system['total_objects'], df_system['cpu_percent_smoothed'], 1)
            poly_cpu = np.poly1d(coeffs_cpu)
            plt.plot(df_system['total_objects'], poly_cpu(df_system['total_objects']), "r--", label=f'Trend (slope={coeffs_cpu[0]:.2E})')
        except Exception as e:
            print(f"Trend error")

        plt.title('CPU Usage vs Total Number of Objects')
        plt.xlabel('Total Objects (All Types)')
        plt.ylabel('CPU Usage (%)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR_PATH, 'cpu_vs_objects.png'))
        plt.close()

        plt.figure(figsize=(12, 6))
        plt.scatter(df_system['total_objects'], df_system['memory_percent_after'], marker='.', alpha=0.6, label='Memory %', color='orange')
        try:
            coeffs_mem = np.polyfit(df_system['total_objects'], df_system['memory_percent_after'], 1)
            poly_mem = np.poly1d(coeffs_mem)
            plt.plot(df_system['total_objects'], poly_mem(df_system['total_objects']), "r--", label=f'Trend (slope={coeffs_mem[0]:.2E})')
        except Exception as e:
            print(f"Trend error")

        plt.title('Memory Usage vs Total Number of Objects')
        plt.xlabel('Total Objects (All Types)')
        plt.ylabel('Memory Usage (%)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR_PATH, 'memory_vs_objects.png'))
        plt.close()

    except Exception as e:
        print(f"Plot error")
        import traceback
        traceback.print_exc()


def generate_object_specific_plots(object_types, summary_base_path, plots_base_path):
    print("\nGenerating object-specific plots...")
    operations = ["CREATE", "UPDATE", "DELETE"]
    colors = {"CREATE": "blue", "UPDATE": "green", "DELETE": "red"}
    duration_unit = "ms"
    duration_scale = 1000

    for obj_type in object_types:
        print(f"  Generating plots for {obj_type}...")
        obj_summary_dir = os.path.join(summary_base_path, obj_type)
        obj_plot_dir = os.path.join(plots_base_path, obj_type)
        consolidated_filepath = os.path.join(obj_summary_dir, f"{obj_type}_summary.csv")

        try:
            os.makedirs(obj_plot_dir, exist_ok=True)
        except OSError as e:
            print(f"    Warning: Could not create plot directory {obj_plot_dir}: {e}")
            continue

        if not os.path.exists(consolidated_filepath):
            print(f"    Warning: Consolidated summary file not found for {obj_type}, skipping plots: {consolidated_filepath}")
            continue

        try:
            df_ops = pd.read_csv(consolidated_filepath)
            df_ops = df_ops.dropna(subset=[
                'sample_time_sec', 'duration_sec', 'population_at_operation',
                'memory_percent_after', 'cpu_percent_smoothed', 'operation'
            ])

            if df_ops.empty:
                print(f"    Warning: No valid data found in {consolidated_filepath} after cleaning NAs.")
                continue

        except Exception as e:
            print(f"    Error reading or processing {consolidated_filepath}: {e}")
            continue

        def create_plot(x_col, y_col, title_suffix, x_label, y_label, y_scale, filename_suffix, use_scatter=False):
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.suptitle(f'{obj_type.capitalize()}: {title_suffix}', fontsize=14)
            for op in operations:
                df_filtered = df_ops[df_ops['operation'] == op]
                if not df_filtered.empty:
                    if use_scatter:
                         ax.scatter(df_filtered[x_col], df_filtered[y_col] * y_scale,
                                   color=colors[op], label=f'{op}', alpha=0.7, s=15)
                    else:
                         df_filtered = df_filtered.sort_values(by=x_col)
                         ax.plot(df_filtered[x_col], df_filtered[y_col] * y_scale, marker='.', linestyle='-',
                                color=colors[op], label=f'{op}', alpha=0.7)

            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend()
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plot_filename = f"figure_{filename_suffix}.png"
            plot_filepath = os.path.join(obj_plot_dir, plot_filename)
            try:
                plt.savefig(plot_filepath)
            except Exception as e:
                 print(f"    Warning: Failed to save plot {plot_filepath}: {e}")
            plt.close(fig)

        create_plot(x_col='sample_time_sec', y_col='duration_sec',
                    title_suffix='Transaction Time vs Sample Time',
                    x_label='Sample Time (seconds since start)',
                    y_label=f'Transaction Duration ({duration_unit})',
                    y_scale=duration_scale, filename_suffix='1_duration_vs_time',
                    use_scatter=False)

        create_plot(x_col='population_at_operation', y_col='duration_sec',
                    title_suffix='Transaction Time vs Number of Objects',
                    x_label=f'Number of {obj_type.capitalize()} Objects (at operation start)',
                    y_label=f'Transaction Duration ({duration_unit})',
                    y_scale=duration_scale, filename_suffix='2_duration_vs_objects',
                    use_scatter=True)

        create_plot(x_col='sample_time_sec', y_col='memory_percent_after',
                    title_suffix='Memory Use vs Sample Time',
                    x_label='Sample Time (seconds since start)',
                    y_label='Memory Usage (% After Op)',
                    y_scale=1, filename_suffix='3_memory_vs_time',
                    use_scatter=False)

        create_plot(x_col='population_at_operation', y_col='memory_percent_after',
                    title_suffix='Memory Use vs Number of Objects',
                    x_label=f'Number of {obj_type.capitalize()} Objects (at operation start)',
                    y_label='Memory Usage (% After Op)',
                    y_scale=1, filename_suffix='4_memory_vs_objects',
                    use_scatter=True)

        create_plot(x_col='sample_time_sec', y_col='cpu_percent_smoothed',
                    title_suffix='CPU Use vs Sample Time',
                    x_label='Sample Time (seconds since start)',
                    y_label='CPU Usage (% Smoothed After Op)',
                    y_scale=1, filename_suffix='5_cpu_vs_time',
                    use_scatter=False)

        create_plot(x_col='population_at_operation', y_col='cpu_percent_smoothed',
                    title_suffix='CPU Use vs Number of Objects',
                    x_label=f'Number of {obj_type.capitalize()} Objects (at operation start)',
                    y_label='CPU Usage (% Smoothed After Op)',
                    y_scale=1, filename_suffix='6_cpu_vs_objects',
                    use_scatter=True)

        print(f"    Finished plots for {obj_type}.")


def analyze_performance_results():
    print("Performance results:")

    total_duration_overall = time.time() - script_start_time
    measurement_duration = total_duration_overall - population_duration - cleanup_duration
    print(f"Total time")
    print(f"Phase times")
    print(f"Cleanup time")
    if (population_duration + cleanup_duration) > measurement_duration:
        print("Testing overhead")

    system_summary_filepath = os.path.join(SUMMARY_DIR_PATH, "system_performance_summary.csv")
    if os.path.exists(system_summary_filepath):
        try:
            df_system = pd.read_csv(system_summary_filepath)
            df_system = df_system.dropna(subset=['total_objects', 'cpu_percent_smoothed', 'memory_percent_after'])

            if not df_system.empty:
                min_objs = df_system['total_objects'].min()
                max_objs = df_system['total_objects'].max()
                print(f"Resource usage")

                cpu_start = df_system.iloc[0]['cpu_percent_smoothed']
                cpu_end = df_system.iloc[-1]['cpu_percent_smoothed']
                cpu_max = df_system['cpu_percent_smoothed'].max()
                print(f"CPU stats")
                if cpu_end > cpu_start * 1.2:
                     print("CPU increased")
                elif cpu_end < cpu_start * 0.8:
                     print("CPU decreased")
                else:
                     print("CPU stable")

                mem_start = df_system.iloc[0]['memory_percent_after']
                mem_end = df_system.iloc[-1]['memory_percent_after']
                mem_max = df_system['memory_percent_after'].max()
                print(f"Memory stats")
                if mem_end > mem_start * 1.1:
                    print("Memory increased")
                else:
                    print("Memory stable")

            else:
                print("No data")
        except Exception as e:
            print(f"Analysis error")
    else:
        print("No file")

    print("Operations:")
    all_ops_data = []
    for obj_type in OBJECT_TYPES:
        consolidated_filepath = os.path.join(SUMMARY_DIR_PATH, obj_type, f"{obj_type}_summary.csv")
        if os.path.exists(consolidated_filepath):
            try:
                df_ops = pd.read_csv(consolidated_filepath)
                df_ops = df_ops.dropna(subset=['operation', 'duration_sec', 'target_population_step'])
                all_ops_data.append(df_ops)
            except Exception as e:
                print(f"File error")

    if all_ops_data:
        df_all_ops = pd.concat(all_ops_data, ignore_index=True)
        if not df_all_ops.empty:
            avg_durations = df_all_ops.groupby('operation')['duration_sec'].mean()
            print("Avg durations")
            for op, avg_dur in avg_durations.items():
                print(f"{op} time")

            create_ops = df_all_ops[df_all_ops['operation'] == 'CREATE']
            if not create_ops.empty:
                 median_step = np.median(NUM_OBJECTS_STEPS)
                 avg_dur_low_pop = create_ops[create_ops['target_population_step'] <= median_step]['duration_sec'].mean()
                 avg_dur_high_pop = create_ops[create_ops['target_population_step'] > median_step]['duration_sec'].mean()
                 if not (pd.isna(avg_dur_low_pop) or pd.isna(avg_dur_high_pop)):
                     print(f"CREATE trend")
                     if avg_dur_high_pop > avg_dur_low_pop * 1.1:
                         print("Slowed down")
                     else:
                         print("Stable speed")
                 else:
                      print("Insufficient data")
        else:
             print("No data")
    else:
        print("No files")

    print("Analysis done")


if __name__ == "__main__":
    try:
        run_performance_experiments()
        analyze_performance_results()
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Error")
        import traceback
        traceback.print_exc()
    finally:
        try:
            print("Final cleanup")
            cleanup_all_created_objects()
        except Exception as ce:
             print(f"Cleanup error")


    print(f"Test complete")