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


async def test_get_documents(client, auth_headers):
     await client.post(
        "/documents",
        files={
            "file": ("test.pdf", b"fake pdf content", "application/pdf")
        },
        headers=auth_headers
     )

     response = await client.get(
         "/documents",
         headers=auth_headers
     )

     assert response.status_code == 200
     assert len(response.json()) > 0

