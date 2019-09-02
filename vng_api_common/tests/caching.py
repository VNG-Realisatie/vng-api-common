from rest_framework import status
from rest_framework.response import Response


class CacheMixin:
    def assertHasETag(self, response: Response, status_code=status.HTTP_200_OK):
        self.assertEqual(response.status_code, status_code)
        self.assertIn("ETag", response)
        self.assertNotEqual(response["ETag"], "")

    def assertHeadHasETag(self, url: str, status_code=status.HTTP_200_OK, **extra):
        response = self.client.head(url, **extra)

        self.assertHasETag(response)

        # head requests should not return a response body, only headers
        self.assertEqual(response.content, b"")
