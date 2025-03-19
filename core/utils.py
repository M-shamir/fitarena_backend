from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

def generate_jwt_response(user):
    refresh =  RefreshToken.for_user(user)
    refresh['role'] = user.role

    access_token =  str(refresh.access_token)

    response = Response({
        "access" : access_token,
        "message" :"Login Success"
    })
    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        secure=True,
        httponly=True,
        samesite="Lax",
        path="/user/token/refresh/"
    )
    return response