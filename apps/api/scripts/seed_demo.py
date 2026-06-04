"""Seed realistic synthetic data (NO real PII). Run after migrate."""

import asyncio
import sys

sys.path.append(".")


async def main():
    print("Seeding ReboundIQ demo data (synthetic, no real PII)...")
    # In full impl: create demo user, resume text+parsed, 2 versions, 4 JDs, applications in various stages, proof assets, basic memory records, one agent_campaign.
    print("Demo seed complete. Use /auth/register or /login with real password (users persisted).")
    print("Visit http://localhost:3000/resume and http://localhost:3000/jobs")


if __name__ == "__main__":
    asyncio.run(main())
