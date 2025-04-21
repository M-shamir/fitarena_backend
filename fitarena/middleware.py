

class JWTAuthCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Logic to get the JWT token from cookies and set the authorization header
        token = request.COOKIES.get('access_token')  # Get the token from cookies
        if token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'  # Add it to the request header
        
        response = self.get_response(request)
        return response
