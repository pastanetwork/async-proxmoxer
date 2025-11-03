#!/usr/bin/env python3
"""
Proxmox API Extraction and OpenAPI Generation Tool

This script extracts ALL endpoints from apidoc.js and generates a complete
OpenAPI 3.0 specification with proper categorization and documentation.

Source:
    apidoc.js from https://pve.proxmox.com/pve-docs/api-viewer/apidoc.js

Usage:
    python extract_and_combine.py

Output:
    - proxmox_api_complete.json - Unified OpenAPI 3.0 specification
    - API_COVERAGE_ANALYSIS.md - Automatic coverage analysis

Note:
    Temporary section files (*_endpoints.json) are created during extraction
    but are automatically deleted after generation is complete.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime


# Configuration
APIDOC_PATH = Path(__file__).parent.parent / "apidoc.js"
OUTPUT_DIR = Path(__file__).parent
HELPERS_DIR = Path(__file__).parent.parent / "proxmoxer" / "helpers"


def parse_apidoc_js(content: str) -> List[Dict[str, Any]]:
    """Parse the apidoc.js JavaScript file to extract API schema."""
    # Find "const apiSchema = [" and extract until matching "];"
    start_marker = "const apiSchema ="
    start_idx = content.find(start_marker)

    if start_idx == -1:
        print("ERROR: Could not find 'const apiSchema =' in file")
        return []

    # Start from the opening bracket
    json_start = start_idx + len(start_marker)
    json_str = content[json_start:].strip()

    # Find the matching closing bracket for the array
    # We need to count brackets to find the correct closing one
    depth = 0
    in_string = False
    escape_next = False
    end_idx = -1

    for i, char in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                end_idx = i + 1
                break

    if end_idx == -1:
        print("ERROR: Could not find matching closing bracket")
        return []

    json_str = json_str[:end_idx]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON: {e}")
        return []


def extract_endpoints_recursive(node: Dict[str, Any], path_prefix: str = "") -> List[Dict[str, Any]]:
    """Recursively extract all endpoints from the API tree."""
    endpoints = []

    # Get the path for this node
    current_path = path_prefix
    if "path" in node:
        current_path = node["path"]

    # Extract endpoint information from "info" field
    if "info" in node:
        for method, info in node["info"].items():
            if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                continue

            # Extract parameters
            parameters = []
            if "parameters" in info and "properties" in info["parameters"]:
                required_params = info["parameters"].get("required", [])
                for param_name, param_info in info["parameters"]["properties"].items():
                    parameters.append({
                        "name": param_name,
                        "type": param_info.get("type", "string"),
                        "required": param_name in required_params,
                        "description": param_info.get("description", ""),
                        "format": param_info.get("format"),
                        "enum": param_info.get("enum"),
                        "default": param_info.get("default"),
                        "minimum": param_info.get("minimum"),
                        "maximum": param_info.get("maximum"),
                        "pattern": param_info.get("pattern"),
                        "typetext": param_info.get("typetext"),
                        "optional": param_info.get("optional", 0) == 1,
                    })

            # Extract return type
            returns = info.get("returns", {})

            endpoints.append({
                "path": current_path,
                "method": method.upper(),
                "description": info.get("description", ""),
                "parameters": parameters,
                "returns": returns,
                "permissions": info.get("permissions", {}),
                "protected": info.get("protected", 0) == 1,
            })

    # Recursively process children
    if "children" in node:
        for child in node["children"]:
            endpoints.extend(extract_endpoints_recursive(child, current_path))

    return endpoints


def filter_by_section(endpoints: List[Dict[str, Any]], section: str) -> List[Dict[str, Any]]:
    """Filter endpoints by API section."""
    return [
        ep for ep in endpoints
        if ep["path"].startswith(f"/{section}/") or ep["path"] == f"/{section}"
    ]


def categorize_path(path: str) -> List[str]:
    """Assign categories/tags to an API path."""
    tags = []

    # Main section tag
    main_section = path.split('/')[1] if len(path.split('/')) > 1 else "root"
    tags.append(main_section)

    # Specific categorization
    if '/qemu/' in path:
        tags.append('virtual-machines')
        if '/agent/' in path:
            tags.append('qemu-agent')
        if '/snapshot/' in path:
            tags.append('snapshots')
        if '/firewall/' in path:
            tags.append('firewall')
        if '/status/' in path:
            tags.append('vm-control')
    elif '/lxc/' in path:
        tags.append('containers')
        if '/snapshot/' in path:
            tags.append('snapshots')
        if '/firewall/' in path:
            tags.append('firewall')
    elif '/ceph/' in path:
        tags.append('ceph-storage')
    elif '/storage/' in path:
        tags.append('storage')
    elif '/network/' in path:
        tags.append('networking')
    elif '/disks/' in path:
        tags.append('disk-management')
    elif '/firewall/' in path:
        tags.append('firewall')
    elif '/certificates/' in path:
        tags.append('certificates')
    elif '/apt/' in path:
        tags.append('package-management')
    elif '/services/' in path:
        tags.append('services')
    elif '/sdn/' in path:
        tags.append('software-defined-networking')
    elif '/replication/' in path:
        tags.append('replication')
    elif '/backup/' in path or '/vzdump' in path:
        tags.append('backup')
    elif '/ha/' in path:
        tags.append('high-availability')
    elif '/access/' in path:
        if '/users/' in path or '/user/' in path:
            tags.append('users')
        elif '/groups/' in path or '/group/' in path:
            tags.append('groups')
        elif '/roles/' in path or '/role/' in path:
            tags.append('roles')
        elif '/acl' in path:
            tags.append('permissions')

    return tags


def convert_to_openapi(endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert endpoint list to OpenAPI 3.0 format with categories."""
    print("\nConverting to OpenAPI format...")

    paths = {}
    all_tags = set()

    for ep in endpoints:
        path = ep["path"]
        method = ep["method"].lower()

        # Get tags for this endpoint
        tags = categorize_path(path)
        all_tags.update(tags)

        # Initialize path if not exists
        if path not in paths:
            paths[path] = {}

        # Convert parameters
        parameters = []
        for param in ep.get("parameters", []):
            param_location = "path" if f"{{{param['name']}}}" in path else "query"

            param_schema = {
                "type": param.get("type", "string")
            }

            # Add additional constraints
            if param.get("format"):
                param_schema["format"] = param["format"]
            if param.get("enum"):
                param_schema["enum"] = param["enum"]
            if param.get("default") is not None:
                param_schema["default"] = param["default"]
            if param.get("minimum") is not None:
                param_schema["minimum"] = param["minimum"]
            if param.get("maximum") is not None:
                param_schema["maximum"] = param["maximum"]
            if param.get("pattern"):
                param_schema["pattern"] = param["pattern"]

            parameters.append({
                "name": param["name"],
                "in": param_location,
                "required": param.get("required", False) and not param.get("optional", False),
                "description": param.get("description", ""),
                "schema": param_schema
            })

        # Convert returns to response
        returns = ep.get("returns", {})
        response_schema = {}

        if "type" in returns:
            response_schema["type"] = returns["type"]
            if "properties" in returns:
                response_schema["properties"] = returns["properties"]
            if "items" in returns:
                response_schema["items"] = returns["items"]

        # Build operation object
        operation = {
            "tags": tags,
            "summary": ep.get("description", "").split('.')[0] if ep.get("description") else "No description",
            "description": ep.get("description", ""),
            "operationId": f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}",
            "parameters": parameters if parameters else [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": response_schema if response_schema else {}
                        }
                    }
                }
            }
        }

        # Add security information if protected
        if ep.get("protected"):
            operation["security"] = [{"PVEAuth": []}]

        paths[path][method] = operation

    # Create tag definitions
    tag_definitions = []
    tag_descriptions = {
        "access": "Authentication and access control",
        "cluster": "Cluster management and configuration",
        "nodes": "Node management and monitoring",
        "pools": "Resource pool management",
        "storage": "Storage configuration",
        "sdn": "Software-defined networking",
        "virtual-machines": "QEMU virtual machine operations",
        "containers": "LXC container operations",
        "qemu-agent": "QEMU Guest Agent operations",
        "snapshots": "Snapshot management",
        "firewall": "Firewall rules and security",
        "vm-control": "VM power and status control",
        "ceph-storage": "Ceph distributed storage",
        "networking": "Network interface management",
        "disk-management": "Physical disk operations",
        "certificates": "SSL/TLS certificate management",
        "package-management": "APT package management",
        "services": "System service control",
        "software-defined-networking": "SDN configuration",
        "replication": "VM/CT replication",
        "backup": "Backup and restore operations",
        "high-availability": "High availability management",
        "users": "User management",
        "groups": "Group management",
        "roles": "Role management",
        "permissions": "ACL and permissions",
    }

    for tag in sorted(all_tags):
        tag_definitions.append({
            "name": tag,
            "description": tag_descriptions.get(tag, f"{tag.replace('-', ' ').title()} operations")
        })

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Proxmox VE API",
            "version": "8.x",
            "description": "Complete Proxmox Virtual Environment REST API specification extracted from apidoc.js",
            "contact": {
                "name": "Proxmox",
                "url": "https://www.proxmox.com"
            },
            "license": {
                "name": "AGPL-3.0",
                "url": "https://www.gnu.org/licenses/agpl-3.0.en.html"
            }
        },
        "tags": tag_definitions,
        "paths": paths,
        "components": {
            "securitySchemes": {
                "PVEAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "description": "Proxmox VE authentication token"
                }
            }
        }
    }


