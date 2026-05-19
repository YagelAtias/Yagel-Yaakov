import os
import sys


# Read the original message from stdin
original = sys.stdin.read()

# git passes the SHA via env var
sha = os.environ.get("GIT_COMMIT", "").lower()

# Map SHAs to new, down-to-earth messages while keeping Conventional Commits style
messages = {
    # HEAD on feat/postgres-migration
    "46d47d1": "feat(config): Pull all config into one place and connect it (DB/JWT/CORS); remove auto-create tables on startup; trim the dashboard payload",
    # Snapshot tag points here too; we only affect the branch ref
    "a6d2555": "chore: Take a full snapshot right before starting the Postgres move",
    "10faf1d": "feat(ui): Add a conversation archive modal with Hebrew date sort and filter",
    "58a533e": "docs: Update README and Code Book to match the current architecture and setup",
    "92c111d": "feat(services): Add email alerts via SMTP for distress spikes and leave actions",
    "321964a": "feat(audio): Add voice transcription safely and auto-format loud/quiet parts for the UI",
    "65e5409": "feat(ui): Allow teachers to mark a student as returned early from a leave",
    "dd22cba": "feat(ui): Make student cards expandable and show fuller leave context",
    "d44e88d": "fix(engine): Fill default values in the risk profile to prevent a UI crash on empty logs",
    "f34de7f": "chore(database): Update seed script and DB settings for smoother local runs",
    "f9e9fd0": "feat(security): Keep users signed in between sessions and sign them out after 15 minutes idle",
    "be70e5f": "feat(frontend): Build the admin area and connect the clinical risk view",
}

new_msg = messages.get(sha, original)
sys.stdout.write(new_msg)
