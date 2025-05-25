#ifndef ALGORITHMS_H
#define ALGORITHMS_H

#include <vector>
#include "Pallet.h"

void runBruteForce(const std::vector<Pallet>&, int);
void runBruteForceBacktrack(const std::vector<Pallet>&, int);
void runDynamicProgramming(const std::vector<Pallet>&, int);
void runDynamicProgramming1D(const std::vector<Pallet>&, int);
void runGreedyApproach(const std::vector<Pallet>&, int);

#endif
