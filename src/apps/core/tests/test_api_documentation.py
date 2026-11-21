from rest_framework.test import APIClient


def test_swagger_ui_is_available() -> None:
    response = APIClient().get("/api/docs/")

    assert response.status_code == 200
    assert b"SwaggerUIBundle" in response.content


def test_openapi_schema_documents_current_api_routes() -> None:
    response = APIClient().get("/api/schema/?format=json")

    assert response.status_code == 200
    paths = response.data["paths"]
    assert "/api/v1/health/" in paths
    assert "/api/v1/auth/google/" in paths
    assert "/api/v1/auth/firebase/" in paths
    assert "/api/v1/auth/refresh/" in paths
    assert "/api/v1/auth/logout/" in paths
    assert "/api/v1/users/me/" in paths
    assert "/api/v1/users/me/profile/" in paths
    assert "/api/v1/users/me/preferences/" in paths
    assert paths["/api/v1/auth/google/"]["post"]["summary"] == "Sign in with Google"
    assert paths["/api/v1/users/me/"]["get"]["security"] == [{"bearerAuth": []}]
