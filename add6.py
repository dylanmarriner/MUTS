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
        
        # Calculate loss
        loss = nn.MSELoss()(current_q.squeeze(), target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update exploration rate
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

class AITuningSystem:
    """Complete AI-powered tuning system for Mazdaspeed 3"""
    
    def __init__(self):
        self.rl_tuner = ReinforcementTuner()
        self.performance_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.knock_model = RandomForestRegressor(n_estimators=50, random_state=42)
        
        self.learning_data = []
        self.tuning_rules = self._initialize_tuning_rules()
        
        # Tuning constraints
        self.safety_limits = {
            'max_boost': 22.0,           # PSI
            'max_timing_advance': 12.0,  # Degrees
            'min_afr': 10.8,             # Rich limit
            'max_afr': 12.5,             # Lean limit
            'max_knock_retard': -8.0,    # Degrees
            'max_egt': 950,              # °C
            'max_injector_duty': 85,     # %
            'max_manifold_pressure': 250 # kPa
        }
    
    def _initialize_tuning_rules(self):
        """Initialize expert tuning rules based on Mazdaspeed 3 characteristics"""
        rules = {
            'boost_spool_optimization': {
                'principle': 'Lower initial WGDC for faster spool, higher top-end for power',
                'implementation': self._optimize_boost_spool,
                'parameters': ['rpm', 'target_boost', 'current_boost']
            },
            'timing_optimization': {
                'principle': 'Advanced timing for torque, conservative for safety',
                'implementation': self._optimize_ignition_timing,
                'parameters': ['rpm', 'load', 'knock_count', 'intake_temp']
            },
            'vvt_optimization': {
                'principle': 'Early intake closing for dynamic compression',
                'implementation': self._optimize_vvt_timing,
                'parameters': ['rpm', 'load', 'throttle_position']
            },
            'afr_optimization': {
                'principle': 'Richer for power and safety, leaner for economy',
                'implementation': self._optimize_afr,
                'parameters': ['rpm', 'load', 'boost', 'coolant_temp']
            }
        }
        return rules
    
    def real_time_optimization(self, current_data):
        """
        Perform real-time optimization based on current engine conditions
        Returns optimized tuning parameters
        """
        # Extract current state
        state = self._create_state_vector(current_data)
        
        # Get AI recommendation
        ai_adjustments = self._get_ai_adjustments(state)
        
        # Apply expert rules
        rule_adjustments = self._apply_expert_rules(current_data)
        
        # Combine AI and rule-based adjustments
        final_adjustments = self._combine_adjustments(ai_adjustments, rule_adjustments)
        
        # Apply safety limits
        safe_adjustments = self._apply_safety_limits(final_adjustments, current_data)
        
        # Learn from this optimization
        self._learn_from_optimization(current_data, safe_adjustments)
        
        return safe_adjustments
    
    def _create_state_vector(self, data):
        """Create normalized state vector for AI system"""
        state = [
            data['rpm'] / 7000.0,                    # Normalized RPM
            data['load'] / 1.6,                      # Normalized load
            data['boost_psi'] / 22.0,                # Normalized boost
            data['ignition_timing'] / 25.0,          # Normalized timing
            (data['afr'] - 10.0) / 5.0,              # Normalized AFR
            abs(data['knock_retard']) / 8.0,         # Normalized knock
            data['intake_temp'] / 60.0,              # Normalized IAT
            data['coolant_temp'] / 110.0,            # Normalized ECT
            data['throttle_position'] / 100.0,       # Normalized throttle
            data['manifold_pressure'] / 250.0,       # Normalized MAP
            data['vvt_intake_angle'] / 50.0,         # Normalized VVT
            data['fuel_trim_long'] / 25.0            # Normalized fuel trim
        ]
        return np.array(state)
    
    def _get_ai_adjustments(self, state):
        """Get adjustments from reinforcement learning system"""
        action = self.rl_tuner.act(state)
        
        # Map action to actual adjustments
        adjustment_map = {
            0: {'ignition_timing': 0.5},    # Small timing advance
            1: {'ignition_timing': -0.5},   # Small timing retard
            2: {'boost_target': 0.2},       # Small boost increase
            3: {'boost_target': -0.2},      # Small boost decrease
            4: {'target_afr': -0.1},        # Slightly richer
            5: {'target_afr': 0.1},         # Slightly leaner
        }
        
        return adjustment_map.get(action, {})
    
    def _apply_expert_rules(self, data):
        """Apply expert tuning rules based on Mazdaspeed 3 specific knowledge"""
        adjustments = {}
        
        # Boost spool optimization
        boost_adj = self.tuning_rules['boost_spool_optimization']['implementation'](data)
        if boost_adj:
            adjustments.update(boost_adj)
        
        # Timing optimization
        timing_adj = self.tuning_rules['timing_optimization']['implementation'](data)
        if timing_adj:
            adjustments.update(timing_adj)
        
        # VVT optimization
        vvt_adj = self.tuning_rules['vvt_optimization']['implementation'](data)
        if vvt_adj:
            adjustments.update(vvt_adj)
        
        return adjustments
    
    def _optimize_boost_spool(self, data):
        """
        Advanced boost spool optimization
        Secret: Lower initial WGDC creates faster spool without sacrificing top-end
        """
        rpm = data['rpm']
        current_boost = data['boost_psi']
        target_boost = data.get('target_boost', 18.0)
        
        adjustments = {}
        
        if rpm < 3000:
            # Spool phase - reduce WGDC for faster response
            if current_boost < target_boost * 0.8:
                # Increase spool by reducing WGDC
                adjustments['wgdc_reduction'] = 5.0  # % reduction
                adjustments['boost_target'] = min(target_boost, 16.0)  # Conservative target during spool
        
        elif rpm > 5000:
            # High RPM - maintain boost with optimal WGDC
            if current_boost < target_boost * 0.95:
                adjustments['wgdc_increase'] = 3.0  # Small increase to hold boost
        
        return adjustments
    
    def _optimize_ignition_timing(self, data):
        """
        Advanced ignition timing optimization
        Secret: Use VVT to allow more timing advance without knock
        """
        rpm = data['rpm']
        load = data['load']
        knock_retard = data['knock_retard']
        intake_temp = data['intake_temp']
        
        adjustments = {}
        
        # Base timing adjustment based on conditions
        base_timing_adj = 0.0
        
        # Cooler intake air allows more timing
        if intake_temp < 25:
            base_timing_adj += 1.0
        elif intake_temp > 40:
            base_timing_adj -= 1.5
        
        # Knock response
        if knock_retard < -2.0:
            base_timing_adj -= 2.0
        elif knock_retard > -1.0 and load > 0.8:
            # Aggressive but safe timing advance
            base_timing_adj += 0.5
        
        # RPM-based timing optimization
        if 3000 <= rpm <= 5000:
            # Torque peak area - conservative timing
            base_timing_adj = min(base_timing_adj, 0.0)
        elif rpm > 6000:
            # High RPM - can run more timing due to reduced time for knock
            base_timing_adj += 1.0
        
        if abs(base_timing_adj) > 0.1:
            adjustments['ignition_timing'] = base_timing_adj
        
        return adjustments
    
    def _optimize_vvt_timing(self, data):
        """
        Variable Valve Timing optimization
        Secret: Early intake valve closing increases dynamic compression for low-end torque
        """
        rpm = data['rpm']
        load = data['load']
        throttle = data['throttle_position']
        
        adjustments = {}
        
        if rpm < 3500 and throttle > 70:
            # Low RPM, high load - advance intake for torque
            adjustments['vvt_intake_advance'] = 5.0
        elif rpm > 5000:
            # High RPM - retard intake for volumetric efficiency
            adjustments['vvt_intake_retard'] = 3.0
        
        return adjustments
    
    def _optimize_afr(self, data):
        """
        Air-Fuel Ratio optimization
        Secret: Slightly richer than stoichiometric in mid-range for power, 
                leaner in cruise for economy
        """
        rpm = data['rpm']
        load = data['load']
        boost = data['boost_psi']
        
        adjustments = {}
        
        if load > 0.8 and boost > 10:
            # High load, high boost - run richer for safety and power
            adjustments['target_afr'] = 11.2
        elif load < 0.3 and boost < 5:
            # Cruise conditions - run leaner for economy
            adjustments['target_afr'] = 14.7
        else:
            # Normal operation - balanced AFR
            adjustments['target_afr'] = 12.5
        
        return adjustments
    
    def _combine_adjustments(self, ai_adjustments, rule_adjustments):
        """Intelligently combine AI and rule-based adjustments"""
        combined = {}
        
        # Start with rule-based adjustments (expert knowledge)
        combined.update(rule_adjustments)
        
        # Carefully incorporate AI adjustments
        for key, ai_value in ai_adjustments.items():
            if key in combined:
                # Average AI and rule-based with 30% AI weight
                combined[key] = 0.7 * combined[key] + 0.3 * ai_value
            else:
                # Use AI adjustment directly but scaled down
                combined[key] = ai_value * 0.5
        
        return combined
    
    def _apply_safety_limits(self, adjustments, current_data):
        """Ensure all adjustments stay within safe operating limits"""
        safe_adjustments = adjustments.copy()
        
        # Check ignition timing limits
        if 'ignition_timing' in safe_adjustments:
            current_timing = current_data['ignition_timing']
            new_timing = current_timing + safe_adjustments['ignition_timing']
            max_timing = self.safety_limits['max_timing_advance']
            
            if new_timing > max_timing:
                safe_adjustments['ignition_timing'] = max_timing - current_timing
        
        # Check boost limits
        if 'boost_target' in safe_adjustments:
            new_boost = safe_adjustments['boost_target']
            if new_boost > self.safety_limits['max_boost']:
                safe_adjustments['boost_target'] = self.safety_limits['max_boost']
        
        # Check AFR limits
        if 'target_afr' in safe_adjustments:
            new_afr = safe_adjustments['target_afr']
            if new_afr < self.safety_limits['min_afr']:
                safe_adjustments['target_afr'] = self.safety_limits['min_afr']
            elif new_afr > self.safety_limits['max_afr']:
                safe_adjustments['target_afr'] = self.safety_limits['max_afr']
        
        return safe_adjustments
    
    def _learn_from_optimization(self, current_data, adjustments):
        """Learn from optimization results to improve future decisions"""
        # Calculate reward based on performance improvement
        reward = self._calculate_reward(current_data, adjustments)
        
        # Create state and next state
        state = self._create_state_vector(current_data)
        next_state = state.copy()  # Simplified - would be actual next state
        
        # Store in replay memory
        action = self._adjustments_to_action(adjustments)
        done = False  # Episode continues
        
        self.rl_tuner.remember(state, action, reward, next_state, done)
        
        # Train network
        self.rl_tuner.replay()
    
    def _calculate_reward(self, data, adjustments):
        """Calculate reward for reinforcement learning"""
        reward = 0.0
        
        # Positive rewards
        if data['knock_retard'] > -1.0:  # Little to no knock
            reward += 2.0
        
        if data['boost_psi'] > data.get('target_boost', 15.0) * 0.95:  # Good boost response
            reward += 1.0
        
        if 11.0 <= data['afr'] <= 12.0:  # Good AFR for power
            reward += 1.5
        
        # Negative rewards (penalties)
        if data['knock_retard'] < -5.0:  # Excessive knock
            reward -= 5.0
        
        if data['afr'] < 10.5 or data['afr'] > 13.0:  # AFR out of safe range
            reward -= 3.0
        
        if data['boost_psi'] > self.safety_limits['max_boost']:  # Overboost
            reward -= 10.0
        
        return reward
    
    def _adjustments_to_action(self, adjustments):
        """Convert adjustments dictionary to action index"""
        # Simplified mapping - in practice would be more sophisticated
        if 'ignition_timing' in adjustments:
            if adjustments['ignition_timing'] > 0:
                return 0  # Timing advance
            else:
                return 1  # Timing retard
        elif 'boost_target' in adjustments:
            if adjustments['boost_target'] > 0:
                return 2  # Boost increase
            else:
                return 3  # Boost decrease
        elif 'target_afr' in adjustments:
            if adjustments['target_afr'] < 12.0:
                return 4  # Richer
            else:
                return 5  # Leaner
        
        return 0  # Default action
    
    def save_models(self, filepath):
        """Save trained AI models"""
        torch.save(self.rl_tuner.q_network.state_dict(), f"{filepath}_q_network.pth")
        torch.save(self.rl_tuner.target_network.state_dict(), f"{filepath}_target_network.pth")
        joblib.dump(self.performance_model, f"{filepath}_performance_model.pkl")
        joblib.dump(self.knock_model, f"{filepath}_knock_model.pkl")
    
    def load_models(self, filepath):
        """Load trained AI models"""
        self.rl_tuner.q_network.load_state_dict(torch.load(f"{filepath}_q_network.pth"))
        self.rl_tuner.target_network.load_state_dict(torch.load(f"{filepath}_target_network.pth"))
        self.performance_model = joblib.load(f"{filepath}_performance_model.pkl")
        self.knock_model = joblib.load(f"{filepath}_knock_model.pkl")