"""Auth module — validates bearer tokens on incoming requests before normalization."""


class Auth:
    def __init__(self, config: dict):
        pass

    def verify(self, authorization_header: str | None) -> bool:
        pass
