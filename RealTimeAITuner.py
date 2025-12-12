"""
RealTimeAITuner - Neural network-based real-time tuning system.

This module provides a PyTorch-based neural network for real-time parameter tuning
with safety constraints and feature extraction.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass, field
import logging
from enum import Enum
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NormalizationMethod(Enum):
    """Supported normalization methods."""
    MINMAX = "minmax"
    STANDARD = "standard"
    ROBUST = "robust"

@dataclass
class FeatureConfig:
    """Configuration for input feature extraction."""
    name: str
    min_val: float
    max_val: float
    mean: Optional[float] = None
    std: Optional[float] = None
    clip: bool = True
    normalization: NormalizationMethod = NormalizationMethod.MINMAX

@dataclass
class OutputConfig:
    """Configuration for output parameters."""
    name: str
    min_val: float
    max_val: float
    default: float
    learning_rate: float = 0.01
    momentum: float = 0.9

class FeatureExtractor:
    """Handles feature extraction and normalization."""
    
    def __init__(self, configs: Dict[str, FeatureConfig]):
        """
        Initialize feature extractor with configuration.
        
        Args:
            configs: Dictionary of feature configurations
        """
        self.configs = configs
        self._validate_configs()
    
    def _validate_configs(self) -> None:
        """Validate feature configurations."""
        for name, config in self.configs.items():
            if config.normalization == NormalizationMethod.STANDARD and \
               (config.mean is None or config.std is None):
                raise ValueError(f"Standard normalization requires mean and std for feature {name}")
    
    def extract_features(self, raw_data: Dict[str, float]) -> Dict[str, float]:
        """
        Extract and normalize features from raw data.
        
        Args:
            raw_data: Dictionary of raw sensor/input data
            
        Returns:
            Dictionary of normalized features
        """
        features = {}
        
        for name, config in self.configs.items():
            if name not in raw_data:
                raise ValueError(f"Missing input feature: {name}")
            
            value = raw_data[name]
            
            # Apply clipping if enabled
            if config.clip:
                value = max(config.min_val, min(config.max_val, value))
            
            # Apply normalization
            if config.normalization == NormalizationMethod.MINMAX:
                # Min-max normalization to [0, 1]
                if config.max_val > config.min_val:  # Avoid division by zero
                    value = (value - config.min_val) / (config.max_val - config.min_val)
                else:
                    value = 0.0
            
            elif config.normalization == NormalizationMethod.STANDARD:
                # Standard score normalization (z-score)
                if config.std and config.std > 0:  # Avoid division by zero
                    value = (value - config.mean) / config.std
                else:
                    value = 0.0
            
            elif config.normalization == NormalizationMethod.ROBUST:
                # Robust scaling using IQR (placeholder implementation)
                # In practice, you'd want to calculate robust statistics
                value = value  # Placeholder - implement robust scaling
            
            features[name] = value
        
        return features

class SafetyController:
    """Handles safety constraints and output clamping."""
    
    def __init__(self, configs: Dict[str, OutputConfig]):
        """
        Initialize safety controller with output configurations.
        
        Args:
            configs: Dictionary of output configurations
        """
        self.configs = configs
    
    def clamp_outputs(self, outputs: Dict[str, float]) -> Dict[str, float]:
        """
        Clamp output values to safe ranges.
        
        Args:
            outputs: Dictionary of output values
            
        Returns:
            Dictionary of clamped output values
        """
        clamped = {}
        
        for name, value in outputs.items():
            if name not in self.configs:
                logger.warning(f"No safety config for output: {name}")
                clamped[name] = value
                continue
                
            config = self.configs[name]
            clamped_value = max(config.min_val, min(config.max_val, value))
            
            # Log if clamping occurred
            if clamped_value != value:
                logger.warning(f"Clamped {name}: {value:.4f} -> {clamped_value:.4f}")
            
            clamped[name] = clamped_value
        
        return clamped
    
    def get_default_outputs(self) -> Dict[str, float]:
        """Get default (safe) output values."""
        return {name: config.default for name, config in self.configs.items()}

class RealTimeTuner(nn.Module):
    """Neural network-based real-time tuner."""
    
    def __init__(
        self,
        input_size: int,
        output_size: int,
        hidden_layers: List[int] = None,
        activation: str = "leaky_relu",
        dropout: float = 0.1
    ):
        """
        Initialize the neural network.
        
        Args:
            input_size: Number of input features
            output_size: Number of output parameters
            hidden_layers: List of hidden layer sizes
            activation: Activation function name
            dropout: Dropout probability
        ""
        super().__init__()
        
        # Set default hidden layers if not provided
        if hidden_layers is None:
            hidden_layers = [64, 64]
        
        # Create activation function
        activation_fn = self._get_activation(activation)
        
        # Build network layers
        layers = []
        prev_size = input_size
        
        # Add hidden layers
        for size in hidden_layers:
            layers.append(nn.Linear(prev_size, size))
            layers.append(activation_fn())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev_size = size
        
        # Add output layer
        layers.append(nn.Linear(prev_size, output_size))
        
        # Create sequential model
        self.network = nn.Sequential(*layers)
        
        # Initialize weights
        self._init_weights()
        
        # Set device (GPU if available)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.to(self.device)
        
        # Training state
        self.optimizer = None
        self.scheduler = None
        self.loss_fn = None
        self.feature_order = None  # Will be set during training
    
    def _init_weights(self) -> None:
        """Initialize network weights."""
        for module in self.network.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0.1)
    
    @staticmethod
    def _get_activation(name: str) -> nn.Module:
        """Get activation function by name."""
        activations = {
            "relu": nn.ReLU,
            "leaky_relu": nn.LeakyReLU,
            "tanh": nn.Tanh,
            "sigmoid": nn.Sigmoid,
            "selu": nn.SELU,
        }
        return activations.get(name.lower(), nn.LeakyReLU)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.network(x)
    
    def setup_optimizer(
        self,
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5,
        optimizer_class: str = "Adam"
    ) -> None:
        """
        Set up the optimizer and loss function.
        
        Args:
            learning_rate: Learning rate
            weight_decay: L2 regularization
            optimizer_class: Name of optimizer class (Adam, SGD, etc.)
        ""
        optimizers = {
            "adam": optim.Adam,
            "sgd": optim.SGD,
            "rmsprop": optim.RMSprop,
            "adagrad": optim.Adagrad,
        }
        
        optimizer_class = optimizers.get(optimizer_class.lower(), optim.Adam)
        
        self.optimizer = optimizer_class(
            self.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Use learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=10,
            verbose=True
        )
        
        # Mean squared error loss
        self.loss_fn = nn.MSELoss()
    
    def optimise_step(
        self,
        input_features: Dict[str, float],
        target_outputs: Dict[str, float],
        feature_order: List[str],
        output_order: List[str]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Perform a single optimization step.
        
        Args:
            input_features: Dictionary of input features
            target_outputs: Dictionary of target outputs
            feature_order: List of feature names in the correct order
            output_order: List of output names in the correct order
            
        Returns:
            Tuple of (loss, output_dict) where output_dict contains the predicted outputs
        """
        if self.optimizer is None or self.loss_fn is None:
            raise RuntimeError("Optimizer and loss function must be set up first")
        
        # Set network to training mode
        self.train()
        
        # Convert inputs to tensors in the correct order
        x = torch.tensor([input_features[name] for name in feature_order], 
                        dtype=torch.float32, device=self.device).unsqueeze(0)
        
        y_true = torch.tensor([target_outputs[name] for name in output_order],
                            dtype=torch.float32, device=self.device).unsqueeze(0)
        
        # Zero gradients
        self.optimizer.zero_grad()
        
        # Forward pass
        y_pred = self(x)
        
        # Calculate loss
        loss = self.loss_fn(y_pred, y_true)
        
        # Backward pass and optimize
        loss.backward()
        self.optimizer.step()
        
        # Update learning rate
        if self.scheduler:
            self.scheduler.step(loss)
        
        # Convert predictions to dictionary
        output_dict = {
            name: y_pred[0, i].item() 
            for i, name in enumerate(output_order)
        }
        
        return loss.item(), output_dict
    
    def predict(
        self, 
        input_features: Dict[str, float], 
        feature_order: List[str]
    ) -> Dict[str, float]:
        """
        Make a prediction without training.
        
        Args:
            input_features: Dictionary of input features
            feature_order: List of feature names in the correct order
            
        Returns:
            Dictionary of predicted outputs
        """
        self.eval()
        
        with torch.no_grad():
            x = torch.tensor([input_features[name] for name in feature_order],
                           dtype=torch.float32, device=self.device).unsqueeze(0)
            
            y_pred = self(x)
            
            # Convert to dictionary (output order is fixed during training)
            output_order = [f"output_{i}" for i in range(y_pred.shape[1])]
            return {
                name: y_pred[0, i].item() 
                for i, name in enumerate(output_order)
            }

