import re

# Regex pattern for version parsing (captures major, minor, patch and optional pre-release parts)
_version_pattern = re.compile(
    r"^v?(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?((?:alpha|beta|a|b)?)?(\d*)$",
    re.IGNORECASE,
)


def _parse_version(version):
    """Parse a version tag and return a tuple for sorting.

    Parameters
    ----------
    version : str
        The version tag to parse.

    Returns
    -------
    tuple
        The parsed version tuple:
        (major, minor, maintenance, patch, pre_release_type, pre_release_number)
    """
    match = _version_pattern.match(version)
    if match:
        major, minor, maintenance, patch = map(
            lambda x: int(x) if x else 0, match.groups()[:4]
        )
        # 'a' for alpha, 'b' for beta, or None
        pre_release_type = match.group(5)[0] if match.group(5) else None
        # alpha/beta version number or 0
        pre_release_number = (
            int(match.group(6)) if match.group(6) and pre_release_type else 0
        )
        return (
            major,
            minor,
            maintenance,
            patch,
            pre_release_type or "",
            pre_release_number,
        )
    # if no valid version
    return (0, 0, 0, 0, "", 0)
