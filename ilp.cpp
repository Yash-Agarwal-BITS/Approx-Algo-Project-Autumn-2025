/*
 * Maximum Independent Set of Rectangles (MISR) - ILP Solution using GLPK
 * 
 * This finds the OPTIMAL solution to MISR using Integer Linear Programming.
 * 
 * Formulation:
 *   - Variables: x_i ∈ {0,1} for each rectangle i (1 = selected, 0 = not selected)
 *   - Objective: maximize Σ w_i * x_i (sum of weights of selected rectangles)
 *   - Constraints: x_i + x_j ≤ 1 for any overlapping pair (i,j)
 * 
 * Input Format:
 *   Line 1: n (number of rectangles)
 *   Next n lines: x1 y1 x2 y2 [weight]
 *     - (x1,y1) = bottom-left corner, (x2,y2) = top-right corner
 *     - weight is optional (defaults to 1.0)
 */

#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <iomanip>
#include <glpk.h>

using namespace std;

struct Rectangle {
    double x1, y1, x2, y2;  // Bottom-left (x1,y1) to top-right (x2,y2)
    double weight;
};

// Check if two rectangles overlap (touching edges/corners doesn't count)
bool rectanglesOverlap(const Rectangle& a, const Rectangle& b) {
    // No overlap if separated horizontally or vertically
    if (min(a.x2, b.x2) <= max(a.x1, b.x1)) return false;
    if (min(a.y2, b.y2) <= max(a.y1, b.y1)) return false;
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // Read number of rectangles
    int numRectangles;
    if (!(cin >> numRectangles) || numRectangles <= 0) {
        cerr << "Error: First line must be a positive integer.\n";
        return 1;
    }

    // Read rectangle data
    vector<Rectangle> rectangles(numRectangles);
    for (int i = 0; i < numRectangles; i++) {
        string line;
        if (!getline(cin, line)) {
            if (i == 0) getline(cin, line);  // Skip potential newline after n
        }
        if (line.empty()) getline(cin, line);
        
        istringstream iss(line);
        double x1, y1, x2, y2, weight = 1.0;
        
        if (!(iss >> x1 >> y1 >> x2 >> y2)) {
            cerr << "Error: Line " << (i+2) << " must have 4 coordinates (x1 y1 x2 y2 [weight]).\n";
            return 1;
        }
        
        iss >> weight;  // Optional weight (stays 1.0 if not provided)
        
        if (x1 >= x2 || y1 >= y2) {
            cerr << "Error: Rectangle " << i << " must satisfy x1 < x2 and y1 < y2.\n";
            return 1;
        }
        
        rectangles[i] = {x1, y1, x2, y2, weight};
    }

    // Find all pairs of overlapping rectangles
    vector<pair<int,int>> conflictPairs;
    conflictPairs.reserve(numRectangles * (numRectangles - 1) / 2);
    
    for (int i = 0; i < numRectangles; i++) {
        for (int j = i + 1; j < numRectangles; j++) {
            if (rectanglesOverlap(rectangles[i], rectangles[j])) {
                conflictPairs.push_back({i, j});
            }
        }
    }
    
    int numConflicts = conflictPairs.size();

    // ========== Setup ILP Problem ==========
    glp_prob* ilp = glp_create_prob();
    glp_set_prob_name(ilp, "MISR");
    glp_set_obj_dir(ilp, GLP_MAX);  // Maximize

    // Create binary variables x_i for each rectangle
    glp_add_cols(ilp, numRectangles);
    for (int i = 1; i <= numRectangles; i++) {
        glp_set_col_name(ilp, i, ("x_" + to_string(i)).c_str());
        glp_set_col_bnds(ilp, i, GLP_DB, 0.0, 1.0);           // 0 ≤ x_i ≤ 1
        glp_set_obj_coef(ilp, i, rectangles[i-1].weight);     // Objective coefficient
        glp_set_col_kind(ilp, i, GLP_BV);                     // Binary variable
    }

    // Add constraints: x_i + x_j ≤ 1 for each overlapping pair (i,j)
    if (numConflicts > 0) {
        glp_add_rows(ilp, numConflicts);
        
        // Build constraint matrix in coordinate format
        int numNonZeros = 2 * numConflicts;
        vector<int> rowIndices(numNonZeros + 1);
        vector<int> colIndices(numNonZeros + 1);
        vector<double> coefficients(numNonZeros + 1);

        int idx = 0;
        for (int row = 1; row <= numConflicts; row++) {
            int i = conflictPairs[row-1].first;   // 0-based rectangle index
            int j = conflictPairs[row-1].second;  // 0-based rectangle index
            
            string constraintName = "overlap_" + to_string(i) + "_" + to_string(j);
            glp_set_row_name(ilp, row, constraintName.c_str());
            glp_set_row_bnds(ilp, row, GLP_UP, 0.0, 1.0);  // x_i + x_j ≤ 1

            // Add coefficients: 1.0 for x_i and 1.0 for x_j
            rowIndices[++idx] = row;  colIndices[idx] = i + 1;  coefficients[idx] = 1.0;
            rowIndices[++idx] = row;  colIndices[idx] = j + 1;  coefficients[idx] = 1.0;
        }
        
        glp_load_matrix(ilp, numNonZeros, rowIndices.data(), colIndices.data(), coefficients.data());
    }

    // ========== Solve ILP ==========
    glp_iocp solverParams;
    glp_init_iocp(&solverParams);
    solverParams.presolve = GLP_ON;
    solverParams.msg_lev = GLP_MSG_OFF;  // Suppress verbose output

    int solveStatus = glp_intopt(ilp, &solverParams);
    if (solveStatus != 0) {
        cerr << "Error: ILP solver failed with status " << solveStatus << "\n";
        glp_delete_prob(ilp);
        return 1;
    }

    // ========== Extract Solution ==========
    double totalWeight = glp_mip_obj_val(ilp);
    vector<int> selectedRectangles;
    
    for (int i = 1; i <= numRectangles; i++) {
        double value = glp_mip_col_val(ilp, i);
        if (value > 0.5) {  // x_i = 1 (selected)  //coz of precision
            selectedRectangles.push_back(i - 1);  // Convert to 0-based index
        }
    }

    // ========== Output Results ==========
    cout << "\n=== OPTIMAL SOLUTION (ILP) ===\n";
    cout << "Number of rectangles selected: " << selectedRectangles.size() << "\n";
    //cout << "Total weight: " << fixed << setprecision(2) << totalWeight << "\n";
    cout << "Selected rectangle indices: ";
    for (int idx : selectedRectangles) {
        cout << idx << " ";
    }
    cout << "\n";
    cout << "\n";
    glp_delete_prob(ilp);
    return 0;
}
