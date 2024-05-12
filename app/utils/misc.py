def make_url(base_url: str, *uris: str) -> str:
    """Make url from base url and arbitrary number of uris.

    Params:
        base_url: Base url.
        uris: Arbitrary number of uris.

    Returns:
    -------
        Url.

    Example:
    -------
        >>> make_url("https://example.com", "api", "v1", "payments")
        "https://example.com/api/v1/payments"

    """
    url = base_url.rstrip("/")
    for uri in uris:
        _uri = uri.strip("/")
        url = f"{url}/{_uri}" if _uri else url
    return url
