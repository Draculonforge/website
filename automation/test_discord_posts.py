import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import discord_posts as posts

class ScheduleTests(unittest.TestCase):
    def test_sunday_boundary(self):
        self.assertEqual(posts.sunday_for(date(2026, 9, 27)), date(2026, 9, 27))
        self.assertEqual(posts.sunday_for(date(2026, 10, 3)), date(2026, 9, 27))

    def test_moony_rotation(self):
        for day in [date(2026, 10, 3), date(2026, 10, 17), date(2026, 10, 31)]:
            self.assertTrue(posts.moony_plays(day))
        for day in [date(2026, 9, 19), date(2026, 9, 26), date(2026, 10, 10)]:
            self.assertFalse(posts.moony_plays(day))

    def test_on_and_off_week(self):
        active = posts.game_payload(date(2026, 9, 27))['embeds'][0]['description']
        inactive = posts.game_payload(date(2026, 10, 4))['embeds'][0]['description']
        self.assertIn('this Saturday**', active)
        self.assertIn('no session this Saturday', inactive)
        self.assertIn(str(posts.start_time(date(2026, 10, 17), '18:00')), inactive)

    def test_dst_and_eastern_conversion(self):
        for day, utc_hour in [(date(2026, 10, 27), 1), (date(2026, 11, 3), 2)]:
            stamp = posts.start_time(day, '20:00')
            self.assertEqual(datetime.fromtimestamp(stamp, ZoneInfo('UTC')).hour, utc_hour)
            self.assertEqual(datetime.fromtimestamp(stamp, ZoneInfo('America/New_York')).hour, 21)

    def test_larry_admin_and_no_pings(self):
        payload = posts.council_payload()
        description = payload['embeds'][0]['description']
        self.assertLess(description.index('larryssanders'), description.index('MODERATORS'))
        self.assertEqual(payload['allowed_mentions'], {'parse': []})

    def test_payload_limits(self):
        for payload in [posts.game_payload(date(2026, 9, 27)), posts.council_payload()]:
            self.assertLess(len(payload['embeds'][0]['description']), 4096)

    def test_invalid_destination_never_sends(self):
        with patch('discord_posts.urlopen') as network:
            with self.assertRaises(ValueError):
                posts.send(posts.council_payload(), 'https://example.com/secret')
            network.assert_not_called()

if __name__ == '__main__':
    unittest.main()
