# Research Engine Specification

## Architecture
```mermaid
graph TD
  A[User Query] --> B(Query Analysis)
  B --> C[Web Search]
  B --> D[Internal Knowledge]
  C --> E[Result Aggregation]
  D --> E
  E --> F[Response Generation]
```
