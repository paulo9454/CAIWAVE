"""
Authenticated API router for Owner Payment Engine v1.

The router is built through dependency injection so this module does not
import the monolithic backend.server module or the live application database.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.owner_payment import (
    OwnerPaymentProfileCreate,
    OwnerPaymentProfileResponse,
    OwnerPaymentProfileUpdate,
)
from backend.services.owner_payment.repository import (
    OwnerPaymentProfileAlreadyExists,
    OwnerPaymentProfileNotFound,
    OwnerPaymentProfileRepository,
)
from backend.services.owner_payment.service import OwnerPaymentProfileService


def create_owner_payment_router(
    *,
    collection: Any,
    owner_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(
        prefix="/owner/payment-profile",
        tags=["Owner Payment Profile"],
    )

    repository = OwnerPaymentProfileRepository(collection)
    service = OwnerPaymentProfileService(repository)

    @router.get(
        "",
        response_model=OwnerPaymentProfileResponse,
    )
    async def get_owner_payment_profile(
        user: dict = Depends(owner_dependency),
    ) -> OwnerPaymentProfileResponse:
        try:
            return await service.get_public_profile(user["id"])
        except OwnerPaymentProfileNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.post(
        "",
        response_model=OwnerPaymentProfileResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_owner_payment_profile(
        request: OwnerPaymentProfileCreate,
        user: dict = Depends(owner_dependency),
    ) -> OwnerPaymentProfileResponse:
        owner_request = request.model_copy(
            update={"owner_id": user["id"]},
        )

        try:
            profile = await service.create_profile(owner_request)
        except OwnerPaymentProfileAlreadyExists as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        return service.to_public_response(profile)

    @router.put(
        "",
        response_model=OwnerPaymentProfileResponse,
    )
    async def update_owner_payment_profile(
        request: OwnerPaymentProfileUpdate,
        user: dict = Depends(owner_dependency),
    ) -> OwnerPaymentProfileResponse:
        try:
            profile = await service.update_profile(
                user["id"],
                request,
            )
        except OwnerPaymentProfileNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        return service.to_public_response(profile)

    return router
