#!/usr/bin/env python3
"""
ADVANCED AI TUNING SYSTEM FOR MAZDASPEED 3
Uses machine learning to optimize tuning parameters in real-time
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from collections import deque
import random

class AITuningNetwork(nn.Module):
    """Neural network for real-time tuning optimization"""
    
    def __init__(self, input_size=15, hidden_size=64, output_size=8):
        super(AITuningNetwork, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, output_size),
            nn.Tanh()  # Output between -1 and 1 for adjustments
        )
        
    def forward(self, x):
        return self.network(x)

class ReinforcementTuner:
    """Reinforcement learning system for autonomous tuning"""
    
    def __init__(self):
        self.state_size = 12  # RPM, Load, Boost, Timing, AFR, Knock, etc.
        self.action_size = 6   # Timing adj, Boost adj, Fuel adj, VVT adj, etc.
        
        self.q_network = AITuningNetwork(self.state_size, 128, self.action_size)
        self.target_network = AITuningNetwork(self.state_size, 128, self.action_size)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)
        
        self.memory = deque(maxlen=10000)
        self.batch_size = 32
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        
        self.scaler = StandardScaler()
        
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        """Choose action based on current state"""
        if np.random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        return np.argmax(q_values.detach().numpy())
    
    def replay(self):
        """Train network on random samples from memory"""
        if len(self.memory) < self.batch_size:
            return
        
        batch = random.sample(self.memory, self.batch_size)
        states = np.array([e[0] for e in batch])
        actions = np.array([e[1] for e in batch])
        rewards = np.array([e[2] for e in batch])
        next_states = np.array([e[3] for e in batch])
        dones = np.array([e[4] for e in batch])
        
        # Convert to tensors
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.BoolTensor(dones)
        
        # Current Q values
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values from target network
        next_q = self.target_network(next_states).max(1)[0].detach()
        next_q[dones] = 0.0  # No future rewards if episode done
        
        # Target Q values
        target_q = rewards + self.gamma * next_q
        
        # Compute loss
        loss = nn.MSELoss()(current_q.squeeze(), target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def update_target_network(self):
        """Copy weights from main network to target network"""
        self.target_network.load_state_dict(self.q_network.state_dict())

class ExpertTuningRules:
    """Expert system with proprietary tuning knowledge"""
    
    def __init__(self):
        self.rules = {
            'knock_correction': {
                'mild_knock': {'timing_retard': -1.0, 'fuel_enrichment': 0.5},
                'moderate_knock': {'timing_retard': -2.0, 'fuel_enrichment': 1.0},
                'severe_knock': {'timing_retard': -4.0, 'fuel_enrichment': 2.0}
            },
            'boost_control': {
                'spool_optimization': {'wgdc_reduction': -10.0, 'target_adjust': 0.0},
                'peak_power': {'wgdc_increase': 5.0, 'timing_advance': 1.0},
                'overboost_protection': {'wgdc_reduction': -15.0, 'timing_retard': -2.0}
            },
            'vvt_optimization': {
                'low_rpm_torque': {'intake_advance': 8.0, 'exhaust_retard': 5.0},
                'mid_range_power': {'intake_advance': 5.0, 'exhaust_retard': 2.0},
                'high_rpm_power': {'intake_retard': -3.0, 'exhaust_retard': 0.0}
            }
        }
    
    def apply_rules(self, conditions):
        """Apply expert rules based on current conditions"""
        adjustments = {}
        
        # Knock correction rules
        if conditions.get('knock_retard', 0) < -0.5:
            if conditions['knock_retard'] < -3.0:
                rule = self.rules['knock_correction']['severe_knock']
            elif conditions['knock_retard'] < -1.5:
                rule = self.rules['knock_correction']['moderate_knock']
            else:
                rule = self.rules['knock_correction']['mild_knock']
            adjustments.update(rule)
        
        # Boost control rules
        rpm = conditions.get('rpm', 0)
        boost = conditions.get('boost', 0)
        
        if 2000 <= rpm <= 3500 and boost < 10.0:
            # Spool optimization
            adjustments.update(self.rules['boost_control']['spool_optimization'])
        elif rpm >= 5500 and boost >= 15.0:
            # Peak power
            adjustments.update(self.rules['boost_control']['peak_power'])
        elif boost > 18.0:
            # Overboost protection
            adjustments.update(self.rules['boost_control']['overboost_protection'])
        
        # VVT optimization rules
        if rpm <= 3000:
            adjustments.update(self.rules['vvt_optimization']['low_rpm_torque'])
        elif 3000 < rpm <= 5500:
            adjustments.update(self.rules['vvt_optimization']['mid_range_power'])
        elif rpm > 5500:
            adjustments.update(self.rules['vvt_optimization']['high_rpm_power'])
        
        return adjustments

class AITuningSystem:
    """Main AI tuning system combining ML and expert rules"""
    
    def __init__(self, model_path='ai_tuning_model.pth'):
        self.model_path = model_path
        self.reinforcement_tuner = ReinforcementTuner()
        self.expert_rules = ExpertTuningRules()
        self.random_forest = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        # Safety limits
        self.safety_limits = {
            'max_boost': 22.0,
            'max_timing_advance': 5.0,
            'min_afr': 10.8,
            'max_egt': 950.0,
            'max_knock_retard': -8.0
        }
        
        # Learning parameters
        self.learning_rate = 0.001
        self.exploration_rate = 0.1
        self.performance_history = deque(maxlen=1000)
        
        # Load existing model if available
        try:
            self.load_model()
        except:
            print("No existing model found, starting fresh")
    
    def real_time_optimization(self, sensor_data):
        """Perform real-time optimization based on sensor data"""
        
        # Extract features
        features = self._extract_features(sensor_data)
        
        # Apply expert rules first
        expert_adjustments = self.expert_rules.apply_rules(sensor_data)
        
        # ML-based adjustments
        ml_adjustments = self._ml_optimize(features)
        
        # Combine adjustments with safety checks
        final_adjustments = self._combine_adjustments(expert_adjustments, ml_adjustments)
        
        # Apply safety limits
        final_adjustments = self._apply_safety_limits(sensor_data, final_adjustments)
        
        # Learn from this iteration
        self._learn_from_adjustment(sensor_data, final_adjustments)
        
        return final_adjustments
    
    def _extract_features(self, sensor_data):
        """Extract relevant features for ML models"""
        features = [
            sensor_data.get('rpm', 0) / 7000.0,  # Normalized RPM
            sensor_data.get('load', 0) / 1.6,     # Normalized load
            sensor_data.get('boost_psi', 0) / 22.0,  # Normalized boost
            sensor_data.get('ignition_timing', 0) / 25.0,
            sensor_data.get('afr', 14.7) / 20.0,
            sensor_data.get('knock_retard', 0) / 8.0,
            sensor_data.get('intake_temp', 25) / 60.0,
            sensor_data.get('coolant_temp', 90) / 110.0,
            sensor_data.get('throttle_position', 0) / 100.0,
            sensor_data.get('manifold_pressure', 100) / 250.0,
            sensor_data.get('vvt_intake_angle', 0) / 50.0,
            sensor_data.get('vvt_exhaust_angle', 0) / 50.0
        ]
        return np.array(features)
    
    def _ml_optimize(self, features):
        """Use machine learning for optimization"""
        # Reinforcement learning action
        state = features[:self.reinforcement_tuner.state_size]
        rl_action = self.reinforcement_tuner.act(state)
        
        # Convert action to adjustments
        adjustments = {}
        if rl_action == 0:  # Timing adjustment
            adjustments['ignition_timing'] = np.random.uniform(-2, 2)
        elif rl_action == 1:  # Boost adjustment
            adjustments['boost_target'] = np.random.uniform(-1, 1)
        elif rl_action == 2:  # Fuel adjustment
            adjustments['fuel_enrichment'] = np.random.uniform(-2, 2)
        elif rl_action == 3:  # VVT intake
            adjustments['vvt_intake'] = np.random.uniform(-5, 5)
        elif rl_action == 4:  # VVT exhaust
            adjustments['vvt_exhaust'] = np.random.uniform(-5, 5)
        elif rl_action == 5:  # WGDC adjustment
            adjustments['wgdc_adjustment'] = np.random.uniform(-10, 10)
        
        return adjustments
    
    def _combine_adjustments(self, expert, ml):
        """Combine expert rule adjustments with ML adjustments"""
        combined = expert.copy()
        
        # Weight expert rules higher for safety
        for key, value in ml.items():
            if key in combined:
                combined[key] = 0.7 * combined[key] + 0.3 * value
            else:
                combined[key] = 0.5 * value  # Reduce ML-only adjustments
        
        return combined
    
    def _apply_safety_limits(self, sensor_data, adjustments):
        """Apply safety limits to all adjustments"""
        safe_adjustments = adjustments.copy()
        
        # Check boost limits
        current_boost = sensor_data.get('boost_psi', 0)
        if 'boost_target' in safe_adjustments:
            new_boost = current_boost + safe_adjustments['boost_target']
            if new_boost > self.safety_limits['max_boost']:
                safe_adjustments['boost_target'] = self.safety_limits['max_boost'] - current_boost
        
        # Check timing limits
        current_timing = sensor_data.get('ignition_timing', 10)
        if 'ignition_timing' in safe_adjustments:
            new_timing = current_timing + safe_adjustments['ignition_timing']
            if new_timing > 25 + self.safety_limits['max_timing_advance']:
                safe_adjustments['ignition_timing'] = 25 + self.safety_limits['max_timing_advance'] - current_timing
        
        # Check AFR limits
        if 'fuel_enrichment' in safe_adjustments:
            # Indirect AFR check via fuel enrichment
            if safe_adjustments['fuel_enrichment'] < -5:  # Too lean
                safe_adjustments['fuel_enrichment'] = -5
        
        # Knock retard check
        if sensor_data.get('knock_retard', 0) < self.safety_limits['max_knock_retard']:
            # Aggressive retard if severe knock
            safe_adjustments['ignition_timing'] = safe_adjustments.get('ignition_timing', 0) - 3
            safe_adjustments['fuel_enrichment'] = safe_adjustments.get('fuel_enrichment', 0) + 2
        
        return safe_adjustments
    
    def _learn_from_adjustment(self, sensor_data, adjustments):
        """Learn from the adjustment made"""
        # Calculate performance score
        score = self._calculate_performance_score(sensor_data)
        
        # Store for reinforcement learning
        state = self._extract_features(sensor_data)
        action = self._adjustments_to_action(adjustments)
        
        # Store experience (simplified - in real implementation would track next state)
        self.reinforcement_tuner.remember(state, action, score, state, False)
        
        # Train periodically
        if len(self.reinforcement_tuner.memory) > 100:
            self.reinforcement_tuner.replay()
        
        # Store performance history
        self.performance_history.append(score)
    
    def _calculate_performance_score(self, sensor_data):
        """Calculate performance score based on sensor data"""
        score = 0
        
        # Power output (estimated)
        rpm = sensor_data.get('rpm', 0)
        torque = sensor_data.get('calculated_torque', 0)
        power_score = (rpm * torque) / 1000000  # Normalized
        score += power_score * 0.4
        
        # Efficiency
        afr = sensor_data.get('afr', 14.7)
        if 11.5 <= afr <= 12.5:  # Optimal range
            score += 0.2
        elif 11.0 <= afr <= 13.0:
            score += 0.1
        
        # Knock penalty
        knock = sensor_data.get('knock_retard', 0)
        if knock < -0.5:
            score -= 0.3
        elif knock < -2.0:
            score -= 0.5
        
        # Boost consistency
        boost = sensor_data.get('boost_psi', 0)
        if 15.0 <= boost <= 18.0:
            score += 0.2
        
        return score
    
    def _adjustments_to_action(self, adjustments):
        """Convert adjustments to reinforcement learning action"""
        # Simplified action mapping
        if 'ignition_timing' in adjustments:
            return 0
        elif 'boost_target' in adjustments:
            return 1
        elif 'fuel_enrichment' in adjustments:
            return 2
        elif 'vvt_intake' in adjustments:
            return 3
        elif 'vvt_exhaust' in adjustments:
            return 4
        else:
            return 5
    
    def save_model(self):
        """Save trained model"""
        torch.save({
            'q_network': self.reinforcement_tuner.q_network.state_dict(),
            'target_network': self.reinforcement_tuner.target_network.state_dict(),
            'optimizer': self.reinforcement_tuner.optimizer.state_dict(),
            'epsilon': self.reinforcement_tuner.epsilon
        }, self.model_path)
    
    def load_model(self):
        """Load trained model"""
        checkpoint = torch.load(self.model_path)
        self.reinforcement_tuner.q_network.load_state_dict(checkpoint['q_network'])
        self.reinforcement_tuner.target_network.load_state_dict(checkpoint['target_network'])
        self.reinforcement_tuner.optimizer.load_state_dict(checkpoint['optimizer'])
        self.reinforcement_tuner.epsilon = checkpoint['epsilon']
    
    def get_performance_stats(self):
        """Get performance statistics"""
        if not self.performance_history:
            return {}
        
        history = list(self.performance_history)
        return {
            'average_score': np.mean(history),
            'max_score': np.max(history),
            'min_score': np.min(history),
            'recent_trend': np.mean(history[-10:]) if len(history) >= 10 else np.mean(history),
            'total_adjustments': len(history)
        }
