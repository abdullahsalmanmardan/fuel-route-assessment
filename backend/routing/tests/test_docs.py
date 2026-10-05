def test_schema_describes_the_route_endpoint(client):
    response = client.get("/api/schema/", {"format": "json"})

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/route/"]["get"]
    assert {p["name"] for p in operation["parameters"]} == {"start", "finish"}
    assert set(operation["responses"]) == {"200", "400", "422", "502"}


def test_swagger_page_is_served(client):
    assert client.get("/api/docs/").status_code == 200
