from services.single_rsc_provisioning_generator import generate_single_rsc_provisioning_file
import os


def build_mikrotik_script(router: dict):
    """
    Production-safe MikroTik script builder.

    Uses the confirmed working RSC provisioning generator
    and avoids incomplete V1 engine dependencies.
    """

    try:
        single_rsc = generate_single_rsc_provisioning_file(
            router_name=router.get("name", "unknown"),
            nas_identifier=router["nas_identifier"],
            radius_secret=router.get("radius_secret", ""),
            radius_host=router.get(
                "radius_host",
                os.environ.get("RADIUS_HOST", "radius.caiwave.com")
            ),
            callback_url=router.get(
                "callback_url",
                os.environ.get("MPESA_CALLBACK_URL", "")
                .replace("/mpesa/callback", "/mikrotik-onboard/confirm")
                if os.environ.get("MPESA_CALLBACK_URL")
                else ""
            )
        )

        return single_rsc.content

    except Exception as e:
        return f"# MikroTik Script Generation Error\n# {str(e)}\n"
