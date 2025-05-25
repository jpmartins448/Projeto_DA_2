try:
    import pandas as pd
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"Error: {e}\nPlease install missing packages using:")
    print("pip3 install pandas matplotlib")
    exit(1)

def analyze_results():
    try:
       
        df = pd.read_csv('results.csv')
        
        print("\nData Sample:")
        print(df)  
        
        # Time comparison plot
        plt.figure(figsize=(12, 6))
        for algo in df['Algorithm'].unique():
            subset = df[df['Algorithm'] == algo]
            plt.plot(subset['Pallets'], subset['Time(ms)'], 'o-', label=algo)
        plt.xlabel('Number of Pallets')
        plt.ylabel('Execution Time (ms)')
        plt.yscale('log')
        plt.title('Algorithm Performance Comparison')
        plt.legend()
        plt.grid(True)
        plt.savefig('performance.png', dpi=300, bbox_inches='tight')
        print("\nSaved performance.png")
        
       

    except FileNotFoundError:
        print("Error: results.csv not found. Run the C++ program first.")
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        raise  # Re-raise to see full traceback

if __name__ == "__main__":
    analyze_results()