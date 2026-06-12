# Infrastructure

The infrastructure lives alongside the application code for a couple of reasons. The API Gateway config maps closely to the code, and since the infrastructure is temporary in this project there's no point adding the complexity of a separate repository.

To keep things tidy it all lives under the `infra/` folder.

## What's provisioned

| Resource                   | Notes                                                                                          |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| ECR repository             | Stores the API's container image; lifecycle policy keeps the last 3 tagged + 1 untagged image  |
| Lambda (API)               | Runs the FastAPI app via Mangum, arm64, image-based                                            |
| Lambda (authorizer)        | Validates the `x-api-key` header against an SSM-stored key, 5-minute cache                     |
| API Gateway (HTTP API)     | Fronts the Lambda, routes guarded by the authorizer                                            |
| DynamoDB table             | Single-table design, pay-per-request, point-in-time recovery, encryption at rest               |
| S3 (frontend) + CloudFront | Static SPA hosting with Origin Access Control; CloudFront also proxies `/api/*` to API Gateway |
| S3 (logs)                  | CloudFront/S3 access logs, 30-day lifecycle expiry                                             |
| WAFv2 Web ACL              | Geo-blocks non-NZ traffic, rate-limits `/api/*` (100 req/IP), AWS managed rule groups          |
| SSM Parameter Store        | Holds the shared API key as a SecureString                                                     |
| CloudWatch                 | Log groups (3-day retention) and alarms for Lambda errors/throttles                            |

## Getting started

You'll need **Terraform** installed and an **AWS** IAM user or role with enough permissions to make changes to your account.

ECR is also managed here rather than in a shared account-wide repo like `wjkw1/aws-foundations`, since it's a temporary resource for this project.

> The OIDC roles GitHub Actions assumes to plan/apply this infrastructure and to deploy the app (`github-actions-tf-plan-*`, `github-actions-tf-apply-*`, `github-actions-deploy-*`) are provisioned separately in `wjkw1/aws-foundations`, not here.

### Steps

1. Copy `backend.hcl.example` to `backend.hcl` and point it at an existing S3 bucket for Terraform state.
2. Review `prod.tfvars` / `stage.tfvars` and override `api_key` (via `-var` or `TF_VAR_api_key`) - never commit a real key.
3. Stand up ECR first, before anything else. This is important because the image needs to exist before the rest of the infrastructure can reference it.

   ```zsh
   terraform apply -var-file=prod.tfvars \
     -target=aws_ecr_repository.api \
     -target=aws_ecr_lifecycle_policy.api
   ```

4. Push an image to ECR. You can do this manually or by raising and merging a PR to let GitHub Actions handle it.

   ```zsh
   # run commands inside infra directory
   export REGION=ap-southeast-2
   export ECR_URL_BASE=$(terraform output -json | jq -r '.ecr_repository_url.value | split("/")[0]')
   export ECR_URL_REPO=$(terraform output -json | jq -r '.ecr_repository_url.value')

   aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL_BASE

   # NOTE: uses arm64 config on my machine
   docker build --platform linux/arm64 --provenance=false -t ${ECR_URL_REPO}:latest ../api

   docker push ${ECR_URL_REPO}:latest
   ```

5. From here GitHub Actions can take over and create everything else.

The first time I set this up I ran the full apply locally just to confirm it worked, then let GitHub Actions own it from the second run onwards.

## Outputs

| Output                       | Used for                                                                                                                    |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `cloudfront_domain_name`     | The app's public URL - set as `CLOUDFRONT_DOMAIN_NAME` repo variable (see [root README](../README.md#repository-variables)) |
| `cloudfront_distribution_id` | CloudFront cache invalidation in the frontend deploy pipeline                                                               |
| `ecr_repository_url`         | Where CI pushes the API image                                                                                               |
| `lambda_function_name`       | Used by CI to update the Lambda's image                                                                                     |
| `api_url`                    | Direct API Gateway invoke URL (bypasses CloudFront)                                                                         |
| `dynamodb_table_name`        | DynamoDB table name                                                                                                         |
| `frontend_bucket_name`       | S3 bucket the frontend deploy syncs `dist/` to                                                                              |
