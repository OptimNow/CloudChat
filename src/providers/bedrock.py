import enum
import warnings
import logging
import os
from typing import TYPE_CHECKING, Any, Optional

import boto3
from botocore.config import Config
from langchain_aws.chat_models import ChatBedrockConverse

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
else:
    BedrockRuntimeClient = object

from src.utils.models import (
    BOTO3_CLIENT_WARNING,
    InferenceConfig,
    ModelId,
    ThinkingConfig,
)

_logger = logging.getLogger(__name__)

class AwsLoginStrategyEnum(enum.StrEnum):
    """AWS login strategies."""
    AWS_SSO = 'aws_sso'
    AWS_KEYS = 'aws_keys'
    AWS_IAM_ROLE = 'aws_iam_role'

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_LOGIN_STRATEGY = os.getenv('AWS_LOGIN_STRATEGY', 'aws_keys').lower()

# SSO Profile-baed access
AWS_PROFILE = os.getenv('AWS_PROFILE', '')

# Key-based access
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN', '')

if AWS_LOGIN_STRATEGY not in {e.value for e in AwsLoginStrategyEnum}:
    raise ValueError(f"Invalid AWS_LOGIN_STRATEGY: {AWS_LOGIN_STRATEGY}")

if AWS_LOGIN_STRATEGY == AwsLoginStrategyEnum.AWS_KEYS:
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_SESSION_TOKEN:
        raise ValueError("AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN must be set for AWS_KEYS login strategy")

    os.environ.pop('AWS_PROFILE', None)
    os.environ.pop('AWS_BEARER_TOKEN_BEDROCK', None)

if AWS_LOGIN_STRATEGY == AwsLoginStrategyEnum.AWS_SSO:
    if not AWS_PROFILE:
        raise ValueError("AWS_PROFILE must be set for AWS_SSO login strategy")

    # Clear other AWS credentials to avoid conflicts
    os.environ.pop('AWS_ACCESS_KEY_ID', None)
    os.environ.pop('AWS_SECRET_ACCESS_KEY', None)
    os.environ.pop('AWS_SESSION_TOKEN', None)

    os.environ.pop('AWS_BEARER_TOKEN_BEDROCK', None)

def get_bedrock_client(region_name: str = AWS_REGION) -> BedrockRuntimeClient:
    """Get a Bedrock client.

    Uses a custom config with retries and read timeout.

    Config is used to set the following:
    - retries: max_attempts=5, mode='adaptive'
    - read_timeout=60

    Returns:
        BedrockRuntimeClient: Bedrock client
    """
    session = None
    if AWS_LOGIN_STRATEGY == AwsLoginStrategyEnum.AWS_SSO:
        _logger.info("Using SSO Profile-based authentication with AWS Bedrock")
        session = boto3.Session(
            region_name=region_name,
            profile_name=AWS_PROFILE,
        )

    if AWS_LOGIN_STRATEGY == AwsLoginStrategyEnum.AWS_KEYS:
        _logger.info("Using AWS keys for authentication with AWS Bedrock")
        session = boto3.Session(
            region_name=region_name,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_session_token=AWS_SESSION_TOKEN,
        )

    if AWS_LOGIN_STRATEGY == AwsLoginStrategyEnum.AWS_IAM_ROLE:
        _logger.info("Using IAM Role for authentication with AWS Bedrock")
        session = boto3.Session(
            region_name=region_name,
        )

    bedrock_client = session.client(
        'bedrock-runtime',
        config=Config(
            retries={'max_attempts': 10, 'mode': 'adaptive'},
            read_timeout=60,
        ),
    )

    return bedrock_client

def get_chat_model(
    model_id: ModelId,
    inference_config: InferenceConfig | None = None,
    client: BedrockRuntimeClient | None = None,
    boto3_kwargs: dict[str, Any] | None = None,
    cross_region: bool = False,
    thinking_config: Optional[ThinkingConfig] = None,
) -> ChatBedrockConverse:
    """Get a ChatBedrockConverse model.

    Args:
        model_id (ModelId): Model ID
        inference_config (InferenceConfig | None): Inference config
        client (BedrockRuntimeClient | None): Bedrock client
        boto3_kwargs (dict[str, Any] | None): Keyword arguments for boto3
        cross_region (bool): Whether to use cross-region inference (default: True)
        thinking_config (ThinkingConfig | None): Thinking config

    Returns:
        ChatBedrockConverse: ChatBedrockConverse model
    """
    # Add cross-region prefix if necessary and convert Enum to string
    _model_id = f'us.{model_id.value}' if cross_region else model_id.value
    if client and boto3_kwargs:
        warnings.warn(BOTO3_CLIENT_WARNING)
    _client = client or get_bedrock_client(**(boto3_kwargs or {}))

    additional_model_request_fields = {}
    # Add thinking config if provided
    if thinking_config:
        additional_model_request_fields['thinking'] = thinking_config.model_dump()

    # Create the ChatBedrockConverse with appropriate parameters
    if inference_config is None:
        return ChatBedrockConverse(
            model=_model_id,
            client=_client,
            additional_model_request_fields=additional_model_request_fields,
        )

    # If inference_config is provided, include temperature and max_tokens
    return ChatBedrockConverse(
        model=_model_id,
        client=_client,
        temperature=inference_config.temperature,
        max_tokens=inference_config.max_tokens,
        additional_model_request_fields=additional_model_request_fields,
    )
