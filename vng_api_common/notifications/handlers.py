import logging


class LoggingHandler:

    def handle(self, message: dict) -> None:
        logger = logging.getLogger('notifications')
        logger.info("Received notification %r", message)


default = LoggingHandler()
