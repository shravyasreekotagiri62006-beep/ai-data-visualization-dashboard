import pandas as pd
import os
import json
import numpy as np

def process_and_clean_file(filepath):
    """ Reads CSV/JSON, cleans it, checks edge cases, and returns a processed pandas DataFrame """
    if filepath.endswith('.csv'):
        try:
            df = pd.read_csv(filepath)
        except pd.errors.EmptyDataError:
            raise ValueError("The uploaded CSV file is completely empty.")
    elif filepath.endswith('.json'):
        try:
            df = pd.read_json(filepath)
        except ValueError:
            raise ValueError("The JSON file is empty or malformed.")
    else:
        raise ValueError("Unsupported file format")

    if df.empty:
        raise ValueError("The dataset contains no rows/data.")

    # Convert object columns that look numeric string into numeric type
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
                
    # 1. Handle missing values securely
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].isnull().all():
                df.drop(col, axis=1, inplace=True) # Drop column if completely empty
                continue
            df[col] = df[col].fillna(df[col].median())
        else:
            if df[col].isnull().all():
                df.drop(col, axis=1, inplace=True)
                continue
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "Unknown")
            
    # Check if empty after droppings
    if df.empty:
        raise ValueError("Dataset became empty after dropping unrecoverable null columns.")
        
    # 2. Outlier Smoothing (Optional based on Z-score for numeric cols)
    for col in df.select_dtypes(include=[np.number]).columns:
        p1 = df[col].quantile(0.01)
        p99 = df[col].quantile(0.99)
        df[col] = df[col].clip(lower=p1, upper=p99)

    return df

def get_column_metrics(df):
    """ Get data summarization and quality metrics """
    metrics = {
        'total_rows': len(df),
        'columns': list(df.columns),
        'numeric_cols': list(df.select_dtypes(include=[np.number]).columns),
        'categorical_cols': list(df.select_dtypes(exclude=[np.number]).columns),
        'stats': {}
    }

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            metrics['stats'][col] = {
                'type': 'numeric',
                'mean': float(df[col].mean()),
                'max': float(df[col].max()),
                'min': float(df[col].min()),
                'std': float(df[col].std()) if pd.notnull(df[col].std()) else 0
            }
        else:
            metrics['stats'][col] = {
                'type': 'categorical',
                'unique_count': int(df[col].nunique()),
                'top_value': str(df[col].mode()[0]) if not df[col].mode().empty else "None"
            }
            
    return metrics
