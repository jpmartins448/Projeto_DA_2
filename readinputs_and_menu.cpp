#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cstdlib>
#include <chrono>
#include <limits>
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

void writeExecutionTimeToCSV(const std::string& filename, const std::string& algorithmName,
    const std::string& dataset, double durationMs) {
std::ofstream file(filename, std::ios::app);
if (!file.is_open()) {
std::cerr << "Failed to open results file." << std::endl;
return;
}

// Write header if file is empty
static bool headerWritten = false;
if (file.tellp() == 0) {
file << "Algorithm,Dataset,Duration(ms)\n";
headerWritten = true;
}

file << algorithmName << "," << dataset << "," << durationMs << "\n";
file.close();
}


int main() {
    int option;
    int capacity = 0, numPallets = 0;
    std::vector<Pallet> pallets;

    while (true) {
        showMenu();

        if (!(std::cin >> option)) {
            std::cin.clear();
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            std::cout << "Invalid input. Try again." << std::endl << std::endl;
            continue;
        }

        if (option == 1) {
            std::string datasetNumber;
            std::cout << "Enter dataset number (e.g., 5): ";
            std::cin >> datasetNumber;

            std::string truckFile = "TP" + datasetNumber + ".csv";
            std::string palletFile = "P" + datasetNumber + ".csv";

            std::cout << "Loading truck file: " << truckFile << std::endl;
            std::cout << "Loading pallet file: " << palletFile << std::endl;

            pallets.clear();

            if (readTruckData(truckFile, capacity, numPallets) &&
                readPalletData(palletFile, pallets)) {

                int algoOption;
                std::cout << "\nChoose an algorithm to run:\n";
                std::cout << "1. Regular Brute-Force approach\n";
                std::cout << "2. Brute-Force with backtracking\n";
                std::cout << "3. Dynamic Programming approach\n";
                std::cout << "4. Optimized Dynamic Programming\n";
                std::cout << "5. Greedy approach\n";
                std::cout << "6. Linear Integer Programming approach\n";
                std::cout << "Enter option: ";
                std::cin >> algoOption;

            
                std::chrono::time_point<std::chrono::high_resolution_clock> start, end;
                double duration;

                switch (algoOption) {
                    case 1:
                        start = std::chrono::high_resolution_clock::now();
                        runBruteForce(pallets, capacity);
                        end = std::chrono::high_resolution_clock::now();
                        duration = std::chrono::duration<double, std::milli>(end - start).count();
                        writeExecutionTimeToCSV("results.csv", "BruteForce", datasetNumber, duration);
                        break;
                    case 2:
                    start = std::chrono::high_resolution_clock::now();
                        runBruteForceBacktrack(pallets, capacity);
                    end = std::chrono::high_resolution_clock::now();
                    duration = std::chrono::duration<double, std::milli>(end - start).count();
                        writeExecutionTimeToCSV("results.csv", "BruteForceBacktrack", datasetNumber, duration);
                        break;
                    case 3:
                    start = std::chrono::high_resolution_clock::now();
                        runDynamicProgramming(pallets, capacity);
                    end = std::chrono::high_resolution_clock::now();
                    duration = std::chrono::duration<double, std::milli>(end - start).count();
                        writeExecutionTimeToCSV("results.csv", "DynamicProgramming", datasetNumber, duration);
                        break;
                    case 4:
                    start = std::chrono::high_resolution_clock::now();
                        runDynamicProgramming1D(pallets, capacity);
                    end = std::chrono::high_resolution_clock::now();
                    duration = std::chrono::duration<double, std::milli>(end - start).count();
                        writeExecutionTimeToCSV("results.csv", "DynammicProgramming1D", datasetNumber, duration);
                        break;
                    case 5:
                    start = std::chrono::high_resolution_clock::now();
                        runGreedyApproach(pallets, capacity);
                    end = std::chrono::high_resolution_clock::now();
                    duration = std::chrono::duration<double, std::milli>(end - start).count();
                        writeExecutionTimeToCSV("results.csv", "Greedy", datasetNumber, duration);    
                        break;
                    case 6: {
                        std::string cmd = "python python.py " + truckFile + " " + palletFile;
                        start = std::chrono::high_resolution_clock::now();
                        int ret = std::system(cmd.c_str());
                        end = std::chrono::high_resolution_clock::now();
                        duration = std::chrono::duration<double, std::milli>(end - start).count();
                        writeExecutionTimeToCSV("results.csv", "LinearIntegerProgramming", datasetNumber, duration);
                        if (ret != 0) {
                            std::cout << "Error running Python solver" << std::endl;
                        }
                        break;
                    }
                    default:
                        std::cout << "Invalid option." << std::endl;
                }
                std::cout << std::endl;
            } else {
                std::cout << "Error loading dataset files." << std::endl << std::endl;
            }
        } else if (option == 2) {
            std::cout << "Exiting..." << std::endl;
            break;
        } else {
            std::cout << "Invalid option. Try again." << std::endl << std::endl;
        }
    }

    return 0;
}
