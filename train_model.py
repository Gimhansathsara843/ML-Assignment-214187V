import pandas as pd
import numpy as np
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import OrdinalEncoder
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_preprocess(filepath):
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} listings.")
    
    # 1. Target: Price
    # Cleanup price (already done in scraper but good to ensure)
    df['Price'] = pd.to_numeric(df['Total price (LKR)'], errors='coerce')
    df = df.dropna(subset=['Price'])
    
    # 2. Features: Extract numeric specs
    def extract_num(val):
        if not val or pd.isna(val): return np.nan
        match = re.search(r'(\d+)', str(val))
        return int(match.group(1)) if match else np.nan

    df['RAM_GB'] = df['RAM'].apply(extract_num)
    df['Storage_GB'] = df['Storage'].apply(extract_num)
    
    # 3. Handle Categorical
    categorical_cols = ['Brand', 'Operating system', 'Warranty']
    for col in categorical_cols:
        df[col] = df[col].fillna('unknown').astype(str)
        
    features = ['RAM_GB', 'Storage_GB', 'Brand', 'Operating system', 'Warranty']
    X = df[features]
    y = df['Price']
    
    return X, y, categorical_cols

def train_eval():
    data_path = 'sri_lanka_mobile_phone_listings.csv'
    if not os.path.exists(data_path):
        print("Data file not found!")
        return

    X, y, cat_cols = load_and_preprocess(data_path)
    
    # Encode categorical features for HistGradientBoostingRegressor
    encoder = OrdinalEncoder()
    X_encoded = X.copy()
    X_encoded[cat_cols] = encoder.fit_transform(X[cat_cols])
    
    # Split: 80% Train, 10% Valid, 10% Test
    X_train, X_temp, y_train, y_temp = train_test_split(X_encoded, y, test_size=0.2, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    
    print(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
    
    # Train Model
    print("Training HistGradientBoostingRegressor...")
    model = HistGradientBoostingRegressor(
        max_iter=1000,
        learning_rate=0.05,
        max_depth=6,
        early_stopping=True,
        categorical_features=[True if col in cat_cols else False for col in X_encoded.columns]
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print("\n--- Model Performance ---")
    print(f"RMSE: LKR {rmse:,.2f}")
    print(f"MAE:  LKR {mae:,.2f}")
    print(f"R2 Score: {r2:.4f}")
    
    # Visualizations
    from sklearn.inspection import permutation_importance
    
    print("\nGenerating plots...")
    # 1. Actual vs Predicted
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_test, y=y_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    plt.xlabel('Actual Price (LKR)')
    plt.ylabel('Predicted Price (LKR)')
    plt.title(f'Actual vs Predicted Mobile Phone Prices (R2={r2:.4f})')
    plt.tight_layout()
    plt.savefig('actual_vs_predicted.png')
    print("Saved actual_vs_predicted.png")

    # 2. Feature Importance
    result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
    sorted_idx = result.importances_mean.argsort()
    
    plt.figure(figsize=(10, 6))
    plt.boxplot(result.importances[sorted_idx].T, vert=False, labels=np.array(X.columns)[sorted_idx])
    plt.title("Permutation Importance (test set)")
    plt.xlabel("Importance Score")
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    print("Saved feature_importance.png")

    # Simple results analysis
    print("\n--- Results Interpretation ---")
    if r2 > 0.7:
        print("The model shows strong predictive power.")
    elif r2 > 0.4:
        print("The model shows moderate predictive power.")
    else:
        print("The model has low predictive power.")

if __name__ == "__main__":
    train_eval()