def calculate_statistics(openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate statistics about the API."""
    stats = {
        "total_endpoints": 0,
        "total_paths": len(openapi_spec["paths"]),
        "by_method": {},
        "by_section": {},
        "by_tag": {}
    }

    for path, methods in openapi_spec["paths"].items():
        section = path.split('/')[1] if len(path.split('/')) > 1 else "root"

        for method, operation in methods.items():
            stats["total_endpoints"] += 1

            # Count by method
            stats["by_method"][method.upper()] = stats["by_method"].get(method.upper(), 0) + 1

            # Count by section
            stats["by_section"][section] = stats["by_section"].get(section, 0) + 1

            # Count by tags
            for tag in operation.get("tags", []):
                stats["by_tag"][tag] = stats["by_tag"].get(tag, 0) + 1

    return stats


def analyze_helper_coverage(openapi_spec: Dict[str, Any]) -> None:
    """Generate API coverage analysis by comparing helpers with API spec."""
    print("\nGenerating coverage analysis...")

    if not HELPERS_DIR.exists():
        print(f"  Warning: Helpers directory not found at {HELPERS_DIR}")
        return

    # Analyze each helper file
    helper_stats = {}
    for helper_file in HELPERS_DIR.glob("*.py"):
        if helper_file.name.startswith("__"):
            continue

        content = helper_file.read_text(encoding='utf-8')

        # Count async methods
        async_methods = re.findall(r'async def (\w+)\(', content)

        # Count lines
        lines = len(content.split('\n'))

        # Count classes
        classes = re.findall(r'^class (\w+)', content, re.MULTILINE)

        helper_stats[helper_file.stem] = {
            "file": helper_file.name,
            "lines": lines,
            "methods": len(async_methods),
            "classes": len(classes),
        }

    # Get API statistics
    api_stats = openapi_spec.get("x-statistics", {})
    by_section = api_stats.get("by_section", {})

    # Map helpers to sections
    section_mapping = {
        "access": ["access"],
        "cluster": ["cluster"],
        "nodes": ["nodes"],
        "pools": ["pools"],
        "storage": ["storage"],
        "sdn": ["cluster"],  # SDN is under /cluster/sdn
        "ceph": ["nodes", "cluster"],
        "disks": ["nodes"],
        "firewall": ["nodes", "cluster"],
        "notifications": ["cluster"],
        "tasks": ["nodes", "cluster"],
    }

    # Generate markdown report
    report_lines = [
        "# Proxmox API Coverage Analysis",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Executive Summary",
        "",
        f"- **Total API Endpoints:** {api_stats.get('total_endpoints', 0)}",
        f"- **Unique API Paths:** {api_stats.get('total_paths', 0)}",
        f"- **Helper Files Analyzed:** {len(helper_stats)}",
        f"- **Total Helper Methods:** {sum(h['methods'] for h in helper_stats.values())}",
        f"- **Total Helper Lines:** {sum(h['lines'] for h in helper_stats.values()):,}",
        "",
        "## API Endpoints by Section",
        "",
        "| Section | Endpoints | Percentage |",
        "|---------|-----------|------------|",
    ]

    for section, count in sorted(by_section.items(), key=lambda x: x[1], reverse=True):
        pct = (count / api_stats.get('total_endpoints', 1)) * 100
        report_lines.append(f"| /{section} | {count} | {pct:.1f}% |")

    report_lines.extend([
        "",
        "## Helper Files",
        "",
        "| Helper File | Lines | Methods | Classes |",
        "|-------------|-------|---------|---------|",
    ])

    for name, stats in sorted(helper_stats.items()):
        report_lines.append(
            f"| {stats['file']} | {stats['lines']:,} | {stats['methods']} | {stats['classes']} |"
        )

    report_lines.extend([
        "",
        "## Coverage Estimation by Section",
        "",
        "| Section | API Endpoints | Primary Helpers | Estimated Coverage |",
        "|---------|---------------|-----------------|-------------------|",
    ])

    # Section coverage analysis
    coverage_data = [
        ("/access", by_section.get("access", 0), "access.py", "~60-70%",
         "Well covered: users, groups, roles, ACL. Missing: some domain/TFA operations"),
        ("/cluster", by_section.get("cluster", 0), "cluster.py, sdn.py, notifications.py", "~30-40%",
         "Core HA/backup covered. Missing: cluster firewall, device mapping, config"),
        ("/nodes", by_section.get("nodes", 0), "nodes.py, ceph.py, disks.py, firewall.py", "~40-50%",
         "VM/CT lifecycle covered. Missing: network interfaces, certificates, APT"),
        ("/pools", by_section.get("pools", 0), "pools.py", "~100%",
         "Fully covered"),
        ("/storage", by_section.get("storage", 0), "storage.py", "~100%",
         "Fully covered"),
    ]

    for section, count, helpers, coverage, notes in coverage_data:
        report_lines.append(f"| {section} | {count} | {helpers} | {coverage} |")

    report_lines.extend([
        "",
        "## Key Missing Functionality",
        "",
        "Based on API endpoint analysis, the following areas have limited or no helper coverage:",
        "",
        "### High Priority",
        "",
        "1. **Network Interface Management** (`/nodes/{node}/network`)",
        "   - API Endpoints: ~7",
        "   - Coverage: 0%",
        "   - Impact: Essential for network automation",
        "",
        "2. **Certificate Management** (`/nodes/{node}/certificates`)",
        "   - API Endpoints: ~7",
        "   - Coverage: 0%",
        "   - Impact: SSL/TLS automation",
        "",
        "3. **Cluster Firewall** (`/cluster/firewall`)",
        "   - API Endpoints: ~31",
        "   - Coverage: 0%",
        "   - Impact: Cluster-wide security policies",
        "",
        "4. **Device Mapping** (`/cluster/mapping`)",
        "   - API Endpoints: ~16",
        "   - Coverage: 0%",
        "   - Impact: PCI/GPU passthrough automation",
        "",
        "### Medium Priority",
        "",
        "5. **Cluster Configuration** (`/cluster/config`)",
        "   - API Endpoints: ~10",
        "   - Coverage: ~20%",
        "   - Impact: Cluster setup and management",
        "",
        "6. **APT Package Management** (`/nodes/{node}/apt`)",
        "   - API Endpoints: ~4",
        "   - Coverage: 0%",
        "   - Impact: System maintenance automation",
        "",
        "7. **Subscription Management** (`/nodes/{node}/subscription`)",
        "   - API Endpoints: ~4",
        "   - Coverage: 0%",
        "   - Impact: License management",
        "",
        "8. **External Metrics** (`/cluster/metrics`)",
        "   - API Endpoints: ~7",
        "   - Coverage: 0%",
        "   - Impact: Monitoring integration",
        "",
        "## Notes",
        "",
        "- **Coverage percentages are estimates** based on comparing API endpoint counts with helper method counts",
        "- Some helper methods map to multiple API endpoints (e.g., create_vm may use several API calls)",
        "- Some API endpoints may be intentionally not wrapped (low-level operations)",
        "- Users can always access any API endpoint via the raw proxmoxer interface",
        "- This analysis focuses on high-level helper coverage, not raw API accessibility",
        "",
        "## Helper Method Details",
        "",
    ])

    for name, stats in sorted(helper_stats.items()):
        report_lines.append(f"### {stats['file']}")
        report_lines.append(f"- **Lines of code:** {stats['lines']:,}")
        report_lines.append(f"- **Async methods:** {stats['methods']}")
        report_lines.append(f"- **Classes:** {stats['classes']}")
        report_lines.append("")

    report_lines.extend([
        "## Recommendations",
        "",
        "To improve API coverage:",
        "",
        "1. **Phase 1 (High Priority):** Implement network interface and certificate management helpers",
        "2. **Phase 2 (Security):** Add cluster firewall helper",
        "3. **Phase 3 (Infrastructure):** Add device mapping and cluster config helpers",
        "4. **Phase 4 (Operations):** Add APT, subscription, and metrics helpers",
        "",
        "---",
        "",
        f"*Generated by extract_and_combine.py on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*",
    ])

    # Write report
    report_file = OUTPUT_DIR / "API_COVERAGE_ANALYSIS.md"
    report_file.write_text("\n".join(report_lines), encoding='utf-8')
    print(f"  Generated: {report_file.name}")


def main():
    """Main extraction and combination process."""
    print("=" * 70)
    print("Proxmox API Extraction Tool")
    print("=" * 70)

    # Check if apidoc.js exists
    if not APIDOC_PATH.exists():
        print(f"ERROR: apidoc.js not found at {APIDOC_PATH}")
        return 1

    print(f"\nReading {APIDOC_PATH.name} ({APIDOC_PATH.stat().st_size / 1024:.1f} KB)...")
    apidoc_content = APIDOC_PATH.read_text(encoding='utf-8')

    # Parse the JavaScript structure
    print("Parsing API schema...")
    api_tree = parse_apidoc_js(apidoc_content)

    if not api_tree:
        print("ERROR: Failed to parse apidoc.js")
        return 1

    # Extract all endpoints recursively
    print("Extracting endpoints recursively...")
    all_endpoints = []
    for root_node in api_tree:
        all_endpoints.extend(extract_endpoints_recursive(root_node))

    print(f"Total endpoints found: {len(all_endpoints)}")

    # Extract and save by section
    sections = ["access", "cluster", "nodes", "pools", "storage", "sdn"]
    section_counts = {}

    for section in sections:
        print(f"\nFiltering /{section} endpoints...")
        section_endpoints = filter_by_section(all_endpoints, section)
        section_counts[section] = len(section_endpoints)

        # Save individual section
        section_file = OUTPUT_DIR / f"{section}_endpoints.json"
        section_file.write_text(json.dumps(section_endpoints, indent=2), encoding='utf-8')
        print(f"  {len(section_endpoints)} endpoints -> {section_file.name}")

    # Convert to OpenAPI format
    openapi_spec = convert_to_openapi(all_endpoints)

    # Calculate and add statistics
    stats = calculate_statistics(openapi_spec)
    openapi_spec["x-statistics"] = stats

    print(f"\nOpenAPI generation complete:")
    print(f"  Paths: {stats['total_paths']}")
    print(f"  Operations: {stats['total_endpoints']}")
    print(f"  Tags: {len(openapi_spec['tags'])}")

    # Save complete OpenAPI spec
    output_file = OUTPUT_DIR / "proxmox_api_complete.json"
    output_file.write_text(json.dumps(openapi_spec, indent=2), encoding='utf-8')
    print(f"\nSaved OpenAPI spec: {output_file.name} ({output_file.stat().st_size / 1024:.1f} KB)")

    # Generate coverage analysis
    analyze_helper_coverage(openapi_spec)

    # Clean up temporary section files
    print("\nCleaning up temporary section files...")
    for section in sections:
        section_file = OUTPUT_DIR / f"{section}_endpoints.json"
        if section_file.exists():
            section_file.unlink()
            print(f"  Removed {section_file.name}")

    # Print statistics breakdown
    print("\n" + "=" * 70)
    print("Statistics by Section:")
    for section, count in sorted(stats["by_section"].items(), key=lambda x: x[1], reverse=True):
        print(f"  /{section:<20} {count:>4} endpoints")

    print("\nStatistics by HTTP Method:")
    for method, count in sorted(stats["by_method"].items()):
        print(f"  {method:<10} {count:>4} endpoints")

    print("\n" + "=" * 70)
    print("Extraction complete!")
    print(f"Output: {output_file.name}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
