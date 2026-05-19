# Maps specific commit SHAs to new, down-to-earth messages while keeping Conventional Commit style.
# This script is used by `git filter-branch --msg-filter`.

$originalMsg = [Console]::In.ReadToEnd()
$sha = $env:GIT_COMMIT.ToLower()

switch ($sha) {
    # HEAD on feat/postgres-migration
    "46d47d1" {
        $new = "feat(config): Pulled all config into one place and hooked it up (DB/JWT/CORS). Dropped auto-create tables on startup and trimmed the dashboard payload"
        break
    }
    # Tag pre-postgres-migration points to this SHA, but we are only rewriting the branch ref.
    "a6d2555" {
        $new = "chore: Took a full snapshot right before starting the Postgres move"
        break
    }
    "10faf1d" {
        $new = "feat(ui): Added a conversation archive modal with simple Hebrew date sort/filter"
        break
    }
    "58a533e" {
        $new = "docs: Freshened up the README and Code Book to match the current architecture and setup"
        break
    }
    "92c111d" {
        $new = "feat(services): Wired up email alerts via SMTP for distress spikes and leave actions"
        break
    }
    "321964a" {
        $new = "feat(audio): Added voice transcription safely and auto-formatted loud/quiet parts for the UI"
        break
    }
    "65e5409" {
        $new = "feat(ui): Let teachers mark a student as returned early from a leave"
        break
    }
    "dd22cba" {
        $new = "feat(ui): Made student cards expandable and show fuller leave context"
        break
    }
    "d44e88d" {
        $new = "fix(engine): Fill in sensible defaults in the risk profile so the UI doesn’t crash on empty logs"
        break
    }
    "f34de7f" {
        $new = "chore(database): Tweaked the seed script and DB settings for smoother local runs"
        break
    }
    "f9e9fd0" {
        $new = "feat(security): Keep users signed in between sessions and auto-logout after 15 minutes idle"
        break
    }
    "be70e5f" {
        $new = "feat(frontend): Put together the admin area and hooked in the clinical risk view"
        break
    }
    Default {
        $new = $originalMsg
    }
}

[Console]::Out.Write($new)
