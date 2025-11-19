# Maximum Independent Set of Rectangles (MISR)

Comparison of optimal vs approximation algorithms for the Maximum Independent Set of Rectangles problem.

## Problem Description

Given a set of rectangles in the 2D plane, find the maximum subset where no two rectangles overlap (open-set intersection - touching edges/corners allowed).

## Algorithms Implemented

### 1. ILP Solver (`ilp.cpp`)
- **Type**: Exact/Optimal solution
- **Method**: Integer Linear Programming using GLPK
- **Complexity**: NP-hard, exponential worst-case
- **Use**: Baseline for measuring approximation quality

### 2. Guillotine Cut DP (`Guillotine_Cut_MISR.cpp`)
- **Type**: Approximation algorithm
- **Method**: Dynamic programming with guillotine-separable restrictions
- **Complexity**: O(n⁵) with coordinate compression
- **Theoretical Bound**: 2-approximation for axis-aligned rectangles

## Repository Structure

```
.
├── ilp.cpp                     # Optimal solver using GLPK
├── Guillotine_Cut_MISR.cpp    # Guillotine DP approximation
├── testing.py                  # Benchmark framework
├── rectangles.txt              # Sample input file
├── experiment_results.csv      # Output data
├── worst_case.txt              # Worst approximation instance
└── README.md
```

## Requirements

### C++ Compilation
- **Compiler**: g++ with C++17 support
- **Library**: GLPK (GNU Linear Programming Kit)

#### Installing GLPK (Windows/MSYS2)
```bash
pacman -S mingw-w64-x86_64-glpk
```

#### Installing GLPK (Linux)
```bash
sudo apt-get install libglpk-dev
```

### Python
- Python 3.7+
- Standard library only (subprocess, csv, random, re, time)

## Compilation

```bash
# ILP solver
g++ ilp.cpp -o ilp.exe -std=c++17 -lglpk

# Guillotine solver
g++ Guillotine_Cut_MISR.cpp -o guillotine.exe -std=c++17
```

## Usage

### Running Individual Solvers

**Input Format** (`rectangles.txt`):
```
n
x1 y1 x2 y2
x1 y1 x2 y2
...
```

Example:
```
3
0 0 2 2
1 1 3 3
0 2 2 4
```

**Execute**:
```bash
# Via stdin
cat rectangles.txt | ./ilp.exe
cat rectangles.txt | ./guillotine.exe

# PowerShell
Get-Content rectangles.txt | .\ilp.exe
Get-Content rectangles.txt | .\guillotine.exe
```

### Running Benchmark Suite

```bash
python testing.py
```

**Configuration** (`testing.py`):
- `NUM_TRIALS`: Number of random instances (default: 100)
- `MIN_RECTANGLES`: Starting problem size (default: 20)
- `MAX_RECTANGLES`: Ending problem size (default: 70)
- `GRID_MULTIPLIER`: Grid size factor (default: 10)
- `ILP_TIMEOUT`: ILP time limit in seconds (default: 30)
- `GUILL_TIMEOUT`: Guillotine time limit in seconds (default: 60)

**Output**:
- Live progress printed to console
- `experiment_results.csv`: Trial-by-trial results with approximation ratios
- `worst_case.txt`: Input instance where Guillotine performed worst

## Output Interpretation

### Approximation Ratio
```
ratio = ILP_score / Guillotine_score
```

- **ratio = 1.0**: Guillotine found the optimal solution
- **ratio = 1.2**: ILP found 20% more rectangles than Guillotine
- **ratio → ∞**: Guillotine failed (returned 0)

### CSV Columns
- `trial`: Trial number
- `n_rectangles`: Number of rectangles in instance
- `grid_size`: Coordinate space dimensions
- `ilp_score`: Optimal solution size
- `guillotine_score`: Approximation solution size
- `ratio`: ILP/Guillotine ratio
- `ilp_time`: ILP execution time (seconds)
- `guillotine_time`: Guillotine execution time (seconds)
- `ilp_status`: `ok`, `timeout`, or `error`
- `guillotine_status`: `ok`, `timeout`, or `error`

## Algorithm Details

### ILP Formulation
```
maximize: Σ xᵢ
subject to:
  xᵢ + xⱼ ≤ 1  for all overlapping pairs (i,j)
  xᵢ ∈ {0,1}
```

### Guillotine Cuts
- **Recursive partitioning**: Split region with vertical/horizontal cuts
- **Coordinate compression**: Maps sparse coordinates to dense indices
- **Memoization**: Caches subproblem results
- **Optimizations**: Limited cut sampling to reduce O(n⁵) overhead

## Performance Notes

- **ILP**: Fast for n ≤ 50, becomes slow beyond n = 70-100
- **Guillotine**: Polynomial but high constant factor; optimized version handles n ≤ 80
- **Grid density**: Sparser grids → fewer conflicts → easier problems

## Known Issues

- Guillotine times out on dense instances with n > 40
- ILP may exceed 30s timeout for n > 60 with many conflicts
- Both algorithms use open-set overlap detection (boundaries don't conflict)

## References

- GLPK Documentation: https://www.gnu.org/software/glpk/
- Guillotine separable rectangles: Classic approximation algorithm for geometric packing

## License

Educational/Research use. Original algorithms from published literature.
