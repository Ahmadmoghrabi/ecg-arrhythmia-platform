# Models

The trained model file (ecg_classifier.pkl) is not stored in git due to GitHub's 100MB file size limit.

To regenerate it, run:
    python3 ml-classifier/src/save_model.py

This will retrain the Random Forest classifier on the MIT-BIH dataset and save the model locally.
