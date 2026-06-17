import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Configuration
INPUT_FILE = "data/training_data.csv"
MODEL_FILE = "model_brain.pkl"
SCALER_FILE = "scaler.pkl"
PREDICTIVE_MODEL_FILE = "models/predictive_model.pkl"
PREDICTIVE_SCALER_FILE = "models/predictive_scaler.pkl"

# Ensure models directory exists
os.makedirs("models", exist_ok=True)

print("🧠 Loading training data...")
# 1. Load Data
df = pd.read_csv(INPUT_FILE)
# Strip whitespace from column names
df.columns = df.columns.str.strip()
print(f"   - Loaded {len(df)} rows.")
print(f"   - Columns: {df.columns.tolist()}")

# 2. Select Features (The columns the AI should look at)
# Use actual column names from the training data
features = ['Humidity', 'Temperature', 'Age', 'Quantity']
X = df[features].values

# 3. Scale the Data (CRITICAL STEP)
# Vibration is ~10, Temp is ~45. We squash them to the same range so the AI plays fair.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Train the Model (Isolation Forest)
# contamination=0.01 means "Assume 1% of this training data might be noise/glitches"
print("🏋️  Training Isolation Forest...")
model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
model.fit(X_scaled)

# 5. Save the Brain and the Scaler
# We need BOTH files to run this on another computer.
joblib.dump(model, MODEL_FILE)
joblib.dump(scaler, SCALER_FILE)

print("✅ Anomaly Detection Training Complete!")
print(f"   - Model saved to: {MODEL_FILE}")
print(f"   - Scaler saved to: {SCALER_FILE}")

# 6. Train Predictive Model (Random Forest Regressor for MTTF)
print("\n🔮 Training Predictive Model (MTTF)...")
if 'MTTF' in df.columns:
    # Features for prediction (same as anomaly detection)
    X_pred = df[features].values
    y_pred = df['MTTF'].values
    
    # Scale features for predictive model
    pred_scaler = StandardScaler()
    X_pred_scaled = pred_scaler.fit_transform(X_pred)
    
    # Train Random Forest Regressor
    pred_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    pred_model.fit(X_pred_scaled, y_pred)
    
    # Save predictive model bundle as a single pickle dict the API expects
    import pickle
    bundle = {
        'model': pred_model,
        'scaler': pred_scaler,
        'features': features,
    }
    with open(PREDICTIVE_MODEL_FILE, 'wb') as f:
        pickle.dump(bundle, f, protocol=4)
    # Optionally save scaler separately for debugging/inspection
    joblib.dump(pred_scaler, PREDICTIVE_SCALER_FILE, protocol=4)
    
    print("✅ Predictive Model Training Complete!")
    print(f"   - Model saved to: {PREDICTIVE_MODEL_FILE}")
    print(f"   - Scaler saved to: {PREDICTIVE_SCALER_FILE}")
else:
    print("⚠️  MTTF column not found. Skipping predictive model training.")
