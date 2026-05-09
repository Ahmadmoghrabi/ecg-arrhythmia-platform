package com.ecgplatform.api.model;

public record PredictResponse(
    String prediction,
    int label,
    double confidence,
    Probabilities probabilities
) {
    public record Probabilities(double normal, double arrhythmia) {}
}
