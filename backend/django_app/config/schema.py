def exclude_internal(endpoints):
    return [endpoint for endpoint in endpoints if not endpoint[0].startswith("/internal/")]