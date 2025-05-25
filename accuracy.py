import pandas as pd
import matplotlib.pyplot as plt

def compare_accuracy():
    try:
        # Read CSV without header names since file has headers
        df = pd.read_csv('results.csv')
        
        # Group by Pallets and Algorithm to handle duplicates
        optimal = df[df['Algorithm'].isin(['Dynamic Programming', 'ILP'])]
        optimal = optimal.groupby('Pallets')['Profit'].max().reset_index()
        
        # Merge optimal profits back to original dataframe
        df = pd.merge(df, optimal, on='Pallets', suffixes=('', '_optimal'))
        
        # Calculate accuracy percentages
        df['Accuracy'] = (df['Profit'] / df['Profit_optimal']) * 100
        
        # Summary statistics
        accuracy_stats = df.groupby('Algorithm')['Accuracy'].agg(['mean', 'min', 'max'])
        print("\nAccuracy Comparison (% of Optimal):")
        print(accuracy_stats.round(2))
        
        # Visualize
        plt.figure(figsize=(12, 6))
        for algo in df['Algorithm'].unique():
            if algo not in ['Dynamic Programming', 'ILP']:
                subset = df[df['Algorithm'] == algo]
                plt.plot(subset['Pallets'], subset['Accuracy'], 'o-', label=algo)
        
        plt.axhline(y=100, color='r', linestyle='--', label='Optimal')
        plt.xlabel('Number of Pallets')
        plt.ylabel('Accuracy (% of Optimal)')
        plt.title('Algorithm Accuracy Comparison')
        plt.legend()
        plt.grid()
        plt.savefig('accuracy_comparison.png', dpi=300, bbox_inches='tight')
        print("\nSaved accuracy_comparison.png")
        
        # Show worst-case greedy performance
        worst_greedy = df[df['Algorithm'] == 'Greedy'].nsmallest(1, 'Accuracy')
        print("\nWorst Greedy Performance:")
        print(worst_greedy[['Pallets', 'Capacity', 'Profit', 'Profit_optimal', 'Accuracy']])
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    compare_accuracy()