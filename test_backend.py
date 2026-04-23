import httpx
import asyncio
import base64
import json

BASE_URL = "http://localhost:8000"

async def test_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"Health Check: {response.status_code} - {response.json()}")
        assert response.status_code == 200

async def test_braille_encode():
    async with httpx.AsyncClient() as client:
        payload = {"text": "Hello"}
        response = await client.post(f"{BASE_URL}/api/braille/encode", json=payload)
        print(f"Braille Encode: {response.status_code} - {response.json()}")
        assert response.status_code == 200

async def test_braille_decode():
    async with httpx.AsyncClient() as client:
        # Unicode for 'Hello' in Braille
        payload = {"braille_unicode": "⠠⠓⠑⠇⠇⠕"}
        response = await client.post(f"{BASE_URL}/api/braille/decode", json=payload)
        print(f"Braille Decode: {response.status_code} - {response.json()}")
        assert response.status_code == 200

async def test_bci_mock():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/bci/mock")
        print(f"BCI Mock: {response.status_code} - {response.json()}")
        assert response.status_code == 200

async def run_tests():
    print("Starting API tests...")
    try:
        await test_health()
        await test_braille_encode()
        await test_braille_decode()
        await test_bci_mock()
        print("All tests passed!")
    except Exception as e:
        print(f"Tests failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
