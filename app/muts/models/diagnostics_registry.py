#!/usr/bin/env python3
"""
Diagnostics Capability Template Registry
Manages and provides diagnostics capability templates for all vehicles
"""

from typing import Dict, List, Optional, Type
from muts.models.diagnostics_template import (
    DiagnosticsCapabilityTemplate,
    DiagnosticModule,
    DiagnosticService,
    ServiceCapability,
    ServiceStatus
)


class DiagnosticsTemplateRegistry:
    """Registry for all diagnostics capability templates"""
    
    def __init__(self):
        self.templates: List[DiagnosticsCapabilityTemplate] = []
        self.register_templates()
    
    def register_templates(self):
        """Register all available capability templates"""
        
        # Alfa Romeo Giulietta templates
        self.register_alfa_giulietta_templates()
        
        # Volkswagen templates
        self.register_vw_templates()
        
        # Holden templates
        self.register_holden_templates()
        
        # Default fallback
        self.register_generic_template()
    
    def register_alfa_giulietta_templates(self):
        """Register Alfa Romeo Giulietta templates"""
        self.templates.extend(self._create_alfa_templates())
        
    def register_vw_templates(self):
        """Register Volkswagen templates"""
        self.templates.extend(self._create_vw_templates())
        
    def register_holden_templates(self):
        """Register Holden templates"""
        self.templates.extend(self._create_holden_templates())
        
    def register_generic_template(self):
        """Register a generic template as a fallback"""
        # TO DO: implement generic template registration
        
    def _create_alfa_templates(self) -> List[DiagnosticsCapabilityTemplate]:
        """Create Alfa Romeo diagnostics templates"""
        templates = []
        
        # Alfa Romeo Giulietta (2012, C-Evo platform)
        giulietta = DiagnosticsCapabilityTemplate(
            manufacturer="Alfa Romeo",
            platform="C-Evo",
            model="Giulietta",
            generation="2012",
            year_range=(2012, 2016),
            engine_variants=["1.4T MultiAir", "1.75TBi", "2.0 JTDm"],
            transmission_variants=["6MT", "TCT"]
        )
        
        # Engine ECU - Standard OBD-II with Alfa extensions
        giulietta.add_module(
            module=DiagnosticModule.ENGINE,
            services={
                DiagnosticService.READ_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Standard OBD-II mode 03"
                ),
                DiagnosticService.CLEAR_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Standard OBD-II mode 04"
                ),
                DiagnosticService.LIVE_DATA: ServiceCapability(
                    status=ServiceStatus.LIMITED,
                    reason="Basic OBD-II PIDs only",
                    details={"supported_pids": ["rpm", "speed", "load", "temp", "maf"]}
                ),
                DiagnosticService.FREEZE_FRAME: ServiceCapability(
                    status=ServiceStatus.LIMITED,
                    reason="If available in ECU"
                ),
                DiagnosticService.READINESS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Standard OBD-II monitors"
                ),
                DiagnosticService.CODING: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires Alfa Examiner or MSDS"
                ),
                DiagnosticService.ADAPTATION: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires manufacturer software"
                ),
                DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Not available without Alfa diagnostic tools"
                )
            },
            notes="Engine ECU accessible via OBD-II with Alfa-specific PIDs",
            protocol_info="ISO_15765_4_CAN_11B_500K"
        )
        
        # Transmission - Manual has no TCM
        giulietta.add_module(
            module=DiagnosticModule.TRANSMISSION,
            services={
                DiagnosticService.READ_DTCS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                ),
                DiagnosticService.CLEAR_DTCS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                ),
                DiagnosticService.LIVE_DATA: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                ),
                DiagnosticService.FREEZE_FRAME: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                ),
                DiagnosticService.READINESS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                ),
                DiagnosticService.CODING: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                ),
                DiagnosticService.ADAPTATION: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                ),
                DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Manual transmission has no separate TCM"
                )
            },
            notes="Manual transmission integrated with engine ECU"
        )
        
        # TCT (Twin Clutch Transmission) - Separate TCM
        giulietta_tct = DiagnosticsCapabilityTemplate(
            manufacturer="Alfa Romeo",
            platform="C-Evo",
            model="Giulietta",
            generation="2012",
            year_range=(2012, 2016),
            engine_variants=["1.4T MultiAir", "1.75TBi", "2.0 JTDm"],
            transmission_variants=["TCT"]
        )
        
        giulietta_tct.add_module(
            module=DiagnosticModule.TCM,
            services={
                DiagnosticService.READ_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="TCT DTCs readable via OBD-II"
                ),
                DiagnosticService.CLEAR_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="TCT DTCs clearable via OBD-II"
                ),
                DiagnosticService.LIVE_DATA: ServiceCapability(
                    status=ServiceStatus.LIMITED,
                    reason="Limited TCT parameters available"
                ),
                DiagnosticService.FREEZE_FRAME: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="TCT does not store freeze frames"
                ),
                DiagnosticService.READINESS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="TCT has no readiness monitors"
                ),
                DiagnosticService.CODING: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires Alfa Examiner"
                ),
                DiagnosticService.ADAPTATION: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires manufacturer software"
                ),
                DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Clutch adaptation requires dealer tools"
                )
            },
            notes="TCT control unit accessible but limited without Alfa tools",
            protocol_info="ISO_15765_4_CAN_11B_500K"
        )
        
        # ABS Module
        for template in [giulietta, giulietta_tct]:
            template.add_module(
                module=DiagnosticModule.ABS,
                services={
                    DiagnosticService.READ_DTCS: ServiceCapability(
                        status=ServiceStatus.SUPPORTED,
                        reason="ABS DTCs readable via OBD-II"
                    ),
                    DiagnosticService.CLEAR_DTCS: ServiceCapability(
                        status=ServiceStatus.SUPPORTED,
                        reason="ABS DTCs clearable via OBD-II"
                    ),
                    DiagnosticService.LIVE_DATA: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="ABS live data not accessible via OBD-II"
                    ),
                    DiagnosticService.FREEZE_FRAME: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="ABS does not store freeze frames"
                    ),
                    DiagnosticService.READINESS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="ABS has no readiness monitors"
                    ),
                    DiagnosticService.CODING: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="Requires manufacturer tools"
                    ),
                    DiagnosticService.ADAPTATION: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="Requires dealer equipment"
                    ),
                    DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="ABS bleeding requires special tools"
                    )
                },
                notes="Basic ABS diagnostics via OBD-II",
                protocol_info="ISO_15765_4_CAN_11B_500K"
            )
            
            # SRS/Airbag Module
            template.add_module(
                module=DiagnosticModule.SRS,
                services={
                    DiagnosticService.READ_DTCS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    ),
                    DiagnosticService.CLEAR_DTCS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    ),
                    DiagnosticService.LIVE_DATA: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    ),
                    DiagnosticService.FREEZE_FRAME: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    ),
                    DiagnosticService.READINESS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    ),
                    DiagnosticService.CODING: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    ),
                    DiagnosticService.ADAPTATION: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    ),
                    DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="SRS requires Alfa Examiner or MSDS"
                    )
                },
                notes="Airbag module locked to manufacturer tools",
                protocol_info="Proprietary Alfa protocol"
            )
            
            # BCM Module
            template.add_module(
                module=DiagnosticModule.BCM,
                services={
                    DiagnosticService.READ_DTCS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    ),
                    DiagnosticService.CLEAR_DTCS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    ),
                    DiagnosticService.LIVE_DATA: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    ),
                    DiagnosticService.FREEZE_FRAME: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    ),
                    DiagnosticService.READINESS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    ),
                    DiagnosticService.CODING: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    ),
                    DiagnosticService.ADAPTATION: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    ),
                    DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                        status=ServiceStatus.NOT_SUPPORTED,
                        reason="BCM requires manufacturer-level access"
                    )
                },
                notes="Body control locked to manufacturer tools",
                protocol_info="Proprietary Alfa protocol"
            )
        
        templates.extend([giulietta, giulietta_tct])
        return templates
    def _create_vw_templates(self) -> List[DiagnosticsCapabilityTemplate]:
        """Create Volkswagen diagnostics templates"""
        templates = []
        
        # VW Golf Mk6 (2011, A6 platform)
        golf_mk6 = DiagnosticsCapabilityTemplate(
            manufacturer="Volkswagen",
            platform="A6",
            model="Golf",
            generation="Mk6",
            year_range=(2010, 2013)
        )
        
        # Engine ECU - MED17
        golf_mk6.add_module(DiagnosticModule.ENGINE, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="VW KWP2000 / UDS",
            notes="MED17 ECU, 1.4 TSI engine"
        ))
        
        # Transmission - DSG DQ200
        golf_mk6.add_module(DiagnosticModule.TCM, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="VW KWP2000",
            notes="7-speed DSG DQ200"
        ))
        
        # ABS - ESP MK60
        golf_mk6.add_module(DiagnosticModule.ABS, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="VW KWP2000",
            notes="ESP MK60 system"
        ))
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="DSG does not store freeze frames"
                ),
                DiagnosticService.READINESS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="DSG has no readiness monitors"
                ),
                DiagnosticService.CODING: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires VCDS"
                ),
                DiagnosticService.ADAPTATION: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires VCDS"
                ),
                DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="DSG adaptations require VCDS"
                )
            },
            notes="DSG mechatronics accessible but limited",
            protocol_info="VW CAN gateway"
        )
        
        templates.extend([vw_pq35, vw_pq35_dsg])
        
        # VW Golf MQB (Mk7/Mk7.5) - similar structure but UDS protocol
        vw_mqb = DiagnosticsCapabilityTemplate(
            manufacturer="Volkswagen",
            platform="MQB",
            model="Golf",
            generation="Mk7/Mk7.5",
            year_range=(2012, 2020),
            transmission_variants=["Manual", "DSG"]
        )
        
        # Copy similar capabilities but note UDS protocol differences
        vw_mqb.add_module(
            module=DiagnosticModule.ENGINE,
            services={
                DiagnosticService.READ_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="UDS protocol with VW extensions"
                ),
                DiagnosticService.CLEAR_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="UDS diagnostic services"
                ),
                DiagnosticService.LIVE_DATA: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Enhanced data via UDS"
                ),
                DiagnosticService.FREEZE_FRAME: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Full freeze frame support"
                ),
                DiagnosticService.READINESS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="OBD-II monitors"
                ),
                DiagnosticService.CODING: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires ODIS or VCDS"
                ),
                DiagnosticService.ADAPTATION: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires ODIS or VCDS"
                ),
                DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires ODIS or VCDS"
                )
            },
            notes="MQB platform uses UDS diagnostic protocol",
            protocol_info="ISO_14229_1_2013 (UDS)"
        )
        
        templates.append(vw_mqb)
        return templates
    
    def _create_holden_templates(self) -> List[DiagnosticsCapabilityTemplate]:
        """Create Holden Commodore diagnostics templates"""
        templates = []
        
        # Holden VT/VX/VY/VZ (pre-CAN)
        holden_early = DiagnosticsCapabilityTemplate(
            manufacturer="Holden",
            model="Commodore",
            generation="VT/VX/VY/VZ",
            year_range=(1997, 2006),
            transmission_variants=["Manual", "Auto"]
        )
        
        holden_early.add_module(
            module=DiagnosticModule.ENGINE,
            services={
                DiagnosticService.READ_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="VPW protocol DTCs readable"
                ),
                DiagnosticService.CLEAR_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="VPW protocol DTCs clearable"
                ),
                DiagnosticService.LIVE_DATA: ServiceCapability(
                    status=ServiceStatus.LIMITED,
                    reason="Limited VPW data stream"
                ),
                DiagnosticService.FREEZE_FRAME: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="VPW protocol does not support freeze frames"
                ),
                DiagnosticService.READINESS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Basic OBD-II monitors"
                ),
                DiagnosticService.CODING: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires Tech2"
                ),
                DiagnosticService.ADAPTATION: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires Tech2"
                ),
                DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires Tech2"
                )
            },
            notes="VPW protocol with limited capabilities",
            protocol_info="SAE_J1850_VPW"
        )
        
        # Holden VE/VF (CAN)
        holden_can = DiagnosticsCapabilityTemplate(
            manufacturer="Holden",
            model="Commodore",
            generation="VE/VF",
            year_range=(2006, 2017),
            transmission_variants=["Manual", "Auto"]
        )
        
        holden_can.add_module(
            module=DiagnosticModule.ENGINE,
            services={
                DiagnosticService.READ_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="GMLAN protocol DTCs readable"
                ),
                DiagnosticService.CLEAR_DTCS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="GMLAN protocol DTCs clearable"
                ),
                DiagnosticService.LIVE_DATA: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Enhanced GMLAN data stream"
                ),
                DiagnosticService.FREEZE_FRAME: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="Freeze frame supported on CAN"
                ),
                DiagnosticService.READINESS: ServiceCapability(
                    status=ServiceStatus.SUPPORTED,
                    reason="OBD-II monitors supported"
                ),
                DiagnosticService.CODING: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires GDS2"
                ),
                DiagnosticService.ADAPTATION: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires GDS2"
                ),
                DiagnosticService.SERVICE_FUNCTIONS: ServiceCapability(
                    status=ServiceStatus.NOT_SUPPORTED,
                    reason="Requires GDS2"
                )
            },
            notes="GMLAN protocol with enhanced capabilities",
            protocol_info="GMLAN CAN"
        )
        
        templates.extend([holden_early, holden_can])
        return templates
    
    def find_template(self, manufacturer: str, platform: Optional[str] = None,
                     model: Optional[str] = None, generation: Optional[str] = None,
                     year: Optional[int] = None, engine: Optional[str] = None,
                     transmission: Optional[str] = None) -> Optional[DiagnosticsCapabilityTemplate]:
        """Find the best matching template for a vehicle"""
        matching_templates = []
        
        for template in self.templates:
            if template.matches_vehicle(
                manufacturer=manufacturer,
                platform=platform,
                model=model,
                generation=generation,
                year=year,
                engine=engine,
                transmission=transmission
            ):
                matching_templates.append(template)
        
        # Return the most specific match (prioritize more specific templates)
        if not matching_templates:
            return None
        
        # Sort by specificity (more criteria = more specific)
        def specificity_score(t):
            score = 0
            if t.platform: score += 1
            if t.model: score += 1
            if t.generation: score += 1
            if t.year_range: score += 1
            if t.engine_variants: score += 1
            if t.transmission_variants: score += 1
            return score
        
        return max(matching_templates, key=specificity_score)
    
    def get_all_templates(self) -> List[DiagnosticsCapabilityTemplate]:
        """Get all registered templates"""
        return self.templates.copy()


# Global registry instance
template_registry = DiagnosticsTemplateRegistry()
