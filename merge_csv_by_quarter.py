#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV Merger Utility for Naver News Crawling Results

This script merges CSV files created by the crawler into quarterly consolidated files,
removing duplicates based on the 'link' column.
"""

import pandas as pd
import os
import glob
from datetime import datetime
import argparse
import re


def sort_data_by_date(df: pd.DataFrame, date_column: str = 'date') -> pd.DataFrame:
    """
    Sort the dataframe by date column.
    
    Args:
        df (pd.DataFrame): Input dataframe
        date_column (str): Name of the date column
    
    Returns:
        pd.DataFrame: Sorted dataframe
    """
    # Convert date column to datetime for proper sorting
    df_copy = df.copy()
    
    # Handle the date format (e.g., "2022.03.23." -> "2022-03-23")
    df_copy[date_column] = df_copy[date_column].str.replace('.', '-').str.rstrip('-')
    
    # Convert to datetime
    df_copy[date_column] = pd.to_datetime(df_copy[date_column], format='%Y-%m-%d', errors='coerce')
    
    # Sort by date (newest first)
    df_copy = df_copy.sort_values(by=date_column, ascending=False)
    
    # Convert back to original format for consistency
    df_copy[date_column] = df_copy[date_column].dt.strftime('%Y.%m.%d.')
    
    return df_copy


def merge_csv_by_quarter(quarter_start_date: str, quarter_end_date: str, 
                         result_path: str = "out/naver_news_crawling_result/",
                         output_filename: str = None):
    """
    Merges all CSV files from a given quarter into a single file, removing duplicates.
    
    Args:
        quarter_start_date (str): Start date in "YY.MM.DD" format (e.g., "22.01.01")
        quarter_end_date (str): End date in "YY.MM.DD" format (e.g., "22.03.31")
        result_path (str): Path to directory containing CSV files
        output_filename (str): Optional custom output filename
    
    Returns:
        str: Path to the merged CSV file
    """
    # Ensure result path exists
    os.makedirs(result_path, exist_ok=True)
    
    # Convert dates to filename format for pattern matching
    # Remove dots and convert to underscore format for pattern matching
    start_date_clean = quarter_start_date.replace('.', '_')
    end_date_clean = quarter_end_date.replace('.', '_')
    
    # Pattern to match CSV files from this quarter
    # Files follow pattern: YY_MM_DD_MM_DD_*.csv
    pattern = os.path.join(result_path, f"{start_date_clean}_{end_date_clean}_*.csv")
    
    # Find all matching CSV files
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        print(f"No CSV files found for quarter {quarter_start_date} to {quarter_end_date}")
        print(f"Pattern searched: {pattern}")
        return None
    
    print(f"Found {len(csv_files)} CSV files to merge:")
    for file in csv_files:
        print(f"  - {os.path.basename(file)}")
    
    # Read and combine all CSV files
    all_data = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
            print(f"  Loaded {len(df)} rows from {os.path.basename(file)}")
            all_data.append(df)
        except Exception as e:
            print(f"  Error reading {file}: {e}")
            continue
    
    if not all_data:
        print("No data could be loaded from CSV files")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined data: {len(combined_df)} rows")
    
    # Remove duplicates based on 'link' column
    before_dedup = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['link'], keep='first')
    after_dedup = len(combined_df)
    duplicates_removed = before_dedup - after_dedup
    
    print(f"Duplicates removed: {duplicates_removed} rows")
    print(f"Final data: {len(combined_df)} rows")
    
    # Sort by date
    print("Sorting data by date...")
    combined_df = sort_data_by_date(combined_df)
    
    # Generate output filename if not provided
    if output_filename is None:
        # Use the same date format as input files
        output_filename = f"merged_{quarter_start_date}_{quarter_end_date}_quarter.csv"
    
    output_path = os.path.join(result_path, output_filename)
    
    # Save merged data
    combined_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Merged data saved to: {output_path}")
    
    return output_path


def merge_csv_by_quarter_name(year: int, quarter: int, 
                             result_path: str = "out/naver_news_crawling_result/",
                             output_filename: str = None):
    """
    Merges all CSV files from a given quarter using the actual filename pattern.
    
    Args:
        year (int): Year (e.g., 2022)
        quarter (int): Quarter number (1, 2, 3, or 4)
        result_path (str): Path to directory containing CSV files
        output_filename (str): Optional custom output filename
    
    Returns:
        str: Path to the merged CSV file
    """
    # Ensure result path exists
    os.makedirs(result_path, exist_ok=True)
    
    # Convert full year to YY format
    year_short = str(year)[-2:]
    
    # Pattern to match CSV files from this quarter
    # Files follow pattern: 22Q1_*.csv
    pattern = os.path.join(result_path, f"{year_short}Q{quarter}_*.csv")
    
    # Find all matching CSV files
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        print(f"No CSV files found for quarter {year}Q{quarter}")
        print(f"Pattern searched: {pattern}")
        return None
    
    print(f"Found {len(csv_files)} CSV files to merge:")
    for file in csv_files:
        print(f"  - {os.path.basename(file)}")
    
    # Read and combine all CSV files
    all_data = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
            print(f"  Loaded {len(df)} rows from {os.path.basename(file)}")
            all_data.append(df)
        except Exception as e:
            print(f"  Error reading {file}: {e}")
            continue
    
    if not all_data:
        print("No data could be loaded from CSV files")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined data: {len(combined_df)} rows")
    
    # Remove duplicates based on 'link' column
    before_dedup = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['link'], keep='first')
    after_dedup = len(combined_df)
    duplicates_removed = before_dedup - after_dedup
    
    print(f"Duplicates removed: {duplicates_removed} rows")
    print(f"Final data: {len(combined_df)} rows")
    
    # Sort by date
    print("Sorting data by date...")
    combined_df = sort_data_by_date(combined_df)
    
    # Generate output filename if not provided
    if output_filename is None:
        output_filename = f"merged_{year_short}Q{quarter}_quarter.csv"
    
    output_path = os.path.join(result_path, output_filename)
    
    # Save merged data
    combined_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Merged data saved to: {output_path}")
    
    return output_path


def get_quarter_dates(year: int, quarter: int):
    """
    Get start and end dates for a given year and quarter.
    
    Args:
        year (int): Year (e.g., 2022)
        quarter (int): Quarter number (1, 2, 3, or 4)
    
    Returns:
        tuple: (start_date, end_date) in "YY.MM.DD" format
    """
    # Convert full year to YY format
    year_short = str(year)[-2:]  # Get last 2 digits
    
    if quarter == 1:
        return f"{year_short}.01.01", f"{year_short}.03.31"
    elif quarter == 2:
        return f"{year_short}.04.01", f"{year_short}.06.30"
    elif quarter == 3:
        return f"{year_short}.07.01", f"{year_short}.09.30"
    elif quarter == 4:
        return f"{year_short}.10.01", f"{year_short}.12.31"
    else:
        raise ValueError("Quarter must be 1, 2, 3, or 4")


def list_available_quarters(result_path: str = "out/naver_news_crawling_result/"):
    """
    List all available quarters that have CSV files.
    
    Args:
        result_path (str): Path to directory containing CSV files
    """
    if not os.path.exists(result_path):
        print(f"Result path does not exist: {result_path}")
        return
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(result_path, "*.csv"))
    
    if not csv_files:
        print("No CSV files found")
        return
    
    # Extract unique quarters from filenames
    quarters = set()
    for file in csv_files:
        filename = os.path.basename(file)
        # Extract quarter from filename (format: 22Q1_*.csv)
        quarter_pattern = r'(\d{2})Q(\d)'
        match = re.search(quarter_pattern, filename)
        
        if match:
            year = match.group(1)
            quarter = match.group(2)
            quarters.add((year, quarter))
    
    if quarters:
        print("Available quarters:")
        for year, quarter in sorted(quarters):
            print(f"  20{year} Q{quarter}")
    else:
        print("No quarters could be extracted from filenames")


def main():
    parser = argparse.ArgumentParser(description='Merge CSV files by quarter')
    parser.add_argument('--start-date', type=str, help='Start date in YY.MM.DD format (e.g., 22.01.01)')
    parser.add_argument('--end-date', type=str, help='End date in YY.MM.DD format (e.g., 22.03.31)')
    parser.add_argument('--year', type=int, help='Year for quarter selection (e.g., 2022)')
    parser.add_argument('--quarter', type=int, choices=[1, 2, 3, 4], help='Quarter number (1-4)')
    parser.add_argument('--result-path', type=str, default='out/naver_news_crawling_result/',
                       help='Path to directory containing CSV files')
    parser.add_argument('--output', type=str, help='Custom output filename')
    parser.add_argument('--list', action='store_true', help='List available quarters')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_quarters(args.result_path)
        return
    
    # Determine dates
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
        print(f"Merging CSV files for period: {start_date} to {end_date}")
        # Merge the files using date range
        result = merge_csv_by_quarter(start_date, end_date, args.result_path, args.output)
    elif args.year and args.quarter:
        print(f"Merging CSV files for {args.year} Q{args.quarter}")
        # Merge the files using quarter
        result = merge_csv_by_quarter_name(args.year, args.quarter, args.result_path, args.output)
    else:
        print("Please provide either --start-date and --end-date, or --year and --quarter")
        print("Use --help for more information")
        return
    
    if result:
        print(f"\nMerge completed successfully!")
        print(f"Output file: {result}")
    else:
        print("\nMerge failed!")


if __name__ == "__main__":
    main() 