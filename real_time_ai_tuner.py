"""
RealTimeAITuner - Machine learning-based tuning optimization system.
Uses scikit-learn models to predict optimal fuel, ignition, and boost parameters
based on real-time telemetry data and driver behavior patterns.
"""

import asyncio
import time
import json
import pickle
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import logging
from pathlib import Path

from models import (
    TelemetryData, TuningParameter, TuningProfile, TuningMode,
    SecurityLevel, SecurityCredentials, VehicleState
)
from real_time_telemetry import RealTimeTelemetry
from secure_database import SecureDatabase


class AIModelType(Enum):
    """Machine learning model types."""
    FUEL_OPTIMIZER = "fuel_optimizer"
    IGNITION_OPTIMIZER = "ignition_optimizer"
    BOOST_OPTIMIZER = "boost_optimizer"
    PERFORMANCE_PREDICTOR = "performance_predictor"
    EFFICIENCY_PREDICTOR = "efficiency_predictor"


@dataclass
class TuningTarget:
    """Target optimization parameters."""
    target_power: float = 0.0  # Target horsepower
    target_torque: float = 0.0  # Target torque
    target_boost: float = 0.0  # Target boost pressure
    target_afr: float = 14.7  # Target air-fuel ratio
    efficiency_weight: float = 0.5  # Weight for efficiency vs power
    safety_margin: float = 0.1  # Safety margin for aggressive tuning
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "target_power": self.target_power,
            "target_torque": self.target_torque,
            "target_boost": self.target_boost,
            "target_afr": self.target_afr,
            "efficiency_weight": self.efficiency_weight,
            "safety_margin": self.safety_margin,
        }


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    mse: float = 0.0
    r2_score: float = 0.0
    cross_val_score: float = 0.0
    training_samples: int = 0
    last_trained: float = 0.0
    prediction_accuracy: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mse": self.mse,
            "r2_score": self.r2_score,
            "cross_val_score": self.cross_val_score,
            "training_samples": self.training_samples,
            "last_trained": self.last_trained,
            "prediction_accuracy": self.prediction_accuracy,
        }


class AITunerError(Exception):
    """AI tuner specific errors."""
    pass


class ModelNotTrainedError(AITunerError):
    """Model not trained error."""
    pass


class InsufficientDataError(AITunerError):
    """Insufficient training data error."""
    pass


