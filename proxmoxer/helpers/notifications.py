"""
Notification system helpers for Proxmoxer.

Provides high-level async API for managing Proxmox notification system
including endpoints (SMTP, Gotify, webhook), matchers, and targets.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


class EndpointType(str, Enum):
    """Notification endpoint types."""

    SENDMAIL = "sendmail"
    SMTP = "smtp"
    GOTIFY = "gotify"
    WEBHOOK = "webhook"


class NotificationSeverity(str, Enum):
    """Notification severity levels."""

    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class NotificationEndpoint:
    """Notification endpoint configuration."""

    name: str
    type: str
    disable: bool = False
    comment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationEndpoint:
        """Create NotificationEndpoint from API response."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            disable=bool(data.get("disable", 0)),
            comment=data.get("comment"),
        )


@dataclass
class SMTPEndpoint(NotificationEndpoint):
    """SMTP notification endpoint."""

    server: str | None = None
    port: int = 25
    username: str | None = None
    mailto: list[str] | None = None
    mailto_user: list[str] | None = None
    from_address: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SMTPEndpoint:
        """Create SMTPEndpoint from API response."""
        mailto = data.get("mailto", "")
        mailto_user = data.get("mailto-user", "")

        return cls(
            name=data.get("name", ""),
            type="smtp",
            disable=bool(data.get("disable", 0)),
            comment=data.get("comment"),
            server=data.get("server"),
            port=data.get("port", 25),
            username=data.get("username"),
            mailto=mailto.split(",") if mailto else None,
            mailto_user=mailto_user.split(",") if mailto_user else None,
            from_address=data.get("from-address"),
        )


@dataclass
class GotifyEndpoint(NotificationEndpoint):
    """Gotify notification endpoint."""

    server: str | None = None
    token: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GotifyEndpoint:
        """Create GotifyEndpoint from API response."""
        return cls(
            name=data.get("name", ""),
            type="gotify",
            disable=bool(data.get("disable", 0)),
            comment=data.get("comment"),
            server=data.get("server"),
            token=data.get("token"),
        )


@dataclass
class NotificationMatcher:
    """Notification matcher configuration."""

    name: str
    target: list[str] | None = None
    mode: str = "all"
    match_field: list[str] | None = None
    match_severity: list[str] | None = None
    match_calendar: list[str] | None = None
    invert_match: bool = False
    disable: bool = False
    comment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationMatcher:
        """Create NotificationMatcher from API response."""
        target = data.get("target", "")
        match_field = data.get("match-field", "")
        match_severity = data.get("match-severity", "")
        match_calendar = data.get("match-calendar", "")

        return cls(
            name=data.get("name", ""),
            target=target.split(",") if target else None,
            mode=data.get("mode", "all"),
            match_field=match_field.split(",") if match_field else None,
            match_severity=match_severity.split(",") if match_severity else None,
            match_calendar=match_calendar.split(",") if match_calendar else None,
            invert_match=bool(data.get("invert-match", 0)),
            disable=bool(data.get("disable", 0)),
            comment=data.get("comment"),
        )


@dataclass
class NotificationTarget:
    """Notification target (group of endpoints)."""

    name: str
    endpoints: list[str] | None = None
    comment: str | None = None
    disable: bool | None = None
    origin: str | None = None
    type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationTarget:
        """Create NotificationTarget from API response."""
        endpoints = data.get("endpoints", "")
        return cls(
            name=data.get("name", ""),
            endpoints=endpoints.split(",") if endpoints else None,
            comment=data.get("comment"),
            disable=bool(data.get("disable", 0)) if data.get("disable") is not None else None,
            origin=data.get("origin"),
            type=data.get("type"),
        )


