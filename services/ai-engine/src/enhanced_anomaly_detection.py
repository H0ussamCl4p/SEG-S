"""
Enhanced Anomaly Detection with Ensemble Methods

Provides multiple anomaly detection algorithms with voting:
1. Isolation Forest - Tree-based anomaly detection
2. Local Outlier Factor (LOF) - Density-based detection
3. One-Class SVM - Support vector machine approach
4. Ensemble Voting - Combines all methods for robust detection

Each algorithm has different strengths:
- Isolation Forest: Fast, good for high-dimensional data
- LOF: Good for clustered data, detects local outliers
- One-Class SVM: Good for well-defined normal regions
"""

import numpy as np
import pickle
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')


class AnomalyAlgorithm(str, Enum):
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "lof"
    ONE_CLASS_SVM = "ocsvm"
    ENSEMBLE = "ensemble"


@dataclass
class AnomalyPrediction:
    """Result of anomaly detection"""
    is_anomaly: bool
    anomaly_score: float  # 0-100, higher = more anomalous
    confidence: float  # 0-100
    algorithm_votes: Dict[str, bool]  # Which algorithms flagged as anomaly
    contributing_factors: List[str]
    risk_level: str  # NORMAL, LOW, MEDIUM, HIGH, CRITICAL


class IsolationForestDetector:
    """Isolation Forest anomaly detector"""
    
    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.05,
        random_state: int = 42,
        max_features: float = 1.0
    ):
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            max_features=max_features,
            n_jobs=-1
        )
        self.scaler = RobustScaler()
        self.is_fitted = False
        self.feature_names: List[str] = []
    
    def fit(self, X: np.ndarray, feature_names: List[str] = None) -> 'IsolationForestDetector':
        """Fit the detector on training data"""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies.
        
        Returns:
            labels: -1 for anomaly, 1 for normal
            scores: Anomaly scores (lower = more anomalous)
        """
        if not self.is_fitted:
            raise ValueError("Detector not fitted. Call fit() first.")
        
        X_scaled = self.scaler.transform(X)
        labels = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        return labels, scores
    
    def score_to_percentage(self, score: float) -> float:
        """Convert raw score to 0-100 anomaly percentage"""
        # Isolation Forest scores typically range from -0.5 to 0.5
        # Lower scores indicate anomalies
        normalized = (0.5 - score) * 100
        return max(0, min(100, normalized))


class LocalOutlierFactorDetector:
    """Local Outlier Factor anomaly detector"""
    
    def __init__(
        self,
        n_neighbors: int = 20,
        contamination: float = 0.05,
        novelty: bool = True
    ):
        self.model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=novelty,
            n_jobs=-1
        )
        self.scaler = RobustScaler()
        self.is_fitted = False
        self.feature_names: List[str] = []
    
    def fit(self, X: np.ndarray, feature_names: List[str] = None) -> 'LocalOutlierFactorDetector':
        """Fit the detector on training data"""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies"""
        if not self.is_fitted:
            raise ValueError("Detector not fitted. Call fit() first.")
        
        X_scaled = self.scaler.transform(X)
        labels = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        return labels, scores
    
    def score_to_percentage(self, score: float) -> float:
        """Convert raw score to 0-100 anomaly percentage"""
        # LOF scores are negative, lower = more anomalous
        # Typical range: -2 to 0 for inliers
        normalized = (-score - 1) * 50
        return max(0, min(100, normalized))


