def validate_mikrotik_script(script: str) -> dict:
    """
    Basic safety + completeness validation
    """

    required_sections = [
        "/ip firewall nat",
        "/ip dhcp-server",
        "/interface bridge",
        "/radius"
    ]

    missing = [s for s in required_sections if s not in script]

    return {
        "valid": len(missing) == 0,
        "missing_sections": missing
    }
