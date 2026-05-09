package com.ecgplatform.api.service;

import com.ecgplatform.api.model.PredictResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

/**
 * Delegates classification to the Python Flask microservice.
 * The Flask service must be running on the configured URL before this can serve requests.
 */
@Service
public class ClassifierService {

    private final RestClient restClient;

    public ClassifierService(@Value("${classifier.url:http://localhost:5000}") String classifierUrl) {
        this.restClient = RestClient.builder().baseUrl(classifierUrl).build();
    }

    @SuppressWarnings("unchecked")
    public PredictResponse classify(List<Double> signal) {
        Map<String, Object> response = restClient.post()
            .uri("/predict")
            .body(Map.of("signal", signal))
            .retrieve()
            .body(Map.class);

        String prediction = (String) response.get("prediction");
        int label = ((Number) response.get("label")).intValue();
        double confidence = ((Number) response.get("confidence")).doubleValue();

        Map<String, Object> proba = (Map<String, Object>) response.get("probabilities");
        double normal = ((Number) proba.get("normal")).doubleValue();
        double arrhythmia = ((Number) proba.get("arrhythmia")).doubleValue();

        return new PredictResponse(prediction, label, confidence,
            new PredictResponse.Probabilities(normal, arrhythmia));
    }

    public boolean isHealthy() {
        try {
            Map<?, ?> response = restClient.get()
                .uri("/health")
                .retrieve()
                .body(Map.class);
            return "ok".equals(response.get("status"));
        } catch (Exception e) {
            return false;
        }
    }
}
