"""
Authenticated owner gateway API.

The router is dependency-injected and does not import backend.server.
Owners cannot self-verify or self-activate payment gateways.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.owner_gateway import (
    GatewayVerificationStatus,
    OwnerGatewayOwnerCreate,
    OwnerGatewayOwnerUpdate,
    OwnerGatewayProfileCreate,
    OwnerGatewayProfileResponse,
    OwnerGatewayProfileUpdate,
    OwnerGatewayStatus,
)
from backend.services.owner_gateway.repository import (
    OwnerGatewayAlreadyExists,
    OwnerGatewayNotFound,
    OwnerGatewayRepository,
)
from backend.services.owner_gateway.service import OwnerGatewayService


def create_owner_gateway_router(
    *,
    collection: Any,
    owner_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(
        prefix="/owner/payment-gateway",
        tags=["Owner Payment Gateway"],
    )

    repository = OwnerGatewayRepository(collection)
    service = OwnerGatewayService(repository)

    @router.get(
        "",
        response_model=OwnerGatewayProfileResponse,
    )
    async def get_owner_gateway(
        user: dict = Depends(owner_dependency),
    ) -> OwnerGatewayProfileResponse:
        try:
            return await service.get_public_profile(user["id"])
        except OwnerGatewayNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @router.post(
        "",
        response_model=OwnerGatewayProfileResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_owner_gateway(
        request: OwnerGatewayOwnerCreate,
        user: dict = Depends(owner_dependency),
    ) -> OwnerGatewayProfileResponse:
        create_request = OwnerGatewayProfileCreate(
            owner_id=user["id"],
            configuration=request.configuration,
            status=OwnerGatewayStatus.DRAFT,
            verification_status=(
                GatewayVerificationStatus.NOT_VERIFIED
            ),
        )

        try:
            profile = await service.create_profile(create_request)
        except OwnerGatewayAlreadyExists as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        return service.to_public_response(profile)

    @router.put(
        "",
        response_model=OwnerGatewayProfileResponse,
    )
    async def update_owner_gateway(
        request: OwnerGatewayOwnerUpdate,
        user: dict = Depends(owner_dependency),
    ) -> OwnerGatewayProfileResponse:
        update_data = request.model_dump(exclude_none=True)

        if "configuration" in update_data:
            # Replacing credentials/configuration invalidates any previous
            # verification and returns the gateway to draft.
            update_data["status"] = OwnerGatewayStatus.DRAFT
            update_data["verification_status"] = (
                GatewayVerificationStatus.NOT_VERIFIED
            )
            update_data["verification_message"] = (
                "Gateway configuration changed and requires verification."
            )
            update_data["last_verified_at"] = None

        internal_request = OwnerGatewayProfileUpdate.model_validate(
            update_data
        )

        try:
            profile = await service.update_profile(
                user["id"],
                internal_request,
            )
        except OwnerGatewayNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        return service.to_public_response(profile)

    return router
