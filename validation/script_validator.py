def validate_script(script):

    if isinstance(script, dict):
        script = script.get("script", "")

    if not isinstance(script, str):
        script = str(script or "")

    issues = []

    dangerous_patterns = [
        "while(true)",
        "gs.sleep",
        "deleteRecord("
    ]

    for pattern in dangerous_patterns:

        if pattern in script:
            issues.append(pattern)

    return {
        "valid": len(issues) == 0,
        "issues": issues
    }
