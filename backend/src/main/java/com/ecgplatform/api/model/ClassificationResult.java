package com.ecgplatform.api.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@Document(collection = "classification_results")
public class ClassificationResult {

    @Id
    private String id;

    @Indexed
    private String ecgRecordId;

    @Indexed
    private String userId;

    private List<BeatResult> beats;
    private Summary summary;

    @CreatedDate
    private Instant classifiedAt;

    public record BeatResult(
        int sampleIndex,
        String prediction,   // N, S, V, F, Q
        int label,
        double confidence,
        Map<String, Double> probabilities
    ) {}

    public record Summary(
        int totalBeats,
        Map<String, Integer> countsByClass,  // N→count, S→count, etc.
        boolean hasArrhythmia                // true if any non-N beats found
    ) {}

    public ClassificationResult() {}

    public ClassificationResult(String ecgRecordId, String userId,
                                List<BeatResult> beats, Summary summary) {
        this.ecgRecordId = ecgRecordId;
        this.userId = userId;
        this.beats = beats;
        this.summary = summary;
    }

    public String getId() { return id; }
    public String getEcgRecordId() { return ecgRecordId; }
    public String getUserId() { return userId; }
    public List<BeatResult> getBeats() { return beats; }
    public Summary getSummary() { return summary; }
    public Instant getClassifiedAt() { return classifiedAt; }

    public void setId(String id) { this.id = id; }
    public void setEcgRecordId(String ecgRecordId) { this.ecgRecordId = ecgRecordId; }
    public void setUserId(String userId) { this.userId = userId; }
    public void setBeats(List<BeatResult> beats) { this.beats = beats; }
    public void setSummary(Summary summary) { this.summary = summary; }
    public void setClassifiedAt(Instant classifiedAt) { this.classifiedAt = classifiedAt; }
}
