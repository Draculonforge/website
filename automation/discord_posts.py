"""Weekly DRACULON-World announcements. Preview by default; --send posts once."""
import argparse
from datetime import date, datetime, time, timedelta
import json
import os
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

CENTRAL = ZoneInfo('America/Chicago')
ANCHOR = date(2026, 10, 3)
GAMES = [
    (0, '18:00', "Spanky's Memorial Mini Campaign", 'YummyTaco'),
    (1, '18:30', 'Lost Mines of Phandelver', 'Larry'),
    (2, '20:00', "Yummytaco's Weekly One-Shot — 1e / 2e / AD&D", 'YummyTaco'),
    (3, '18:30', 'Ghosts of Saltmarsh', 'Larry'),
    (4, '18:00', 'Forgotten Realms', 'Moony'),
    (5, '18:00', 'Curse of Strahd', 'Navy'),
    (6, '13:00', "Phantom's Embrace", 'evilfirefox911'),
]

def sunday_for(day):
    return day - timedelta(days=(day.weekday() + 1) % 7)

def moony_plays(day):
    return day >= ANCHOR and (day - ANCHOR).days % 14 == 0

def start_time(day, clock):
    return int(datetime.combine(day, time.fromisoformat(clock), CENTRAL).timestamp())

def base_payload(title, description):
    return {
        'username': 'Draculon Council',
        'allowed_mentions': {'parse': []},
        'embeds': [{'title': title, 'description': description,
                    'color': 9431584, 'author': {'name': 'DRACULON-World'}}],
    }

def game_payload(day):
    sunday = sunday_for(day)
    saturday = sunday + timedelta(days=6)
    lines = ['All game dates and times display in your local timezone.', '']
    for offset, clock, title, dm in GAMES:
        stamp = start_time(sunday + timedelta(days=offset), clock)
        end = f" – <t:{start_time(saturday, '17:00')}:t>" if title == "Phantom's Embrace" else ''
        lines.extend([f'**{title}**', f'<t:{stamp}:F>{end}', f'DM: {dm or "To be confirmed"}'])
        if title == "Spanky's Memorial Mini Campaign":
            lines.append('Assistant DM: Larry')
        if title == "Phantom's Embrace":
            lines.append('Players: 5 / 8 • 3 open slots')
        lines.append('')
    if moony_plays(saturday):
        stamp = start_time(saturday, '18:00')
        lines.extend(['**Continent of Vilyra — this Saturday**', f'<t:{stamp}:F>', 'DM: Moony', ''])
    else:
        next_game = ANCHOR if saturday < ANCHOR else saturday + timedelta(days=7)
        stamp = start_time(next_game, '18:00')
        lines.extend(['**Continent of Vilyra — no session this Saturday**',
                      f'Next session: <t:{stamp}:F>', 'DM: Moony', ''])
    lines.extend(['**PLAY-BY-POST**', "Terry's Play-by-Post • DM: Terry",
                  'Vampire of the Masquerade • Yummytaco'])
    return base_payload(f'Weekly Games • {sunday:%b %d} – {saturday:%b %d, %Y}', '\n'.join(lines))

def council_payload():
    return base_payload('Meet the Council', '''Your guides and contacts across the realm.

👑 **ADMINS**
**Terry** • terrystoddart
**Walthair** • walthair
**Larry** • larryssanders

🛡️ **MODERATORS**
**Amanda** • cowboyangusw
**Mary** • mary076183
**Mama** • mamamermaid88

🎲 **DUNGEON MASTERS**
**Moony** • darkwolf1580
**Navy** • Navyhm2002
**EvilFoxFire** • evilfirefox911

**Need help?**
Contact an admin for server questions, a moderator for community concerns, or your DM for questions about your game.''')

def send(payload, webhook):
    # Keep credentials out of logs and prevent accidental non-Discord destinations.
    if not re.fullmatch(r'https://discord\.com/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_.-]+', webhook):
        raise ValueError('Missing or invalid Discord webhook secret.')
    request = Request(webhook + '?wait=true', data=json.dumps(payload).encode(),
                      headers={'Content-Type': 'application/json', 'User-Agent': 'DraculonSchedule/1.0'},
                      method='POST')
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        if not result.get('id'):
            raise ValueError('Discord did not confirm a message ID. Check the channel before retrying.')
        print('Discord confirmed the post. Message ID:', result['id'])
    except HTTPError as exc:
        raise ValueError(f'Discord returned HTTP {exc.code}. Check the channel before retrying.') from None
    except (URLError, TimeoutError, OSError):
        raise ValueError('Delivery could not be confirmed. Check Discord before retrying to avoid duplicates.') from None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['games', 'council'], required=True)
    parser.add_argument('--date', type=date.fromisoformat, help='Preview date, YYYY-MM-DD')
    parser.add_argument('--send', action='store_true')
    args = parser.parse_args()
    if args.send and args.date:
        parser.error('--date is for previews only')
    day = args.date or datetime.now(CENTRAL).date()
    # Do not resend on a GitHub job rerun; manual fresh runs are deliberate resends.
    if args.send and int(os.getenv('GITHUB_RUN_ATTEMPT', '1')) > 1:
        parser.error('Rerun posting blocked. Check Discord, then start a new manual run if needed.')
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if args.send and os.getenv('GITHUB_EVENT_NAME') == 'schedule' and event_path:
        event = json.loads(Path(event_path).read_text())
        expected = 6 if args.kind == 'games' else 0
        if day.weekday() != expected:
            parser.error('Scheduled run arrived on the wrong day; refusing a stale post.')
    payload = game_payload(day) if args.kind == 'games' else council_payload()
    if args.send:
        send(payload, os.getenv('DISCORD_WEBHOOK', ''))
    else:
        print(json.dumps(payload, ensure_ascii=True, indent=2))

if __name__ == '__main__':
    try:
        main()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
