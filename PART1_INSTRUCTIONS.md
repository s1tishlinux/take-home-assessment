# Part 1: Pipeline Debugging & Fixes (1 hour)

## Scenario
You've inherited a broken ML deployment pipeline from a previous team member. The pipeline is supposed to deploy a customer churn prediction model, but it's been failing consistently. Your task is to identify and fix all the issues.

## Your Tasks

### 1. Fix the CI/CD Pipeline (30 minutes)
- Review `broken_pipeline.yml` 
- Identify and fix ALL issues
- Create a working version as `fixed_pipeline.yml`

### 2. Fix the Deployment Script (30 minutes)
- Review `model_deployment.py`
- Fix all bugs and security issues
- Add proper error handling and logging
- Create the corrected version as `fixed_deployment.py`

## Deliverables

1. **fixed_pipeline.yml** - Working GitHub Actions workflow
2. **fixed_deployment.py** - Corrected deployment script with proper error handling
3. **requirements_fixed.txt** - Resolved dependency conflicts
4. **FIXES.md** - Document listing each issue found and how you fixed it

## Success Criteria

✅ Pipeline runs without errors  
✅ All security vulnerabilities addressed  
✅ Proper error handling implemented  
✅ Dependencies resolved  
✅ Code follows Python best practices  

## Files Provided

```
broken_files/
├── broken_pipeline.yml       # GitHub Actions workflow with issues
├── model_deployment.py       # Python deployment script with bugs
├── requirements.txt          # Dependencies with conflicts
└── sample_model.pkl          # Mock model file for testing
```

## Common Issues to Look For

- Security vulnerabilities (credentials, permissions)
- Missing error handling
- Dependency conflicts
- Configuration errors
- Poor logging practices
- Missing validation steps

---

**Time Check**: After 1 hour, move to Part 2 regardless of completion status. Document any remaining issues in FIXES.md.
