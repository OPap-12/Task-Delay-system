from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from urllib.parse import parse_qs

@database_sync_to_async
def get_user_from_jwt(token_string):
    try:
        UntypedToken(token_string)
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token_string)
        user = jwt_auth.get_user(validated_token)
        return user
    except (InvalidToken, TokenError, Exception):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware that checks for a JWT token in the query string (e.g. ?token=XYZ).
    """
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        if "token" in query_params:
            token = query_params["token"][0]
            scope["user"] = await get_user_from_jwt(token)
        
        return await super().__call__(scope, receive, send)
