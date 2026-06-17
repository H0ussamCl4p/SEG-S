"""
Model Registry and Versioning System for IIoT Predictive Maintenance

Provides:
- Model versioning with semantic versioning (major.minor.patch)
- Performance metrics tracking
- Model rollback capability
- A/B testing support
- Metadata storage for each model version
"""

import os
import json
import pickle
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np


class ModelType(str, Enum):
    ANOMALY_DETECTION = "anomaly_detection"
    PREDICTIVE = "predictive"
    FORECASTING = "forecasting"
    ENSEMBLE = "ensemble"


class ModelStatus(str, Enum):
    ACTIVE = "active"          # Currently in production
    STAGING = "staging"        # Ready for A/B testing
    ARCHIVED = "archived"      # Older version, kept for rollback
    DEPRECATED = "deprecated"  # Marked for removal


@dataclass
class ModelMetrics:
    """Performance metrics for a model version"""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mae: Optional[float] = None  # Mean Absolute Error (for regression)
    rmse: Optional[float] = None  # Root Mean Square Error
    auc_roc: Optional[float] = None
    confusion_matrix: Optional[List[List[int]]] = None
    training_samples: int = 0
    validation_samples: int = 0
    inference_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ModelVersion:
    """Represents a single model version"""
    version: str  # Semantic version: "1.0.0"
    model_type: ModelType
    status: ModelStatus
    created_at: str
    updated_at: str
    created_by: str
    description: str
    
    # Training configuration
    algorithm: str
    hyperparameters: Dict[str, Any]
    features: List[str]
    
    # Performance
    metrics: ModelMetrics
    
    # File references
    model_file: str
    scaler_file: Optional[str] = None
    
    # Checksums for integrity
    model_checksum: Optional[str] = None
    
    # A/B testing
    traffic_percentage: float = 0.0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['model_type'] = self.model_type.value
        data['status'] = self.status.value
        data['metrics'] = self.metrics.to_dict()
        return data


