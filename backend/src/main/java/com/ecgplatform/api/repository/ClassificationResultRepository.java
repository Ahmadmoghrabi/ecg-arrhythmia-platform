package com.ecgplatform.api.repository;

import com.ecgplatform.api.model.ClassificationResult;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;

public interface ClassificationResultRepository extends MongoRepository<ClassificationResult, String> {
    Optional<ClassificationResult> findByEcgRecordId(String ecgRecordId);
    List<ClassificationResult> findByUserIdOrderByClassifiedAtDesc(String userId);
}
