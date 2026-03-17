def validate_script(script):

    issues = []

    dangerous_patterns = [
        "while(true)",
        "gs.sleep",
        "deleteRecord("
    ]

    for pattern in dangerous_patterns:

        if pattern in script:
            issues.append(pattern)

    return issues