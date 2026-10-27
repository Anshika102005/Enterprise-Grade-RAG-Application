import logfire
from app.config import settings

print("Token exists:", bool(settings.LOGFIRE_TOKEN))
print("Token prefix:", settings.LOGFIRE_TOKEN[:10] if settings.LOGFIRE_TOKEN else "NONE")

logfire.configure(
    service_name="logfire-auth-test",
    send_to_logfire="if-token-present",
    token=settings.LOGFIRE_TOKEN,
)

logfire.info("Testing Logfire from Python SDK")

print("TEST FINISHED")