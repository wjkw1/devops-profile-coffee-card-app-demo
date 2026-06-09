import hmac
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level cache - warm invocations skip SSM after first call
_CACHED_KEY: str | None = None


def handler(event, context):
    global _CACHED_KEY

    incoming = (event.get("headers") or {}).get("x-api-key", "")
    if not incoming:
        logger.info("Denied: missing x-api-key header")
        return {"isAuthorized": False}

    if _CACHED_KEY is None:
        ssm = boto3.client("ssm")
        param = ssm.get_parameter(
            Name=os.environ["SSM_API_KEY_PATH"],
            WithDecryption=True,
        )
        _CACHED_KEY = param["Parameter"]["Value"]

    assert _CACHED_KEY is not None
    authorized = hmac.compare_digest(incoming, _CACHED_KEY)
    if not authorized:
        logger.info("Denied: invalid api key")
    return {"isAuthorized": authorized}
