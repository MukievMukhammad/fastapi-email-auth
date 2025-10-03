class AuthResponse:
    def __init__(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is an abstract class and cannot be instantiated"
        )


class EmailLoginRequest:
    def __init__(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is an abstract class and cannot be instantiated"
        )


class TokenResponse:
    def __init__(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is an abstract class and cannot be instantiated"
        )


class VerifyCodeRequest:
    def __init__(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is an abstract class and cannot be instantiated"
        )
