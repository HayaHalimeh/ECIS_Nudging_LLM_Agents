import pandas as pd
from pathlib import Path
import glob
import os


def find_csv_files(data_path: Path):
    """Return a list of all CSV files in the given folder."""
    csv_files = glob.glob(os.path.join(data_path, "*.csv"))
    print(f"Found {len(csv_files)} CSV files in {data_path}")
    return csv_files


def load_and_combine(csv_files):
    """Load all CSV files, tag with source file, and combine into one DataFrame."""
    dfs = []
    for file in csv_files:
        df = pd.read_csv(file)
        df["source_file"] = os.path.basename(file)
        dfs.append(df)
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(csv_files)} files. Combined shape: {combined_df.shape}")
    return combined_df


def preprocess_data(df):
    """Ensure correct data types."""
    df["condition"] = df["condition"].astype("category")
    df["agent"] = df["agent"].astype("category")
    df["target_product_selected"] = df["target_product_selected"].astype(int)
    return df


def save_combined_data(df, output_path: Path):
    """Save combined DataFrame to CSV."""
    df.to_csv(output_path, index=False)
    print(f"✅ Combined data saved to {output_path}")


def main():
    # Path to your data folder
    data_path = Path("data")
    output_file = data_path / "combined_data.csv"

    csv_files = find_csv_files(data_path)
    if not csv_files:
        print("⚠️ No CSV files found. Exiting.")
        return

    combined_df = load_and_combine(csv_files)
    combined_df = preprocess_data(combined_df)
    save_combined_data(combined_df, output_file)


if __name__ == "__main__":
    main()