class RealTimeAITuner:
    """
    Real-time AI tuning system using machine learning.
    Learns from telemetry data to optimize tuning parameters.
    """
    
    # Feature columns for model training
    FEATURE_COLUMNS = [
        "rpm", "vehicle_speed", "throttle_position", "pedal_position",
        "boost_pressure", "map", "maf", "ect", "iat", "oil_pressure",
        "fuel_pressure", "stft", "ltft", "afr", "timing_advance",
        "load", "knock_retard", "gear"
    ]
    
    # Target columns for optimization
    TARGET_COLUMNS = [
        "fuel_base", "fuel_trim", "timing_advance", "boost_target",
        "wastegate_duty", "vvt_advance", "throttle_response"
    ]
    
    def __init__(self, model_dir: str = "ai_models"):
        """
        Initialize AI tuner.
        
        Args:
            model_dir: Directory to store trained models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.mode = TuningMode.INACTIVE
        self.current_credentials: Optional[SecurityCredentials] = None
        
        # Data interfaces
        self.telemetry: Optional[RealTimeTelemetry] = None
        self.database: Optional[SecureDatabase] = None
        
        # Machine learning models
        self.models: Dict[AIModelType, Any] = {}
        self.scalers: Dict[AIModelType, Any] = {}
        self.model_metrics: Dict[AIModelType, ModelMetrics] = {}
        
        # Training data
        self.training_data: List[Dict[str, Any]] = []
        self.feature_buffer: List[Dict[str, float]] = []
        self.target_buffer: List[Dict[str, float]] = []
        
        # Configuration
        self.min_training_samples = 1000
        self.max_training_samples = 10000
        self.validation_split = 0.2
        self.model_retrain_interval = 3600.0  # 1 hour
        
        # Optimization parameters
        self.tuning_target = TuningTarget()
        self.optimization_constraints = {
            "max_boost": 25.0,  # psi
            "max_timing": 40.0,  # degrees
            "min_afr": 11.5,  # Rich limit
            "max_afr": 16.5,  # Lean limit
            "max_knock": 5.0,  # degrees
        }
        
        # Performance tracking
        self.last_prediction_time = 0.0
        self.prediction_count = 0
        self.optimization_count = 0
        
        self.logger.info("RealTimeAITuner initialized")
    
    def set_telemetry(self, telemetry: RealTimeTelemetry) -> None:
        """Set telemetry interface."""
        self.telemetry = telemetry
        self.logger.info("Telemetry interface set")
    
    def set_database(self, database: SecureDatabase) -> None:
        """Set database interface."""
        self.database = database
        self.logger.info("Database interface set")
    
    def set_credentials(self, credentials: SecurityCredentials) -> None:
        """Set security credentials."""
        self.current_credentials = credentials
        self.logger.info(f"Credentials set for user: {credentials.username}")
    
    def _initialize_models(self) -> None:
        """Initialize machine learning models."""
        try:
            # Initialize models for different optimization targets
            model_configs = {
                AIModelType.FUEL_OPTIMIZER: GradientBoostingRegressor(
                    n_estimators=100, learning_rate=0.1, max_depth=6
                ),
                AIModelType.IGNITION_OPTIMIZER: RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42
                ),
                AIModelType.BOOST_OPTIMIZER: GradientBoostingRegressor(
                    n_estimators=100, learning_rate=0.1, max_depth=6
                ),
                AIModelType.PERFORMANCE_PREDICTOR: RandomForestRegressor(
                    n_estimators=150, max_depth=12, random_state=42
                ),
                AIModelType.EFFICIENCY_PREDICTOR: GradientBoostingRegressor(
                    n_estimators=100, learning_rate=0.05, max_depth=8
                ),
            }
            
            for model_type, model in model_configs.items():
                self.models[model_type] = model
                self.scalers[model_type] = StandardScaler()
                self.model_metrics[model_type] = ModelMetrics()
            
            self.logger.info("AI models initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize models: {e}")
            raise AITunerError(f"Model initialization failed: {e}")
    
    async def start_learning(self) -> bool:
        """Start AI learning mode."""
        if self.mode != TuningMode.INACTIVE:
            self.logger.warning(f"Cannot start learning, current mode: {self.mode.value}")
            return False
        
        try:
            self.mode = TuningMode.LEARNING
            self._initialize_models()
            
            # Load existing training data
            await self._load_training_data()
            
            self.logger.info("AI learning mode started")
            return True
            
        except Exception as e:
            self.mode = TuningMode.INACTIVE
            self.logger.error(f"Failed to start learning: {e}")
            return False
    
    async def stop_learning(self) -> bool:
        """Stop AI learning mode."""
        if self.mode == TuningMode.INACTIVE:
            return True
        
        try:
            # Save current models
            await self._save_models()
            
            self.mode = TuningMode.INACTIVE
            self.logger.info("AI learning mode stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping learning: {e}")
            return False
    
    async def add_telemetry_sample(self, telemetry: TelemetryData,
                                  tuning_parameters: Dict[str, float]) -> None:
        """
        Add telemetry sample with corresponding tuning parameters.
        
        Args:
            telemetry: Telemetry data
            tuning_parameters: Applied tuning parameters
        """
        if self.mode != TuningMode.LEARNING:
            return
        
        try:
            # Extract features from telemetry
            features = self._extract_features(telemetry)
            
            # Combine with tuning parameters
            sample = {
                "timestamp": telemetry.timestamp,
                "features": features,
                "targets": tuning_parameters,
            }
            
            self.training_data.append(sample)
            
            # Limit training data size
            if len(self.training_data) > self.max_training_samples:
                self.training_data = self.training_data[-self.max_training_samples:]
            
            # Check if we should retrain models
            if len(self.training_data) >= self.min_training_samples:
                if (time.time() - self.model_metrics[ModelType.FUEL_OPTIMIZER].last_trained 
                    >= self.model_retrain_interval):
                    await self._retrain_models()
            
        except Exception as e:
            self.logger.error(f"Failed to add telemetry sample: {e}")
    
    def _extract_features(self, telemetry: TelemetryData) -> Dict[str, float]:
        """Extract features from telemetry data."""
        features = {}
        
        for column in self.FEATURE_COLUMNS:
            value = getattr(telemetry, column, 0.0)
            features[column] = float(value) if value is not None else 0.0
        
        # Add calculated features
        features["rpm_squared"] = features.get("rpm", 0) ** 2
        features["load_rpm_ratio"] = (
            features.get("load", 0) / max(features.get("rpm", 1), 1)
        )
        features["boost_load_ratio"] = (
            features.get("boost_pressure", 0) / max(features.get("load", 1), 1)
        )
        
        return features
    
    async def _load_training_data(self) -> None:
        """Load training data from database."""
        if not self.database:
            return
        
        try:
            # Load recent telemetry data
            telemetry_data = await self.database.get_telemetry_data(
                session_id=None,  # Load all sessions
                limit=self.max_training_samples
            )
            
            # Convert to training samples
            for telemetry in telemetry_data:
                features = self._extract_features(telemetry)
                
                # Create synthetic targets (in real implementation, 
                # these would come from actual tuning changes)
                targets = self._generate_synthetic_targets(features)
                
                sample = {
                    "timestamp": telemetry.timestamp,
                    "features": features,
                    "targets": targets,
                }
                
                self.training_data.append(sample)
            
            self.logger.info(f"Loaded {len(self.training_data)} training samples")
            
        except Exception as e:
            self.logger.error(f"Failed to load training data: {e}")
    
    def _generate_synthetic_targets(self, features: Dict[str, float]) -> Dict[str, float]:
        """Generate synthetic tuning targets for training."""
        rpm = features.get("rpm", 2000)
        load = features.get("load", 50)
        boost = features.get("boost_pressure", 0)
        
        # Simple rule-based targets for demonstration
        targets = {
            "fuel_base": 8.0 + (load / 100) * 12.0 + (boost / 10) * 2.0,
            "fuel_trim": 0.0 + (boost / 20) * 5.0,
            "timing_advance": 20.0 - (load / 100) * 10.0 - (boost / 5) * 3.0,
            "boost_target": min(boost + 2.0, self.optimization_constraints["max_boost"]),
            "wastegate_duty": 50.0 + (boost / 10) * 30.0,
            "vvt_advance": 10.0 + (rpm / 1000) * 2.0,
            "throttle_response": 80.0 + (load / 100) * 20.0,
        }
        
        return targets
    
    async def _retrain_models(self) -> None:
        """Retrain all machine learning models."""
        if len(self.training_data) < self.min_training_samples:
            raise InsufficientDataError(
                f"Need at least {self.min_training_samples} samples, "
                f"have {len(self.training_data)}"
            )
        
        try:
            # Prepare training data
            X, y_dict = self._prepare_training_data()
            
            # Train each model
            for model_type in AIModelType:
                if model_type in self.models:
                    await self._train_single_model(model_type, X, y_dict)
            
            self.logger.info("All models retrained successfully")
            
        except Exception as e:
            self.logger.error(f"Model retraining failed: {e}")
            raise AITunerError(f"Model retraining failed: {e}")
    
    def _prepare_training_data(self) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Prepare training data arrays."""
        # Extract features and targets
        features_list = []
        targets_dict = {target: [] for target in self.TARGET_COLUMNS}
        
        for sample in self.training_data:
            features_list.append(list(sample["features"].values()))
            
            for target in self.TARGET_COLUMNS:
                targets_dict[target].append(sample["targets"].get(target, 0.0))
        
        X = np.array(features_list)
        y_dict = {target: np.array(values) for target, values in targets_dict.items()}
        
        return X, y_dict
    
    async def _train_single_model(self, model_type: AIModelType, 
                                 X: np.ndarray, y_dict: Dict[str, np.ndarray]) -> None:
        """Train a single machine learning model."""
        try:
            # Select appropriate target
            target_mapping = {
                AIModelType.FUEL_OPTIMIZER: "fuel_base",
                AIModelType.IGNITION_OPTIMIZER: "timing_advance",
                AIModelType.BOOST_OPTIMIZER: "boost_target",
                AIModelType.PERFORMANCE_PREDICTOR: "fuel_base",  # Simplified
                AIModelType.EFFICIENCY_PREDICTOR: "fuel_trim",
            }
            
            target_name = target_mapping.get(model_type, "fuel_base")
            y = y_dict[target_name]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.validation_split, random_state=42
            )
            
            # Scale features
            scaler = self.scalers[model_type]
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = self.models[model_type]
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            cv_score = cross_val_score(model, X_train_scaled, y_train, cv=5).mean()
            
            # Update metrics
            metrics = self.model_metrics[model_type]
            metrics.mse = mse
            metrics.r2_score = r2
            metrics.cross_val_score = cv_score
            metrics.training_samples = len(X_train)
            metrics.last_trained = time.time()
            metrics.prediction_accuracy = max(0, (1 - mse) * 100)
            
            self.logger.info(
                f"Model {model_type.value} trained: R2={r2:.3f}, "
                f"CV={cv_score:.3f}, Samples={len(X_train)}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to train model {model_type.value}: {e}")
            raise
    
    async def predict_optimal_parameters(self, 
                                       current_telemetry: TelemetryData,
                                       target: Optional[TuningTarget] = None) -> Dict[str, float]:
        """
        Predict optimal tuning parameters for current conditions.
        
        Args:
            current_telemetry: Current telemetry data
            target: Optional tuning target
            
        Returns:
            Dictionary of optimal parameters
        """
        if self.mode == TuningMode.INACTIVE:
            raise ModelNotTrainedError("AI tuner not active")
        
        # Check if models are trained
        if not any(metrics.last_trained > 0 for metrics in self.model_metrics.values()):
            raise ModelNotTrainedError("No trained models available")
        
        try:
            # Use provided target or default
            tuning_target = target or self.tuning_target
            
            # Extract features
            features = self._extract_features(current_telemetry)
            X = np.array([list(features.values())])
            
            # Predict parameters
            predictions = {}
            
            # Fuel optimization
            if self.model_metrics[AIModelType.FUEL_OPTIMIZER].last_trained > 0:
                scaler = self.scalers[AIModelType.FUEL_OPTIMIZER]
                model = self.models[AIModelType.FUEL_OPTIMIZER]
                
                X_scaled = scaler.transform(X)
                fuel_pred = model.predict(X_scaled)[0]
                predictions["fuel_base"] = self._apply_constraints(
                    fuel_pred, "fuel_base", features
                )
            
            # Ignition optimization
            if self.model_metrics[AIModelType.IGNITION_OPTIMIZER].last_trained > 0:
                scaler = self.scalers[AIModelType.IGNITION_OPTIMIZER]
                model = self.models[AIModelType.IGNITION_OPTIMIZER]
                
                X_scaled = scaler.transform(X)
                timing_pred = model.predict(X_scaled)[0]
                predictions["timing_advance"] = self._apply_constraints(
                    timing_pred, "timing_advance", features
                )
            
            # Boost optimization
            if self.model_metrics[AIModelType.BOOST_OPTIMIZER].last_trained > 0:
                scaler = self.scalers[AIModelType.BOOST_OPTIMIZER]
                model = self.models[AIModelType.BOOST_OPTIMIZER]
                
                X_scaled = scaler.transform(X)
                boost_pred = model.predict(X_scaled)[0]
                predictions["boost_target"] = self._apply_constraints(
                    boost_pred, "boost_target", features
                )
            
            # Apply safety margins
            predictions = self._apply_safety_margins(predictions, tuning_target)
            
            self.last_prediction_time = time.time()
            self.prediction_count += 1
            self.optimization_count += 1
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Failed to predict optimal parameters: {e}")
            raise AITunerError(f"Prediction failed: {e}")
    
    def _apply_constraints(self, value: float, parameter: str, 
                          features: Dict[str, float]) -> float:
        """Apply safety constraints to parameter values."""
        rpm = features.get("rpm", 2000)
        load = features.get("load", 50)
        
        if parameter == "fuel_base":
            # Fuel constraints based on RPM and load
            min_fuel = 5.0 + (load / 100) * 5.0
            max_fuel = 25.0 + (load / 100) * 10.0
            return max(min_fuel, min(max_fuel, value))
        
        elif parameter == "timing_advance":
            # Timing constraints based on RPM and boost
            boost = features.get("boost_pressure", 0)
            max_timing = 40.0 - (boost * 2.0) - (load / 100) * 10.0
            min_timing = 5.0
            return max(min_timing, min(max_timing, value))
        
        elif parameter == "boost_target":
            # Boost constraints
            max_boost = self.optimization_constraints["max_boost"]
            min_boost = 0.0
            return max(min_boost, min(max_boost, value))
        
        return value
    
    def _apply_safety_margins(self, predictions: Dict[str, float],
                            target: TuningTarget) -> Dict[str, float]:
        """Apply safety margins to predictions."""
        safe_predictions = predictions.copy()
        
        # Apply safety margin to aggressive parameters
        for param, value in safe_predictions.items():
            if param in ["boost_target", "timing_advance"]:
                safe_predictions[param] = value * (1.0 - target.safety_margin)
        
        return safe_predictions
    
    async def optimize_for_target(self, target: TuningTarget) -> Dict[str, Any]:
        """
        Optimize parameters for specific target.
        
        Args:
            target: Tuning target specification
            
        Returns:
            Optimization results
        """
        if not self.telemetry:
            raise AITunerError("Telemetry interface not set")
        
        try:
            # Get current telemetry
            current_telemetry = self.telemetry.get_latest_telemetry()
            
            # Predict optimal parameters
            optimal_params = await self.predict_optimal_parameters(
                current_telemetry, target
            )
            
            # Estimate performance
            estimated_performance = await self._estimate_performance(
                current_telemetry, optimal_params
            )
            
            results = {
                "optimal_parameters": optimal_params,
                "estimated_performance": estimated_performance,
                "target": target.to_dict(),
                "timestamp": time.time(),
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Target optimization failed: {e}")
            raise AITunerError(f"Target optimization failed: {e}")
    
    async def _estimate_performance(self, telemetry: TelemetryData,
                                   parameters: Dict[str, float]) -> Dict[str, float]:
        """Estimate performance with given parameters."""
        try:
            # Use performance predictor model if available
            if self.model_metrics[AIModelType.PERFORMANCE_PREDICTOR].last_trained > 0:
                features = self._extract_features(telemetry)
                # Add parameters to features
                for param, value in parameters.items():
                    features[f"target_{param}"] = value
                
                X = np.array([list(features.values())])
                scaler = self.scalers[AIModelType.PERFORMANCE_PREDICTOR]
                model = self.models[AIModelType.PERFORMANCE_PREDICTOR]
                
                X_scaled = scaler.transform(X)
                performance = model.predict(X_scaled)[0]
                
                return {
                    "estimated_power": max(0, performance),
                    "estimated_torque": max(0, performance * 1.3),
                    "estimated_efficiency": max(0, 100 - performance * 0.1),
                }
            
            # Fallback estimation
            return {
                "estimated_power": 250.0,  # Default estimate
                "estimated_torque": 325.0,
                "estimated_efficiency": 85.0,
            }
            
        except Exception as e:
            self.logger.error(f"Performance estimation failed: {e}")
            return {
                "estimated_power": 0.0,
                "estimated_torque": 0.0,
                "estimated_efficiency": 0.0,
            }
    
    async def _save_models(self) -> None:
        """Save trained models to disk."""
        try:
            for model_type, model in self.models.items():
                model_path = self.model_dir / f"{model_type.value}_model.pkl"
                scaler_path = self.model_dir / f"{model_type.value}_scaler.pkl"
                metrics_path = self.model_dir / f"{model_type.value}_metrics.json"
                
                # Save model
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                
                # Save scaler
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scalers[model_type], f)
                
                # Save metrics
                with open(metrics_path, 'w') as f:
                    json.dump(self.model_metrics[model_type].to_dict(), f, indent=2)
            
            self.logger.info("Models saved to disk")
            
        except Exception as e:
            self.logger.error(f"Failed to save models: {e}")
    
    async def load_models(self) -> bool:
        """Load trained models from disk."""
        try:
            models_loaded = 0
            
            for model_type in AIModelType:
                model_path = self.model_dir / f"{model_type.value}_model.pkl"
                scaler_path = self.model_dir / f"{model_type.value}_scaler.pkl"
                metrics_path = self.model_dir / f"{model_type.value}_metrics.json"
                
                if model_path.exists() and scaler_path.exists():
                    # Load model
                    with open(model_path, 'rb') as f:
                        self.models[model_type] = pickle.load(f)
                    
                    # Load scaler
                    with open(scaler_path, 'rb') as f:
                        self.scalers[model_type] = pickle.load(f)
                    
                    # Load metrics
                    if metrics_path.exists():
                        with open(metrics_path, 'r') as f:
                            metrics_dict = json.load(f)
                            self.model_metrics[model_type] = ModelMetrics(**metrics_dict)
                    
                    models_loaded += 1
            
            self.logger.info(f"Loaded {models_loaded} models from disk")
            return models_loaded > 0
            
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about trained models."""
        info = {}
        
        for model_type, metrics in self.model_metrics.items():
            info[model_type.value] = {
                "trained": metrics.last_trained > 0,
                "metrics": metrics.to_dict(),
            }
        
        return {
            "models": info,
            "mode": self.mode.value,
            "training_samples": len(self.training_data),
            "predictions_made": self.prediction_count,
            "optimizations_performed": self.optimization_count,
        }
    
    def set_tuning_target(self, target: TuningTarget) -> None:
        """Set tuning optimization target."""
        self.tuning_target = target
        self.logger.info(f"Tuning target updated: {target.to_dict()}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get AI tuner statistics."""
        return {
            "mode": self.mode.value,
            "training_samples": len(self.training_data),
            "predictions_made": self.prediction_count,
            "optimizations_performed": self.optimization_count,
            "last_prediction": self.last_prediction_time,
            "model_count": len([m for m in self.model_metrics.values() if m.last_trained > 0]),
        }
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            # Save models if trained
            if any(metrics.last_trained > 0 for metrics in self.model_metrics.values()):
                asyncio.create_task(self._save_models())
        except Exception:
            pass