class RealTimeAITuner:
    """High-level interface for the real-time AI tuner."
    
    def __init__(
        self,
        feature_configs: Dict[str, FeatureConfig],
        output_configs: Dict[str, OutputConfig],
        model_path: Optional[str] = None
    ):
        """
        Initialize the AI tuner.
        
        Args:
            feature_configs: Dictionary of feature configurations
            output_configs: Dictionary of output configurations
            model_path: Path to load/save the model (optional)
        """
        self.feature_extractor = FeatureExtractor(feature_configs)
        self.safety_controller = SafetyController(output_configs)
        self.model_path = model_path
        
        # Initialize model
        self.model = RealTimeTuner(
            input_size=len(feature_configs),
            output_size=len(output_configs)
        )
        
        # Set up optimizer with default parameters
        self.model.setup_optimizer()
        
        # Feature and output order (alphabetical by default)
        self.feature_order = sorted(feature_configs.keys())
        self.output_order = sorted(output_configs.keys())
        
        # Load model if path is provided
        if model_path:
            self.load_model(model_path)
    
    def process(
        self, 
        raw_inputs: Dict[str, float], 
        target_outputs: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Process inputs and return optimized outputs.
        
        Args:
            raw_inputs: Raw input features
            target_outputs: Target outputs (for training, optional)
            
        Returns:
            Dictionary of optimized output parameters
        """
        try:
            # Extract and normalize features
            features = self.feature_extractor.extract_features(raw_inputs)
            
            if target_outputs is not None:
                # Training mode
                loss, outputs = self.model.optimise_step(
                    features,
                    target_outputs,
                    self.feature_order,
                    self.output_order
                )
                logger.debug(f"Training loss: {loss:.6f}")
            else:
                # Prediction mode
                outputs = self.model.predict(features, self.feature_order)
            
            # Apply safety constraints
            safe_outputs = self.safety_controller.clamp_outputs(outputs)
            
            return safe_outputs
            
        except Exception as e:
            logger.error(f"Error in process: {e}")
            # Return default safe values on error
            return self.safety_controller.get_default_outputs()
    
    def save_model(self, path: Optional[str] = None) -> None:
        """Save the model to disk."""
        save_path = path or self.model_path
        if not save_path:
            raise ValueError("No path provided for saving the model")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.model.optimizer.state_dict() if self.model.optimizer else None,
            'feature_order': self.feature_order,
            'output_order': self.output_order,
        }, save_path)
        
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, path: str) -> None:
        """Load a model from disk."""
        try:
            checkpoint = torch.load(path, map_location=self.model.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            
            if self.model.optimizer and 'optimizer_state_dict' in checkpoint:
                self.model.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            
            if 'feature_order' in checkpoint:
                self.feature_order = checkpoint['feature_order']
            if 'output_order' in checkpoint:
                self.output_order = checkpoint['output_order']
            
            logger.info(f"Model loaded from {path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

# Example usage
def example_usage():
    """Example of how to use the RealTimeAITuner."""
    # Define feature configurations
    feature_configs = {
        'rpm': FeatureConfig(
            name='rpm',
            min_val=0,
            max_val=8000,
            mean=3000,
            std=1500,
            normalization=NormalizationMethod.STANDARD
        ),
        'throttle': FeatureConfig(
            name='throttle',
            min_val=0,
            max_val=100,
            normalization=NormalizationMethod.MINMAX
        ),
        'load': FeatureConfig(
            name='load',
            min_val=0,
            max_val=100,
            normalization=NormalizationMethod.MINMAX
        ),
    }
    
    # Define output configurations
    output_configs = {
        'ignition_advance': OutputConfig(
            name='ignition_advance',
            min_val=0,
            max_val=50,
            default=10.0,
            learning_rate=0.01
        ),
        'fuel_pulse_width': OutputConfig(
            name='fuel_pulse_width',
            min_val=1.0,
            max_val=20.0,
            default=5.0,
            learning_rate=0.005
        ),
    }
    
    # Create the tuner
    tuner = RealTimeAITuner(
        feature_configs=feature_configs,
        output_configs=output_configs,
        model_path="real_time_tuner.pt"
    )
    
    # Example input data
    inputs = {
        'rpm': 4500.0,
        'throttle': 75.0,
        'load': 80.0
    }
    
    # Get optimized outputs (inference)
    outputs = tuner.process(inputs)
    print("Optimized outputs:", outputs)
    
    # Example training step (with target outputs)
    target_outputs = {
        'ignition_advance': 25.0,
        'fuel_pulse_width': 12.5
    }
    
    # Perform a training step
    tuner.process(inputs, target_outputs)
    
    # Save the trained model
    tuner.save_model()

if __name__ == "__main__":
    example_usage()
