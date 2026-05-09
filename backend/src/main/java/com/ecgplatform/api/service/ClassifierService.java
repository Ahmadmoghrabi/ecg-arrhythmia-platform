package com.ecgplatform.api.service;

import com.ecgplatform.api.model.ClassificationResult;
import com.ecgplatform.api.model.ClassificationResult.BeatResult;
import com.ecgplatform.api.model.ClassificationResult.Summary;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Delegates all ML classification to the Python Flask microservice.
 * Flask must be running at classifier.url before requests can be served.
 */
@Service
public class ClassifierService {

    private final RestClient restClient;

    public ClassifierService(@Value("${classifier.url:http://localhost:5001}") String classifierUrl) {
        this.restClient = RestClient.builder().baseUrl(classifierUrl).build();
    }

    public boolean isHealthy() {
        try {
            Map<?, ?> response = restClient.get().uri("/health").retrieve().body(Map.class);
            return "ok".equals(response.get("status"));
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Classify every beat in a WFDB record.
     * recordPath is the absolute path to the record without file extension.
     */
    @SuppressWarnings("unchecked")
    public RecordClassification classifyRecord(String recordPath) {
        Map<String, Object> response = restClient.post()
            .uri("/classify/record")
            .body(Map.of("record_path", recordPath))
            .retrieve()
            .body(Map.class);

        List<Map<String, Object>> rawBeats = (List<Map<String, Object>>) response.get("beats");
        Map<String, Object> rawSummary = (Map<String, Object>) response.get("summary");

        List<BeatResult> beats = rawBeats.stream().map(b -> new BeatResult(
            ((Number) b.get("sampleIndex")).intValue(),
            (String) b.get("prediction"),
            ((Number) b.get("label")).intValue(),
            ((Number) b.get("confidence")).doubleValue(),
            ((Map<String, Number>) b.get("probabilities")).entrySet().stream()
                .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().doubleValue()))
        )).collect(Collectors.toList());

        Map<String, Integer> counts = ((Map<String, Number>) rawSummary.get("countsByClass"))
            .entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().intValue()));

        Summary summary = new Summary(
            ((Number) rawSummary.get("totalBeats")).intValue(),
            counts,
            (Boolean) rawSummary.get("hasArrhythmia")
        );

        return new RecordClassification(beats, summary);
    }

    public record RecordClassification(List<BeatResult> beats, Summary summary) {}
}
