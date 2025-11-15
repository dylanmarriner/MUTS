# agents.md
This file describes all agents in the MUTS ecosystem.

## Overview
The MUTS architecture includes a set of specialized agents that work together:
- ECUCommsAgent
- DiagnosticsAgent
- TuningAgent
- SafetyAgent
- FlashAgent
- LogAnalysisAgent
- TorqueAdvisorAgent
- SWASAgent
- UIOrchestratorAgent

## Agents

### 1. ECUCommsAgent
Handles communication via J2534, ISO-TP, UDS, KWP2000.

### 2. DiagnosticsAgent
Runs full system scans, retrieves DTCs, freeze frames.

### 3. TuningAgent
Evaluates and edits tuning profiles, ensures safe configuration.

### 4. SafetyAgent
Enforces safety_limits.yml, blocks invalid flashes or dangerous tunes.

### 5. FlashAgent
Manages ECU flashing, rollback, verification, checksum patching.

### 6. LogAnalysisAgent
Processes driving logs, dyno calculations, torque predictions.

### 7. TorqueAdvisorAgent
Suggests per-gear torque limits based on logs.

### 8. SWASAgent
Manages steering-angle-based torque reduction.

### 9. UIOrchestratorAgent
Coordinates updates between backend agents and the GUI.
