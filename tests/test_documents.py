async def test_upload_document_success(client, auth_headers):
    response = await client.post(
        "/documents",
        files={
            "file": ("test.pdf", b"fake pdf content", "application/pdf")
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["filename"] is not None


async def test_upload_unsupported_file(client, auth_headers):
    response = await client.post(
        "documents",
        files={
            "file": ("test.txt", b"fake pdt content", "application/txt")
        },
        headers=auth_headers
    )

    assert response.status_code == 415
    assert "Unsupported Content-Type" in response.json()["detail"]


async def test_get_documents(client, auth_headers, test_document):
     response = await client.get(
         "/documents",
         headers=auth_headers
     )

     assert response.status_code == 200
     assert len(response.json()) > 0



async def test_delete_document(client, auth_headers, test_document):
    response = await client.delete(
        f"/documents/{test_document['id']}",
        headers=auth_headers
    )

    assert response.status_code == 204


async def test_delete_document_not_found(client, auth_headers):
    response = await client.delete(
        "/documents/10000",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


async def test_delete_not_authorized_user(client,test_document):
    response = await client.delete(
        f"/documents/{test_document['id']}",
        headers=None
    )

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


async def test_delete_someone_else_document(client, test_document, auth_headers2):
    response = await client.delete(
        f"/documents/{test_document['id']}",
        headers=auth_headers2
    )

    assert response.status_code == 403
    assert "not allowed" in response.json()["detail"]