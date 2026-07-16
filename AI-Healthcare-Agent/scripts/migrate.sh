#!/bin/bash
# Database migration helper

set -e

cd "$(dirname "$0")/../backend"

case "${1:-help}" in
    "new")
        alembic revision --autogenerate -m "${2:?Provide migration message}"
        ;;
    "upgrade")
        alembic upgrade head
        ;;
    "downgrade")
        alembic downgrade "${2:--1}"
        ;;
    "history")
        alembic history
        ;;
    "current")
        alembic current
        ;;
    *)
        echo "Usage: ./migrate.sh <command> [args]"
        echo ""
        echo "Commands:"
        echo "  new <message>    Create new migration"
        echo "  upgrade          Apply all pending migrations"
        echo "  downgrade [rev]  Revert migration (default: -1)"
        echo "  history          Show migration history"
        echo "  current          Show current migration"
        ;;
esac
