import re
from app.schemas.router import SafetyCheckResult

# Saudi Emergency Guidelines (Red Flag Symptoms)
EMERGENCY_KEYWORDS = [
    "chest pain", "pressure in chest", "shortness of breath", "difficulty breathing",
    "stroke", "numbness on one side", "severe bleeding", "unconscious", "fainting",
    "coughing blood", "anaphylaxis", "severe allergic reaction", "ألم في الصدر", "ضيق في التنفس"
]

OUT_OF_SCOPE_KEYWORDS = [
    "crypto", "bitcoin", "recipe", "python code", "write a essay", "politics", "stocks"
]


class GuardrailService:
    def evaluate(self, message: str) -> SafetyCheckResult:
        msg_lower = message.lower().strip()

        # 1. Emergency Detection
        for kw in EMERGENCY_KEYWORDS:
            if kw in msg_lower:
                return SafetyCheckResult(
                    is_safe=False,
                    trigger_reason="Emergency medical symptom detected",
                    is_emergency=True,
                    should_escalate=True
                )

        # 2. Explicit Human Escalation Request
        if any(term in msg_lower for term in ["agent", "human", "representative", "speak to someone", "إنسان", "موظف"]):
            return SafetyCheckResult(
                is_safe=True,
                trigger_reason="User explicitly requested human transfer",
                is_emergency=False,
                should_escalate=True
            )

        # 3. Out-of-Scope / Misuse Detection
        for kw in OUT_OF_SCOPE_KEYWORDS:
            if kw in msg_lower:
                return SafetyCheckResult(
                    is_safe=False,
                    trigger_reason="Query is outside healthcare assistant domain",
                    is_emergency=False,
                    should_escalate=False
                )

        return SafetyCheckResult(
            is_safe=True,
            trigger_reason=None,
            is_emergency=False,
            should_escalate=False
        )


# Singleton instance
guardrail_service = GuardrailService()
