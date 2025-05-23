#include <iostream>
#include <vector>
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

        if (totalWeight <= capacity && totalProfit > maxProfit) {
            maxProfit = totalProfit;
            bestSubset = currentSubset;
            cout << "I got here" << endl;
        }
    }

    cout << "[Brute-Force] Max Profit: " << maxProfit << "\n";
    cout << "Selected Pallets: ";
    for (int id : bestSubset) {
        cout << id << " ";
    }
    cout << "\n";
    return; 
}

void backtrackKnapsack(const vector<Pallet>& pallets, int index, int capacity,
                       int currentWeight, int currentProfit, vector<int>& currentSet,
                       int& maxProfit, vector<int>& bestSet) {
    if (index == pallets.size()) {
        if (currentWeight <= capacity && currentProfit > maxProfit) {
            maxProfit = currentProfit;
            bestSet = currentSet;
        }
        return;
    }

    if (currentWeight > capacity)
        return;

    backtrackKnapsack(pallets, index + 1, capacity,
                      currentWeight, currentProfit,
                      currentSet, maxProfit, bestSet);

    currentSet.push_back(pallets[index].id);
    backtrackKnapsack(pallets, index + 1, capacity,
                      currentWeight + pallets[index].weight,
                      currentProfit + pallets[index].profit,
                      currentSet, maxProfit, bestSet);
    currentSet.pop_back();
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


void runDynamicProgramming(const std::vector<Pallet>&, int){

}

void runGreedyApproach(const std::vector<Pallet>&, int){

}

void runLinearIntegerProgramming(const std::vector<Pallet>&, int){

}




