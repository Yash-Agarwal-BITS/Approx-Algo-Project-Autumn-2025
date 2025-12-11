/*
 * MISR - Local Search Approximation (1-swap-2)
 *
 * Algorithm:
 * 1. Initialize with a Greedy solution (earliest finish time heuristic).
 * 2. Iteratively search for a "move" that increases the set size:
 * - (0, 1) Move: Add a rectangle that fits without conflict.
 * - (1, 2) Move: Remove 1 rectangle from the solution to add 2 new ones.
 * 3. Repeat until no more improvements can be found.
 *
 * Time Complexity: O(N^3). 
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <set>

using namespace std;

struct Rect {
    int id;
    double x1, y1, x2, y2;
};

bool overlap(const Rect& a, const Rect& b) {
    if (a.x2 <= b.x1 || b.x2 <= a.x1) return false;
    if (a.y2 <= b.y1 || b.y2 <= a.y1) return false;
    return true;
}

// Generate conflict list
vector<vector<int>> buildConflictGraph(const vector<Rect>& rects) {
    int n = rects.size();
    vector<vector<int>> adj(n);
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            if (overlap(rects[i], rects[j])) {
                adj[i].push_back(j);
                adj[j].push_back(i);
            }
        }
    }
    return adj;
}

// Greedy Initialization (Sort by x2)
vector<int> greedyInit(const vector<Rect>& rects) {
    vector<int> p(rects.size());
    for(int i=0; i<rects.size(); ++i) p[i] = i;
    
    // Sort indices by right edge
    sort(p.begin(), p.end(), [&](int a, int b) {
        return rects[a].x2 < rects[b].x2;
    });

    vector<int> solution;
    for (int idx : p) {
        bool conflict = false;
        for (int selected : solution) {
            if (overlap(rects[idx], rects[selected])) {
                conflict = true;
                break;
            }
        }
        if (!conflict) {
            solution.push_back(idx);
        }
    }
    return solution;
}

int main() {
    // --- Input ---
    int n;
    if (!(cin >> n)) return 0;

    vector<Rect> rects(n);
    for (int i = 0; i < n; i++) {
        rects[i].id = i;
        cin >> rects[i].x1 >> rects[i].y1 >> rects[i].x2 >> rects[i].y2;
    }

    // --- Precompute Conflicts ---
    vector<vector<int>> adj = buildConflictGraph(rects);

    // --- 1. Initial Solution (Greedy) ---
    vector<int> currentSol = greedyInit(rects);
    
    // Track which rectangles are currently selected
    vector<bool> isSelected(n, false);
    for (int id : currentSol) isSelected[id] = true;

    bool improved = true;
    while (improved) {
        improved = false;

        // --- 2. Try (0, 1) Insertions ---
        for (int i = 0; i < n; i++) {
            if (isSelected[i]) continue;

            bool canAdd = true;
            for (int solId : currentSol) {
                if (overlap(rects[i], rects[solId])) {
                    canAdd = false;
                    break;
                }
            }

            if (canAdd) {
                currentSol.push_back(i);
                isSelected[i] = true;
                improved = true; // Restart search immediately after improvement
                break; 
            }
        }
        if (improved) continue;

        // --- 3. Try (1, 2) Swaps ---
        // Find 1 rectangle in Solution (r_out) and 2 outside (r_in1, r_in2) such that removing r_out allows r_in1 and r_in2 to fit.
        
        for (int r_out_idx = 0; r_out_idx < currentSol.size(); ++r_out_idx) {
            int u = currentSol[r_out_idx]; // The candidate to remove

            // Candidates to insert: must not be in set, and must ONLY conflict with u (or nothing)
            // within the current solution.
            vector<int> candidates;
            
            for (int v = 0; v < n; v++) {
                if (isSelected[v]) continue;

                // Check conflicts with *other* members of solution
                bool blockedByOthers = false;
                for (int solId : currentSol) {
                    if (solId == u) continue; // Ignore the one we might remove
                    if (overlap(rects[v], rects[solId])) {
                        blockedByOthers = true;
                        break;
                    }
                }
                if (!blockedByOthers) {
                    candidates.push_back(v);
                }
            }

            // Now look for a non-overlapping pair in 'candidates'
            for (int i = 0; i < candidates.size(); ++i) {
                for (int j = i + 1; j < candidates.size(); ++j) {
                    int c1 = candidates[i];
                    int c2 = candidates[j];

                    if (!overlap(rects[c1], rects[c2])) {
                        // Found a valid (1, 2) swap!
                        // Remove u
                        isSelected[u] = false;
                        currentSol.erase(currentSol.begin() + r_out_idx);
                        
                        // Add c1, c2
                        isSelected[c1] = true;
                        isSelected[c2] = true;
                        currentSol.push_back(c1);
                        currentSol.push_back(c2);

                        improved = true;
                        goto end_loop; // Break out of nested loops
                    }
                }
            }
        }
        end_loop:;
    }

    // --- Output ---
    cout << "Rectangles selected: " << currentSol.size() << endl;
    // Optional: Print indices if needed for debugging
    for(int id : currentSol) cout << id << " ";
    cout << endl;

    return 0;
}