GOLD_STANDARD_CASES = [
    {"name": "synthetic identity bust-out", "expected_decision": "ESCALATE", "narrative": "new identity with rapid high-value wires"},
    {"name": "clean retail transfer", "expected_decision": "CLEAR", "narrative": "routine domestic retail transfer"},
    {"name": "covert Panama transshipment", "expected_decision": "ESCALATE", "narrative": "nominee company routes funds through Panama"},
    {"name": "structured layering", "expected_decision": "ESCALATE", "narrative": "multiple deposits just below the reporting threshold"},
    {"name": "low-confidence supervisor rejection", "expected_decision": "REJECT_HANDOFF", "narrative": "agent evidence confidence is 0.42"},
]