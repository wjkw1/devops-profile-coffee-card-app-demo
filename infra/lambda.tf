resource "aws_lambda_function" "api" {
  function_name = "${var.app_name}-api-${var.environment}"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  # Bootstrapped by CI/CD: terraform apply -target=aws_ecr_repository.api,
  # push an image, then run full terraform apply.
  image_uri   = "${aws_ecr_repository.api.repository_url}:latest"
  timeout     = 30
  memory_size = 1024

  architectures = ["arm64"]

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      APP_ENV    = var.environment
      TABLE_NAME = aws_dynamodb_table.this.name
      LOG_LEVEL  = "DEBUG"
    }
  }

  # image_uri is managed by CI/CD via `aws lambda update-function-code`
  lifecycle {
    ignore_changes = [image_uri]
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]

  tags = {
    Name        = "${var.app_name}-api-${var.environment}"
    Environment = var.environment
  }
}
