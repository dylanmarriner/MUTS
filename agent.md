# agent.md
This file defines a single MUTS agent behavior specification.

## Agent Purpose
A MUTS internal agent responsible for performing a discrete domain-specific task such as:
- ECU communication
- Diagnostics
- Tuning recommendations
- Flashing safety checks
- Log analysis

## Required Capabilities
Every agent must:
- Operate autonomously within its domain
- Fail safely with error reporting
- Respect safety_limits.yml
- Log its actions
- Accept structured input and return structured output

## Standard Agent Structure
```python
class Agent:
    def __init__(self, context):
        self.context = context

    def run(self, input):
        raise NotImplementedError()

    def describe(self):
        return "Agent description"
```

## Example
```python
class DiagnosticsAgent(Agent):
    def run(self, ecu):
        return ecu.read_all_dtcs()
```
