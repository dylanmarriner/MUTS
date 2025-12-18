# Coverage Plan to Achieve 100% Code Coverage

## Current Status
- **Overall Coverage**: ~10%
- **Tests Passing**: 88+ tests
- **Target**: 100% coverage

## Module Coverage Status

### Core Modules (core/)
- ✅ `app_state.py`: 88% - Needs error handling paths
- ✅ `safety_validator.py`: 82% - Needs live data validation edge cases
- ⚠️ `rom_verifier.py`: 62% - Needs error handling and edge cases
- ❌ `ecu_communication.py`: 0% - Needs comprehensive tests
- ❌ `connection_monitor.py`: 0% - Needs tests
- ❌ `versa_tuning_core.py`: 0% - Needs tests

### MUTS Modules (muts/)
- ⚠️ `comms/can_interface.py`: 38% - Needs more CAN message handling tests
- ⚠️ `database/ecu_database.py`: 71% - Needs edge cases
- ✅ `database/tuning_database.py`: 100% - Complete
- ❌ `core/main.py`: 17% - Needs comprehensive tests
- ❌ `models/engine_models.py`: 13% - Needs tests
- ❌ `models/turbo_models.py`: 14% - Needs tests
- ❌ `security/seed_key.py`: 27% - Needs tests
- ❌ `services/ai_tuner.py`: 0% - Needs tests (with torch mocking)
- ❌ `services/dealer_service.py`: 0% - Needs tests
- ❌ `services/performance_features.py`: 0% - Needs tests
- ❌ `services/physics_engine.py`: 0% - Needs tests
- ❌ `utils/calculations.py`: 0% - Needs tests
- ❌ `utils/security.py`: 0% - Needs tests (import fixed)

## Testing Strategy

### Phase 1: Complete Core Modules (Priority 1)
1. ✅ app_state.py - Complete remaining 12%
2. ✅ safety_validator.py - Complete remaining 18%
3. ✅ rom_verifier.py - Complete remaining 38%
4. ❌ ecu_communication.py - Create comprehensive tests
5. ❌ connection_monitor.py - Create tests

### Phase 2: Complete Communication & Database (Priority 2)
1. ⚠️ can_interface.py - Complete remaining 62%
2. ⚠️ ecu_database.py - Complete remaining 29%

### Phase 3: Complete Service Modules (Priority 3)
1. ❌ utils/calculations.py - Create tests
2. ❌ utils/security.py - Create tests (fix import issues)
3. ❌ services/queue.py - Already tested, verify coverage
4. ❌ services/*.py - Create tests with proper mocking

### Phase 4: Complete Model & Core Modules (Priority 4)
1. ❌ models/engine_models.py - Create tests
2. ❌ models/turbo_models.py - Create tests
3. ❌ core/main.py - Create tests
4. ❌ security/seed_key.py - Create tests

### Phase 5: Verify 100% Coverage
- Run full coverage report
- Identify any missed lines
- Add edge case tests
- Verify all branches covered

## Test Creation Guidelines

1. **Mock External Dependencies**: Use unittest.mock for torch, can bus, etc.
2. **Test All Code Paths**: Include success, failure, and edge cases
3. **Test Error Handling**: Exception paths, invalid inputs
4. **Test Edge Cases**: Boundary values, null/None inputs
5. **Test Integration**: How modules work together

## Running Coverage Reports

```bash
# Generate coverage report
pytest tests/ --cov=muts --cov=core --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

