#include <iostream>
#include <vector>
#include <algorithm>
#include "Algorithms.h"

using namespace std;

void runBruteForce(const vector<Pallet>& pallets, int capacity) {
    int n = pallets.size();
    int maxProfit = 0;
    vector<int> bestSubset;

    int totalSubsets = 1 << n;
    for (int total = 0; total < totalSubsets; total++) {
        int temp = total;
        vector<bool> isSelected(n, false);

        for (int i = 0; i < n; ++i) {
            isSelected[i] = temp % 2;
            temp /= 2;
        }

        int totalWeight = 0;
        int totalProfit = 0;
        vector<int> currentSubset;

        for (int i = 0; i < n; ++i) {
            if (isSelected[i]) {
                totalWeight += pallets[i].weight;
                totalProfit += pallets[i].profit;
                currentSubset.push_back(pallets[i].id);
            }
        }

        if (totalWeight <= capacity) {
            if (totalProfit > maxProfit ||
                (totalProfit == maxProfit && currentSubset.size() < bestSubset.size()) ||
                (totalProfit == maxProfit && currentSubset.size() == bestSubset.size() && currentSubset < bestSubset)) {

                maxProfit = totalProfit;
                bestSubset = currentSubset;
            }
        }
    }

    cout << "[Brute-Force] Max Profit: " << maxProfit << "\n";
    cout << "Selected Pallets: ";
    for (int id : bestSubset) {
        cout << id << " ";
    }
    cout << "\n";
}


void backtrackKnapsack(const vector<Pallet>& pallets, int index, int capacity,
                       int currentWeight, int currentProfit, vector<int>& currentSet,
                       int& maxProfit, vector<int>& bestSet) {
    if (index == pallets.size()) {
        if (currentWeight <= capacity) {
            if (currentProfit > maxProfit ||
                (currentProfit == maxProfit && currentSet.size() < bestSet.size()) ||
                (currentProfit == maxProfit && currentSet.size() == bestSet.size() && currentSet < bestSet)) {
                maxProfit = currentProfit;
                bestSet = currentSet;
            }
        }
        return;
    }

    if (currentWeight > capacity)
        return;

    // Option 1: skip current item
    backtrackKnapsack(pallets, index + 1, capacity,
                      currentWeight, currentProfit,
                      currentSet, maxProfit, bestSet);

    // Option 2: include current item
    currentSet.push_back(pallets[index].id);
    backtrackKnapsack(pallets, index + 1, capacity,
                      currentWeight + pallets[index].weight,
                      currentProfit + pallets[index].profit,
                      currentSet, maxProfit, bestSet);
    currentSet.pop_back(); // backtrack
}


void runBruteForceBacktrack(const vector<Pallet>& pallets, int capacity) {
    int maxProfit = 0;
    vector<int> currentSet, bestSet;

    backtrackKnapsack(pallets, 0, capacity, 0, 0, currentSet, maxProfit, bestSet);

    cout << "[Backtracking] Max Profit: " << maxProfit << endl;
    cout << "Selected Pallets: ";
    for (int id : bestSet) {
        cout << id << " ";
    }
    cout << endl;
}

struct DPCell {  //the purpose of this struct is to solve ties according to the given rules
    int profit;
    int numPallets;
    vector<int> subset;

    bool operator<(const DPCell& other) const {
        if (profit != other.profit) return profit < other.profit;
        if (numPallets != other.numPallets) return numPallets > other.numPallets;
        return subset > other.subset;
    }
};



void runDynamicProgramming(const vector<Pallet>& pallets, int capacity) {
    int n = pallets.size();
    vector<vector<DPCell>> dp(n + 1, vector<DPCell>(capacity + 1));

    // Initialize first row with profit = 0
    for (int j = 0; j <= capacity; ++j) {
        dp[0][j] = {0, 0, {}};
    }

    for (int i = 1; i <= n; ++i) {
        int w = pallets[i - 1].weight;
        int p = pallets[i - 1].profit;
        int id = pallets[i - 1].id;

        for (int j = 0; j <= capacity; ++j) {
            // Case 1: skip pallet i
            DPCell without = dp[i - 1][j];

            // Case 2: include pallet i
            DPCell with = {0, 0, {}};
            if (j >= w) {
                with = dp[i - 1][j - w];
                with.profit += p;
                with.numPallets += 1;
                with.subset.push_back(id);
            }

            // Take the better one according to custom logic
            dp[i][j] = max(without, with);
        }
    }

    const DPCell& best = dp[n][capacity];

    cout << "[Dynamic Programming] Max Profit: " << best.profit << "\n";
    cout << "Selected Pallets: ";
    for (int id : best.subset) {
        cout << id << " ";
    }
    cout << "\n";
}

void runDynamicProgramming1D(const vector<Pallet>& pallets, int capacity) {
    int n = pallets.size();
    vector<DPCell> dp(capacity + 1, {0, 0, {}});

    for (int i = 0; i < n; ++i) {
        int w = pallets[i].weight;
        int p = pallets[i].profit;
        int id = pallets[i].id;

        // Traverse backwards to prevent overwriting previous states
        for (int j = capacity; j >= w; --j) {
            DPCell with = dp[j - w];
            with.profit += p;
            with.numPallets += 1;
            with.subset.push_back(id);

            if (dp[j] < with) {
                dp[j] = with;
            }
        }
    }

    // Find best solution across all weights
    DPCell best = dp[0];
    for (int j = 1; j <= capacity; ++j) {
        if (best < dp[j]) {
            best = dp[j];
        }
    }

    cout << "[DP 1D Optimized] Max Profit: " << best.profit << endl;
    cout << "Selected Pallets: ";
    for (int id : best.subset) {
        cout << id << " ";
    }
    cout << endl;
}




void runGreedyApproach(const vector<Pallet>& pallets, int capacity) {
    struct GreedyItem { //this is simply the DP struct from above but adapted to this problem
        int id;
        int weight;
        int profit;
        double ratio;

        bool operator<(const GreedyItem& other) const {
            if (ratio != other.ratio) return ratio < other.ratio;
            return id > other.id;
        }
    };

    vector<GreedyItem> items;
    for (const Pallet& p : pallets) {
        items.push_back({p.id, p.weight, p.profit, (double)p.weight / p.profit});
    }

    sort(items.begin(), items.end());

    int totalWeight = 0;
    int totalProfit = 0;
    vector<int> selected;

    for (const GreedyItem& item : items) {
        if (totalWeight + item.weight <= capacity) {
            totalWeight += item.weight;
            totalProfit += item.profit;
            selected.push_back(item.id);
        }
    }

    sort(selected.begin(), selected.end());

    cout << "[Greedy] Approximate Profit: " << totalProfit << "\n";
    cout << "Selected Pallets: ";
    for (int id : selected) {
        cout << id << " ";
    }
    cout << "\n";
}

void runLinearIntegerProgramming(const std::vector<Pallet>&, int){

}




