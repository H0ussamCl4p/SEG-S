"""
Enhanced Model Training Script with Model Registry Integration

This script:
1. Trains models using the enhanced anomaly detection ensemble
2. Registers models with versioning and metrics
3. Supports both anomaly detection and predictive models
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_registry import (
    ModelRegistry, ModelType, ModelStatus, ModelMetrics, get_registry
)
from enhanced_anomaly_detection import (
    EnsembleAnomalyDetector, train_ensemble_detector
)


# Configuration
DATA_DIR = os.getenv("DATA_DIR", "data")
MODEL_DIR = os.getenv("MODEL_DIR", "models")
INPUT_FILE = os.path.join(DATA_DIR, "training_data.csv")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


def load_training_data(filepath: str) -> pd.DataFrame:
    """Load and preprocess training data"""
    print(f"📂 Loading training data from {filepath}...")
    
    df = pd.read_csv(filepath)
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    print(f"   Loaded {len(df)} rows")
    print(f"   Columns: {df.columns.tolist()}")
    
    # Basic data validation
    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        print(f"   ⚠️  Warning: Found null values:\n{null_counts[null_counts > 0]}")
        df = df.dropna()
        print(f"   Dropped null rows. Remaining: {len(df)}")
    
    return df


def train_anomaly_detection_model(
    df: pd.DataFrame,
    features: list,
    contamination: float = 0.05,
    register: bool = True
) -> EnsembleAnomalyDetector:
    """
    Train ensemble anomaly detection model.
    
    Args:
        df: Training DataFrame
        features: List of feature column names
        contamination: Expected fraction of anomalies
        register: Whether to register in model registry
    
    Returns:
        Trained EnsembleAnomalyDetector
    """
    print("\n" + "="*60)
    print("🧠 TRAINING ANOMALY DETECTION MODEL (Ensemble)")
    print("="*60)
    
    X = df[features].values
    
    # Train ensemble detector
    detector, metrics = train_ensemble_detector(
        X=X,
        feature_names=features,
        contamination=contamination,
        validation_split=0.2
    )
    
    # Save model
    model_path = os.path.join(MODEL_DIR, "ensemble_anomaly_detector.pkl")
    detector.save(model_path)
    print(f"   💾 Saved model to {model_path}")
    
    # Register in model registry
    if register:
        registry = get_registry()
        
        model_metrics = ModelMetrics(
            accuracy=1.0 - abs(metrics['anomaly_rate'] - metrics['expected_anomaly_rate']),
            training_samples=int(len(X) * 0.8),
            validation_samples=metrics['validation_samples']
        )
        
        version = registry.register_model(
            model=detector,
            model_type=ModelType.ENSEMBLE,
            algorithm="EnsembleAnomalyDetector (IF + LOF + OCSVM)",
            hyperparameters={
                'contamination': contamination,
                'voting_threshold': 0.5,
                'weights': detector.weights
            },
            features=features,
            metrics=model_metrics,
            scaler=None,  # Scalers are internal to detector
            description="Ensemble anomaly detector combining Isolation Forest, LOF, and One-Class SVM",
            version_bump="minor",
            status=ModelStatus.STAGING
        )
        
        print(f"   📋 Registered as v{version.version} (status: {version.status.value})")
    
    # Also save in legacy format for backward compatibility
    legacy_path = os.path.join(MODEL_DIR, "anomaly_model.pkl")
    detector.save(legacy_path)
    print(f"   💾 Saved legacy format to {legacy_path}")
    
    return detector


def train_predictive_model(
    df: pd.DataFrame,
    features: list,
    target: str = 'MTTF',
    register: bool = True
) -> tuple:
    """
    Train predictive model for MTTF estimation.
    
    Args:
        df: Training DataFrame
        features: List of feature column names
        target: Target column name
        register: Whether to register in model registry
    
    Returns:
        Tuple of (model, scaler, metrics)
    """
    print("\n" + "="*60)
    print("🔮 TRAINING PREDICTIVE MODEL (MTTF)")
    print("="*60)
    
    if target not in df.columns:
        print(f"   ⚠️  Target column '{target}' not found. Skipping predictive model.")
        return None, None, None
    
    X = df[features].values
    y = df[target].values
    
    print(f"   Features: {features}")
    print(f"   Target: {target}")
    print(f"   Target range: {y.min():.1f} - {y.max():.1f} (mean: {y.mean():.1f})")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest Regressor
    print("   Training Random Forest Regressor...")
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='neg_mean_absolute_error')
    print(f"   Cross-validation MAE: {-cv_scores.mean():.2f} (+/- {cv_scores.std():.2f})")
    
    # Fit final model
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n   📊 Test Metrics:")
    print(f"      MAE:  {mae:.2f}")
    print(f"      RMSE: {rmse:.2f}")
    print(f"      R²:   {r2:.4f}")
    
    # Feature importances
    importances = dict(zip(features, model.feature_importances_.tolist()))
    print(f"\n   📈 Feature Importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"      {feat}: {imp:.4f}")
    
    # Create metrics object
    metrics = {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'cv_mae_mean': float(-cv_scores.mean()),
        'cv_mae_std': float(cv_scores.std()),
        'feature_importances': importances
    }
    
    # Save model bundle
    import pickle
    bundle = {
        'model': model,
        'scaler': scaler,
        'features': features,
        'target': target,
        'metrics': metrics
    }
    
    model_path = os.path.join(MODEL_DIR, "predictive_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(bundle, f, protocol=4)
    print(f"\n   💾 Saved model to {model_path}")
    
    # Register in model registry
    if register:
        registry = get_registry()
        
        model_metrics = ModelMetrics(
            mae=mae,
            rmse=rmse,
            training_samples=len(X_train),
            validation_samples=len(X_test)
        )
        
        version = registry.register_model(
            model=model,
            model_type=ModelType.PREDICTIVE,
            algorithm="RandomForestRegressor",
            hyperparameters={
                'n_estimators': 150,
                'max_depth': 12,
                'min_samples_split': 5,
                'min_samples_leaf': 2
            },
            features=features,
            metrics=model_metrics,
            scaler=scaler,
            description=f"MTTF prediction model. R²={r2:.4f}, MAE={mae:.2f}",
            version_bump="minor",
            status=ModelStatus.STAGING
        )
        
        print(f"   📋 Registered as v{version.version} (status: {version.status.value})")
    
    return model, scaler, metrics


def main():
    """Main training pipeline"""
    print("\n" + "="*60)
    print("🚀 IIoT PREDICTIVE MAINTENANCE - MODEL TRAINING")
    print("="*60 + "\n")
    
    # Load data
    df = load_training_data(INPUT_FILE)
    
    # Define features
    features = ['Humidity', 'Temperature', 'Age', 'Quantity']
    
    # Verify features exist
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        print(f"❌ Missing features: {missing_features}")
        print(f"   Available columns: {df.columns.tolist()}")
        return
    
    # Train anomaly detection model
    anomaly_detector = train_anomaly_detection_model(
        df=df,
        features=features,
        contamination=0.05,
        register=True
    )
    
    # Train predictive model
    pred_model, pred_scaler, pred_metrics = train_predictive_model(
        df=df,
        features=features,
        target='MTTF',
        register=True
    )
    
    # Show registry summary
    print("\n" + "="*60)
    print("📋 MODEL REGISTRY SUMMARY")
    print("="*60)
    
    registry = get_registry()
    summary = registry.get_registry_summary()
    
    for model_type, info in summary.items():
        if info['total_versions'] > 0:
            print(f"\n   {model_type}:")
            print(f"      Total versions: {info['total_versions']}")
            print(f"      Active version: {info['active_version'] or 'None (promote a version)'}")
            print(f"      All versions: {info['versions']}")
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60 + "\n")
    
    print("Next steps:")
    print("  1. Review model metrics")
    print("  2. Promote models to ACTIVE status via API or registry.promote_model()")
    print("  3. Monitor model performance in production")


if __name__ == "__main__":
    main()
