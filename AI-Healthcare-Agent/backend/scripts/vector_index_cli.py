#!/usr/bin/env python3
"""CLI commands for vector index management.

Usage:
    python -m scripts.vector_index_cli rebuild-all
    python -m scripts.vector_index_cli rebuild-report <report-uuid>
    python -m scripts.vector_index_cli verify-index
    python -m scripts.vector_index_cli cleanup-orphans
    python -m scripts.vector_index_cli show-status
"""

import sys
import uuid


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: vector_index_cli <command> [args]")
        print("Commands: rebuild-all, rebuild-report <id>, verify-index, cleanup-orphans, show-status")
        sys.exit(1)

    command = args[0]

    from app.vector_recovery.recovery_manager import RecoveryManager

    mgr = RecoveryManager()

    if command == "rebuild-all":
        print("Starting full rebuild of vector index...")
        count = mgr.rebuild_all()
        print(f"Rebuild complete: {count} reports indexed")
        health = mgr.check_health()
        print(f"Index status: {health.status} ({health.indexed_reports}/{health.total_reports})")

    elif command == "rebuild-report":
        if len(args) < 2:
            print("Error: report UUID required")
            sys.exit(1)
        try:
            uuid.UUID(args[1])
        except ValueError:
            print(f"Error: invalid UUID format: {args[1]}")
            sys.exit(1)
        success = mgr.rebuild_report(args[1])
        if success:
            print(f"Report {args[1]} indexed successfully")
        else:
            print(f"Failed to index report {args[1]}")
            sys.exit(1)

    elif command == "verify-index":
        result = mgr.verify_index()
        print("Vector Index Verification:")
        print(f"  Collection exists:       {result['collection_exists']}")
        print(f"  Total reports:           {result['total_reports']}")
        print(f"  State entries:           {result['state_entries']}")
        print(f"  Indexed:                 {result['indexed']}")
        print(f"  Pending:                 {result['pending']}")
        print(f"  Stale:                   {result['stale']}")
        print(f"  Failed:                  {result['failed']}")
        print(f"  Version mismatches:      {result['version_mismatch']}")
        print(f"  Current model:           {result['current_embedding_model']}")
        print(f"  Healthy:                 {'✅' if result['healthy'] else '❌'}")

    elif command == "cleanup-orphans":
        count = mgr.cleanup_orphans()
        print(f"Cleaned up {count} orphaned state entries")

    elif command == "show-status":
        status = mgr.show_status()
        import json
        print(json.dumps(status, indent=2, default=str))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
