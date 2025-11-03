"""
NotificationManager Example - Notification System

This example demonstrates notification configuration including SMTP,
Gotify, webhooks, matchers, and targets.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import NotificationManager, EndpointType, NotificationSeverity


async def main():
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )
    notif = NotificationManager(proxmox)

    print("=" * 60)
    print("NotificationManager Examples - Notification System")
    print("=" * 60)

    # CREATE SMTP ENDPOINT
    print("\n[1] CREATE SMTP ENDPOINT")
    print("-" * 60)
    await notif.create_smtp_endpoint(
        name="smtp-gmail",
        server="smtp.gmail.com",
        port=587,
        username="notifications@example.com",
        password="app_password",
        mailto=["admin@example.com", "ops@example.com"],
        from_address="proxmox@example.com",
        comment="Gmail SMTP for notifications",
    )
    print("Created SMTP endpoint: smtp-gmail")

    # CREATE SENDMAIL ENDPOINT
    print("\n[2] CREATE SENDMAIL ENDPOINT")
    print("-" * 60)
    await notif.create_sendmail_endpoint(
        name="sendmail",
        mailto=["root@localhost"],
        from_address="proxmox@localhost",
        comment="Local sendmail",
    )
    print("Created sendmail endpoint")

    # CREATE GOTIFY ENDPOINT
    print("\n[3] CREATE GOTIFY ENDPOINT")
    print("-" * 60)
    await notif.create_gotify_endpoint(
        name="gotify",
        server="https://gotify.example.com",
        token="ABCDEFGHIJKLMN",
        comment="Gotify push notifications",
    )
    print("Created Gotify endpoint")

    # CREATE WEBHOOK ENDPOINT
    print("\n[4] CREATE WEBHOOK ENDPOINT")
    print("-" * 60)
    await notif.create_webhook_endpoint(
        name="webhook-slack",
        url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        method="POST",
        header=["Content-Type: application/json"],
        body='{"text": "Proxmox Alert: {{subject}}"}',
        comment="Slack webhook",
    )
    print("Created webhook endpoint for Slack")

    # LIST ENDPOINTS
    print("\n[5] LIST ENDPOINTS")
    print("-" * 60)
    endpoints = await notif.list_endpoints()
    print(f"Notification endpoints: {len(endpoints)}")
    for endpoint in endpoints:
        print(f"  - {endpoint.name} ({endpoint.type})")
        if endpoint.comment:
            print(f"    {endpoint.comment}")

    # CREATE MATCHERS
    print("\n[6] CREATE NOTIFICATION MATCHERS")
    print("-" * 60)

    # Matcher for critical errors
    await notif.create_matcher(
        name="critical-alerts",
        target=["smtp-gmail", "gotify"],
        match_severity=[NotificationSeverity.ERROR],
        comment="Send critical errors to email and Gotify",
    )
    print("Created matcher: critical-alerts")

    # Matcher for backup notifications
    await notif.create_matcher(
        name="backup-notifications",
        target=["smtp-gmail"],
        match_field=["type:backup"],
        match_severity=[NotificationSeverity.INFO, NotificationSeverity.ERROR],
        comment="Backup job notifications",
    )
    print("Created matcher: backup-notifications")

    # Matcher for HA events
    await notif.create_matcher(
        name="ha-events",
        target=["gotify", "webhook-slack"],
        match_field=["type:ha"],
        comment="High Availability events",
    )
    print("Created matcher: ha-events")

    # LIST MATCHERS
    print("\n[7] LIST MATCHERS")
    print("-" * 60)
    matchers = await notif.list_matchers()
    print(f"Notification matchers: {len(matchers)}")
    for matcher in matchers:
        print(f"  - {matcher.name}")
        if matcher.target:
            print(f"    Targets: {', '.join(matcher.target)}")
        if matcher.match_severity:
            print(f"    Severities: {', '.join(matcher.match_severity)}")

    # UPDATE ENDPOINT
    print("\n[8] UPDATE ENDPOINT")
    print("-" * 60)
    await notif.update_smtp_endpoint(
        name="smtp-gmail",
        mailto=["admin@example.com", "ops@example.com", "security@example.com"],
        comment="Gmail SMTP - Updated recipients",
    )
    print("Updated SMTP endpoint")

    # UPDATE MATCHER
    print("\n[9] UPDATE MATCHER")
    print("-" * 60)
    await notif.update_matcher(
        name="critical-alerts",
        match_severity=[NotificationSeverity.ERROR, NotificationSeverity.WARNING],
    )
    print("Updated matcher to include warnings")

    # TEST ENDPOINT
    print("\n[10] TEST ENDPOINT")
    print("-" * 60)
    try:
        await notif.test_endpoint("smtp-gmail", EndpointType.SMTP)
        print("Test notification sent successfully")
    except Exception as e:
        print(f"Test failed: {e}")

    # LIST TARGETS
    print("\n[11] LIST TARGETS")
    print("-" * 60)
    targets = await notif.list_targets()
    print(f"Notification targets: {len(targets)}")
    for target in targets:
        print(f"  - {target.name}")
        if target.endpoints:
            print(f"    Endpoints: {', '.join(target.endpoints)}")

    # NOTIFICATION SEVERITY LEVELS
    print("\n[12] NOTIFICATION SEVERITY LEVELS")
    print("-" * 60)
    print("Available severity levels:")
    print(f"  - {NotificationSeverity.INFO.value}: Informational messages")
    print(f"  - {NotificationSeverity.NOTICE.value}: Normal but significant")
    print(f"  - {NotificationSeverity.WARNING.value}: Warning conditions")
    print(f"  - {NotificationSeverity.ERROR.value}: Error conditions")

    # CLEANUP (OPTIONAL)
    print("\n[13] CLEANUP")
    print("-" * 60)

    # Delete matcher
    await notif.delete_matcher("ha-events")
    print("Deleted matcher: ha-events")

    # Delete endpoint
    await notif.delete_endpoint("webhook-slack", EndpointType.WEBHOOK)
    print("Deleted webhook endpoint")

    print("\n" + "=" * 60)
    print("NOTIFICATION SYSTEM SUMMARY")
    print("=" * 60)
    print("Create SMTP endpoints with authentication")
    print("Create Sendmail endpoints")
    print("Create Gotify endpoints")
    print("Create Webhook endpoints (Slack, Teams, etc.)")
    print("Create matchers with severity/field filtering")
    print("Update endpoints and matchers")
    print("Test endpoints")
    print("List endpoints, matchers, and targets")
    print("\nUse Cases:")
    print("  - Email alerts for critical errors")
    print("  - Push notifications via Gotify")
    print("  - Slack/Teams integration via webhooks")
    print("  - Backup job notifications")
    print("  - HA event monitoring")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
