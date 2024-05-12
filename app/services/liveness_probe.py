import typing

import attrs

from app.utils import cached


class LivenessProbeInterface(typing.Protocol):
    async def is_alive(self) -> bool: ...


@typing.final
@attrs.define(slots=True, frozen=True, kw_only=True)
class LivenessProbeSrv:
    _resources: typing.Mapping[str, LivenessProbeInterface]

    def __getitem__(self, service: str) -> LivenessProbeInterface:
        return self._resources[service]

    def __contains__(self, service: str) -> bool:
        return service in self._resources

    @cached()
    async def is_alive(self, service: str) -> bool:
        return await self._resources[service].is_alive()

    @cached()
    async def all_alive(self) -> bool:
        return all([await self.is_alive(service=service) for service in self._resources])
