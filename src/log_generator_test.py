import re
import unittest
from datetime import timedelta

import log_generator


class LogGeneratorTestCase(unittest.TestCase):
    def test_default_options(self):
        options = log_generator.read_options()

        # There must be a default config
        self.assertIsNotNone(options)

        # A default path to the log file
        self.assertEquals("logfile.log", options.logfile, 'Invalid default log file location \'%s\'' % options.logfile)

        # A default time range is 1 day
        self.assertEquals('1d', options.duration, 'Invalid default time range: %s' % options.duration)

        # There are new log events every 5 minutes
        self.assertEquals('5m', options.increment, 'Invalid default increment: %s' % options.increment)

        # DDoS is inactive
        self.assertFalse(options.ddos, 'DDoS is supposed to be inactive by default')

        # DDoS, once it is activated, should trigger 4 hours into the day, generate 10x the usual load
        # and last for 2 minutes.
        self.assertEquals('1000 4h 10m', options.ddos_conf, 'Invalid default DDoS conf: \'%s\'' % options.ddos_conf)

    def test_parse_duration_days(self):
        days = timedelta(days=10)
        self.verify_time_options(days, self.parse_duration_options('10d'))
        self.verify_time_options(days, self.parse_duration_options('10D'))

    def test_parse_duration_hours(self):
        hours = timedelta(hours=3)
        self.verify_time_options(hours, self.parse_duration_options('3h'))
        self.verify_time_options(hours, self.parse_duration_options('3H'))

    def test_parse_duration_minutes(self):
        minutes = timedelta(minutes=125)
        self.verify_time_options(minutes, self.parse_duration_options('125m'))
        self.verify_time_options(minutes, self.parse_duration_options('125M'))

    def test_parse_duration_seconds(self):
        seconds = timedelta(seconds=59)
        self.verify_time_options(seconds, self.parse_duration_options('59s'))
        self.verify_time_options(seconds, self.parse_duration_options('59S'))

    def test_parse_duration_invalid_entry(self):
        self.verify_time_options(timedelta(days=2), self.parse_duration_options('invalid entry'))

    def test_parse_ddos_conf_default(self):
        expected = (1000, timedelta(hours=4), timedelta(minutes=10))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('1000 4h 10m'))

    def test_parse_ddos_conf_case_insensitive(self):
        expected = (1000, timedelta(hours=4), timedelta(minutes=10))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('1000 4H 10M'))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('1000 4h 10M'))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('1000 4H 10m'))

    def test_parse_ddos_conf_hours_only(self):
        expected = (100000, timedelta(hours=5), timedelta(hours=7))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('100000 5h 7h'))

    def test_parse_ddos_conf_hours_minutes(self):
        expected = (100, timedelta(hours=1), timedelta(minutes=15))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('100 1h 15m'))

    def test_parse_ddos_conf_hours_seconds(self):
        expected = (1500, timedelta(hours=1), timedelta(seconds=600))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('1500 1h 600s'))

    def test_parse_ddos_conf_minutes_only(self):
        expected = (120, timedelta(minutes=30), timedelta(minutes=5))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('120 30m 5m'))

    def test_parse_ddos_conf_minutes_hours(self):
        expected = (2000, timedelta(minutes=10), timedelta(hours=3))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('2000 10m 3h'))

    def test_parse_ddos_conf_minutes_seconds(self):
        expected = (10000, timedelta(minutes=3), timedelta(seconds=180))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('10000 3m 180s'))

    def test_parse_ddos_conf_seconds_only(self):
        expected = (1000000, timedelta(seconds=30), timedelta(seconds=25))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('1000000 30s 25s'))

    def test_parse_ddos_conf_seconds_hours(self):
        expected = (1300, timedelta(seconds=10), timedelta(hours=15))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('1300 10s 15h'))

    def test_parse_ddos_conf_seconds_minutes(self):
        expected = (3000, timedelta(seconds=2), timedelta(minutes=15))
        self.verify_ddos_options(expected, self.parse_ddos_conf_options('3000 2s 15m'))

    def test_parse_increment_minutes(self):
        minutes_min = timedelta(minutes=15, seconds=0)
        minutes_max = timedelta(minutes=15, seconds=59)
        self.verify_time_range_options(minutes_min, minutes_max, self.parse_increment_options('15m'))
        self.verify_time_range_options(minutes_min, minutes_max, self.parse_increment_options('15M'))

    def test_parse_increment_seconds(self):
        seconds_min = timedelta(seconds=10, milliseconds=0)
        seconds_max = timedelta(seconds=10, milliseconds=1000)
        self.verify_time_range_options(seconds_min, seconds_max, self.parse_increment_options('10s'))
        self.verify_time_range_options(seconds_min, seconds_max, self.parse_increment_options('10S'))

    def test_parse_increment_milliseconds(self):
        ms_min = timedelta(milliseconds=500, microseconds=0)
        ms_max = timedelta(milliseconds=500, microseconds=1000)
        self.verify_time_range_options(ms_min, ms_max, self.parse_increment_options('500ms'))
        self.verify_time_range_options(ms_min, ms_max, self.parse_increment_options('500MS'))
        self.verify_time_range_options(ms_min, ms_max, self.parse_increment_options('500Ms'))
        self.verify_time_range_options(ms_min, ms_max, self.parse_increment_options('500mS'))

    def verify_time_options(self, expected, actual):
        self.assertEquals(expected, actual, 'Wrong time delta %s' % actual)

    def verify_time_range_options(self, expected_min, expected_max, actual):
        self.assertTrue(expected_min <= actual <= expected_max, 'Wrong time delta %s' % actual)

    def verify_ddos_options(self, expected, actual):
        self.assertEquals(expected, actual, 'Wrong DDoS conf: \'%s\'' % ','.join(map(lambda x: str(x), actual)))

    @staticmethod
    def parse_duration_options(expression):
        options = log_generator.read_options()
        options.duration = expression
        return log_generator.parse_duration(options)

    @staticmethod
    def parse_increment_options(expression):
        options = log_generator.read_options()
        options.increment = expression
        return log_generator.parse_increment(options)

    @staticmethod
    def parse_ddos_conf_options(expression):
        options = log_generator.read_options()
        options.ddos_conf = expression
        return log_generator.parse_ddos_conf(options)

    def test_rand_ip(self):
        ip = log_generator.rand_ip()

        # There must be a new generated IP
        self.assertIsNotNone(ip)

        # The IP must be public
        self.assertFalse(re.match('^(10|127|169|172|192)\..*$', ip), 'Invalid IP %s' % ip)

        # The IP must be of v4
        octets = ip.split('.')
        self.assertEquals(4, len(octets))
        for octet in octets:
            self.assertTrue(1 <= int(octet) <= 255, 'Invalid octet value \'%s\'' % octet)

    def test_rand_user_agent(self):
        user_agent = log_generator.rand_user_agent()

        # There must be a new generated user agent
        self.assertIsNotNone(user_agent)

        # The generated agent must be one of the available user agents
        user_agents = map(lambda x: str(x).strip(), log_generator.read_conf('user_agents.txt'))
        self.assertTrue(user_agent in user_agents, 'Invalid user agent \'%s\'' % user_agent)

    def test_rand_auth(self):
        # An anonymous user
        self.assertEquals('-', log_generator.rand_auth(True))

        # Naming conventions: first_name.last_name
        username = log_generator.rand_auth(False)
        self.assertIsNotNone(username)
        (fname, lname) = username.split('.')
        self.assertIsNotNone(fname)
        self.assertIsNotNone(lname)

        # The generated username must match user records
        def f(x): return str(x).strip().lower()
        fnames = map(f, log_generator.read_conf('fnames.txt'))
        lnames = map(f, log_generator.read_conf('lnames.txt'))
        self.assertTrue(fname in fnames, 'Invalid first name \'%s\'' % fname)
        self.assertTrue(lname in lnames, 'Invalid last name \'%s\'' % lname)

    def test_rand_url(self):
        url = log_generator.rand_url()
        self.assertIsNotNone(url)

        # The url conforms to the expected format
        self.assertTrue(re.match('^http[s]?://www\.\w[-]?\w.*(jpg|png|html|xml|php|asp)$', url),
                        'Invalid URL \'%s\'' % url)

    def test_rand_http_status(self):
        status = log_generator.rand_http_status()
        self.assertTrue(status in map(lambda x: str(x), (200, 302, 404, 500)), 'Invalid HTTP status: %s' % status)

    def test_rand_res_size(self):
        size = log_generator.rand_res_size()
        self.assertTrue(1 <= size <= 5000000, 'Invalid resource size: %d' % size)


if __name__ == '__main__':
    unittest.main()
