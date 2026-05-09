package com.ecgplatform.api.controller;

import com.ecgplatform.api.model.PredictRequest;
import com.ecgplatform.api.model.PredictResponse;
import com.ecgplatform.api.service.ClassifierService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1")
public class EcgController {

    private final ClassifierService classifierService;

    public EcgController(ClassifierService classifierService) {
        this.classifierService = classifierService;
    }

    @PostMapping("/classify")
    public PredictResponse classify(@Valid @RequestBody PredictRequest request) {
        return classifierService.classify(request.signal());
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        boolean classifierUp = classifierService.isHealthy();
        Map<String, Object> body = Map.of(
            "status", classifierUp ? "ok" : "degraded",
            "classifier", classifierUp ? "up" : "down"
        );
        return classifierUp
            ? ResponseEntity.ok(body)
            : ResponseEntity.status(503).body(body);
    }
}
