#!/usr/bin/env python3
"""
MAZDASPEED 3 2011 COMPLETE CONFIGURATION
All vehicle-specific parameters and tuning limits
"""

# Engine Specifications
ENGINE_SPECS = {
    'model': 'MZR 2.3L DISI TURBO',
    'displacement_cc': 2261,
    'displacement_liters': 2.261,
    'bore_mm': 87.5,
    'stroke_mm': 94.0,
    'compression_ratio': 9.5,
    'cylinders': 4,
    'valves_per_cylinder': 4,
    'fuel_system': 'Direct Injection',
    'max_power_stock': 263,  # HP
    'max_torque_stock': 280,  # lb-ft
    'redline_rpm': 6700,
    'fuel_cut_rpm': 6800
}

# Turbocharger Specifications
TURBO_SPECS = {
    'model': 'KK4 (Mitsubishi TD04-HL-15T-6)',
    'compressor_wheel': '44.5/60.0 mm',
    'turbine_wheel': '54.0 mm',
    'housing_ar': 0.64,
    'wastegate_type': 'Internal',
    'max_boost_stock': 15.6,  # PSI
    'max_flow': 0.18,  # kg/s
    'peak_efficiency': 0.78
}

# Fuel System Specifications
FUEL_SYSTEM_SPECS = {
    'injector_flow_rate': 265,  # cc/min @ 3 bar
    'fuel_pressure_base': 3.0,  # bar
    'fuel_pressure_max': 15.0,  # bar (high pressure pump)
    'injector_type': 'Solenoid DI',
    'max_injector_duty': 85,  # %
    'fuel_rail_volume': 25  # cc
}

# Ignition System Specifications
IGNITION_SYSTEM_SPECS = {
    'coil_type': 'Pencil Coil',
    'spark_plug_gap': 0.8,  # mm
    'ignition_energy': 80,  # mJ
    'dwell_time': 3.5,  # ms
}

# Tuning Safety Limits
SAFETY_LIMITS = {
    'max_boost_psi': 22.0,
    'max_manifold_pressure_kpa': 250,
    'max_engine_rpm': 7200,
    'max_ignition_timing': 12.0,  # degrees advance over stock
    'min_afr_wot': 10.8,
    'max_afr_wot': 12.5,
    'max_egt_celsius': 950,
    'max_injector_duty': 85,
    'max_knock_retard': -8.0,
    'max_intake_temp': 60,
    'max_coolant_temp': 105
}

# Transmission Specifications
TRANSMISSION_SPECS = {
    'type': '6-Speed Manual',
    'gear_ratios': [3.36, 2.06, 1.38, 1.03, 0.85, 0.67],
    'final_drive_ratio': 4.39,
    'differential_type': 'Helical Limited Slip',
    'clutch_type': 'Dual Mass Flywheel'
}

# Vehicle Specifications
VEHICLE_SPECS = {
    'curb_weight_kg': 1480,
    'weight_distribution': '63/37',  # Front/Rear
    'drag_coefficient': 0.31,
    'frontal_area_m2': 2.2,
    'tire_size': '225/40R18',
    'tire_radius_m': 0.325,
    'wheelbase_m': 2.64,
    'track_width_m': 1.54
}

# ECU Memory Addresses (MZR DISI Specific)
ECU_MEMORY_MAP = {
    'ignition_timing_base': 0xFFA000,
    'fuel_map_primary': 0xFFA800,
    'boost_target_map': 0xFFB000,
    'vvt_intake_map': 0xFFB400,
    'vvt_exhaust_map': 0xFFB500,
    'rev_limiter_soft': 0xFFB800,
    'rev_limiter_hard': 0xFFB810,
    'torque_management': 0xFFBC00,
    'knock_learn_table': 0xFFC000,
    'fuel_trim_adaptive': 0xFFC200
}

# Diagnostic Parameters
DIAGNOSTIC_CONFIG = {
    'can_bus_speed': 500000,  # 500kbps
    'obd_protocol': 'ISO15765-4',
    'ecu_address': 0x7E0,
    'tcm_address': 0x7E1,
    'supported_pids': [
        '0100', '0101', '0103', '0104', '0105', '0106', '0107', '010B',
        '010C', '010D', '010E', '010F', '0110', '0111', '0112', '0113',
        '0114', '0115', '011F', '0121', '0122', '0123', '0124', '0125'
    ]
}

# AI Tuning Configuration
AI_TUNING_CONFIG = {
    'learning_rate': 0.001,
    'discount_factor': 0.95,
    'exploration_start': 1.0,
    'exploration_end': 0.01,
    'exploration_decay': 0.995,
    'replay_memory_size': 10000,
    'batch_size': 32,
    'update_target_every': 1000,
    'hidden_layer_size': 256
}

# Performance Targets
PERFORMANCE_TARGETS = {
    'stage1': {
        'target_power': 300,  # HP
        'target_torque': 330,  # lb-ft
        'target_boost': 18.0,  # PSI
        'required_mods': ['High-flow air filter', 'Stage 1 tune']
    },
    'stage2': {
        'target_power': 340,  # HP
        'target_torque': 370,  # lb-ft
        'target_boost': 20.0,  # PSI
        'required_mods': ['Downpipe', 'Intercooler', 'Stage 2 tune']
    },
    'stage3': {
        'target_power': 380,  # HP
        'target_torque': 400,  # lb-ft
        'target_boost': 22.0,  # PSI
        'required_mods': ['Turbo upgrade', 'Fuel pump', 'Stage 3 tune']
    }
}