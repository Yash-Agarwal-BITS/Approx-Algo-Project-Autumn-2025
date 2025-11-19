/*
C++ implementation of the O(n⁵) dynamic programming algorithm to find the optimal 
guillotine-separable solution for the Maximum Independent Set of Rectangles (MISR) problem.

The algorithm works by recursively partitioning the plane and finding the best combination of 
non-overlapping rectangles that can be isolated by a sequence of edge-to-edge guillotine cuts.
*/

#include <bits/stdc++.h>
using namespace std;

struct Rect { long long xl, yb, xr, yt; };
struct Choice { int type = 0, param = -1; }; // 1 = leaf rect (rid), 2 = vertical cut at xi, 3 = horizontal cut at yk
struct Answer { int val = 0; Choice ch; };

struct Key {
    int xi, xj, yk, yl;
    bool operator==(const Key& o) const { return xi==o.xi && xj==o.xj && yk==o.yk && yl==o.yl; }
};
struct KeyHash {
    size_t operator()(const Key& k) const {
        uint64_t h = 1469598103934665603ull;
        auto mix=[&](uint64_t v){ h^=v; h*=1099511628211ull; };
        mix(k.xi); mix(k.xj); mix(k.yk); mix(k.yl);
        return (size_t)h;
    }
};

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // ---------- Read rectangles from input ----------
    int n;
    if (!(cin >> n) || n <= 0) {
        cerr << "Error: first line must be a positive integer n.\n";
        return 1;
    }

    vector<Rect> R(n);
    for (int i = 0; i < n; ++i) {
        if (!(cin >> R[i].xl >> R[i].yb >> R[i].xr >> R[i].yt)) {
            cerr << "Error: line " << (i+2) << " must have 4 numbers (xl yb xr yt).\n";
            return 1;
        }
        if (!(R[i].xl < R[i].xr && R[i].yb < R[i].yt)) {
            cerr << "Error: rectangle " << i << " must satisfy xl<xr and yb<yt.\n";
            return 1;
        }
    }

    // ---------- Coordinate compression ----------
    vector<long long> xs, ys;
    xs.reserve(2*n); ys.reserve(2*n);
    for (auto &r : R) { xs.push_back(r.xl); xs.push_back(r.xr); ys.push_back(r.yb); ys.push_back(r.yt); }
    sort(xs.begin(), xs.end()); xs.erase(unique(xs.begin(), xs.end()), xs.end());
    sort(ys.begin(), ys.end()); ys.erase(unique(ys.begin(), ys.end()), ys.end());
    const int X = (int)xs.size(), Y = (int)ys.size();   // Stores the number of unique x and y coordinates

    struct RI { int xl, xr, yb, yt; };
    vector<RI> RIv(n);
    for (int i=0;i<n;++i){
        RIv[i].xl = (int)(lower_bound(xs.begin(), xs.end(), R[i].xl) - xs.begin());
        RIv[i].xr = (int)(lower_bound(xs.begin(), xs.end(), R[i].xr) - xs.begin());
        RIv[i].yb = (int)(lower_bound(ys.begin(), ys.end(), R[i].yb) - ys.begin());
        RIv[i].yt = (int)(lower_bound(ys.begin(), ys.end(), R[i].yt) - ys.begin());
    }

    auto exactMatch = [&](int rid, int xi, int xj, int yk, int yl)->bool{
        const auto &q = RIv[rid];
        return q.xl==xi && q.xr==xj && q.yb==yk && q.yt==yl;
    };   // Checks if a given window [xi, xj] × [yk, yl] exactly matches rectangle rid

    //  quick “emptiness” test to exit states that contain no full rectangle
    auto windowHasAnyRect = [&](int xi,int xj,int yk,int yl)->bool{
        for(int rid=0; rid<n; ++rid){
            const auto &q = RIv[rid];
            if (q.xl>=xi && q.xr<=xj && q.yb>=yk && q.yt<=yl) return true;
        }
        return false;
    };

    unordered_map<Key, Answer, KeyHash> memo;

    function<Answer(int,int,int,int)> solve = [&](int xi, int xj, int yk, int yl)->Answer {
        if (xi>=xj || yk>=yl) return Answer{0,{}};

        Key key{xi,xj,yk,yl};
        if (auto it = memo.find(key); it != memo.end()) return it->second;

        // If no rectangle lies fully inside this window, value is 0 (no point cutting further)
        if (!windowHasAnyRect(xi,xj,yk,yl)) return memo[key] = Answer{0,{}};

        Answer best{0,{}};

        // Leaf option: if the window exactly equals some rectangle, we can take it and stop.
        for (int rid=0; rid<n; ++rid) {
            if (exactMatch(rid, xi, xj, yk, yl)) {
                best = {1, {1, rid}};
                break; 
            }
        }  // still try cuts; a split might yield >1 total

        // Try ALL vertical cuts xi < c < xj (guillotine cut slices across; rectangles cut by it are discarded)
        for (int c = xi+1; c <= xj-1; ++c) {
            Answer L  = solve(xi, c, yk, yl);
            Answer Rw = solve(c,  xj, yk, yl);
            int v = L.val + Rw.val;
            if (v > best.val) best = {v, {2, c}};
        }

        // Try ALL horizontal cuts yk < c < yl
        for (int c = yk+1; c <= yl-1; ++c) {
            Answer B = solve(xi, xj, yk, c);
            Answer T = solve(xi, xj, c,  yl);
            int v = B.val + T.val;
            if (v > best.val) best = {v, {3, c}};
        }

        return memo[key] = best;
    };

    // Solve on global bounding window
    Answer ans = solve(0, X-1, 0, Y-1);

    // Reconstruct chosen rectangles
    vector<int> chosen;
    function<void(int,int,int,int)> recon = [&](int xi,int xj,int yk,int yl){
        auto it = memo.find(Key{xi,xj,yk,yl});
        if (it==memo.end()) return;
        const auto &A = it->second;
        if (A.val==0) return;
        if (A.ch.type==1) { chosen.push_back(A.ch.param); return; }
        if (A.ch.type==2) { int c=A.ch.param; recon(xi,c,yk,yl); recon(c,xj,yk,yl); return; }
        if (A.ch.type==3) { int c=A.ch.param; recon(xi,xj,yk,c); recon(xi,xj,c,yl); return; }
    };
    recon(0, X-1, 0, Y-1);

    cout << "\n=== Best Guillotine-Separable Independent Set ===\n";
    cout << "Rectangles selected: " << ans.val << "\n";
    for (int rid : chosen)
        cout << "Rect " << rid << ": (" << R[rid].xl << "," << R[rid].yb
             << ")-(" << R[rid].xr << "," << R[rid].yt << ")\n";
    
    cout << "\n";
    return 0;
}