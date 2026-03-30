from __future__ import annotations

from aurora.contracts.host import HostProfile


def host_package_block_reason(profile: HostProfile) -> tuple[str, str]:
    if profile.mutability == "atomic":
        reason = (
            "o host Linux foi detectado como Atomic/imutavel, e o dominio host_package "
            "permanece bloqueado por politica nesta abertura."
        )
        message = (
            "❌ este host Linux foi detectado como Atomic/imutavel; o dominio host_package "
            "permanece bloqueado por politica nesta rodada."
        )
        return reason, message

    reason = "a familia Linux deste host ficou fora do recorte atual de host_package."
    message = "❌ a familia Linux deste host ficou fora do recorte atual de host_package."
    return reason, message
