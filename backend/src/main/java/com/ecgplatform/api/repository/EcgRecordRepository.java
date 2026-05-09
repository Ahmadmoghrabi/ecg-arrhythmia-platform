package com.ecgplatform.api.repository;

import com.ecgplatform.api.model.EcgRecord;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface EcgRecordRepository extends MongoRepository<EcgRecord, String> {
    List<EcgRecord> findByUserIdOrderByUploadedAtDesc(String userId);
    List<EcgRecord> findByUserIdAndStatus(String userId, String status);
}
