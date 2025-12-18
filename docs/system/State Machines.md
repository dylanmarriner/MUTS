# State Machine Diagrams

## Bonding State Machine
```mermaid
stateDiagram-v2
  [*] --> Initializing
  Initializing --> Idle: Initialized
  Idle --> Processing: NewThought
  Processing --> Responding: ThoughtProcessed
  Responding --> Idle: ResponseSent
```
