# Maximum Independent Set of Rectangles (MISR) Solvers

This repository contains implementations of various algorithms to solve the **Maximum Independent Set of Rectangles (MISR)** problem. The goal is to find the maximum cardinality subset of non-overlapping axis-parallel rectangles from a given input set.

The repository includes an exact solver (ILP), a theoretical approximation algorithm (Guillotine Cuts), and a practical heuristic (Local Search), along with test scripts to benchmark their performance.

## Algorithms Implemented

### 1. Integer Linear Programming (ILP) - Optimal
* **File:** `ilp.cpp`
* **Description:** Finds the mathematically optimal independent set using the **GLPK** (GNU Linear Programming Kit) solver.
* **Method:** Formulates the problem as maximizing the total weight $\sum x_i$ subject to the constraint $x_i + x_j \le 1$ for all overlapping pairs $(i, j)$, where $x_i \in \{0,1\}$ is a binary variable indicating if rectangle $i$ is selected.
* **Complexity:** **NP-Hard** (Exponential time).

### 2. Guillotine Cut Dynamic Programming
* **File:** `Guillotine_Cut_MISR.cpp`
* **Description:** Finds the maximum independent set obtainable via a sequence of edge-to-edge guillotine cuts. This serves as a $\frac{n}{1+\log n}$ approximation to the general MISR problem.
* **Method:** Implements an $O(n^5)$ dynamic programming algorithm that recursively partitions the plane. The recurrence relation used is:
    $$DP[C] = \max_{C_1, C_2} (DP[C_1] \cup DP[C_2])$$
    for all valid guillotine cuts.
* **Note:** While polynomial time, the high complexity makes it computationally expensive for $N > 50$.

### 3. Local Search Heuristic
* **File:** `localsearch.cpp`
* **Description:** A fast approximation algorithm based on $(k, k+1)$-swaps.
* **Method:** Starts with a greedy solution and iteratively attempts to improve the solution size by replacing **1** rectangle in the current set with **2** rectangles from outside the set (a (1,2)-swap) until a local optimum is reached.
* **Performance:** Empirically effective and significantly faster than the exact or DP approaches for random instances.
* **Complexity:** $N \times O(N^3) = O(N^4)$.

## Dependencies

* **C++ Compiler:** `g++` (supports C++11 or later).
* **GLPK (GNU Linear Programming Kit):** Required for the ILP solver.
    * *Ubuntu/Debian:* `sudo apt-get install libglpk-dev`
    * *MacOS:* `brew install glpk`
* **Python 3:** Required for running the test scripts.

## Compilation

To compile all solvers, run the following commands in your terminal:

```bash
# Compile Optimal ILP Solver
g++ -O3 ilp.cpp -lglpk -o ilp

# Compile Guillotine DP Solver
g++ -O3 Guillotine_Cut_MISR.cpp -o guillotine

# Compile Local Search Solver
g++ -O3 localsearch.cpp -o localsearch