# data_collector.py
#
# Purpose:
# This script automates the collection of performance and accuracy data for pallet
# optimization algorithms. It runs a Python-based PuLP solver and (attempts to)
# compile and run a C++ optimization algorithm for various problem instances.
# Results, including runtime, achieved profit/weight, and comparison against
# optimal solutions, are saved to a CSV file.
#
# How to Run:
# python data_collector.py
#
# Dependencies:
# - Python 3.x
# - PuLP library for python.py (install with: pip install pulp)
# - g++ compiler (and build essentials) for C++ compilation (e.g., sudo apt-get install build-essential)
#   (Needed if recompilation of the C++ part is triggered/desired)
#
# Expected Input Files (must be in the same directory as this script):
# 1. python.py: The Python script implementing the PuLP-based optimization.
# 2. P*.csv: CSV files containing pallet data for different problem instances (e.g., P5.csv, P10.csv).
#    Format: id,weight,profit (with header)
# 3. TP*.csv: CSV files containing truck data (capacity) for corresponding problem instances (e.g., TP5.csv).
#    Format: capacity,num_pallets (with header) - Note: num_pallets from TP file is not directly used by python.py or C++ in current setup.
# 4. OptimalSolution_*.txt: Text files containing the known optimal solutions for benchmarking.
#    Format can be:
#    - "optimal_profit, optimal_weight" (single line)
#    - "optimal_profit" (single line, weight assumed N/A)
#    - Multiple lines of "pallet_id, pallet_weight, pallet_profit" (profit & weight are summed)
# 5. C++ Source Files (for the C++ algorithm part):
#    - algorithms.cpp: Contains implementations of C++ optimization algorithms.
#    - readinputs_and_menu.cpp: Contains the main function and file reading for C++ (currently interactive).
#    - Algorithms.h (or Pallet.h): Header file for C++ algorithms, defining Pallet struct etc.
#      (Note: The script assumes these are present if C++ compilation is attempted.)
#
# Output File:
# - performance_results.csv: A CSV file summarizing the performance metrics for each
#   algorithm and problem instance.
#
# C++ Integration Note:
# The current C++ code (`readinputs_and_menu.cpp`) is interactive. For full, automated
# execution by this script, the C++ `main()` function would need modification to:
# 1. Accept input file paths as command-line arguments.
# 2. Bypass interactive menus when run with command-line arguments.
# 3. Ensure its output format includes total weight and matches the patterns expected by this script's
#    parsing functions (e.g., "Exact solution: Profit = P, Weight = W, Pallets = IDs").
# The script attempts one initial compilation of the C++ code. If this fails or the
# resulting executable has issues, C++ results will be logged as errors/placeholders.

import csv
import glob
import os
import subprocess
import time
import re

# Global variable to store the status of the initial C++ compilation attempt.
# This prevents repeated compilation attempts, especially in constrained environments.
CPP_COMPILATION_STATUS = {
    "compiled_successfully": False,
    "status_message": "NotAttempted",  # Initial status
    "executable_path": "./pallet_optimizer" # Target name for the compiled Linux C++ executable
}

def parse_python_output(output_str):
    """
    Parses the standard output string from the python.py script to extract
    total profit, total weight, and the list of selected pallet IDs.
    """
    profit, weight, pallets = None, None, [] # Initialize with default/None values

    # Regex to find "Total Profit: <value>"
    profit_match = re.search(r"Total Profit: (\S+)", output_str)
    if profit_match:
        try:
            profit = float(profit_match.group(1))
        except ValueError:
            profit = "ErrorParsingProfit" # Mark if conversion to float fails
    else:
        profit = "NoProfitInOutput" # Mark if pattern not found

    # Regex to find "Total Weight: <value>"
    weight_match = re.search(r"Total Weight: (\S+)", output_str)
    if weight_match:
        try:
            weight = float(weight_match.group(1))
        except ValueError:
            weight = "ErrorParsingWeight"
    else:
        weight = "NoWeightInOutput"

    # Regex to find "Selected Pallets: [<id1>, <id2>, ...]"
    pallets_match = re.search(r"Selected Pallets: \[([^\]]*)\]", output_str)
    if pallets_match:
        pallets_str = pallets_match.group(1) # Content between brackets
        if pallets_str:  # If not empty (e.g., "[]")
            try:
                # Split by comma, strip whitespace, convert to int, ignore if empty string after split
                pallets = [int(p.strip()) for p in pallets_str.split(',') if p.strip()]
            except ValueError:
                pallets = ["ErrorParsingPallets"] # Mark if int conversion fails for any pallet ID
        else:
            pallets = []  # Empty list if "Selected Pallets: []"
    else:
        pallets = ["NoPalletLineInOutput"] # Mark if the "Selected Pallets" line is entirely missing

    return profit, weight, pallets

