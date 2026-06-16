# Models

The trained model file (`ecg_classifier.pkl`) is not stored in git due to GitHub's 100 MB file size limit.

To regenerate it, run from the project root:

```bash
cd ml/src && python3 save_model.py
```

This retrains the Random Forest classifier on the MIT-BIH dataset and saves the model to this directory.

**Requires:** MIT-BIH records in `ml/data/mitdb/` (see main [README](../../README.md)).
