package com.ecgplatform.api.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

/**
 * Metadata for an uploaded ECG file. The raw signal is stored in S3;
 * this document holds the pointer and processing status.
 */
@Document(collection = "ecg_records")
public class EcgRecord {

    @Id
    private String id;

    @Indexed
    private String userId;

    private String s3Key;           // S3 object key for the raw ECG file
    private String filename;        // original uploaded filename
    private String status;          // UPLOADED, PROCESSING, COMPLETED, FAILED
    private String errorMessage;

    @CreatedDate
    private Instant uploadedAt;

    public EcgRecord() {}

    public EcgRecord(String userId, String s3Key, String filename) {
        this.userId = userId;
        this.s3Key = s3Key;
        this.filename = filename;
        this.status = "UPLOADED";
    }

    public String getId() { return id; }
    public String getUserId() { return userId; }
    public String getS3Key() { return s3Key; }
    public String getFilename() { return filename; }
    public String getStatus() { return status; }
    public String getErrorMessage() { return errorMessage; }
    public Instant getUploadedAt() { return uploadedAt; }

    public void setId(String id) { this.id = id; }
    public void setUserId(String userId) { this.userId = userId; }
    public void setS3Key(String s3Key) { this.s3Key = s3Key; }
    public void setFilename(String filename) { this.filename = filename; }
    public void setStatus(String status) { this.status = status; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    public void setUploadedAt(Instant uploadedAt) { this.uploadedAt = uploadedAt; }
}