class ModelRegistry:
    """
    Central registry for managing ML model versions.
    
    Directory structure:
    /models/
        registry.json           # Registry metadata
        anomaly_detection/
            v1.0.0/
                model.pkl
                scaler.pkl
                metadata.json
            v1.1.0/
                ...
        predictive/
            v1.0.0/
                ...
    """
    
    def __init__(self, base_path: str = "/app/models"):
        self.base_path = base_path
        self.registry_file = os.path.join(base_path, "registry.json")
        self.registry: Dict[str, List[Dict]] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from disk"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    self.registry = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load registry: {e}")
                self.registry = {}
        else:
            self.registry = {}
            self._save_registry()
    
    def _save_registry(self) -> None:
        """Persist registry to disk"""
        os.makedirs(self.base_path, exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def _compute_checksum(self, file_path: str) -> str:
        """Compute SHA256 checksum for file integrity"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_next_version(self, model_type: ModelType, bump: str = "patch") -> str:
        """Get next version number based on existing versions"""
        type_key = model_type.value
        if type_key not in self.registry or not self.registry[type_key]:
            return "1.0.0"
        
        # Get latest version
        versions = [v['version'] for v in self.registry[type_key]]
        versions.sort(key=lambda v: [int(x) for x in v.split('.')])
        latest = versions[-1]
        
        major, minor, patch = map(int, latest.split('.'))
        
        if bump == "major":
            return f"{major + 1}.0.0"
        elif bump == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"
    
    def register_model(
        self,
        model: Any,
        model_type: ModelType,
        algorithm: str,
        hyperparameters: Dict[str, Any],
        features: List[str],
        metrics: ModelMetrics,
        scaler: Any = None,
        description: str = "",
        created_by: str = "system",
        version_bump: str = "patch",
        status: ModelStatus = ModelStatus.STAGING
    ) -> ModelVersion:
        """
        Register a new model version in the registry.
        
        Args:
            model: Trained model object
            model_type: Type of model (anomaly_detection, predictive, etc.)
            algorithm: Algorithm name (e.g., "IsolationForest", "RandomForestRegressor")
            hyperparameters: Training hyperparameters
            features: List of feature names used
            metrics: Performance metrics
            scaler: Optional scaler object
            description: Human-readable description
            created_by: Username or system identifier
            version_bump: "major", "minor", or "patch"
            status: Initial model status
        
        Returns:
            ModelVersion object
        """
        type_key = model_type.value
        version = self._get_next_version(model_type, version_bump)
        
        # Create version directory
        version_dir = os.path.join(self.base_path, type_key, f"v{version}")
        os.makedirs(version_dir, exist_ok=True)
        
        # Save model
        model_file = os.path.join(version_dir, "model.pkl")
        with open(model_file, 'wb') as f:
            pickle.dump(model, f, protocol=4)
        
        # Save scaler if provided
        scaler_file = None
        if scaler is not None:
            scaler_file = os.path.join(version_dir, "scaler.pkl")
            with open(scaler_file, 'wb') as f:
                pickle.dump(scaler, f, protocol=4)
        
        # Compute checksum
        model_checksum = self._compute_checksum(model_file)
        
        now = datetime.utcnow().isoformat() + "Z"
        
        # Create version object
        model_version = ModelVersion(
            version=version,
            model_type=model_type,
            status=status,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            description=description,
            algorithm=algorithm,
            hyperparameters=hyperparameters,
            features=features,
            metrics=metrics,
            model_file=model_file,
            scaler_file=scaler_file,
            model_checksum=model_checksum,
            traffic_percentage=0.0
        )
        
        # Save metadata
        metadata_file = os.path.join(version_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(model_version.to_dict(), f, indent=2)
        
        # Update registry
        if type_key not in self.registry:
            self.registry[type_key] = []
        self.registry[type_key].append(model_version.to_dict())
        self._save_registry()
        
        print(f"✓ Registered {model_type.value} model v{version}")
        return model_version
    
    def get_active_model(self, model_type: ModelType) -> Optional[Tuple[Any, Any, ModelVersion]]:
        """
        Get the currently active model for a given type.
        
        Returns:
            Tuple of (model, scaler, ModelVersion) or None
        """
        type_key = model_type.value
        if type_key not in self.registry:
            return None
        
        # Find active model
        for version_dict in self.registry[type_key]:
            if version_dict.get('status') == ModelStatus.ACTIVE.value:
                return self._load_model_version(version_dict)
        
        return None
    
    def get_model_by_version(self, model_type: ModelType, version: str) -> Optional[Tuple[Any, Any, ModelVersion]]:
        """Get a specific model version"""
        type_key = model_type.value
        if type_key not in self.registry:
            return None
        
        for version_dict in self.registry[type_key]:
            if version_dict.get('version') == version:
                return self._load_model_version(version_dict)
        
        return None
    
    def _load_model_version(self, version_dict: Dict) -> Tuple[Any, Any, ModelVersion]:
        """Load model and scaler from disk"""
        model_file = version_dict['model_file']
        scaler_file = version_dict.get('scaler_file')
        
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        scaler = None
        if scaler_file and os.path.exists(scaler_file):
            with open(scaler_file, 'rb') as f:
                scaler = pickle.load(f)
        
        # Reconstruct ModelVersion
        metrics = ModelMetrics(**version_dict.get('metrics', {}))
        model_version = ModelVersion(
            version=version_dict['version'],
            model_type=ModelType(version_dict['model_type']),
            status=ModelStatus(version_dict['status']),
            created_at=version_dict['created_at'],
            updated_at=version_dict['updated_at'],
            created_by=version_dict['created_by'],
            description=version_dict['description'],
            algorithm=version_dict['algorithm'],
            hyperparameters=version_dict['hyperparameters'],
            features=version_dict['features'],
            metrics=metrics,
            model_file=version_dict['model_file'],
            scaler_file=version_dict.get('scaler_file'),
            model_checksum=version_dict.get('model_checksum'),
            traffic_percentage=version_dict.get('traffic_percentage', 0.0)
        )
        
        return model, scaler, model_version
    
    def promote_model(self, model_type: ModelType, version: str) -> bool:
        """
        Promote a model version to ACTIVE status.
        Demotes any currently active model to ARCHIVED.
        """
        type_key = model_type.value
        if type_key not in self.registry:
            return False
        
        found = False
        for version_dict in self.registry[type_key]:
            if version_dict.get('status') == ModelStatus.ACTIVE.value:
                version_dict['status'] = ModelStatus.ARCHIVED.value
                version_dict['traffic_percentage'] = 0.0
                version_dict['updated_at'] = datetime.utcnow().isoformat() + "Z"
            
            if version_dict.get('version') == version:
                version_dict['status'] = ModelStatus.ACTIVE.value
                version_dict['traffic_percentage'] = 100.0
                version_dict['updated_at'] = datetime.utcnow().isoformat() + "Z"
                found = True
        
        if found:
            self._save_registry()
            print(f"✓ Promoted {model_type.value} v{version} to ACTIVE")
        
        return found
    
    def rollback(self, model_type: ModelType, to_version: Optional[str] = None) -> bool:
        """
        Rollback to a previous model version.
        If to_version is None, rolls back to the most recent archived version.
        """
        type_key = model_type.value
        if type_key not in self.registry:
            return False
        
        if to_version is None:
            # Find most recent archived version
            archived = [v for v in self.registry[type_key] 
                       if v.get('status') == ModelStatus.ARCHIVED.value]
            if not archived:
                return False
            archived.sort(key=lambda v: v['created_at'], reverse=True)
            to_version = archived[0]['version']
        
        return self.promote_model(model_type, to_version)
    
    def list_versions(self, model_type: ModelType) -> List[Dict[str, Any]]:
        """List all versions for a model type"""
        type_key = model_type.value
        if type_key not in self.registry:
            return []
        
        versions = []
        for v in self.registry[type_key]:
            versions.append({
                'version': v['version'],
                'status': v['status'],
                'algorithm': v['algorithm'],
                'created_at': v['created_at'],
                'metrics': v.get('metrics', {}),
                'traffic_percentage': v.get('traffic_percentage', 0)
            })
        
        versions.sort(key=lambda v: v['created_at'], reverse=True)
        return versions
    
    def get_model_for_ab_test(self, model_type: ModelType) -> Tuple[Any, Any, ModelVersion]:
        """
        Get a model based on A/B test traffic allocation.
        Uses traffic_percentage to probabilistically select model.
        """
        type_key = model_type.value
        if type_key not in self.registry:
            raise ValueError(f"No models registered for {model_type.value}")
        
        # Get models with traffic allocation
        candidates = [v for v in self.registry[type_key] 
                     if v.get('traffic_percentage', 0) > 0]
        
        if not candidates:
            # Fallback to active model
            active = self.get_active_model(model_type)
            if active:
                return active
            raise ValueError(f"No active model for {model_type.value}")
        
        # Probabilistic selection
        rand = np.random.uniform(0, 100)
        cumulative = 0
        
        for v in candidates:
            cumulative += v.get('traffic_percentage', 0)
            if rand <= cumulative:
                return self._load_model_version(v)
        
        # Fallback to last candidate
        return self._load_model_version(candidates[-1])
    
    def set_ab_traffic(self, model_type: ModelType, allocations: Dict[str, float]) -> bool:
        """
        Set A/B test traffic allocations.
        
        Args:
            allocations: Dict mapping version to traffic percentage
                        e.g., {"1.0.0": 80, "1.1.0": 20}
        """
        type_key = model_type.value
        if type_key not in self.registry:
            return False
        
        total = sum(allocations.values())
        if abs(total - 100) > 0.01:
            raise ValueError(f"Traffic allocations must sum to 100, got {total}")
        
        for version_dict in self.registry[type_key]:
            version = version_dict['version']
            version_dict['traffic_percentage'] = allocations.get(version, 0)
            version_dict['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        self._save_registry()
        return True
    
    def delete_version(self, model_type: ModelType, version: str, force: bool = False) -> bool:
        """
        Delete a model version. Cannot delete ACTIVE models unless force=True.
        """
        type_key = model_type.value
        if type_key not in self.registry:
            return False
        
        for i, version_dict in enumerate(self.registry[type_key]):
            if version_dict.get('version') == version:
                if version_dict.get('status') == ModelStatus.ACTIVE.value and not force:
                    raise ValueError("Cannot delete active model. Use force=True or promote another version first.")
                
                # Delete files
                version_dir = os.path.dirname(version_dict['model_file'])
                if os.path.exists(version_dir):
                    shutil.rmtree(version_dir)
                
                # Remove from registry
                self.registry[type_key].pop(i)
                self._save_registry()
                
                print(f"✓ Deleted {model_type.value} v{version}")
                return True
        
        return False
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of all registered models"""
        summary = {}
        for model_type in ModelType:
            type_key = model_type.value
            versions = self.registry.get(type_key, [])
            
            active_version = None
            for v in versions:
                if v.get('status') == ModelStatus.ACTIVE.value:
                    active_version = v['version']
                    break
            
            summary[type_key] = {
                'total_versions': len(versions),
                'active_version': active_version,
                'versions': [v['version'] for v in versions]
            }
        
        return summary


# Global registry instance
_registry = None


def get_registry() -> ModelRegistry:
    """Always reload the model registry from disk for latest state"""
    base_path = os.getenv("MODEL_REGISTRY_PATH", "/app/models")
    return ModelRegistry(base_path)
