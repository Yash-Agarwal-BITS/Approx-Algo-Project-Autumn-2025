import subprocess
import random
import re
import time
import csv

# --- CONFIGURATION ---
NUM_TRIALS = 100
MIN_RECTANGLES = 20
MAX_RECTANGLES = 70
GRID_MULTIPLIER = 10            # grid_size = n_rectangles * GRID_MULTIPLIER
OUTPUT_FILE = "experiment_results.csv"
WORST_CASE_FILE = "worst_case.txt"

ILP_EXECUTABLE = "ilp.exe"
GUILL_EXECUTABLE = "guillotine.exe"

ILP_TIMEOUT = 30.0              # seconds
GUILL_TIMEOUT = 60.0            # seconds

RANDOM_SEED = 0 


# --- INSTANCE GENERATION ---

def generate_rectangles(n, grid_size):
    """
    Generates rectangles on a grid. They may overlap.
    They are small compared to the grid, which tends to help guillotine cuts.
    Format returned: list of strings "x1 y1 x2 y2".
    """
    rects = []
    for _ in range(n):
        # ensure these are at least 1
        min_w = max(1, grid_size // 20)
        max_w = max(1, grid_size // 10)
        min_h = max(1, grid_size // 20)
        max_h = max(1, grid_size // 10)

        w = random.randint(min_w, max_w)
        h = random.randint(min_h, max_h)

        # Random position ensuring the rectangle fits
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

    Assumes:
      - Input is provided on stdin in format:
            n
            x1 y1 x2 y2
            ...
      - Output contains either:
            "Number of rectangles selected: X"
        or  "Rectangles selected: X"

    Returns:
      (score, elapsed_time, raw_output, status)

      score  : int or None (None on error/timeout/parse failure)
      status : "ok", "timeout", or "error"
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
            print(f"[WARN] {executable} exited with code {process.returncode}")
            return None, elapsed_time, output, "error"

        # Extract number of selected rectangles
        match = re.search(
            r"(?:Number of rectangles selected|Rectangles selected):\s*(\d+)",
            output
        )
        if match:
            score = int(match.group(1))
            return score, elapsed_time, output, "ok"

        print(f"[WARN] Could not parse score from {executable} output.")
        return None, elapsed_time, output, "error"

    except subprocess.TimeoutExpired as e:
        elapsed_time = time.time() - start_time
        msg = f"TIMEOUT after {timeout} seconds: {e}"
        print(f"[WARN] {msg}")
        return None, elapsed_time, msg, "timeout"

    except Exception as e:
        elapsed_time = time.time() - start_time
        msg = f"Exception: {e}"
        print(f"[ERROR] Error running {executable}: {e}")
        return None, elapsed_time, msg, "error"


# --- MAIN EXPERIMENT ---

def main():
    random.seed(RANDOM_SEED)

    results = []
    worst_ratio = 0.0
    worst_case_input = ""

    fieldnames = [
        'trial',
        'n_rectangles',
        'grid_size',
        'ilp_score',
        'guillotine_score',
        'ratio',
        'ilp_time',
        'guillotine_time',
        'ilp_status',
        'guillotine_status',
    ]

    print(f"{'Trial':<6} | {'N':<4} | {'ILP':<6} | {'Guill':<6} | {'Ratio':<9} | {'ILP_Time':<9} | {'G_Time':<9} | Status")
    print("-" * 100)

    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(NUM_TRIALS):
            # Gradually increase rectangle count from MIN to MAX
            if NUM_TRIALS > 1:
                n_rectangles = MIN_RECTANGLES + int((MAX_RECTANGLES - MIN_RECTANGLES) * i / (NUM_TRIALS - 1))
            else:
                n_rectangles = MIN_RECTANGLES

            grid_size = int(n_rectangles * GRID_MULTIPLIER)
            rect_data = generate_rectangles(n_rectangles, grid_size)
            input_str = f"{n_rectangles}\n" + "\n".join(rect_data)

            # Run ILP (optimal solution)
            ilp_score, ilp_time, ilp_output, ilp_status = run_solver(
                ILP_EXECUTABLE, input_str, ILP_TIMEOUT
            )

            # Run Guillotine DP (approximation)
            guill_score, guill_time, guill_output, guill_status = run_solver(
                GUILL_EXECUTABLE, input_str, GUILL_TIMEOUT
            )

            # Calculate approximation ratio (OPT / Guillotine)
            ratio = None
            status_summary = f"ILP:{ilp_status}, G:{guill_status}"

            if ilp_score is not None and guill_score is not None:
                if guill_score == 0:
                    if ilp_score > 0:
                        ratio = float('inf')
                    else:
                        ratio = 1.0
                else:
                    ratio = ilp_score / guill_score

            # Print per-trial line
            ratio_str = f"{ratio:.4f}" if isinstance(ratio, (int, float)) and ratio != float('inf') else str(ratio)
            print(
                f"{i+1:<6} | {n_rectangles:<4} | "
                f"{(ilp_score if ilp_score is not None else '-'): <6} | "
                f"{(guill_score if guill_score is not None else '-'): <6} | "
                f"{ratio_str:<9} | {ilp_time:<9.4f} | {guill_time:<9.4f} | {status_summary}"
            )

            results.append(ratio)

            row = {
                'trial': i + 1,
                'n_rectangles': n_rectangles,
                'grid_size': grid_size,
                'ilp_score': ilp_score if ilp_score is not None else "",
                'guillotine_score': guill_score if guill_score is not None else "",
                'ratio': ratio if (isinstance(ratio, (int, float)) and ratio != float('inf')) else "",
                'ilp_time': ilp_time,
                'guillotine_time': guill_time,
                'ilp_status': ilp_status,
                'guillotine_status': guill_status,
            }
            writer.writerow(row)
            csvfile.flush()

            # Track worst finite ratio where both solvers succeeded
            if (
                ratio is not None
                and ratio != float('inf')
                and ilp_status == "ok"
                and guill_status == "ok"
                and ratio > worst_ratio
            ):
                worst_ratio = ratio
                worst_case_input = input_str

    print(f"\nResults saved to {OUTPUT_FILE}")

    # --- ANALYSIS ---
    # Consider only finite ratios
    valid_ratios = [
        r for r in results
        if isinstance(r, (int, float)) and r not in (None, float('inf'))
    ]

    if valid_ratios:
        avg_ratio = sum(valid_ratios) / len(valid_ratios)
        max_ratio = max(valid_ratios)
        min_ratio = min(valid_ratios)

        print("\n=== SUMMARY (finite ratios only) ===")
        print(f"Average Ratio (OPT/Guillotine): {avg_ratio:.4f}")
        print(f"Worst Case Ratio: {max_ratio:.4f}")
        print(f"Best Case Ratio: {min_ratio:.4f}")
        print(f"Valid trials (finite ratios): {len(valid_ratios)}/{NUM_TRIALS}")

        if worst_case_input:
            with open(WORST_CASE_FILE, "w") as f:
                f.write(worst_case_input)
            print(f"\nWorst case input saved to '{WORST_CASE_FILE}'")
    else:
        print("\nNo valid finite ratios to analyze.")


if __name__ == "__main__":
    main()