# ─── API Key stored in SSM Parameter Store ───────────────────────────────────
# Value is never hardcoded here — pass -var="api_key=..." in CI/CD or via
# TF_VAR_api_key environment variable. Stored as SecureString (AES-256 via
# the default aws/ssm KMS managed key).

resource "aws_ssm_parameter" "api_key" {
  name  = "/${var.app_name}/${var.environment}/api-key"
  type  = "SecureString"
  value = var.api_key

  tags = {
    Name        = "${var.app_name}-${var.environment}-api-key"
    Environment = var.environment
  }
}

# ─── Zip the authorizer source for Lambda ────────────────────────────────────
# archive_file generates the zip at plan/apply time from the committed source
# file — no separate build step needed. Output goes to build/ (gitignored).

data "archive_file" "authorizer" {
  type        = "zip"
  source_file = "${path.module}/lambda_authorizer.py"
  output_path = "${path.module}/build/lambda_authorizer.zip"
}

# ─── IAM Role for the Authorizer Lambda ──────────────────────────────────────

data "aws_iam_policy_document" "authorizer_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "authorizer" {
  name               = "${var.app_name}-${var.environment}-authorizer"
  assume_role_policy = data.aws_iam_policy_document.authorizer_assume_role.json

  tags = {
    Name        = "${var.app_name}-${var.environment}-authorizer"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "authorizer_basic_execution" {
  role       = aws_iam_role.authorizer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "authorizer_ssm" {
  statement {
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.api_key.arn]
    # Using the default aws/ssm managed key so no kms:Decrypt needed here.
    # Switch to a CMK and add kms:Decrypt for that key ARN for stricter control.
  }
}

resource "aws_iam_role_policy" "authorizer_ssm" {
  name   = "ssm-read-api-key"
  role   = aws_iam_role.authorizer.id
  policy = data.aws_iam_policy_document.authorizer_ssm.json
}

# ─── Authorizer Lambda Function ───────────────────────────────────────────────

resource "aws_lambda_function" "authorizer" {
  function_name    = "${var.app_name}-api-${var.environment}-authorizer"
  role             = aws_iam_role.authorizer.arn
  filename         = data.archive_file.authorizer.output_path
  source_code_hash = data.archive_file.authorizer.output_base64sha256
  handler          = "lambda_authorizer.handler"
  runtime          = "python3.12"

  environment {
    variables = {
      SSM_API_KEY_PATH = aws_ssm_parameter.api_key.name
    }
  }

  tags = {
    Name        = "${var.app_name}-api-${var.environment}-authorizer"
    Environment = var.environment
  }
}

resource "aws_lambda_permission" "authorizer_api_gateway" {
  statement_id  = "AllowAPIGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*"
}

# ─── Attach Authorizer to HTTP API ────────────────────────────────────────────

resource "aws_apigatewayv2_authorizer" "api_key" {
  api_id          = aws_apigatewayv2_api.this.id
  authorizer_type = "REQUEST"
  authorizer_uri  = aws_lambda_function.authorizer.invoke_arn
  name            = "api-key"

  # API Gateway caches the allow/deny result per unique x-api-key value for
  # the TTL — the authorizer Lambda only runs on cache misses, not every request.
  identity_sources                  = ["$request.header.x-api-key"]
  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = true
  authorizer_result_ttl_in_seconds  = 300
}
