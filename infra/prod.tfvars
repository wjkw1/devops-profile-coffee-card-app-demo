aws_region         = "ap-southeast-2"
app_name           = "coffee-card"
environment        = "prod"
cors_allow_origins = ["*"]
api_key            = "EXAMPLE_API_KEY" # Override via TF_VAR_api_key or -var in CI/CD; never hardcode in real usage!
