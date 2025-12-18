#!/usr/bin/env python3
"""
AI TUNING SYSTEM CONFIGURATION
Complete configuration for machine learning and reinforcement learning systems
"""

# Neural Network Architecture
NEURAL_NETWORK_CONFIG = {
    'actor_network': {
        'input_size': 15,
        'hidden_layers': [256, 128, 64],
        'output_size': 8,
        'activation': 'relu',
        'output_activation': 'tanh',
        'dropout_rate': 0.1,
        'batch_norm': True
    },
    'critic_network': {
        'state_input_size': 15,
        'action_input_size': 8,
        'hidden_layers': [256, 128],
        'output_size': 1,
        'activation': 'relu',
        'dropout_rate': 0.1
    },
    'training': {
        'learning_rate_actor': 0.001,
        'learning_rate_critic': 0.002,
        'weight_decay': 0.0001,
        'gradient_clip': 1.0,
        'target_update_tau': 0.005
    }
}

# Reinforcement Learning Parameters
REINFORCEMENT_LEARNING_CONFIG = {
    'replay_buffer': {
        'capacity': 10000,
        'batch_size': 64,
        'priority_exponent': 0.6,
        'importance_sampling_exponent': 0.4
    },
    'exploration': {
        'noise_type': 'ornstein_uhlenbeck',
        'noise_theta': 0.15,
        'noise_sigma': 0.2,
        'noise_decay': 0.9995,
        'min_noise': 0.01
    },
    'learning': {
        'discount_factor': 0.99,
        'soft_update_factor': 0.005,
        'learning_starts': 1000,
        'train_frequency': 4
    }
}

# Reward Function Configuration
REWARD_CONFIG = {
    'performance_rewards': {
        'horsepower_weight': 0.3,
        'torque_weight': 0.2,
        'throttle_response_weight': 0.15,
        'boost_response_weight': 0.15
    },
    'safety_penalties': {
        'knock_penalty': -2.0,
        'overboost_penalty': -5.0,
        'overtemp_penalty': -3.0,
        'afr_out_of_range_penalty': -2.0
    },
    'efficiency_rewards': {
        'fuel_efficiency_weight': 0.1,
        'smooth_operation_weight': 0.05,
        'stable_boost_weight': 0.05
    }
}

# Feature Engineering Configuration
FEATURE_ENGINEERING_CONFIG = {
    'input_features': [
        'engine_rpm',
        'engine_load', 
        'boost_psi',
        'ignition_timing',
        'afr',
        'knock_retard',
        'intake_temp',
        'coolant_temp',
        'throttle_position',
        'manifold_pressure',
        'vvt_intake_angle',
        'vvt_exhaust_angle',
        'fuel_trim_long',
        'fuel_trim_short',
        'vehicle_speed'
    ],
    'normalization': {
        'method': 'min_max',  # 'min_max', 'standard', 'robust'
        'feature_ranges': {
            'engine_rpm': (0, 7000),
            'engine_load': (0, 1.6),
            'boost_psi': (0, 22),
            'ignition_timing': (0, 25),
            'afr': (10, 16),
            'knock_retard': (-8, 0),
            'intake_temp': (0, 60),
            'coolant_temp': (0, 110),
            'throttle_position': (0, 100),
            'manifold_pressure': (0, 250),
            'vvt_intake_angle': (0, 50),
            'vvt_exhaust_angle': (0, 50),
            'fuel_trim_long': (-25, 25),
            'fuel_trim_short': (-25, 25),
            'vehicle_speed': (0, 200)
        }
    },
    'feature_engineering': {
        'create_interactions': True,
        'polynomial_features': False,
        'rolling_statistics': True,
        'statistics_window': 10
    }
}

# Action Space Configuration
ACTION_SPACE_CONFIG = {
    'continuous_actions': {
        'ignition_timing': {'min': -5.0, 'max': 5.0, 'scale': 0.1},
        'boost_target': {'min': -2.0, 'max': 2.0, 'scale': 0.1},
        'target_afr': {'min': -0.5, 'max': 0.5, 'scale': 0.05},
        'wgdc_adjustment': {'min': -10.0, 'max': 10.0, 'scale': 0.5},
        'vvt_intake': {'min': -5.0, 'max': 5.0, 'scale': 0.2},
        'vvt_exhaust': {'min': -5.0, 'max': 5.0, 'scale': 0.2},
        'fuel_enrichment': {'min': -5.0, 'max': 5.0, 'scale': 0.2},
        'throttle_compensation': {'min': -5.0, 'max': 5.0, 'scale': 0.2}
    },
    'discrete_actions': {
        'performance_mode': ['street', 'track', 'drag'],
        'als_mode': ['off', 'soft', 'aggressive', 'rally'],
        'traction_control': ['off', 'low', 'medium', 'high']
    }
}

# Training Schedule
TRAINING_SCHEDULE = {
    'initial_exploration': {
        'duration_episodes': 1000,
        'exploration_rate': 1.0,
        'learning_rate_multiplier': 1.0
    },
    'main_training': {
        'duration_episodes': 5000,
        'exploration_decay': 0.9995,
        'learning_rate_decay': 0.9999
    },
    'fine_tuning': {
        'duration_episodes': 2000,
        'exploration_rate': 0.01,
        'learning_rate_multiplier': 0.1
    }
}

# Model Persistence
MODEL_PERSISTENCE = {
    'save_frequency_episodes': 100,
    'keep_best_models': 5,
    'model_format': 'pytorch',  # 'pytorch', 'onnx', 'tensorflow'
    'compression': True,
    'encryption': True
}

# Performance Targets
PERFORMANCE_TARGETS = {
    'street': {
        'target_horsepower': 300,
        'target_torque': 330,
        'target_0_60': 5.8,
        'target_quarter_mile': 14.2,
        'fuel_economy_penalty_max': 0.15  # 15% max fuel economy reduction
    },
    'track': {
        'target_horsepower': 340,
        'target_torque': 370,
        'target_0_60': 5.4,
        'target_quarter_mile': 13.8,
        'fuel_economy_penalty_max': 0.25  # 25% max fuel economy reduction
    },
    'drag': {
        'target_horsepower': 380,
        'target_torque': 400,
        'target_0_60': 5.0,
        'target_quarter_mile': 13.2,
        'fuel_economy_penalty_max': 0.35  # 35% max fuel economy reduction
    }
}

# Safety Constraints
SAFETY_CONSTRAINTS = {
    'hard_limits': {
        'max_boost_psi': 22.0,
        'max_engine_rpm': 7200,
        'max_exhaust_temp': 950.0,
        'max_intake_temp': 60.0,
        'max_coolant_temp': 105.0,
        'min_afr': 10.8,
        'max_knock_retard': -8.0
    },
    'soft_limits': {
        'preferred_boost_range': (12.0, 20.0),
        'preferred_afr_range': (11.2, 12.5),
        'preferred_timing_range': (8.0, 20.0),
        'max_boost_variance': 2.0,  # PSI
        'max_afr_variance': 0.5
    }
}
