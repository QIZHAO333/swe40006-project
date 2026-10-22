"""Offline release-gate checks: no AWS or website access."""

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.deploy import deploy, validate_config, verify_health


@pytest.fixture
def config():
    return {
        "AWS_REGION": "ap-southeast-2",
        "EC2_INSTANCE_ID": "i-0123456789abcdef0",
        "IMAGE_REFERENCE": "sadmannooh/studyboard@sha256:" + "a" * 64,
        "DEPLOYMENT_URL": "http://staging.example",
        "EXPECTED_ENV": "staging",
        "EXPECTED_SHA": "b" * 40,
    }


def test_accepts_digest_configuration(config):
    validate_config(config)


@pytest.mark.parametrize("value", ["sadmannooh/studyboard:latest", "x; echo bad"])
def test_rejects_mutable_or_invalid_image(config, value):
    config["IMAGE_REFERENCE"] = value
    with pytest.raises(ValueError, match="digest"):
        validate_config(config)


def test_ssm_uses_exact_digest_and_waits_for_success(config):
    with patch("scripts.deploy.aws") as aws:
        aws.side_effect = [
            {"Command": {"CommandId": "command-1"}},
            {"Status": "Success", "ResponseCode": 0},
        ]
        deploy(config)
    parameters = aws.call_args_list[0].args[-1]
    assert config["IMAGE_REFERENCE"] in json.loads(parameters)["commands"][0]
    assert aws.call_count == 2


def test_failed_ssm_blocks_release(config):
    with patch("scripts.deploy.aws") as aws:
        aws.side_effect = [
            {"Command": {"CommandId": "command-1"}},
            {"Status": "Failed", "ResponseCode": 1},
        ]
        with pytest.raises(RuntimeError, match="failed"):
            deploy(config)


@pytest.mark.parametrize("field,value", [("sha", "old"), ("env", "production")])
def test_wrong_version_or_environment_blocks_release(config, field, value):
    health = {
        "status": "ok", "database": "ok", "env": "staging",
        "sha": config["EXPECTED_SHA"],
    }
    health[field] = value
    response = MagicMock()
    response.status = 200
    with (
        patch("scripts.deploy.urlopen") as urlopen,
        patch("scripts.deploy.json.load", return_value=health),
        patch("scripts.deploy.time.sleep"),
    ):
        urlopen.return_value.__enter__.return_value = response
        with pytest.raises(RuntimeError, match="verification failed"):
            verify_health(config)


def test_healthy_correct_version_passes(config):
    response = MagicMock()
    response.status = 200
    health = {
        "status": "ok", "database": "ok", "env": "staging",
        "sha": config["EXPECTED_SHA"],
    }
    with (
        patch("scripts.deploy.urlopen") as urlopen,
        patch("scripts.deploy.json.load", return_value=health),
    ):
        urlopen.return_value.__enter__.return_value = response
        verify_health(config)
