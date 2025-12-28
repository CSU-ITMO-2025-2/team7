import httpx
from fastapi import HTTPException, status

from .config import settings


async def get_dataset_from_artifacts_service(dataset_id: int, token: str, user_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.artifacts_service.url}/datasets",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
            response.raise_for_status()
            datasets = response.json()

            # Find the dataset with the matching ID
            dataset = next((ds for ds in datasets if ds["id"] == dataset_id), None)
            if dataset is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"dataset {dataset_id} not found",
                )
            if dataset.get("user_id") != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="access denied to dataset"
                )
            return dataset

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"dataset {dataset_id} not found",
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"failed to fetch dataset from artifacts service: {exc}",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"failed to connect to artifacts service: {exc}",
            )