def parse_optimal_solution(filepath):
    """
    Parses the OptimalSolution_*.txt file to extract optimal profit and weight.
    Handles multiple potential formats:
    1. Single line: "optimal_profit, optimal_weight"
    2. Single line: "optimal_profit" (weight becomes None)
    3. Multi-line (or single line): "pallet_id, pallet_weight, pallet_profit" per line,
       where profit and weight are summed up. This is based on observation of OptimalSolution_10.txt.
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip() # Read and remove leading/trailing whitespace
        lines = content.splitlines() # Split content into lines

        if not lines: # File is empty or contains only whitespace
            return None, None

        # Case 1 & 3 (single line parsing)
        if len(lines) == 1:
            line_content = lines[0].strip()
            if not line_content: # Single line is empty
                 return "ErrorOptimal_EmptyLine", "ErrorOptimal_EmptyLine"

            parts = [p.strip() for p in line_content.split(',')]
            
            # Try "optimal_profit, optimal_weight" format
            if len(parts) == 2:
                try:
                    return float(parts[0]), float(parts[1])
                except ValueError:
                    # If not two floats, it's an error for this specific format
                    return "ErrorOptimal_SingleLine2PartNonNumeric", "ErrorOptimal_SingleLine2PartNonNumeric"
            
            # Try "optimal_profit" format (single value)
            elif len(parts) == 1:
                try:
                    return float(parts[0]), None # Weight is not specified
                except ValueError:
                    return "ErrorOptimal_SingleLine1PartNonNumeric", "ErrorOptimal_SingleLine1PartNonNumeric"

            # Try "ID, Weight, Profit" format on a single line (e.g. if OptimalSolution_10.txt was one line)
            elif len(parts) == 3:
                 try:
                     # Assuming order ID, Weight, Profit; we want Profit and Weight
                     return float(parts[2]), float(parts[1])
                 except ValueError:
                     return "ErrorOptimal_SingleLine3PartNonNumeric", "ErrorOptimal_SingleLine3PartNonNumeric"
            else: # Single line, but not 1, 2, or 3 parts after splitting by comma
                return "ErrorOptimal_SingleLineUnrecognizedParts", "ErrorOptimal_SingleLineUnrecognizedParts"


        # Case 2 (multi-line parsing, summing "ID, Weight, Profit")
        total_profit_sum, total_weight_sum, pallets_found_in_list_format = 0, 0, 0
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped: continue # Skip empty lines within a multi-line file

            parts = [p.strip() for p in line_stripped.split(',')]
            if len(parts) == 3: # Expecting "ID, Weight, Profit"
                try:
                    # Assuming standard knapsack: profit is value, weight is cost.
                    # From typical CSV structure: ID, Weight, Profit
                    total_profit_sum += float(parts[2]) # Accumulate profit
                    total_weight_sum += float(parts[1]) # Accumulate weight
                    pallets_found_in_list_format += 1
                except ValueError: # Non-numeric value found where number expected
                    return "ErrorOptimal_PalletList_NonNumeric", "ErrorOptimal_PalletList_NonNumeric"
            # If a line is not 3 parts, and we previously found lines that were 3 parts, implies mixed format.
            elif pallets_found_in_list_format > 0:
                return "ErrorOptimal_MixedFormat", "ErrorOptimal_MixedFormat"
            else: # Line is not 3 parts, and no 3-part lines found yet. This implies a malformed multi-line file.
                  # This condition also catches cases where len(lines)>1 but format is unexpected.
                return f"ErrorOptimal_Line{i+1}_Not3Parts", f"ErrorOptimal_Line{i+1}_Not3Parts"

        if pallets_found_in_list_format > 0:
            return total_profit_sum, total_weight_sum
        
        # Fallback if no known format was successfully parsed
        return "ErrorOptimal_UnknownFormatOrStructure", "ErrorOptimal_UnknownFormatOrStructure"

    except FileNotFoundError:
        return None, None # Standard return if the optimal solution file doesn't exist
    except Exception as e: # Catch-all for other unexpected errors during file reading/parsing
        print(f"Generic error parsing optimal solution file {filepath}: {e}")
        return "ErrorReadingOptimalFile", "ErrorReadingOptimalFile"


def run_python_method(problem_id, tp_file, p_file):
    """
    Runs the python.py (PuLP solver) script as a subprocess for a given problem instance.
    Measures runtime and captures output for parsing.
    """
    command = ["python", "python.py", tp_file, p_file]
    start_time = time.time()
    try:
        # Execute the command. Timeout is set to handle cases where PuLP might take excessively long.
        process = subprocess.run(command, capture_output=True, text=True, timeout=600) # 10 minutes timeout
        runtime = time.time() - start_time
        if process.returncode == 0: # Successful execution
            return runtime, *parse_python_output(process.stdout) # Parse and unpack results
        else: # Script ran but returned an error code
            error_message = process.stderr or process.stdout # Get error message
            print(f"Error running python.py for {problem_id} (RC {process.returncode}): {error_message[:250]}")
            # Return error placeholders, including part of the error message for context
            return runtime, "PythonError", "PythonError", [f"ReturnCode{process.returncode}_{error_message[:50].replace(',',';').replaceCHR(10,' ')}"]
    except subprocess.TimeoutExpired:
        print(f"Timeout running python.py for {problem_id} after 600s")
        return 600.0, "Timeout", "Timeout", ["Timeout"]
    except FileNotFoundError: # python interpreter or python.py script not found
        print(f"Python interpreter or script 'python.py' not found for {problem_id}")
        return 0, "PythonNotFound", "PythonNotFound", ["PythonNotFound"]
    except Exception as e: # Other exceptions during subprocess execution
        print(f"Exception running python.py for {problem_id}: {e}")
        return time.time() - start_time, "PythonException", "PythonException", [str(e)[:100].replace(',',';').replaceCHR(10,' ')]

def attempt_initial_cpp_compilation():
    """
    Attempts to compile the C++ source files ONCE at the beginning of the script.
    Updates the global CPP_COMPILATION_STATUS dictionary.
    This avoids repeated, resource-intensive compilation attempts.
    """
    global CPP_COMPILATION_STATUS # Modify the global status variable
    executable_path = CPP_COMPILATION_STATUS["executable_path"]

    # Clean up: Remove pre-existing executables to ensure a fresh compile.
    # This handles cases where an incompatible (e.g., Windows .exe) or old version might exist.
    windows_style_exe = "./pallet_optimizer.exe" # Common name if from a Windows environment
    if os.path.exists(windows_style_exe):
        try:
            os.remove(windows_style_exe)
            print(f"Removed existing Windows-style exe: {windows_style_exe}.")
        except OSError as e:
            print(f"Warning: Could not remove {windows_style_exe}: {e}")

    if os.path.exists(executable_path): # Target Linux-style executable
        try:
            os.remove(executable_path)
            print(f"Removed existing Linux-style executable: {executable_path} for fresh compile.")
        except OSError as e:
            # If removal fails, update status and abort compilation attempt for this run
            CPP_COMPILATION_STATUS.update({
                "status_message": f"ErrorRemovingOldLinuxBinary: {e}",
                "compiled_successfully": False
            })
            return

    # Check for necessary C++ source files
    cpp_source_files = ["algorithms.cpp", "readinputs_and_menu.cpp"]
    # Assuming Algorithms.h or Pallet.h is also needed but g++ checks for headers during compilation.
    if not all(os.path.exists(f) for f in cpp_source_files):
        missing_files = [f for f in cpp_source_files if not os.path.exists(f)]
        print(f"C++ source files missing, cannot compile: {missing_files}")
        CPP_COMPILATION_STATUS.update({
            "status_message": f"CppSourceMissing: {missing_files}",
            "compiled_successfully": False
        })
        return

    # Define the g++ compilation command
    # -std=c++11 for compatibility
    # -O2 for optimization (can be removed if it causes issues with specific C++ code)
    compile_command = ["g++"] + cpp_source_files + ["-o", executable_path, "-std=c++11", "-O2"]
    print(f"Attempting initial C++ compilation: {' '.join(compile_command)}")
    
    try:
        # Run the compilation command
        compile_proc = subprocess.run(compile_command, capture_output=True, text=True, check=True, timeout=300) # 5 min timeout for compilation
        os.chmod(executable_path, 0o755) # Set execute permission on the new binary
        print(f"C++ compilation successful. Executable at {executable_path}")
        CPP_COMPILATION_STATUS.update({
            "compiled_successfully": True,
            "status_message": "CompilationSuccessful"
        })
    except subprocess.CalledProcessError as e: # g++ returned an error
        error_detail = e.stderr[:500].replace('\n', ' ') # Get first 500 chars of stderr, newline to space
        print(f"C++ compilation failed: {error_detail}")
        CPP_COMPILATION_STATUS.update({
            "status_message": f"CompilationFailed: {error_detail}",
            "compiled_successfully": False
        })
    except subprocess.TimeoutExpired:
        print("C++ compilation timed out after 300s.")
        CPP_COMPILATION_STATUS.update({
            "status_message": "CompilationTimeout",
            "compiled_successfully": False
        })
    except FileNotFoundError: # g++ compiler itself not found
         print("g++ compiler not found. Please ensure it is installed and in system PATH.")
         CPP_COMPILATION_STATUS.update({
             "status_message": "CompilerNotFound(g++)",
             "compiled_successfully": False
         })
    except Exception as e: # Other unexpected errors during compilation process
        print(f"An unexpected error occurred during C++ compilation: {e}")
        CPP_COMPILATION_STATUS.update({
            "status_message": f"CppCompileException: {str(e)[:200]}", # Store part of exception message
            "compiled_successfully": False
        })

def run_cpp_method(problem_id, tp_file, p_file):
    """
    Runs the compiled C++ algorithm for a given problem instance.
    Relies on the status of the initial compilation attempt (CPP_COMPILATION_STATUS).
    """
    global CPP_COMPILATION_STATUS
    # If initial compilation was not successful, return the error status from that attempt.
    if not CPP_COMPILATION_STATUS["compiled_successfully"]:
        status_msg_short = CPP_COMPILATION_STATUS['status_message'][:100] # Truncate for CSV
        return 0, status_msg_short, status_msg_short, [status_msg_short]

    executable_path = CPP_COMPILATION_STATUS["executable_path"]
    # Verify the executable exists and is executable right before trying to run it.
    # This is a safeguard in case something deleted/changed it after initial compilation.
    if not (os.path.exists(executable_path) and os.access(executable_path, os.X_OK)):
        err_msg = "CppExeMissingOrNotExecAtRuntime"
        print(f"Error: C++ executable {executable_path} missing or not executable at runtime for {problem_id}.")
        return 0, err_msg, err_msg, [err_msg]

    # Command to run the C++ executable, passing input files as arguments.
    # Note: This assumes the C++ main() is modified to handle these arguments.
    command = [executable_path, tp_file, p_file]
    start_time = time.time()
    
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=300) # 5 min timeout for C++ run
        runtime = time.time() - start_time

        if process.returncode == 0: # Successful execution of C++ program
            output_str = process.stdout
            profit, weight, pallets = None, None, [] # Initialize parse results

            # Regex patterns to parse C++ output.
            # Primary pattern expected (modify C++ to output this for its chosen algorithm):
            # "Exact solution: Profit = <P>, Weight = <W>, Pallets = <ID1> <ID2> ..."
            # or "Heuristic solution: Profit = <P>, Weight = <W>, Pallets = <ID1> <ID2> ..."
            primary_match = re.search(r"(?:Exact|Heuristic) solution: Profit = (\d+(?:\.\d+)?), Weight = (\d+(?:\.\d+)?), Pallets = ([\d\s]*)", output_str)
            if not primary_match:
                 # Fallback pattern, less specific, might be from other C++ output structures
                 primary_match = re.search(r"Total profit:\s*(\d+(?:\.\d+)?)\s*Total weight:\s*(\d+(?:\.\d+)?)\s*Selected pallets \(ID\):\s*([\d\s]*)", output_str, re.IGNORECASE)
            
            if primary_match:
                try:
                    profit = float(primary_match.group(1))
                    weight = float(primary_match.group(2))
                    pallets_str = primary_match.group(3).strip()
                    # Convert space-separated IDs to list of ints
                    pallets = [int(p) for p in pallets_str.split()] if pallets_str else []
                except ValueError: # Error parsing numbers from the matched groups
                    profit, weight, pallets = "CppParseError_MatchNum", "CppParseError_MatchNum", ["CppParseError_MatchNum"]
                except Exception as e: # Other errors during parsing of matched groups
                     profit, weight, pallets = "CppParseError_MatchExc", "CppParseError_MatchExc", [str(e)[:50].replace(',',';')]
            else: # No detailed pattern matched. Try to find generic "Profit: X" or "Weight: Y".
                profit_m = re.search(r"Profit:\s*(\d+(?:\.\d+)?)", output_str, re.IGNORECASE)
                if profit_m: profit = float(profit_m.group(1))
                
                weight_m = re.search(r"Weight:\s*(\d+(?:\.\d+)?)", output_str, re.IGNORECASE)
                if weight_m: weight = float(weight_m.group(1))
                
                if profit is None and weight is None: # No profit/weight info found at all.
                    return runtime, "CppNoOutputPattern", "CppNoOutputPattern", [f"Output: {output_str[:100]}...".replace('\n',' ').replace(',',';')]
                # If some profit/weight found but pallets not parsed from main patterns
                pallets = ["CppPalletsNotParsedGeneric"] if (profit is not None or weight is not None) else []
            return runtime, profit, weight, pallets
        else: # C++ program ran but returned a non-zero exit code (indicates an error)
            error_message = (process.stderr or process.stdout)[:200].replace('\n',' ').replace(',',';')
            # Specific check for file opening error message seen in the C++ source
            if "Error opening file" in error_message:
                print(f"C++: Reported error opening input files for {problem_id}: {error_message}")
                return runtime, "CppFileOpenError", "CppFileOpenError", [f"Err: {error_message}"]
            print(f"Error running C++ for {problem_id} (RC {process.returncode}): {error_message}")
            return runtime, f"CppErrorReturn{process.returncode}", f"CppErrorReturn{process.returncode}", [f"Err: {error_message}"]
    except OSError as e: # OS-level errors, e.g., "Exec format error" (e.errno == 8) if binary is incompatible
        error_msg = str(e)[:100].replace('\n',' ').replace(',',';')
        print(f"OSError running C++ for {problem_id} (errno {e.errno}): {error_msg}")
        # Note: No re-compilation is attempted here to conserve resources. Initial compile is final.
        return time.time() - start_time, f"CppOSError_e{e.errno}", f"CppOSError_e{e.errno}", [error_msg]
    except subprocess.TimeoutExpired:
        print(f"Timeout running C++ for {problem_id} after 300s")
        return 300.0, "CppTimeout", "CppTimeout", ["CppTimeout"]
    except Exception as e: # Other unexpected errors during C++ execution
        error_msg = str(e)[:100].replace('\n',' ').replace(',',';')
        print(f"Exception running C++ for {problem_id}: {error_msg}")
        return time.time() - start_time, "CppRunException", "CppRunException", [error_msg]

def main():
    """
    Main function to coordinate data collection.
    1. Attempts C++ compilation once.
    2. Finds and iterates through problem definition files (P*.csv).
    3. For each problem:
        a. Reads corresponding TP*.csv and OptimalSolution_*.txt.
        b. Runs Python (PuLP) method.
        c. Runs C++ method (if compiled successfully).
        d. Stores results.
    4. Writes aggregated results to performance_results.csv.
    """
    # Attempt C++ compilation once at the beginning of the script.
    # The result is stored in the global CPP_COMPILATION_STATUS.
    attempt_initial_cpp_compilation()
    print(f"Initial C++ compilation status: {CPP_COMPILATION_STATUS['status_message']}")

    results_data = [] # List to store dictionaries, each representing a row in the CSV

    # Find P*.csv files (problem instances).
    # Sort them based on the numeric part of their filename for ordered processing.
    problem_files = sorted(glob.glob("P[0-9]*.csv"), key=lambda x: int(re.search(r"P(\d+)\.csv", x).group(1)))

    if not problem_files:
        print("No problem files (P*.csv) found in the current directory. Creating empty performance_results.csv.")
        # Define CSV headers even if no data, for consistency
        fieldnames = ["method_name", "problem_id", "runtime", "profit_achieved", "optimal_profit", "weight_achieved", "optimal_weight", "selected_pallets"]
        try:
            with open("performance_results.csv", 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader() # Write only header if no problems
        except IOError as e:
            print(f"Error writing empty performance_results.csv: {e}")
        return # Exit if no problem files

    print(f"Found problem files: {problem_files}")

    for p_file_path in problem_files: # Iterate through each problem file
        p_file_name = os.path.basename(p_file_path)
        
        # Extract problem number (e.g., "5" from "P5.csv")
        problem_id_match = re.search(r"P(\d+)\.csv", p_file_name)
        if not problem_id_match: # Should not happen if glob pattern is correct
            print(f"Could not extract problem ID from {p_file_name}, skipping.")
            continue
        
        problem_num_str = problem_id_match.group(1)
        problem_id_for_csv = f"P{problem_num_str}" # e.g., "P5"

        # Construct filenames for corresponding truck data and optimal solution files
        tp_file_path = f"TP{problem_num_str}.csv"
        # Optimal solution filenames are zero-padded (e.g., OptimalSolution_05.txt)
        optimal_sol_file_path = f"OptimalSolution_{problem_num_str.zfill(2)}.txt"

        # Check if the corresponding TP file exists; skip problem if not
        if not os.path.exists(tp_file_path):
            print(f"Corresponding TP file {tp_file_path} not found for {p_file_path}. Skipping {problem_id_for_csv}.")
            # Add a row to results indicating this setup error
            results_data.append({
                "method_name": "SetupError", "problem_id": problem_id_for_csv, "runtime": 0,
                "profit_achieved": "TPFileNotFound", "optimal_profit": "N/A",
                "weight_achieved": "TPFileNotFound", "optimal_weight": "N/A", "selected_pallets": ""
            })
            continue # Move to the next problem file
        
        print(f"\nProcessing problem: {problem_id_for_csv} (PFile: {p_file_path}, TPFile: {tp_file_path})")

        # Process Optimal Solution data
        print(f"Reading optimal solution from: {optimal_sol_file_path}")
        opt_profit, opt_weight = parse_optimal_solution(optimal_sol_file_path)
        if opt_profit is None and opt_weight is None: # File not found by parser
            print(f"Optimal solution file {optimal_sol_file_path} not found or empty.")
            opt_profit, opt_weight = "OptFileNotFound", "OptFileNotFound" # Placeholders for CSV
        elif "ErrorOptimal" in str(opt_profit) or "ErrorReading" in str(opt_profit): # Parsing error
            print(f"Error parsing optimal solution file {optimal_sol_file_path}: P='{opt_profit}', W='{opt_weight}'")
        else: # Successfully parsed
            print(f"Optimal solution for {problem_id_for_csv}: Profit={opt_profit}, Weight={opt_weight}")

        # Run Python/PuLP method
        print(f"Running Python_PuLP for {problem_id_for_csv}...")
        py_rt, py_pr, py_wt, py_pal = run_python_method(problem_id_for_csv, tp_file_path, p_file_path)
        # Format pallet list for CSV: comma-separated string, or error/status string
        py_pal_str = ','.join(map(str, py_pal)) if isinstance(py_pal, list) and any(isinstance(p, int) for p in py_pal) else (str(py_pal) if not isinstance(py_pal, list) else "ErrorOrEmptyPalletList")
        results_data.append({
            "method_name": "Python_PuLP", "problem_id": problem_id_for_csv,
            "runtime": f"{py_rt:.4f}" if isinstance(py_rt, float) else py_rt, # Format float runtime
            "profit_achieved": py_pr, "optimal_profit": opt_profit if opt_profit is not None else "N/A",
            "weight_achieved": py_wt, "optimal_weight": opt_weight if opt_weight is not None else "N/A",
            "selected_pallets": py_pal_str
        })
        print(f"Python_PuLP for {problem_id_for_csv}: Time={py_rt if isinstance(py_rt, str) else f'{py_rt:.2f}s'}, P={py_pr}, W={py_wt}, Pals='{py_pal_str}'")

        # Run C++ method (will use placeholders/error status if compilation failed or runtime errors occur)
        print(f"Running CPP_Algorithm for {problem_id_for_csv}...")
        cpp_rt, cpp_pr, cpp_wt, cpp_pal = run_cpp_method(problem_id_for_csv, tp_file_path, p_file_path)
        cpp_pal_str = ','.join(map(str, cpp_pal)) if isinstance(cpp_pal, list) and any(isinstance(p, int) for p in cpp_pal) else (str(cpp_pal) if not isinstance(cpp_pal, list) else "ErrorOrEmptyPalletList")
        results_data.append({
            "method_name": "CPP_Algorithm", "problem_id": problem_id_for_csv,
            "runtime": f"{cpp_rt:.4f}" if isinstance(cpp_rt, float) else cpp_rt,
            "profit_achieved": cpp_pr, "optimal_profit": opt_profit if opt_profit is not None else "N/A", 
            "weight_achieved": cpp_wt, "optimal_weight": opt_weight if opt_weight is not None else "N/A", 
            "selected_pallets": cpp_pal_str
        })
        print(f"CPP_Algorithm for {problem_id_for_csv}: Time={cpp_rt if isinstance(cpp_rt, str) else f'{cpp_rt:.2f}s'}, P={cpp_pr}, W={cpp_wt}, Pals='{cpp_pal_str}'")

    # After processing all problem files, write aggregated results to CSV
    output_csv_file = "performance_results.csv"
    fieldnames = ["method_name", "problem_id", "runtime", "profit_achieved", "optimal_profit", "weight_achieved", "optimal_weight", "selected_pallets"]
    try:
        with open(output_csv_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader() # Write the header row
            for row_dict in results_data:
                # Ensure all expected fields are present in the row_dict, defaulting to "N/A" if missing
                for field in fieldnames:
                    row_dict.setdefault(field, "N/A")
                writer.writerow(row_dict) # Write the data row
        print(f"\nResults successfully written to {output_csv_file}")
    except IOError as e: # Handle potential errors during file writing
        print(f"Error writing results to {output_csv_file}: {e}. Displaying to stdout instead:")
        # Fallback: Print CSV content to console if file write fails
        header_str = ",".join(fieldnames)
        print(header_str)
        for row_dict in results_data:
            row_values = [str(row_dict.get(f, "N/A")) for f in fieldnames]
            print(",".join(row_values))

if __name__ == "__main__":
    # Basic chmod for python.py, primarily for consistency or if environment treats it as directly executable.
    # Standard `python script.py` invocation doesn't strictly need execute permission on the script itself.
    try:
        if os.path.exists("python.py"):
            os.chmod("python.py", 0o755) 
    except Exception as e:
        print(f"Warning: Could not set execute permission on python.py: {e}")
    
    main() # Execute the main data collection logic
