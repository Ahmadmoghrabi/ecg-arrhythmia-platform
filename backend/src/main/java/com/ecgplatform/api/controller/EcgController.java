package com.ecgplatform.api.controller;

import com.ecgplatform.api.model.ClassificationResult;
import com.ecgplatform.api.model.EcgRecord;
import com.ecgplatform.api.service.ClassifierService;
import com.ecgplatform.api.service.EcgService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

@RestController
@RequestMapping("/api/v1")
public class EcgController {

    private final EcgService ecgService;
    private final ClassifierService classifierService;

    public EcgController(EcgService ecgService, ClassifierService classifierService) {
        this.ecgService = ecgService;
        this.classifierService = classifierService;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        boolean classifierUp = classifierService.isHealthy();
        return ResponseEntity
            .status(classifierUp ? 200 : 503)
            .body(Map.of(
                "status", classifierUp ? "ok" : "degraded",
                "classifier", classifierUp ? "up" : "down"
            ));
    }

    /**
     * Register a MIT-BIH record by ID so it can be classified.
     * POST /api/v1/ecg/upload
     * Body: { "recordId": "100", "userId": "user123" }
     *
     * userId will be extracted from JWT token in Day 11.
     * recordId will be replaced by a real file upload + S3 in Day 12.
     */
    @PostMapping("/ecg/upload")
    public ResponseEntity<EcgRecord> upload(@RequestBody Map<String, String> body) {
        String recordId = body.get("recordId");
        String userId   = body.get("userId");

        if (recordId == null || recordId.isBlank()) {
            return ResponseEntity.badRequest().build();
        }
        if (userId == null || userId.isBlank()) {
            return ResponseEntity.badRequest().build();
        }

        EcgRecord saved = ecgService.registerRecord(recordId, userId);
        return ResponseEntity.status(201).body(saved);
    }

    /**
     * Trigger classification for a previously registered ECG record.
     * POST /api/v1/ecg/{id}/classify
     * Body: { "userId": "user123" }
     */
    @PostMapping("/ecg/{id}/classify")
    public ResponseEntity<?> classify(@PathVariable String id,
                                      @RequestBody Map<String, String> body) {
        String userId = body.get("userId");
        if (userId == null || userId.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "userId required"));
        }

        try {
            ClassificationResult result = ecgService.classify(id, userId);
            return ResponseEntity.ok(result);
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(404).body(Map.of("error", e.getMessage()));
        } catch (RuntimeException e) {
            return ResponseEntity.status(502).body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * Fetch the classification results for an ECG record.
     * GET /api/v1/ecg/{id}/results
     */
    @GetMapping("/ecg/{id}/results")
    public ResponseEntity<?> getResults(@PathVariable String id) {
        try {
            return ResponseEntity.ok(ecgService.getResults(id));
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(404).body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * List all ECG records for a user.
     * GET /api/v1/ecg?userId=user123
     */
    @GetMapping("/ecg")
    public List<EcgRecord> listRecords(@RequestParam String userId) {
        return ecgService.listRecords(userId);
    }
}
