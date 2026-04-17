import os
import csv
import glob
from pathlib import Path

def count_lines_in_csv(file_path):
    """Count number of data rows in a CSV file (excluding header)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header if present
            header = next(reader, None)
            row_count = sum(1 for row in reader)
            return row_count, header is not None
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return 0, False

def analyze_csv_files(directory="."):
    """Analyze all CSV files in the given directory"""
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {directory}")
        return
    
    print("=" * 70)
    print(f"📊 CSV FILE ANALYSIS - {directory}")
    print("=" * 70)
    print()
    
    results = []
    total_rows = 0
    total_files = 0
    
    # Sort files alphabetically for consistent output
    csv_files.sort()
    
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        row_count, has_header = count_lines_in_csv(file_path)
        
        if row_count > 0 or has_header:
            results.append({
                'file': file_name,
                'rows': row_count,
                'has_header': has_header
            })
            total_rows += row_count
            total_files += 1
            
            print(f"📄 {file_name}")
            print(f"   Data rows: {row_count:,}")
            if has_header:
                print(f"   Has header: Yes")
            print()
    
    # Summary
    print("=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    print(f"Total files analyzed: {total_files}")
    print(f"Total data rows across all files: {total_rows:,}")
    
    # Optional: Show breakdown by file type/group
    print("\n📁 BREAKDOWN BY FILE:")
    for result in results:
        print(f"   {result['file']}: {result['rows']:,} rows")
    
    return results, total_rows

def analyze_specific_files(file_list):
    """Analyze specific CSV files passed as a list"""
    total_rows = 0
    results = []
    
    print("=" * 70)
    print("📊 SPECIFIC CSV FILE ANALYSIS")
    print("=" * 70)
    print()
    
    for file_path in file_list:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            row_count, has_header = count_lines_in_csv(file_path)
            
            results.append({
                'file': file_name,
                'rows': row_count,
                'has_header': has_header
            })
            total_rows += row_count
            
            print(f"📄 {file_name}: {row_count:,} rows")
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print()
    print("=" * 70)
    print(f"📈 TOTAL ROWS: {total_rows:,}")
    print("=" * 70)
    
    return results, total_rows

def main():
    """Main function with user input"""
    print("CSV Line Counter")
    print("=" * 40)
    print()
    print("Options:")
    print("1. Analyze all CSV files in current directory")
    print("2. Analyze all CSV files in specific directory")
    print("3. Analyze specific CSV files")
    print()
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        analyze_csv_files(".")
    
    elif choice == "2":
        directory = input("Enter directory path: ").strip()
        analyze_csv_files(directory)
    
    elif choice == "3":
        print("Enter file paths (one per line, empty line to finish):")
        files = []
        while True:
            file_path = input().strip()
            if not file_path:
                break
            files.append(file_path)
        if files:
            analyze_specific_files(files)
        else:
            print("No files provided.")
    
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()