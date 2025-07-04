from .services.notification import send_notification_to_user

def some_view(request):
    # Example: sending a notification after some action
    send_notification_to_user(request.user.id, "Your workout has been scheduled!")
    return JsonResponse({"status": "Notification sent"})
