"""
Optional app to manage notifications.

Components can send and receive notifications. This app provides hooks to
configure and register webhooks for notifications, and a generic APIView to
receive incoming notifications.
"""
default_app_config = "vng_api_common.notifications.apps.NotificationsConfig"
