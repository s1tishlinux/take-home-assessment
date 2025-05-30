# Additional Files Needed for Complete Assessment

## Files to Generate Before Sending to Candidates

The assessment references several files that need to be created. Here's what needs to be generated:

### 1. Test Data File
**File**: `test_data.csv`
**Purpose**: Used by `model_deployment.py` for model validation
**Generation**: Run `create_realistic_model.py` to generate both the model and compatible test data

### 2. Model File  
**File**: `model.pkl`
**Purpose**: Trained model used in deployment script
**Generation**: Created by `create_realistic_model.py`

### 3. Missing Configuration Files
Create these additional files to make the assessment more realistic:

#### `config.yml` (referenced in pipeline)
```yaml
model:
  type: "logistic_regression"
  parameters:
    random_state: 42
    max_iter: 1000

training:
  test_size: 0.2
  validation_split: 0.1

deployment:
  min_accuracy_threshold: 0.75
  performance_window: "7d"
```

#### `train_model.py` (referenced in pipeline)
```python
#!/usr/bin/env python3
import sys
print("Mock training completed successfully")
sys.exit(0)
```

#### `validate_model.py` (referenced in pipeline)  
```python
#!/usr/bin/env python3
import sys
print("Model validation passed")
sys.exit(0)
```

## Setup Instructions for Hiring Team

Before sending the assessment to candidates:

1. **Generate the data and model files**:
   ```bash
   cd broken_files/
   python create_realistic_model.py
   ```

2. **Create the mock training files**:
   ```bash
   echo 'import sys; print("Training completed"); sys.exit(0)' > train_model.py
   echo 'import sys; print("Validation passed"); sys.exit(0)' > validate_model.py
   ```

3. **Add config file**:
   ```bash
   echo 'model: {type: logistic_regression}' > config.yml
   ```

4. **Verify all files are present**:
   ```
   broken_files/
   ├── broken_pipeline.yml
   ├── model_deployment.py  
   ├── requirements.txt
   ├── test_data.csv           # Generated
   ├── model.pkl              # Generated  
   ├── train_model.py         # Created
   ├── validate_model.py      # Created
   └── config.yml             # Created
   ```

## Alternative: Simplify the Assessment

If you prefer not to generate additional files, you can modify the broken code to remove these dependencies:

### Option 1: Remove file dependencies
- Remove the `test_data.csv` reference from `model_deployment.py`
- Remove training/validation steps from pipeline
- Focus purely on deployment logic

### Option 2: Mock the dependencies
- Add checks for file existence with fallbacks
- Use in-memory mock data when files are missing
- This tests the candidate's error handling skills

## Recommendation

**Use the complete setup** with all files provided. This gives candidates:
- A realistic working environment
- Ability to test their fixes
- Complete context for the ML pipeline
- Better assessment of their debugging skills

The additional setup time (5 minutes) is worth the improved assessment quality.
