import httpx
import pytest

# These tests expect the docker-compose setup to be running locally on their respective ports.

@pytest.mark.asyncio
async def test_gateway_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200
            assert response.json()["service"] == "gateway"
        except httpx.RequestError:
            pytest.skip("Gateway service is not running")

@pytest.mark.asyncio
async def test_ingest_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/health")
            assert response.status_code == 200
            assert response.json()["service"] == "ingest"
        except httpx.RequestError:
            pytest.skip("Ingest service is not running")

@pytest.mark.asyncio
async def test_flood_ml_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8002/health")
            assert response.status_code == 200
            assert response.json()["service"] == "flood_ml"
        except httpx.RequestError:
            pytest.skip("Flood ML service is not running")

@pytest.mark.asyncio
async def test_geo_core_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8003/health")
            assert response.status_code == 200
            assert response.json()["service"] == "geo_core"
        except httpx.RequestError:
            pytest.skip("Geo Core service is not running")

@pytest.mark.asyncio
async def test_report_health():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8004/health")
            assert response.status_code == 200
            assert response.json()["service"] == "report"
        except httpx.RequestError:
            pytest.skip("Report service is not running")
