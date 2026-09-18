# DRACULON-World Discord announcements

Sunday games and Monday council posts at 9 AM America/Chicago.

Setup: create DISCORD_GAMES_WEBHOOK and DISCORD_COUNCIL_WEBHOOK as GitHub Actions repository secrets. Use channel-specific Discord webhooks. Never commit webhook URLs.

Automatic posts stay off until the repository Actions variable DISCORD_POSTING_ENABLED is set to true. First run manual previews with Send unchecked, then test each channel with Send checked. Remove the old Sapphire repeating rules before enabling this system.

GitHub scheduled jobs can be delayed or dropped. Public repository schedules are disabled after 60 days without repository activity; check Actions periodically.

Dates use Central time with daylight saving adjustments. Discord renders each game in the reader's local timezone. Moony's Saturday rotation starts October 3, 2026, every 14 days. Larry is an admin.

Tests: python -m unittest discover -s automation -v
Preview: python automation/discord_posts.py --kind games

Delivery failures are not automatically retried. Check the channel before a fresh manual run; reruns of the same run cannot post.
