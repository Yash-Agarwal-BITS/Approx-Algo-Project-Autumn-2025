import subprocess
import random
import re
import time
import csv
import sys

# --- CONFIGURATION ---
NUM_TRIALS = 50                 # Number of random tests
MIN_RECTANGLES = 40             # Start complexity
MAX_RECTANGLES = 100            # Local search is fast, so we can test larger N
GRID_MULTIPLIER = 2             # grid_size = n_rectangles * GRID_MULTIPLIER
OUTPUT_FILE = "results_local_vs_ilp.csv"

# Executable names
ILP_EXECUTABLE = "./ilp" if sys.platform != "win32" else "ilp.exe"
LOCAL_EXECUTABLE = "./localsearch" if sys.platform != "win32" else "localsearch.exe"

ILP_TIMEOUT = 60.0              # ILP might struggle with N=100
LOCAL_TIMEOUT = 10.0            # Local search should be very fast

# --- INSTANCE GENERATION ---

def generate_rectangles(n, grid_size):
    """
    Generates rectangles on a grid.
    """
    rects = []
    max_dim = max(1, grid_size // 3) 
    min_dim = max(1, grid_size // 10)

    for _ in range(n):
        w = random.randint(min_dim, max_dim)
        h = random.randint(min_dim, max_dim)
        x1 = random.randint(0, max(0, grid_size - w))
        y1 = random.randint(0, max(0, grid_size - h))
        x2 = x1 + w
        y2 = y1 + h
        rects.append(f"{x1} {y1} {x2} {y2}")
    return rects

# --- SOLVER RUNNER ---

def run_solver(executable, input_str, timeout):
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
            return None, elapsed_time, output, "error"

        # Regex to match output from either solver
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
    except Exception as e:
        return None, 0, str(e), "exception"

# --- MAIN EXPERIMENT ---

def main():
    print(f"Comparing ILP (Opt) vs Local Search (Approx) for N={MIN_RECTANGLES}-{MAX_RECTANGLES}")
    print(f"{'Trial':<6} | {'N':<4} | {'ILP':<6} | {'Local':<6} | {'Ratio':<8} | {'ILP_T':<7} | {'Loc_T':<7} | Status")
    print("-" * 95)

    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        fieldnames = [
            'trial', 'n_rectangles', 'grid_size', 
            'ilp_score', 'local_score', 'ratio', 
            'ilp_time', 'local_time', 'status'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        ratios = []

        for i in range(NUM_TRIALS):
            # Random N
            n_rectangles = random.randint(MIN_RECTANGLES, MAX_RECTANGLES)
            grid_size = int(n_rectangles * GRID_MULTIPLIER)
            rect_data = generate_rectangles(n_rectangles, grid_size)
            input_str = f"{n_rectangles}\n" + "\n".join(rect_data)

            # 1. Run ILP
            ilp_score, ilp_time, _, ilp_stat = run_solver(ILP_EXECUTABLE, input_str, ILP_TIMEOUT)

            # 2. Run Local Search
            loc_score, loc_time, _, loc_stat = run_solver(LOCAL_EXECUTABLE, input_str, LOCAL_TIMEOUT)

            # 3. Analysis
            ratio = None
            note = ""
            
            if ilp_score is not None and loc_score is not None and loc_score > 0:
                ratio = ilp_score / loc_score
                ratios.append(ratio)
                if ratio > 1.0:
                    note = "*"  # Mark non-optimal approximations
            elif ilp_score == 0 and loc_score == 0:
                ratio = 1.0
                ratios.append(1.0)

            # Formatting
            r_str = f"{ratio:.4f}" if ratio else "-"
            i_str = str(ilp_score) if ilp_score is not None else "-"
            l_str = str(loc_score) if loc_score is not None else "-"
            
            status_summary = "OK"
            if ilp_stat == "timeout": status_summary = "ILP_TO"
            elif loc_stat == "timeout": status_summary = "LOC_TO"

            print(
                f"{i+1:<6} | {n_rectangles:<4} | "
                f"{i_str:<6} | {l_str:<6} | "
                f"{r_str:<8} | {ilp_time:<7.2f} | {loc_time:<7.4f} | {note} {status_summary}"
            )

            writer.writerow({
                'trial': i + 1,
                'n_rectangles': n_rectangles,
                'grid_size': grid_size,
                'ilp_score': i_str,
                'local_score': l_str,
                'ratio': r_str,
                'ilp_time': f"{ilp_time:.4f}",
                'local_time': f"{loc_time:.4f}",
                'status': status_summary
            })
            csvfile.flush()

    if ratios:
        print("\n" + "="*30)
        print(f"Average Approximation Ratio: {sum(ratios)/len(ratios):.4f}")
        print(f"Worst Approximation Ratio:   {max(ratios):.4f}")
        print("="*30)
        print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()