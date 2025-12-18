#!/usr/bin/env python3
"""
Diagnostics Template Registry - Clean version with Holden templates
"""

from typing import List, Optional
from muts.models.diagnostics_template import (
    DiagnosticsCapabilityTemplate,
    DiagnosticModule,
    DiagnosticService,
    ServiceCapability,
    ServiceStatus,
    ModuleCapability
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
        # TODO: implement generic template registration
    
    def _create_alfa_templates(self) -> List[DiagnosticsCapabilityTemplate]:
        """Create Alfa Romeo diagnostics templates"""
        templates = []
        
        # Alfa Romeo Giulietta (2012, C-Evo platform)
        giulietta = DiagnosticsCapabilityTemplate(
            manufacturer="Alfa Romeo",
            platform="C-Evo",
            model="Giulietta",
            generation="2012",
            year_range=(2010, 2020)
        )
        
        # Add modules for Giulietta...
        # (Implementation from existing code)
        
        templates.append(giulietta)
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
        
        # SRS - Airbag
        golf_mk6.add_module(DiagnosticModule.SRS, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="VW KWP2000",
            notes="Airbag control module"
        ))
        
        # BCM - Body control
        golf_mk6.add_module(DiagnosticModule.BCM, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="VW KWP2000",
            notes="Body control module"
        ))
        
        # Cluster - Not supported
        golf_mk6.add_module(DiagnosticModule.CLUSTER, ModuleCapability(
            status=ServiceStatus.NOT_SUPPORTED,
            protocol_info=None,
            notes="Instrument cluster requires special tools"
        ))
        
        templates.append(golf_mk6)
        
        return templates
    
    def _create_holden_templates(self) -> List[DiagnosticsCapabilityTemplate]:
        """Create Holden diagnostics templates"""
        templates = []
        
        # Holden Commodore VF (2013-2017, Zeta platform)
        commodore_vf = DiagnosticsCapabilityTemplate(
            manufacturer="Holden",
            platform="Zeta",
            model="Commodore",
            generation="VF",
            year_range=(2013, 2017)
        )
        
        # Engine ECU - E39A
        commodore_vf.add_module(DiagnosticModule.ENGINE, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="GM GMLAN / ISO9141",
            notes="E39A ECU, 3.0L V6 LFW engine"
        ))
        
        # Transmission - 6L80
        commodore_vf.add_module(DiagnosticModule.TCM, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="GM GMLAN",
            notes="6-speed automatic 6L80"
        ))
        
        # ABS - Bosch 9.0
        commodore_vf.add_module(DiagnosticModule.ABS, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="GM GMLAN",
            notes="Bosch 9.0 ABS/ESP"
        ))
        
        # SRS - Airbag
        commodore_vf.add_module(DiagnosticModule.SRS, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="GM GMLAN",
            notes="Airbag control module SDM"
        ))
        
        # BCM - Body control
        commodore_vf.add_module(DiagnosticModule.BCM, ModuleCapability(
            status=ServiceStatus.SUPPORTED,
            protocol_info="GM GMLAN",
            notes="Body control module"
        ))
        
        # Cluster - Partial support
        commodore_vf.add_module(DiagnosticModule.CLUSTER, ModuleCapability(
            status=ServiceStatus.UNKNOWN,
            protocol_info="GM GMLAN",
            notes="Limited support, basic functions only"
        ))
        
        templates.append(commodore_vf)
        
        return templates
    
    def find_template(self, manufacturer: str, model: str, year: int, 
                     platform: Optional[str] = None) -> Optional[DiagnosticsCapabilityTemplate]:
        """Find the most specific template for a vehicle"""
        # First try exact match
        for template in self.templates:
            if (template.manufacturer == manufacturer and 
                template.model == model and
                template.matches_year(year)):
                return template
        
        # Then try manufacturer + platform match
        if platform:
            for template in self.templates:
                if (template.manufacturer == manufacturer and 
                    template.platform == platform and
                    template.matches_year(year)):
                    return template
        
        # Finally try manufacturer match
        for template in self.templates:
            if template.manufacturer == manufacturer and template.matches_year(year):
                return template
        
        return None


# Create global registry instance
template_registry = DiagnosticsTemplateRegistry()