class OneClassSVMDetector:
    """One-Class SVM anomaly detector"""
    
    def __init__(
        self,
        kernel: str = 'rbf',
        gamma: str = 'auto',
        nu: float = 0.05
    ):
        self.model = OneClassSVM(
            kernel=kernel,
            gamma=gamma,
            nu=nu
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names: List[str] = []
    
    def fit(self, X: np.ndarray, feature_names: List[str] = None) -> 'OneClassSVMDetector':
        """Fit the detector on training data"""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies"""
        if not self.is_fitted:
            raise ValueError("Detector not fitted. Call fit() first.")
        
        X_scaled = self.scaler.transform(X)
        labels = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        return labels, scores
    
    def score_to_percentage(self, score: float) -> float:
        """Convert raw score to 0-100 anomaly percentage"""
        # SVM scores: negative = anomaly, positive = normal
        normalized = (1 - score) * 25
        return max(0, min(100, normalized))


class EnsembleAnomalyDetector:
    """
    Ensemble anomaly detector combining multiple algorithms.
    
    Uses voting mechanism with configurable weights and thresholds.
    """
    
    def __init__(
        self,
        contamination: float = 0.05,
        voting_threshold: float = 0.5,  # Fraction of detectors that must agree
        weights: Optional[Dict[str, float]] = None
    ):
        self.contamination = contamination
        self.voting_threshold = voting_threshold
        self.weights = weights or {
            'isolation_forest': 0.4,
            'lof': 0.35,
            'ocsvm': 0.25
        }
        
        # Initialize individual detectors
        self.detectors = {
            'isolation_forest': IsolationForestDetector(contamination=contamination),
            'lof': LocalOutlierFactorDetector(contamination=contamination),
            'ocsvm': OneClassSVMDetector(nu=contamination)
        }
        
        self.is_fitted = False
        self.feature_names: List[str] = []
        self.feature_importances_: Optional[np.ndarray] = None
    
    def fit(self, X: np.ndarray, feature_names: List[str] = None) -> 'EnsembleAnomalyDetector':
        """Fit all detectors on training data"""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        for name, detector in self.detectors.items():
            try:
                detector.fit(X, self.feature_names)
                print(f"  ✓ Fitted {name}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not fit {name}: {e}")
        
        # Estimate feature importances using Isolation Forest
        if hasattr(self.detectors['isolation_forest'].model, 'feature_importances_'):
            self.feature_importances_ = self.detectors['isolation_forest'].model.feature_importances_
        else:
            # Estimate via permutation importance
            self._estimate_feature_importance(X)
        
        self.is_fitted = True
        return self
    
    def _estimate_feature_importance(self, X: np.ndarray) -> None:
        """Estimate feature importance via score variance"""
        n_features = X.shape[1]
        importances = np.zeros(n_features)
        
        base_labels, base_scores = self.detectors['isolation_forest'].predict(X[:100])
        base_anomaly_rate = (base_labels == -1).mean()
        
        for i in range(n_features):
            X_permuted = X[:100].copy()
            np.random.shuffle(X_permuted[:, i])
            
            perm_labels, _ = self.detectors['isolation_forest'].predict(X_permuted)
            perm_anomaly_rate = (perm_labels == -1).mean()
            
            importances[i] = abs(perm_anomaly_rate - base_anomaly_rate)
        
        # Normalize
        if importances.sum() > 0:
            importances = importances / importances.sum()
        
        self.feature_importances_ = importances
    
    def predict(self, X: np.ndarray) -> AnomalyPrediction:
        """
        Predict anomalies using ensemble voting.
        
        Args:
            X: Input features (single sample or batch)
            
        Returns:
            AnomalyPrediction with detailed results
        """
        if not self.is_fitted:
            raise ValueError("Detector not fitted. Call fit() first.")
        
        X = np.atleast_2d(X)
        
        # Get predictions from each detector
        votes = {}
        scores = {}
        weighted_score = 0
        
        for name, detector in self.detectors.items():
            if not detector.is_fitted:
                continue
            
            try:
                labels, raw_scores = detector.predict(X)
                is_anomaly = labels[0] == -1
                pct_score = detector.score_to_percentage(raw_scores[0])
                
                votes[name] = is_anomaly
                scores[name] = pct_score
                weighted_score += self.weights.get(name, 0.33) * pct_score
                
            except Exception as e:
                print(f"Warning: {name} prediction failed: {e}")
                continue
        
        # Calculate ensemble decision
        n_votes = sum(1 for v in votes.values() if v)
        n_detectors = len(votes)
        vote_ratio = n_votes / n_detectors if n_detectors > 0 else 0
        
        is_anomaly = vote_ratio >= self.voting_threshold
        
        # Calculate confidence based on agreement
        if n_detectors == 0:
            confidence = 0
        elif vote_ratio == 0 or vote_ratio == 1:
            confidence = 95  # High confidence when unanimous
        else:
            # Lower confidence when detectors disagree
            confidence = 50 + abs(vote_ratio - 0.5) * 80
        
        # Determine risk level
        if weighted_score >= 80:
            risk_level = "CRITICAL"
        elif weighted_score >= 60:
            risk_level = "HIGH"
        elif weighted_score >= 40:
            risk_level = "MEDIUM"
        elif weighted_score >= 20:
            risk_level = "LOW"
        else:
            risk_level = "NORMAL"
        
        # Identify contributing factors
        contributing_factors = self._get_contributing_factors(X[0])
        
        return AnomalyPrediction(
            is_anomaly=is_anomaly,
            anomaly_score=weighted_score,
            confidence=confidence,
            algorithm_votes=votes,
            contributing_factors=contributing_factors,
            risk_level=risk_level
        )
    
    def _get_contributing_factors(self, x: np.ndarray) -> List[str]:
        """Identify which features are contributing to anomaly"""
        factors = []
        
        if self.feature_importances_ is None:
            return factors
        
        # Get feature values and their importances
        for i, (name, importance) in enumerate(zip(self.feature_names, self.feature_importances_)):
            if importance > 0.1:  # Significant importance
                value = x[i]
                
                # Check if value is extreme (placeholder logic - enhance with actual thresholds)
                if 'Temperature' in name and value > 70:
                    factors.append(f"High {name}: {value:.1f}°C")
                elif 'Temperature' in name and value > 80:
                    factors.append(f"Critical {name}: {value:.1f}°C")
                elif 'Humidity' in name and value > 80:
                    factors.append(f"High {name}: {value:.1f}%")
                elif 'Vibration' in name and value > 85:
                    factors.append(f"High {name}: {value:.1f}")
                elif 'Age' in name and value > 15:
                    factors.append(f"Equipment aging: {value:.0f} months")
        
        return factors if factors else ["General pattern deviation detected"]
    
    def save(self, filepath: str) -> None:
        """Save the ensemble detector"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'detectors': self.detectors,
                'weights': self.weights,
                'voting_threshold': self.voting_threshold,
                'contamination': self.contamination,
                'feature_names': self.feature_names,
                'feature_importances': self.feature_importances_,
                'is_fitted': self.is_fitted
            }, f, protocol=4)
    
    @classmethod
    def load(cls, filepath: str) -> 'EnsembleAnomalyDetector':
        """Load a saved ensemble detector"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        detector = cls(
            contamination=data['contamination'],
            voting_threshold=data['voting_threshold'],
            weights=data['weights']
        )
        detector.detectors = data['detectors']
        detector.feature_names = data['feature_names']
        detector.feature_importances_ = data['feature_importances']
        detector.is_fitted = data['is_fitted']
        
        return detector


def train_ensemble_detector(
    X: np.ndarray,
    feature_names: List[str],
    contamination: float = 0.05,
    validation_split: float = 0.2
) -> Tuple[EnsembleAnomalyDetector, Dict[str, Any]]:
    """
    Train an ensemble anomaly detector with validation.
    
    Args:
        X: Training data
        feature_names: List of feature names
        contamination: Expected fraction of anomalies
        validation_split: Fraction of data for validation
        
    Returns:
        Trained detector and metrics dictionary
    """
    print("🚀 Training Ensemble Anomaly Detector...")
    print(f"   Data shape: {X.shape}")
    print(f"   Features: {feature_names}")
    print(f"   Contamination: {contamination}")
    
    # Split data
    X_train, X_val = train_test_split(X, test_size=validation_split, random_state=42)
    print(f"   Train samples: {len(X_train)}, Validation samples: {len(X_val)}")
    
    # Train detector
    detector = EnsembleAnomalyDetector(contamination=contamination)
    detector.fit(X_train, feature_names)
    
    # Validate
    print("\n📊 Validating...")
    val_predictions = []
    val_scores = []
    
    for i in range(len(X_val)):
        pred = detector.predict(X_val[i:i+1])
        val_predictions.append(pred.is_anomaly)
        val_scores.append(pred.anomaly_score)
    
    # Calculate metrics (using contamination as proxy for expected anomaly rate)
    anomaly_rate = sum(val_predictions) / len(val_predictions)
    mean_score = np.mean(val_scores)
    score_std = np.std(val_scores)
    
    metrics = {
        'validation_samples': len(X_val),
        'anomaly_rate': anomaly_rate,
        'expected_anomaly_rate': contamination,
        'mean_anomaly_score': mean_score,
        'score_std': score_std,
        'feature_importances': dict(zip(feature_names, detector.feature_importances_.tolist()))
    }
    
    print(f"\n✅ Training Complete!")
    print(f"   Anomaly rate: {anomaly_rate:.2%} (expected: {contamination:.2%})")
    print(f"   Mean score: {mean_score:.1f} (std: {score_std:.1f})")
    print(f"   Feature importances: {metrics['feature_importances']}")
    
    return detector, metrics
