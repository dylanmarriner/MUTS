            # Pistons
            EngineComponentDatabase(
                component_type="piston",
                component_name="OEM Forged Piston",
                oem_part_number="L3K9114071",
                material="Aluminum Forged",
                tensile_strength=350.0,
                yield_strength=280.0,
                hardness="HB 120-140",
                weight=420.0,
                dimensions=json.dumps({
                    'bore': 87.5,
                    'compression_height': 30.2,
                    'pin_diameter': 21.0,
                    'ring_land_thickness': 1.5
                }),
                clearance_specs=json.dumps({
                    'piston_to_wall': 0.03,
                    'ring_end_gap_top': 0.25,
                    'ring_end_gap_second': 0.40,
                    'ring_end_gap_oil': 0.15
                }),
                max_temperature=350.0,
                max_pressure=120.0,
                max_rpm=7500.0,
                common_failure_modes=json.dumps([
                    "Ring land cracking under detonation",
                    "Skirt scuffing from insufficient warm-up",
                    "Pin bore deformation from excessive boost"
                ])
            ),
            
            # Connecting Rods
            EngineComponentDatabase(
                component_type="connecting_rod",
                component_name="OEM Powdered Metal Rod",
                oem_part_number="L3K9113020",
                material="Powdered Metal Steel",
                tensile_strength=800.0,
                yield_strength=650.0,
                hardness="HRC 28-32",
                weight=620.0,
                dimensions=json.dumps({
                    'center_to_center': 150.0,
                    'big_end_diameter': 52.0,
                    'small_end_diameter': 21.0,
                    'beam_width': 24.0
                }),
                max_rpm=7200.0,
                fatigue_life=json.dumps({
                    'design_life': '200,000 cycles at 6000 RPM',
                    'safety_factor': '2.5 at redline',
                    'upgrade_recommendation': 'Forged steel for >400whp'
                }),
                common_failure_modes=json.dumps([
                    "Bolt stretch at high RPM",
                    "Big end deformation from excessive power",
                    "Small end bushing wear"
                ])
            ),
            
            # Crankshaft
            EngineComponentDatabase(
                component_type="crankshaft",
                component_name="OEM Forged Crankshaft",
                oem_part_number="L3K9113010",
                material="Forged Steel",
                tensile_strength=900.0,
                yield_strength=750.0,
                hardness="HRC 55-60",
                weight=12500.0,
                dimensions=json.dumps({
                    'stroke': 94.0,
                    'main_journal_diameter': 57.0,
                    'rod_journal_diameter': 48.0,
                    'counterweight_design': '8 counterweights'
                }),
                max_rpm=7500.0,
                common_failure_modes=json.dumps([
                    "Main bearing wear from oil starvation",
                    "Thrust surface wear from clutch load",
                    "Keyway damage from harmonic vibrations"
                ])
            ),
            
            # Fuel Injectors
            EngineComponentDatabase(
                component_type="fuel_injector",
                component_name="OEM DISI Injector",
                oem_part_number="L3K9133020",
                material="Stainless Steel/Copper",
                max_temperature=120.0,
                max_pressure=150.0,
                dimensions=json.dumps({
                    'flow_rate': '265cc/min @ 3bar',
                    'static_flow': '320cc/min @ 5bar',
                    'spray_pattern': '6-hole conical',
                    'resistance': '12-16 ohms'
                }),
                common_failure_modes=json.dumps([
                    "Clogging from poor fuel quality",
                    "Coil failure from heat cycling",
                    "O-ring degradation from ethanol"
                ])
            )
        ]
        
        self.session.add_all(components)
        self.session.commit()
    
    def _initialize_tuning_secrets(self):
        """Initialize proprietary tuning secrets database"""
        
        tuning_secrets = [
            TuningSecret(
                secret_name="Faster Spool with Lower Initial WGDC",
                category="boost",
                description="Reducing initial wastegate duty cycle creates faster turbo spool without sacrificing top-end power",
                technical_basis="Lower WGDC reduces backpressure during spool phase, allowing turbo to accelerate faster. The K04 turbo responds well to aggressive spool tuning due to its small turbine wheel.",
                implementation_method="Reduce WGDC by 8-15% in the 2000-3500 RPM range, then gradually increase to maintain target boost. Use progressive WGDC mapping that starts low and ramps up.",
                expected_benefits=json.dumps([
                    "1.0-1.5 second faster spool to 15 PSI",
                    "Improved throttle response in daily driving",
                    "Better transient boost response"
                ]),
                potential_risks=json.dumps([
                    "Potential overboost if not properly controlled",
                    "Increased exhaust backpressure at high RPM if too aggressive"
                ]),
                applicable_conditions="Best for street driving and autocross. Less beneficial for drag racing where top-end power is prioritized.",
                vehicle_specific_notes="Mazdaspeed 3 benefits greatly from this technique due to its relatively large 2.3L displacement and small K04 turbo.",
                safety_limits=json.dumps({
                    'minimum_wgdc': '25% to prevent overboost',
                    'max_boost_spike': '2 PSI over target',
                    'monitor_exhaust_temps': 'Keep below 900°C during spool'
                })
            ),
            
            TuningSecret(
                secret_name="VVT Torque Optimization for Broad Powerband",
                category="vvt",
                description="Strategic VVT tuning creates a broader torque curve by optimizing cam timing across the RPM range",
                technical_basis="Early intake valve closing increases dynamic compression for low-end torque. Late intake closing improves volumetric efficiency for high-RPM power. The MZR DISI engine responds exceptionally well to VVT optimization.",
                implementation_method="Advance intake cam 5-8° below 3500 RPM for torque, retard 3-5° above 5500 RPM for power. Use exhaust cam retard below 3000 RPM for scavenging.",
                expected_benefits=json.dumps([
                    "15-20 lb-ft gain in mid-range torque",
                    "Broader powerband with less peakiness",
                    "Improved drivability in daily use"
                ]),
                potential_risks=json.dumps([
                    "Potential valve-to-piston contact if too aggressive",
                    "Reduced top-end power if intake closing too early"
                ]),
                applicable_conditions="All driving conditions. Particularly effective for street and track use where broad powerband is desired.",
                vehicle_specific_notes="MZR DISI has relatively conservative factory VVT mapping. Aggressive but safe optimization can yield significant gains.",
                safety_limits=json.dumps({
                    'max_intake_advance': '25° absolute',
                    'max_exhaust_retard': '15° absolute',
                    'oil_temperature': 'Must be above 60°C for full advance'
                })
            ),
            
            TuningSecret(
                secret_name="Ignition Timing with Knock Margin Management",
                category="ignition",
                description="Dynamic ignition timing based on calculated knock margin rather than reactive knock control",
                technical_basis="Predictive knock management uses physics-based models to anticipate knock conditions before they occur, allowing more aggressive timing in safe conditions while being conservative when knock risk is high.",
                implementation_method="Calculate knock margin based on intake temperature, coolant temperature, fuel quality, and cylinder pressure. Adjust timing proactively rather than reactively.",
                expected_benefits=json.dumps([
                    "2-3° more timing in safe conditions",
                    "Better power consistency across conditions",
                    "Reduced false knock detection"
                ]),
                potential_risks=json.dumps([
                    "Requires accurate modeling of knock conditions",
                    "Potential for actual knock if model is incorrect"
                ]),
                applicable_conditions="All performance levels. Particularly beneficial for vehicles running different fuel qualities or in varying climate conditions.",
                vehicle_specific_notes="Mazdaspeed 3 knock sensors are sensitive but can be overly conservative. Predictive management allows more precise control.",
                safety_limits=json.dumps({
                    'max_timing_advance': '5° over factory WOT timing',
                    'minimum_knock_margin': '2° safety margin',
                    'fallback_to_reactive': 'Always maintain reactive knock control as backup'
                })
            ),
            
            TuningSecret(
                secret_name="Boost Taper with Timing Compensation",
                category="boost",
                description="Intelligent boost taper at high RPM combined with timing advance to maintain power while ensuring safety",
                technical_basis="As volumetric efficiency drops at high RPM, lower boost with optimized timing can make more power than higher boost with retarded timing. This reduces stress on the turbo and engine while maintaining performance.",
                implementation_method="Begin boost taper at 6000 RPM, reducing 0.5 PSI per 500 RPM. Compensate with 0.5° timing advance per PSI reduction.",
                expected_benefits=json.dumps([
                    "Reduced turbo and engine stress at high RPM",
                    "Maintained or improved top-end power",
                    "Better reliability for track use"
                ]),
                potential_risks=json.dumps([
                    "Potential power loss if taper too aggressive",
                    "Requires precise timing compensation"
                ]),
                applicable_conditions="Best for high-RPM operation - track use, highway pulls. Less beneficial for drag racing where mid-range is key.",
                vehicle_specific_notes="K04 turbo efficiency drops significantly above 6000 RPM. Tapering boost reduces heat and backpressure.",
                safety_limits=json.dumps({
                    'minimum_boost_taper': '15 PSI at redline',
                    'max_timing_compensation': '3° total advance from taper',
                    'monitor_egt': 'Keep below 950°C during taper'
                })
            ),
            
            TuningSecret(
                secret_name="Direct Injection Fueling Optimization",
                category="fuel",
                description="Advanced DI fueling strategies for better combustion and power",
                technical_basis="MZR DISI uses sophisticated multiple injection strategies. Optimizing injection timing and patterns can improve combustion efficiency, reduce knock tendency, and increase power.",
                implementation_method="Use pilot injection for smoother combustion, main injection optimized for power, and post injection for cooling. Adjust injection timing based on load and RPM.",
                expected_benefits=json.dumps([
                    "2-4% power increase from improved combustion",
                    "Reduced knock tendency",
                    "Better fuel economy at part throttle"
                ]),
                potential_risks=json.dumps([
                    "Potential injector wear from aggressive strategies",
                    "Carbon buildup if strategies not optimized"
                ]),
                applicable_conditions="All driving conditions. Particularly effective for high-boost applications.",
                vehicle_specific_notes="MZR DISI has robust fueling system capable of advanced strategies. Factory calibration is conservative for emissions.",
                safety_limits=json.dumps({
                    'max_injector_duty': '85% sustained',
                    'injection_pressure': 'Keep below 150 bar for reliability',
                    'monitor_afr': 'Maintain 11.0-12.0 at WOT'
                })
            )
        ]
        
        self.session.add_all(tuning_secrets)
        self.session.commit()
    
    def _initialize_diagnostic_codes(self):
        """Initialize complete diagnostic trouble code database"""
        
        dtc_list = [
            # Engine-related DTCs
            DiagnosticTroubleCode(
                code="P0300",
                description="Random/Multiple Cylinder Misfire Detected",
                severity="HIGH",
                system_affected="Ignition/Fuel System",
                possible_causes=json.dumps([
                    "Faulty spark plugs or ignition coils",
                    "Fuel injector issues",
                    "Low fuel pressure",
                    "Compression loss",
                    "Vacuum leaks"
                ]),
                diagnostic_procedure="Check spark plugs, ignition coils, fuel pressure, compression test, smoke test for vacuum leaks",
                common_on_mazdaspeed3=True,
                ms3_specific_causes=json.dumps([
                    "Failed ignition coil (common issue)",
                    "Carbon buildup on intake valves (DIRECT INJECTION ISSUE)",
                    "High-pressure fuel pump failure",
                    "Boost leaks from intercooler piping"
                ]),
                ms3_repair_tips="Start with ignition system diagnosis. Common coil failure pattern. Check for carbon buildup if mileage over 60k."
            ),
            
            DiagnosticTroubleCode(
                code="P0234",
                description="Turbocharger Overboost Condition",
                severity="HIGH",
                system_affected="Turbocharger System",
                possible_causes=json.dumps([
                    "Wastegate stuck closed",
                    "Boost control solenoid failure",
                    "Boost leak causing erratic control",
                    "ECU calibration issue"
                ]),
                diagnostic_procedure="Check wastegate operation, boost control solenoid, boost leak test, inspect ECU tuning",
                common_on_mazdaspeed3=True,
                ms3_specific_causes=json.dumps([
                    "Aftermarket tune too aggressive",
                    "Wastegate actuator failure (common)",
                    "Boost control solenoid clogged",
                    "Intercooler pipe popped off"
                ]),
                ms3_repair_tips="Common on tuned vehicles. Check wastegate actuator first. Verify boost control solenoid operation."
            ),
            
            DiagnosticTroubleCode(
                code="P0011",
                description="Intake Camshaft Position Timing Over-Advanced",
                severity="MEDIUM",
                system_affected="Variable Valve Timing",
                possible_causes=json.dumps([
                    "VVT solenoid failure",
                    "Oil pressure issues",
                    "Timing chain stretched",
                    "Camshaft position sensor fault"
                ]),
                diagnostic_procedure="Check oil level and pressure, test VVT solenoid, inspect timing chain, verify cam sensor operation",
                common_on_mazdaspeed3=True,
                ms3_specific_causes=json.dumps([
                    "VVT solenoid clogged (very common)",
                    "Low oil pressure from worn engine",
                    "Timing chain tensioner failure",
                    "Aftermarket oil filter causing flow issues"
                ]),
                ms3_repair_tips="Very common on high-mileage MS3. Start with VVT solenoid replacement. Use OEM oil filters only."
            ),
            
            DiagnosticTroubleCode(
                code="P0087",
                description="Fuel Rail/System Pressure Too Low",
                severity="HIGH",
                system_affected="Fuel System",
                possible_causes=json.dumps([
                    "High-pressure fuel pump failure",
                    "Low-pressure fuel pump weak",
                    "Fuel pressure sensor fault",
                    "Fuel filter clogged"
                ]),
                diagnostic_procedure="Check low and high pressure fuel pumps, fuel pressure sensor, fuel filter, inspect for leaks",
                common_on_mazdaspeed3=True,
                ms3_specific_causes=json.dumps([
                    "HPFP failure (common on tuned vehicles)",
                    "LPFP unable to keep up with modifications",
                    "Cam lobe wear affecting HPFP operation",
                    "Fuel pressure sensor failure"
                ]),
                ms3_repair_tips="Common on modified vehicles. Upgrade HPFP for tuned applications. Check cam lobe for wear."
            ),
            
            DiagnosticTroubleCode(
                code="P2187",
                description="Cooling System Performance",
                severity="MEDIUM",
                system_affected="Cooling System",
                possible_causes=json.dumps([
                    "Thermostat stuck open",
                    "Coolant temperature sensor fault",
                    "Cooling system air pocket",
                    "Radiator fan not operating"
                ]),
                diagnostic_procedure="Check thermostat operation, coolant temp sensor, bleed cooling system, test radiator fan",
                common_on_mazdaspeed3=False,
                ms3_specific_causes=json.dumps([
                    "Thermostat failure (common)",
                    "Coolant air pocket from improper service",
                    "Radiator fan relay failure",
                    "Aftermarket radiator issues"
                ]),
                ms3_repair_tips="Check thermostat first. Common failure item. Ensure proper cooling system bleeding procedure followed."
            ),
            
            # Transmission-related DTCs
            DiagnosticTroubleCode(
                code="P0841",
                description="Transmission Fluid Pressure Sensor/Switch A Circuit Range/Performance",
                severity="MEDIUM",
                system_affected="Transmission",
                possible_causes=json.dumps([
                    "Transmission fluid pressure sensor failure",
                    "Low transmission fluid",
                    "Valve body issues",
                    "Internal transmission problems"
                ]),
                diagnostic_procedure="Check transmission fluid level and condition, test pressure sensor, inspect valve body",
                common_on_mazdaspeed3=True,
                ms3_specific_causes=json.dumps([
                    "Transmission fluid degradation",
                    "Pressure sensor failure",
                    "Valve body wear",
                    "Clutch pack wear"
                ]),
                ms3_repair_tips="Common on high-mileage vehicles. Start with fluid change and sensor replacement. Use OEM fluid only."
            )
        ]
        
        self.session.add_all(dtc_list)
        self.session.commit()
    
    # Helper methods for creating complex data structures
    
    def _create_ignition_corrections(self):
        """Create ignition timing correction maps"""
        return {
            'intake_temp_correction': {
                '-40°C': 5.0, '-20°C': 3.0, '0°C': 2.0, '20°C': 0.0, 
                '40°C': -2.0, '60°C': -4.0, '80°C': -6.0
            },
            'coolant_temp_correction': {
                '-40°C': 4.0, '0°C': 2.0, '40°C': 0.0, '80°C': -1.0,
                '100°C': -2.0, '110°C': -4.0
            },
            'barometric_correction': {
                '70 kPa': 2.0, '80 kPa': 1.5, '90 kPa': 1.0, '100 kPa': 0.0,
                '110 kPa': -1.0
            }
        }
    
    def _create_afr_target_map(self):
        """Create target AFR map"""
        return [
            [14.7, 14.7, 14.7, 14.7, 14.7, 14.7, 14.5, 14.2, 13.5, 12.8, 12.2, 11.8, 11.5, 11.5, 11.5, 11.5],
            [14.7, 14.7, 14.7, 14.7, 14.7, 14.5, 14.2, 13.8, 13.2, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5],
            [14.7, 14.7, 14.7, 14.7, 14.5, 14.2, 13.8, 13.5, 12.8, 12.2, 11.8, 11.6, 11.5, 11.5, 11.5, 11.5],
            [14.7, 14.7, 14.7, 14.5, 14.2, 13.8, 13.5, 13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5],
            [14.7, 14.7, 14.5, 14.2, 13.8, 13.5, 13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [14.7, 14.5, 14.2, 13.8, 13.5, 13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [14.5, 14.2, 13.8, 13.5, 13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [14.2, 13.8, 13.5, 13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [13.8, 13.5, 13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [13.5, 13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [13.0, 12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [12.5, 12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [12.0, 11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [11.7, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5],
            [11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5, 11.5]
        ]
    
    def _create_wgdc_base_map(self):
        """Create wastegate duty cycle base map"""
        return [
            [30, 32, 35, 38, 42, 48, 55, 62, 68, 72, 75, 78, 80, 80, 80, 80],
            [32, 34, 37, 40, 44, 50, 57, 64, 70, 74, 77, 79, 80, 80, 80, 80],
            [34, 36, 39, 42, 46, 52, 59, 66, 72, 76, 78, 80, 80, 80, 80, 80],
            [36, 38, 41, 44, 48, 54, 61, 68, 74, 77, 79, 80, 80, 80, 80, 80],
            [38, 40, 43, 46, 50, 56, 63, 70, 75, 78, 80, 80, 80, 80, 80, 80],
            [40, 42, 45, 48, 52, 58, 65, 71, 76, 79, 80, 80, 80, 80, 80, 80],
            [42, 44, 47, 50, 54, 60, 67, 73, 77, 79, 80, 80, 80, 80, 80, 80],
            [44, 46, 49, 52, 56, 62, 68, 74, 78, 80, 80, 80, 80, 80, 80, 80],
            [46, 48, 51, 54, 58, 64, 70, 75, 78, 80, 80, 80, 80, 80, 80, 80],
            [48, 50, 53, 56, 60, 66, 71, 76, 79, 80, 80, 80, 80, 80, 80, 80],
            [50, 52, 55, 58, 62, 67, 72, 77, 79, 80, 80, 80, 80, 80, 80, 80],
            [52, 54, 57, 60, 64, 69, 74, 78, 80, 80, 80, 80, 80, 80, 80, 80],
            [54, 56, 59, 62, 66, 71, 75, 78, 80, 80, 80, 80, 80, 80, 80, 80],
            [56, 58, 61, 64, 68, 72, 76, 79, 80, 80, 80, 80, 80, 80, 80, 80],
            [58, 60, 63, 66, 70, 74, 77, 79, 80, 80, 80, 80, 80, 80, 80, 80],
            [60, 62, 65, 68, 72, 75, 78, 80, 80, 80, 80, 80, 80, 80, 80, 80]
        ]
    
    def _create_rev_limiters(self):
        """Create rev limiter settings"""
        return {
            'soft_limit': 6700,
            'fuel_cut_limit': 6800,
            'launch_control_limit': 4500,
            'flat_shift_limit': 6500,
            'overrev_protection': 7200
        }
    
    def _create_torque_limiters(self):
        """Create torque limiter settings"""
        return {
            'max_engine_torque': 380,
            'max_transmission_torque': 350,
            'per_gear_limits': {
                1: 320, 2: 340, 3: 360, 4: 380, 5: 380, 6: 380
            },
            'torque_reduction_duration': 0.5
        }
    
    def _create_base_dtc_list(self):
        """Create base DTC list"""
        return [
            {'code': 'P0101', 'description': 'Mass Air Flow Circuit Range/Performance'},
            {'code': 'P0128', 'description': 'Coolant Thermostat Malfunction'},
            {'code': 'P0420', 'description': 'Catalyst System Efficiency Below Threshold'},
            {'code': 'P0455', 'description': 'Evaporative Emission System Leak Detected'},
            {'code': 'P2096', 'description': 'Post Catalyst Fuel Trim System Too Lean'}
        ]
    
    def _create_stage1_ignition_advance(self):
        """Create stage 1 ignition advance map"""
        return [
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5],
            [0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5]
        ]
    
    def _create_stage1_boost_increase(self):
        """Create stage 1 boost increase map"""
        return {
            'base_increase': 2.5,
            'rpm_compensation': {
                '2000': 1.0, '3000': 2.0, '4000': 2.5, '5000': 2.5, '6000': 2.0, '7000': 1.5
            },
            'max_boost': 18.0
        }
    
    def _create_k04_compressor_map(self):
        """Create K04 compressor performance map"""
        return {
            'pressure_ratios': [1.5, 1.7, 1.9, 2.1, 2.3, 2.5, 2.7],
            'corrected_speeds': [60000, 80000, 100000, 120000, 140000, 160000],
            'efficiency_map': [
                [0.64, 0.68, 0.72, 0.74, 0.76, 0.77, 0.78],
                [0.62, 0.66, 0.70, 0.73, 0.75, 0.77, 0.78],
                [0.60, 0.64, 0.68, 0.71, 0.74, 