import subprocess
import random
import re
import time
import csv
import sys

# --- CONFIGURATION ---
NUM_TRIALS = 50                 # Run many trials to increase chance of finding bad cases
MIN_RECTANGLES = 40             # Start at 40 (where complexity begins to ramp up)
MAX_RECTANGLES = 50             # Cap at 50 to avoid timeouts (N=50 takes ~30s)
GRID_MULTIPLIER = 2             # grid_size = n_rectangles * GRID_MULTIPLIER
OUTPUT_FILE = "experiment_results.csv"

# Executable names
ILP_EXECUTABLE = "./ilp" if sys.platform != "win32" else "ilp.exe"
GUILL_EXECUTABLE = "./guillotine" if sys.platform != "win32" else "guillotine.exe"

ILP_TIMEOUT = 60.0              # seconds
GUILL_TIMEOUT = 60.0            # seconds (N=50 can take ~30-40s)

# REMOVED FIXED SEED to ensure new random instances every run
# random.seed(42) 


# --- INSTANCE GENERATION ---

def generate_rectangles(n, grid_size):
    """
    Generates rectangles on a grid.
    """
    rects = []
    # Dimensions relative to grid
    max_dim = max(1, grid_size // 3) 
    min_dim = max(1, grid_size // 10)

    for _ in range(n):
        w = random.randint(min_dim, max_dim)
        h = random.randint(min_dim, max_dim)

        # Random position ensuring the rectangle fits inside the grid
        x1 = random.randint(0, max(0, grid_size - w))
        y1 = random.randint(0, max(0, grid_size - h))
        x2 = x1 + w
        y2 = y1 + h

        rects.append(f"{x1} {y1} {x2} {y2}")
    return rects


# --- SOLVER RUNNER ---

def run_solver(executable, input_str, timeout):
    """
    Run a solver executable and extract the number of selected rectangles.
    """
    start_time = time.time()
    try:
        process = subprocess.run(
            [executable],
            input=input_str,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        elapsed_time = time.time() - start_time
        output = (process.stdout or "") + (process.stderr or "")

        if process.returncode != 0:
            return None, elapsed_time, output, f"error (code {process.returncode})"

        # Extract number of selected rectangles
        match = re.search(
            r"(?:Number of rectangles selected|Rectangles selected):\s*(\d+)",
            output
        )
        if match:
            score = int(match.group(1))
            return score, elapsed_time, output, "ok"

        return None, elapsed_time, output, "parse_error"

    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        return None, elapsed_time, "", "timeout"

    except FileNotFoundError:
        return None, 0, "", "exec_not_found"

    except Exception as e:
        elapsed_time = time.time() - start_time
        return None, elapsed_time, str(e), "exception"


# --- MAIN EXPERIMENT ---

def main():
    results = []
    interesting_cases = 0

    fieldnames = [
        'trial', 'n_rectangles', 'grid_size', 
        'ilp_score', 'guillotine_score', 'ratio', 
        'ilp_time', 'guillotine_time', 
        'ilp_status', 'guillotine_status'
    ]

    print(f"Searching for hard instances (Ratio > 1) with N={MIN_RECTANGLES}-{MAX_RECTANGLES}...")
    print(f"{'Trial':<6} | {'N':<4} | {'ILP':<6} | {'Guill':<6} | {'Ratio':<8} | {'ILP_T':<7} | {'G_T':<7} | Note")
    print("-" * 100)

    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(NUM_TRIALS):
            # Randomly pick N in the range for this trial
            n_rectangles = random.randint(MIN_RECTANGLES, MAX_RECTANGLES)

            grid_size = int(n_rectangles * GRID_MULTIPLIER)
            rect_data = generate_rectangles(n_rectangles, grid_size)
            input_str = f"{n_rectangles}\n" + "\n".join(rect_data)

            # 1. Run ILP (Optimal)
            ilp_score, ilp_time, ilp_out, ilp_stat = run_solver(
                ILP_EXECUTABLE, input_str, ILP_TIMEOUT
            )

            # 2. Run Guillotine (Approximation)
            guill_score, guill_time, guill_out, guill_stat = run_solver(
                GUILL_EXECUTABLE, input_str, GUILL_TIMEOUT
            )

            # 3. Calculate Ratio
            ratio = None
            note = ""
            if ilp_score is not None and guill_score is not None and guill_score > 0:
                ratio = ilp_score / guill_score
                results.append(ratio)
                if ratio > 1.000001:  # Floating point tolerance
                    note = "*** RATIO > 1 ***"
                    interesting_cases += 1
            elif ilp_score == 0 and guill_score == 0:
                ratio = 1.0
                results.append(1.0)
            
            # Format outputs
            r_str = f"{ratio:.4f}" if ratio else "-"
            i_score_str = str(ilp_score) if ilp_score is not None else "-"
            g_score_str = str(guill_score) if guill_score is not None else "-"
            
            # If timeout, mark clearly
            if ilp_stat == "timeout" or guill_stat == "timeout":
                note = "TIMEOUT"

            print(
                f"{i+1:<6} | {n_rectangles:<4} | "
                f"{i_score_str:<6} | {g_score_str:<6} | "
                f"{r_str:<8} | {ilp_time:<7.2f} | {guill_time:<7.2f} | {note}"
            )

            # Save results
            writer.writerow({
                'trial': i + 1,
                'n_rectangles': n_rectangles,
                'grid_size': grid_size,
                'ilp_score': i_score_str,
                'guillotine_score': g_score_str,
                'ratio': r_str,
                'ilp_time': f"{ilp_time:.4f}",
                'guillotine_time': f"{guill_time:.4f}",
                'ilp_status': ilp_stat,
                'guillotine_status': guill_stat,
            })
            csvfile.flush()

    # --- SUMMARY ---
    print("\n" + "="*30)
    print(" EXPERIMENT COMPLETE")
    print("="*30)
    
    if results:
        print(f"Mean Ratio: {sum(results)/len(results):.4f}")
    
    print(f"Interesting cases (Ratio > 1): {interesting_cases}")
    print(f"Full results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()