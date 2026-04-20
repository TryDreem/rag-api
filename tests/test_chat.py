async def test_ask_question(client, auth_headers, test_document):
    response = await client.post(
        f"/chat/{test_document['id']}",
        json={"question": "fake question"},
        headers=auth_headers
    )

    assert response.status_code == 201
    assert len(response.json()) > 0


async def test_ask_question_not_found(client, auth_headers):
    response = await client.post(
        f"/chat/10000000",
        json={"question": "fake question"},
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]



async def test_get_history(client, auth_headers,test_document):
    await client.post(
        f"/chat/{test_document['id']}",
        json={"question": "fake question"},
        headers=auth_headers
    )

    response = await client.get(
        f"/chat/{test_document['id']}/history",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert len(response.json()) > 0



async def test_ask_question_access_denied(client, auth_headers2, test_document):
    response = await client.post(
        f"/chat/{test_document['id']}",
        json={"question": "fake question"},
        headers=auth_headers2
    )
    assert response.status_code == 403
    assert "not allowed" in response.json()["detail"]










