import os
import sys


# Read the original message from stdin
original = sys.stdin.read()

# git passes the SHA via env var
sha = os.environ.get("GIT_COMMIT", "").lower()

# Map SHAs to new, down-to-earth messages while keeping Conventional Commits style
messages = {
    # HEAD on feat/postgres-migration
    "46d47d1": "feat(config): Pulled all config into one place and hooked it up (DB/JWT/CORS). Dropped auto-create tables on startup and trimmed the dashboard payload",
    # Snapshot tag points here too; we only affect the branch ref
    "a6d2555": "chore: Took a full snapshot right before starting the Postgres move",
    "10faf1d": "feat(ui): Added a conversation archive modal with simple Hebrew date sort/filter",
    "58a533e": "docs: Freshened up the README and Code Book to match the current architecture and setup",
    "92c111d": "feat(services): Wired up email alerts via SMTP for distress spikes and leave actions",
    "321964a": "feat(audio): Added voice transcription safely and auto-formatted loud/quiet parts for the UI",
    "65e5409": "feat(ui): Let teachers mark a student as returned early from a leave",
    "dd22cba": "feat(ui): Made student cards expandable and show fuller leave context",
    "d44e88d": "fix(engine): Fill in sensible defaults in the risk profile so the UI doesn’t crash on empty logs",
    "f34de7f": "chore(database): Tweaked the seed script and DB settings for smoother local runs",
    "f9e9fd0": "feat(security): Keep users signed in between sessions and auto-logout after 15 minutes idle",
    "be70e5f": "feat(frontend): Put together the admin area and hooked in the clinical risk view",
}

new_msg = messages.get(sha, original)
sys.stdout.write(new_msg)
