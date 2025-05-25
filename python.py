import sys
import csv
import pulp

def read_truck_data(filename):
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            capacity = int(row['Capacity'])
            pallets_count = int(row['Pallets'])
            return capacity, pallets_count
    raise ValueError("Truck data file is empty or malformed")

def read_pallet_data(filename):
    pallets = []
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            pallet_id = int(row['Pallet'])
            weight = int(row['Weight'])
            profit = int(row['Profit'])
            pallets.append({'id': pallet_id, 'weight': weight, 'profit': profit})
    return pallets

def solve_knapsack(pallets, capacity):
    
    n = len(pallets)
    B = n + 1 

    prob = pulp.LpProblem("Knapsack_Lexico", pulp.LpMaximize)
    x = {p['id']: pulp.LpVariable(f"x_{p['id']}", cat='Binary') for p in pallets}

    prob += (
        pulp.lpSum(p['profit'] * (B**2) * x[p['id']] for p in pallets)
        - pulp.lpSum(B * x[p['id']] for p in pallets)
        - pulp.lpSum(p['id'] * x[p['id']] for p in pallets)
    )

    prob += pulp.lpSum(p['weight'] * x[p['id']] for p in pallets) <= capacity

    prob.solve()

    selected = [p['id'] for p in pallets if pulp.value(x[p['id']]) > 0.5]
    total_profit = sum(p['profit'] for p in pallets if p['id'] in selected)
    total_weight = sum(p['weight'] for p in pallets if p['id'] in selected)
    status = pulp.LpStatus[prob.status]

    return {
        'selected_pallets': sorted(selected),
        'total_profit': total_profit,
        'total_weight': total_weight,
        'status': status
    }

if _name_ == "_main_":
    if len(sys.argv) < 3:
        print("Usage: python python.py TP5.csv P5.csv")
        sys.exit(1)

    truck_file = sys.argv[1]
    pallet_file = sys.argv[2]

    try:
        capacity, pallets_count = read_truck_data(truck_file)
        pallets = read_pallet_data(pallet_file)
        if pallets_count != len(pallets):
            print(f"Warning: Truck file says {pallets_count} pallets "
                  f"but pallet data file has {len(pallets)} entries")

        result = solve_knapsack(pallets, capacity)

        print("Status:", result['status'])
        print("Total Profit:", result['total_profit'])
        print("Total Weight:", result['total_weight'])
        print("Selected Pallets:", result['selected_pallets'])

    except Exception as e:
        print("Error:", e)
        sys.exit(1)