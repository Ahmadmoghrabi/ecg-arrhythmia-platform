package com.ecgplatform.api.service;

import com.ecgplatform.api.model.ClassificationResult;
import com.ecgplatform.api.model.EcgRecord;
import com.ecgplatform.api.repository.ClassificationResultRepository;
import com.ecgplatform.api.repository.EcgRecordRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.NoSuchElementException;

@Service
public class EcgService {

    private final EcgRecordRepository ecgRecordRepository;
    private final ClassificationResultRepository classificationResultRepository;
    private final ClassifierService classifierService;
    private final String mitdbPath;

    public EcgService(
        EcgRecordRepository ecgRecordRepository,
        ClassificationResultRepository classificationResultRepository,
        ClassifierService classifierService,
        @Value("${mitdb.path}") String mitdbPath
    ) {
        this.ecgRecordRepository = ecgRecordRepository;
        this.classificationResultRepository = classificationResultRepository;
        this.classifierService = classifierService;
        this.mitdbPath = mitdbPath;
    }

    /**
     * Register a MIT-BIH record for processing.
     * recordId is a record number like "100", "200" etc.
     * S3 upload replaces this on Day 12.
     */
    public EcgRecord registerRecord(String recordId, String userId) {
        String recordPath = mitdbPath + "/" + recordId;
        EcgRecord ecgRecord = new EcgRecord(userId, recordPath, recordId + ".dat");
        return ecgRecordRepository.save(ecgRecord);
    }

    /**
     * Classify all beats in an EcgRecord and persist the results.
     */
    public ClassificationResult classify(String ecgRecordId, String userId) {
        EcgRecord record = ecgRecordRepository.findById(ecgRecordId)
            .orElseThrow(() -> new NoSuchElementException("ECG record not found: " + ecgRecordId));

        record.setStatus("PROCESSING");
        ecgRecordRepository.save(record);

        try {
            ClassifierService.RecordClassification classification =
                classifierService.classifyRecord(record.getS3Key());

            ClassificationResult result = new ClassificationResult(
                ecgRecordId, userId,
                classification.beats(),
                classification.summary()
            );
            classificationResultRepository.save(result);

            record.setStatus("COMPLETED");
            ecgRecordRepository.save(record);

            return result;

        } catch (Exception e) {
            record.setStatus("FAILED");
            record.setErrorMessage(e.getMessage());
            ecgRecordRepository.save(record);
            throw new RuntimeException("Classification failed: " + e.getMessage(), e);
        }
    }

    public ClassificationResult getResults(String ecgRecordId) {
        return classificationResultRepository.findByEcgRecordId(ecgRecordId)
            .orElseThrow(() -> new NoSuchElementException("No results found for record: " + ecgRecordId));
    }

    public List<EcgRecord> listRecords(String userId) {
        return ecgRecordRepository.findByUserIdOrderByUploadedAtDesc(userId);
    }
}
