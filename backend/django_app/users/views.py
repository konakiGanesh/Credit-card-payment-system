from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class MeView(APIView):
    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    @extend_schema(request=inline_serializer(name="LogoutRequest", fields={"refresh": serializers.CharField()}), responses={204: None})
    def post(self, request):
        refresh = request.data.get("refresh")
        if not isinstance(refresh, str):
            return Response({"detail": "A refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh)
            if str(token["user_id"]) != str(request.user.pk):
                return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
            token.blacklist()
        except (TokenError, KeyError):
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)