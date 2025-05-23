
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include "Algorithms.h"


bool readTruckData(const std::string& filename, int& capacity, int& numPallets) {
    std::ifstream file(filename);
    if (!file.is_open()) return false;

    std::string line;
    std::getline(file, line); // skip header
    std::getline(file, line); // actual data

    std::stringstream ss(line);
    std::string value;

    std::getline(ss, value, ',');
    capacity = std::stoi(value);

    std::getline(ss, value, ',');
    numPallets = std::stoi(value);

    return true;
}

bool readPalletData(const std::string& filename, std::vector<Pallet>& pallets) {
    std::ifstream file(filename);
    if (!file.is_open()) return false;

    std::string line;
    std::getline(file, line); // skip header

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string token;
        Pallet p;

        std::getline(ss, token, ',');
        p.id = std::stoi(token);
        std::getline(ss, token, ',');
        p.weight = std::stoi(token);
        std::getline(ss, token, ',');
        p.profit = std::stoi(token);

        pallets.push_back(p);
    }

    return true;
}

void showMenu() {
    std::cout << "==== Pallet Packing Optimization Tool ====" << std::endl;
    std::cout << "1. Load dataset" << std::endl;
    std::cout << "2. Exit" << std::endl;
    std::cout << "Choose an option: ";
}

int main() {
    int option;
    int capacity = 0, numPallets = 0;
    std::vector<Pallet> pallets;

    while (true) {
        showMenu();
        std::cin >> option;

        if (option == 1) {
            std::string truckFile, palletFile;
            std::cout << "Enter truck file (e.g., TruckAndPallets_01.csv): ";
            std::cin >> truckFile;
            std::cout << "Enter pallet file (e.g., Pallets_01.csv): ";
            std::cin >> palletFile;


            if (readTruckData(truckFile, capacity, numPallets) &&
                readPalletData(palletFile, pallets)) {

                    std::cout << "Pallet ID: " << pallets.at(2).id
                    << ", Weight: " << pallets.at(2).weight
                    << ", Profit: " << pallets.at(2).profit << std::endl;
          
                    int algoOption;
                    std::cout << "\nChoose an algorithm to run:\n";
                    std::cout << "1. Regular Brute-Force approach\n";
                    std::cout << "2. Brute-Force with backtracking\n";
                    std::cout << "3. Dynamic Programming approach\n";
                    std::cout << "4. Greedy approach\n";
                    std::cout << "5. Linear Integer Programming approach\n";
                    std::cout << "Enter option: ";
                    std::cin >> algoOption;

                    
                    
                    switch (algoOption) {
                        case 1:
                            runBruteForce(pallets, capacity);
                            break;
                        case 2:
                            runBruteForceBacktrack(pallets, capacity);
                            break;
                        case 3:
                            runDynamicProgramming(pallets, capacity);
                            break;
                        case 4:
                            runGreedyApproach(pallets, capacity);
                            break;
                        case 5:
                            runLinearIntegerProgramming(pallets, capacity);
                            break;
                        default:
                            std::cout << "Invalid option." << std::endl;
                    }
            } else {
                std::cout << "Error loading dataset files." << std::endl;
            }
        } else if (option == 2) {
            std::cout << "Exiting program." << std::endl;
            break;
        } else {
            std::cout << "Invalid option. Try again." << std::endl;
        }
    }

    return 0;
}