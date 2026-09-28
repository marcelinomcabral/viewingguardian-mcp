"""
Amazon Bedrock integration for scene analysis.
Falls back gracefully when AWS credentials are not configured.
"""
import os
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

SYSTEM_PROMPT = """You are a child viewing safety analyst. Given a scene
description and a child's profile, return a JSON verdict. Be conservative:
if uncertain, recommend caution. Never guarantee allergen-free or
medically safe content."""

ANALYSIS_PROMPT = """Analyze this scene for a child viewer.

Scene description: {scene_description}
Scene intensity: {intensity}
Scene flags: {flags}

Child age: {age}
Child sensitivities: {sensitivities}
Household rules: {household_rules}

Return ONLY valid JSON with these keys:
- verdict: "safe" | "caution" | "flag" | "skip"
- reason: one sentence explaining the verdict
- recommended_action: "none" | "pause" | "skip_forward" | "suggest_alternative"
- skip_seconds: integer (0 if no skip needed)
"""


async def analyze_scene_with_llm(
    scene_description: str,
    intensity: str,
    flags: list[str],
    profile: dict,
) -> dict:
    """
    Call Bedrock to analyze a scene. Returns a verdict dict.
    Falls back to a rule-based verdict if AWS credentials are unavailable.
    """
    prompt = ANALYSIS_PROMPT.format(
        scene_description=scene_description,
        intensity=intensity,
        flags=", ".join(flags) if flags else "none",
        age=profile.get("age", 10),
        sensitivities=json.dumps(profile.get("sensitivities", {})),
        household_rules=json.dumps(profile.get("household_rules", {})),
    )

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    })

    try:
        response = bedrock.invoke_model(
            body=body,
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
        )
        response_body = json.loads(response["body"].read())
        text = response_body["content"][0]["text"]

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    except NoCredentialsError:
        # No AWS credentials — fall back to rule-based analysis
        return _rule_based_fallback(intensity, flags, profile)

    except (ClientError, json.JSONDecodeError, KeyError):
        # AWS responded with an error — fall back too
        return _rule_based_fallback(intensity, flags, profile)


def _rule_based_fallback(intensity: str, flags: list[str], profile: dict) -> dict:
    """Deterministic verdict from scene metadata. No LLM required."""
    if "jump_scare" in flags:
        return {
            "verdict": "skip",
            "reason": f"Jump scare detected. Not suitable for {profile.get('name', 'child')}.",
            "recommended_action": "skip_forward",
            "skip_seconds": 12,
        }
    if "peril" in flags:
        return {
            "verdict": "flag",
            "reason": "Peril sequence detected.",
            "recommended_action": "skip_forward",
            "skip_seconds": 8,
        }
    if "mild_profanity" in flags:
        return {
            "verdict": "caution",
            "reason": "Mild profanity detected.",
            "recommended_action": "replace_dialogue",
            "skip_seconds": 0,
        }
    if intensity == "high":
        return {
            "verdict": "caution",
            "reason": "High intensity scene.",
            "recommended_action": "pause",
            "skip_seconds": 0,
        }
    return {
        "verdict": "safe",
        "reason": "No flags detected.",
        "recommended_action": "none",
        "skip_seconds": 0,
    }


# ─── Pre-fetch cache ──────────────────────────────────────────────────
_analysis_cache: dict[str, dict] = {}


def cache_analysis(scene_id: str, verdict: dict, ttl: int = 120):
    _analysis_cache[scene_id] = verdict


def get_cached_analysis(scene_id: str) -> dict | None:
    return _analysis_cache.get(scene_id)