import json
from datetime import datetime

TARGETS = {
    "/api/auth/jwt/create/",   # simplejwt (djoser)
    "/api/auth/jwt/refresh/",
}

class LogAuthPayloadMiddleware:
    """Пишет в stdout (docker logs) метод, путь, Host и тело запроса на auth-эндпоинты."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.path in TARGETS:     # чтобы не шуметь
                body = request.body.decode("utf-8", errors="replace")
                # ограничим размер (на всякий случай)
                if len(body) > 2000:
                    body = body[:2000] + "...(truncated)"
                print(
                    f"[AUTH-DEBUG] {datetime.utcnow().isoformat()}Z "
                    f"{request.method} {request.get_host()}{request.path} "
                    f"CT={request.META.get('CONTENT_TYPE')} "
                    f"Body={body}"
                )
        except Exception as e:
            print("[AUTH-DEBUG] error while logging:", repr(e))
        return self.get_response(request)
