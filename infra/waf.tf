# WAFv2 Web ACL must be in us-east-1 for CloudFront scope
#
# Rules use aws_wafv2_web_acl_rule (separate resources) rather than inline rules
# to avoid provider limitations. The ACL resource carries lifecycle { ignore_changes = [rule] }
# to prevent conflicts with the externally-managed rule resources.

resource "aws_wafv2_web_acl" "cloudfront" {
  provider    = aws.us_east_1
  name        = "${var.app_name}-${var.environment}"
  description = "CloudFront WAF geo-block, rate limiting, managed rules"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.app_name}-${var.environment}-waf"
    sampled_requests_enabled   = true
  }

  lifecycle {
    ignore_changes = [rule]
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_wafv2_web_acl_rule" "geo_block" {
  provider    = aws.us_east_1
  name        = "GeoBlockNonNZ"
  web_acl_arn = aws_wafv2_web_acl.cloudfront.arn
  priority    = 0

  statement {
    not_statement {
      statement {
        geo_match_statement {
          country_codes = ["NZ"]
        }
      }
    }
  }

  action {
    block {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.app_name}-geo-block"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_rule" "rate_limit_api" {
  provider    = aws.us_east_1
  name        = "RateLimitAPI"
  web_acl_arn = aws_wafv2_web_acl.cloudfront.arn
  priority    = 1

  statement {
    rate_based_statement {
      limit              = 100
      aggregate_key_type = "IP"

      scope_down_statement {
        byte_match_statement {
          field_to_match {
            uri_path {}
          }
          positional_constraint = "STARTS_WITH"
          search_string         = "/api/"
          text_transformation {
            priority = 0
            type     = "LOWERCASE"
          }
        }
      }
    }
  }

  action {
    block {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.app_name}-rate-limit-api"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_rule" "common_rule_set" {
  provider    = aws.us_east_1
  name        = "AWSManagedRulesCommonRuleSet"
  web_acl_arn = aws_wafv2_web_acl.cloudfront.arn
  priority    = 2

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesCommonRuleSet"
      vendor_name = "AWS"
    }
  }

  override_action {
    none {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.app_name}-crs"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_rule" "known_bad_inputs" {
  provider    = aws.us_east_1
  name        = "AWSManagedRulesKnownBadInputsRuleSet"
  web_acl_arn = aws_wafv2_web_acl.cloudfront.arn
  priority    = 3

  statement {
    managed_rule_group_statement {
      name        = "AWSManagedRulesKnownBadInputsRuleSet"
      vendor_name = "AWS"
    }
  }

  override_action {
    none {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.app_name}-known-bad-inputs"
    sampled_requests_enabled   = true
  }
}
