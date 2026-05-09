package com.ecgplatform.api.controller;

import com.ecgplatform.api.model.ClassificationResult;
import com.ecgplatform.api.model.EcgRecord;
import com.ecgplatform.api.service.ClassifierService;
import com.ecgplatform.api.service.EcgService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
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
     * Register a MIT-BIH record for classification.
     * POST /api/v1/ecg/upload
     * Header: Authorization: Bearer <token>
     * Body: { "recordId": "100" }
     */
    @PostMapping("/ecg/upload")
    public ResponseEntity<?> upload(@RequestBody Map<String, String> body,
                                    Authentication auth) {
        String recordId = body.get("recordId");
        if (recordId == null || recordId.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "recordId required"));
        }
        String userId = (String) auth.getPrincipal();
        EcgRecord saved = ecgService.registerRecord(recordId, userId);
        return ResponseEntity.status(201).body(saved);
    }

    /**
     * Trigger classification for a registered ECG record.
     * POST /api/v1/ecg/{id}/classify
     * Header: Authorization: Bearer <token>
     */
    @PostMapping("/ecg/{id}/classify")
    public ResponseEntity<?> classify(@PathVariable String id, Authentication auth) {
        String userId = (String) auth.getPrincipal();
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
     * Fetch classification results for an ECG record.
     * GET /api/v1/ecg/{id}/results
     * Header: Authorization: Bearer <token>
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
     * List all ECG records for the authenticated user.
     * GET /api/v1/ecg
     * Header: Authorization: Bearer <token>
     */
    @GetMapping("/ecg")
    public List<EcgRecord> listRecords(Authentication auth) {
        String userId = (String) auth.getPrincipal();
        return ecgService.listRecords(userId);
    }
}
