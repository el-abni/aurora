from .arch import build_arch_search_route
from .debian import build_debian_search_route
from .fedora import build_fedora_search_route
from .opensuse import build_opensuse_search_route

__all__ = [
    "build_arch_search_route",
    "build_debian_search_route",
    "build_fedora_search_route",
    "build_opensuse_search_route",
]
