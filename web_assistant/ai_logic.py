from __future__ import annotations

import logging

from openai import OpenAI

from runtime_policy import (
    ResponsePolicyInput,
    StructuredAIResponse,
    build_system_prompt,
    build_user_prompt,
    fallback_response,
    parse_structured_response,
    resolve_response_policy,
    response_to_dict,
)


LOGGER = logging.getLogger(__name__)

CONTACT_LABEL = "phone or email"


class AssistantAI:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def respond(
        self,
        *,
        current_step: str,
        known_fields: dict,
        validation_result: str,
        offscript_count: int,
        last_user_message: str,
        correlation_id: str,
    ) -> StructuredAIResponse:
        policy_input = ResponsePolicyInput(
            current_step=current_step,
            known_fields=known_fields,
            validation_result=validation_result,
            offscript_count=offscript_count,
            last_user_message=last_user_message,
        )
        try:
            system_prompt = build_system_prompt(CONTACT_LABEL)
            user_prompt = build_user_prompt(policy_input, CONTACT_LABEL)
            LOGGER.debug(
                "[web_assistant.ai] Sending structured prompt",
                extra={
                    "step": current_step,
                    "validation_result": validation_result or "none",
                    "session_id": correlation_id,
                    "allowed_contact_format": CONTACT_LABEL,
                },
            )
            response = self._client.responses.create(
                model=self._model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            parsed = parse_structured_response(response.output_text)
            LOGGER.info(
                "[web_assistant.ai] Structured response parsed",
                extra={
                    "step": current_step,
                    "session_id": correlation_id,
                    "intent": parsed.detected_intent,
                    "used_fallback": parsed.used_fallback,
                },
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.error(
                "[web_assistant.ai] Structured model call failed: %s",
                error,
                extra={"step": current_step, "session_id": correlation_id},
            )
            return fallback_response(current_step, validation_result, reason="model_call_failed")

        resolved = resolve_response_policy(policy_input, parsed)
        if resolved.used_fallback:
            LOGGER.warning(
                "[web_assistant.ai] Deterministic fallback activated",
                extra={
                    "step": current_step,
                    "session_id": correlation_id,
                    "fallback_reason": resolved.fallback_reason,
                },
            )
        else:
            LOGGER.debug(
                "[web_assistant.ai] Structured policy resolved",
                extra={
                    "step": current_step,
                    "session_id": correlation_id,
                    "policy": response_to_dict(resolved),
                },
            )
        return resolved

    def reply(self, step: str, draft: dict, user_text: str, validation_hint: str) -> str:
        response = self.respond(
            current_step=step,
            known_fields=draft,
            validation_result=validation_hint,
            offscript_count=0,
            last_user_message=user_text,
            correlation_id="unknown",
        )
        return response.user_facing_message
