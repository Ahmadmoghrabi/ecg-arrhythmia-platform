# AWS Deployment (Day 12+)

Planned cloud architecture for the ECG platform. Not yet implemented.

## Target architecture

```
API Gateway
    │
    ├──► Lambda (auth / orchestration)
    │
    ├──► S3 (ECG file storage — replaces local mitdb path)
    │
    └──► DynamoDB (classification results)
            │
            └──► Python Lambda or container (ML inference)
```

## Planned components

| Service | Purpose |
|---------|---------|
| **S3** | Store uploaded ECG recordings |
| **Lambda** | Trigger classification on upload |
| **DynamoDB** | Persist classification results |
| **API Gateway** | Public HTTPS endpoint |

## Local development

The full stack currently runs locally:

- Flask ML API on port **5001**
- Spring Boot backend on port **8080**
- MongoDB for persistence

See the main [README](../README.md) for setup instructions.

## Next steps

1. Define Terraform/CDK in `aws/infra/`
2. Package ML inference for Lambda in `aws/lambda/`
3. Replace `mitdb.path` file reads with S3 object keys in the backend
4. Migrate MongoDB results schema to DynamoDB (or keep MongoDB Atlas)