class NotificationManager:
    """
    High-level manager for Proxmox notification system.

    Provides methods for managing notification endpoints, matchers, and targets.

    Example:
        >>> notif = NotificationManager(proxmox)
        >>> await notif.create_smtp_endpoint(
        ...     name="email",
        ...     server="smtp.example.com",
        ...     mailto=["admin@example.com"]
        ... )
        >>> await notif.create_matcher(
        ...     name="critical",
        ...     target=["email"],
        ...     match_severity=["error"]
        ... )
        >>> await notif.test_endpoint("email")
    """

    def __init__(self, proxmox: Any):
        """
        Initialize NotificationManager.

        Args:
            proxmox: Proxmoxer instance
        """
        self.proxmox = proxmox

    # Endpoints
    async def list_endpoints(self) -> list[NotificationEndpoint]:
        """
        List all notification endpoints.

        Returns:
            List of NotificationEndpoint objects
        """
        data: ResponseData = await self.proxmox.cluster.notifications.endpoints.get()
        return [NotificationEndpoint.from_dict(e) for e in data]

    async def create_sendmail_endpoint(
        self,
        name: str,
        mailto: list[str] | None = None,
        mailto_user: list[str] | None = None,
        from_address: str | None = None,
        comment: str | None = None,
        disable: bool = False,
    ) -> None:
        """
        Create sendmail notification endpoint.

        Args:
            name: Endpoint name
            mailto: Email addresses
            mailto_user: User IDs to notify
            from_address: From address
            comment: Comment
            disable: Disable endpoint
        """
        params = {"name": name}
        if mailto:
            params["mailto"] = ",".join(mailto)
        if mailto_user:
            params["mailto-user"] = ",".join(mailto_user)
        if from_address:
            params["from-address"] = from_address
        if comment:
            params["comment"] = comment
        if disable:
            params["disable"] = 1

        await self.proxmox.cluster.notifications.endpoints.sendmail.post(**params)

    async def create_smtp_endpoint(
        self,
        name: str,
        server: str,
        mailto: list[str] | None = None,
        mailto_user: list[str] | None = None,
        port: int = 25,
        username: str | None = None,
        password: str | None = None,
        from_address: str | None = None,
        author: str | None = None,
        comment: str | None = None,
        disable: bool = False,
    ) -> None:
        """
        Create SMTP notification endpoint.

        Args:
            name: Endpoint name
            server: SMTP server
            mailto: Email addresses
            mailto_user: User IDs to notify
            port: SMTP port
            username: SMTP username
            password: SMTP password
            from_address: From address
            author: Author name
            comment: Comment
            disable: Disable endpoint
        """
        params = {"name": name, "server": server, "port": port}
        if mailto:
            params["mailto"] = ",".join(mailto)
        if mailto_user:
            params["mailto-user"] = ",".join(mailto_user)
        if username:
            params["username"] = username
        if password:
            params["password"] = password
        if from_address:
            params["from-address"] = from_address
        if author:
            params["author"] = author
        if comment:
            params["comment"] = comment
        if disable:
            params["disable"] = 1

        await self.proxmox.cluster.notifications.endpoints.smtp.post(**params)

    async def create_gotify_endpoint(
        self,
        name: str,
        server: str,
        token: str,
        comment: str | None = None,
        disable: bool = False,
    ) -> None:
        """
        Create Gotify notification endpoint.

        Args:
            name: Endpoint name
            server: Gotify server URL
            token: Gotify token
            comment: Comment
            disable: Disable endpoint
        """
        params = {"name": name, "server": server, "token": token}
        if comment:
            params["comment"] = comment
        if disable:
            params["disable"] = 1

        await self.proxmox.cluster.notifications.endpoints.gotify.post(**params)

    async def create_webhook_endpoint(
        self,
        name: str,
        url: str,
        method: str = "POST",
        header: list[str] | None = None,
        body: str | None = None,
        secret: str | None = None,
        comment: str | None = None,
        disable: bool = False,
    ) -> None:
        """
        Create webhook notification endpoint.

        Args:
            name: Endpoint name
            url: Webhook URL
            method: HTTP method (POST, PUT)
            header: HTTP headers (format: "Name: value")
            body: Request body template
            secret: Secret for HMAC signature
            comment: Comment
            disable: Disable endpoint
        """
        params = {"name": name, "url": url, "method": method}
        if header:
            params["header"] = header
        if body:
            params["body"] = body
        if secret:
            params["secret"] = secret
        if comment:
            params["comment"] = comment
        if disable:
            params["disable"] = 1

        await self.proxmox.cluster.notifications.endpoints.webhook.post(**params)

    async def get_endpoint(self, name: str) -> dict[str, Any]:
        """
        Get endpoint configuration.

        Args:
            name: Endpoint name

        Returns:
            Endpoint configuration dict
        """
        endpoints = await self.list_endpoints()
        for endpoint in endpoints:
            if endpoint.name == name:
                # Get detailed config based on type
                if endpoint.type == "smtp":
                    return await self.proxmox.cluster.notifications.endpoints.smtp(name).get()
                elif endpoint.type == "sendmail":
                    return await self.proxmox.cluster.notifications.endpoints.sendmail(name).get()
                elif endpoint.type == "gotify":
                    return await self.proxmox.cluster.notifications.endpoints.gotify(name).get()
                elif endpoint.type == "webhook":
                    return await self.proxmox.cluster.notifications.endpoints.webhook(name).get()

        raise ValueError(f"Endpoint '{name}' not found")

    async def update_smtp_endpoint(
        self,
        name: str,
        server: str | None = None,
        port: int | None = None,
        mailto: list[str] | None = None,
        username: str | None = None,
        password: str | None = None,
        from_address: str | None = None,
        comment: str | None = None,
        disable: bool | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update SMTP endpoint.

        Args:
            name: Endpoint name
            server: SMTP server
            port: SMTP port
            mailto: Email addresses
            username: SMTP username
            password: SMTP password
            from_address: From address
            comment: Comment
            disable: Disable endpoint
            delete: Properties to delete
        """
        params = {}
        if server is not None:
            params["server"] = server
        if port is not None:
            params["port"] = port
        if mailto is not None:
            params["mailto"] = ",".join(mailto)
        if username is not None:
            params["username"] = username
        if password is not None:
            params["password"] = password
        if from_address is not None:
            params["from-address"] = from_address
        if comment is not None:
            params["comment"] = comment
        if disable is not None:
            params["disable"] = 1 if disable else 0
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.notifications.endpoints.smtp(name).put(**params)

    async def delete_endpoint(self, name: str, type: EndpointType | str) -> None:
        """
        Delete notification endpoint.

        Args:
            name: Endpoint name
            type: Endpoint type
        """
        if isinstance(type, EndpointType):
            type_str = type.value
        else:
            type_str = type

        if type_str == "smtp":
            await self.proxmox.cluster.notifications.endpoints.smtp(name).delete()
        elif type_str == "sendmail":
            await self.proxmox.cluster.notifications.endpoints.sendmail(name).delete()
        elif type_str == "gotify":
            await self.proxmox.cluster.notifications.endpoints.gotify(name).delete()
        elif type_str == "webhook":
            await self.proxmox.cluster.notifications.endpoints.webhook(name).delete()

    async def test_endpoint(self, name: str, type: EndpointType | str) -> None:
        """
        Test notification endpoint.

        Args:
            name: Endpoint name
            type: Endpoint type
        """
        if isinstance(type, EndpointType):
            type_str = type.value
        else:
            type_str = type

        if type_str == "smtp":
            await self.proxmox.cluster.notifications.endpoints.smtp(name).test.post()
        elif type_str == "sendmail":
            await self.proxmox.cluster.notifications.endpoints.sendmail(name).test.post()
        elif type_str == "gotify":
            await self.proxmox.cluster.notifications.endpoints.gotify(name).test.post()
        elif type_str == "webhook":
            await self.proxmox.cluster.notifications.endpoints.webhook(name).test.post()

    # Matchers
    async def list_matchers(self) -> list[NotificationMatcher]:
        """
        List all notification matchers.

        Returns:
            List of NotificationMatcher objects
        """
        data: ResponseData = await self.proxmox.cluster.notifications.matchers.get()
        return [NotificationMatcher.from_dict(m) for m in data]

    async def get_matcher(self, name: str) -> NotificationMatcher:
        """
        Get matcher configuration.

        Args:
            name: Matcher name

        Returns:
            NotificationMatcher object
        """
        data: ResponseData = await self.proxmox.cluster.notifications.matchers(name).get()
        data["name"] = name
        return NotificationMatcher.from_dict(data)

    async def create_matcher(
        self,
        name: str,
        target: list[str],
        mode: str = "all",
        match_field: list[str] | None = None,
        match_severity: list[str | NotificationSeverity] | None = None,
        match_calendar: list[str] | None = None,
        invert_match: bool = False,
        comment: str | None = None,
        disable: bool = False,
    ) -> None:
        """
        Create notification matcher.

        Args:
            name: Matcher name
            target: Target names
            mode: Match mode (all, any)
            match_field: Field matchers (e.g., "type:fencing")
            match_severity: Severity filter
            match_calendar: Calendar matchers
            invert_match: Invert match
            comment: Comment
            disable: Disable matcher
        """
        params = {"name": name, "target": ",".join(target), "mode": mode}
        if match_field:
            params["match-field"] = ",".join(match_field)
        if match_severity:
            severity_strs = [
                s.value if isinstance(s, NotificationSeverity) else s
                for s in match_severity
            ]
            params["match-severity"] = ",".join(severity_strs)
        if match_calendar:
            params["match-calendar"] = ",".join(match_calendar)
        if invert_match:
            params["invert-match"] = 1
        if comment:
            params["comment"] = comment
        if disable:
            params["disable"] = 1

        await self.proxmox.cluster.notifications.matchers.post(**params)

    async def update_matcher(
        self,
        name: str,
        target: list[str] | None = None,
        mode: str | None = None,
        match_field: list[str] | None = None,
        match_severity: list[str] | None = None,
        match_calendar: list[str] | None = None,
        invert_match: bool | None = None,
        comment: str | None = None,
        disable: bool | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update notification matcher.

        Args:
            name: Matcher name
            target: Target names
            mode: Match mode
            match_field: Field matchers
            match_severity: Severity filter
            match_calendar: Calendar matchers
            invert_match: Invert match
            comment: Comment
            disable: Disable matcher
            delete: Properties to delete
        """
        params = {}
        if target is not None:
            params["target"] = ",".join(target)
        if mode is not None:
            params["mode"] = mode
        if match_field is not None:
            params["match-field"] = ",".join(match_field)
        if match_severity is not None:
            params["match-severity"] = ",".join(match_severity)
        if match_calendar is not None:
            params["match-calendar"] = ",".join(match_calendar)
        if invert_match is not None:
            params["invert-match"] = 1 if invert_match else 0
        if comment is not None:
            params["comment"] = comment
        if disable is not None:
            params["disable"] = 1 if disable else 0
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.notifications.matchers(name).put(**params)

    async def delete_matcher(self, name: str) -> None:
        """
        Delete notification matcher.

        Args:
            name: Matcher name
        """
        await self.proxmox.cluster.notifications.matchers(name).delete()

    # Targets
    async def list_targets(self) -> list[NotificationTarget]:
        """
        List all notification targets.

        Returns:
            List of NotificationTarget objects
        """
        data: ResponseData = await self.proxmox.cluster.notifications.targets.get()
        return [NotificationTarget.from_dict(t) for t in data]

    async def get_target(self, name: str) -> NotificationTarget:
        """
        Get target configuration.

        Args:
            name: Target name

        Returns:
            NotificationTarget object
        """
        data: ResponseData = await self.proxmox.cluster.notifications.targets(name).get()
        data["name"] = name
        return NotificationTarget.from_dict(data)
