from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserSubscription
from .serializers import UserSubscriptionSerializer

class UserSubscriptionsAPIView(APIView):
    # Доступ только для авторизованных пользователей
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Берем подписки только того юзера, который делает запрос
        subscriptions = UserSubscription.objects.filter(user=request.user)
        serializer = UserSubscriptionSerializer(subscriptions, many=True)
        # Возвращаем чистый JSON
        return Response(serializer.data)
