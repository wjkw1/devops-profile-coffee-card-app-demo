# Infrastructure

The infrastructure lives alongside the application code for a couple of reasons. The API Gateway config maps closely to the code, and since the infrastructure is temporary in this project there's no point adding the complexity of a separate repository.

To keep things tidy it all lives under the `infra/` folder.

## Getting started

You'll need **Terraform** installed and an **AWS** IAM user or role with enough permissions to make changes to your account.

ECR is also managed here rather than in a shared account-wide repo like `wjkw1/aws-foundations`, since it's a temporary resource for this project.

### Steps

1. Copy `backend.hcl.example` to `backend.hcl` and point it at an existing S3 bucket for Terraform state.
2. Do the same with `terraform.tfvars.example` to `terraform.tfvars` and fill in the variables.
3. Stand up ECR first, before anything else. This is important because the image needs to exist before the rest of the infrastructure can reference it.

   ```zsh
   terraform apply \
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
