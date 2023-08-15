from typing import Optional

import cv2, imutils
import pytesseract
import re
from math import pi, cos, sin
config = '--psm 4 --oem 3 -c tessedit_char_whitelist=0123456789.:/'

from tortoise.models import Model
from tortoise import fields
from datetime import date, timedelta

import logging
log = logging.getLogger("Ascension")

class CelesteRun(Model):
    # user_id        = fields.BigIntField()
    id             = fields.UUIDField(pk = True)
    date           = fields.DatetimeField(null = True)
    chapter1_time  = fields.TimeDeltaField()
    chapter2_time  = fields.TimeDeltaField()
    chapter3_time  = fields.TimeDeltaField()
    chapter4_time  = fields.TimeDeltaField()
    chapter5_time  = fields.TimeDeltaField()
    chapter6_time  = fields.TimeDeltaField()
    chapter7_time  = fields.TimeDeltaField()
    chapter1_death = fields.SmallIntField()
    chapter2_death = fields.SmallIntField()
    chapter3_death = fields.SmallIntField()
    chapter4_death = fields.SmallIntField()
    chapter5_death = fields.SmallIntField()
    chapter6_death = fields.SmallIntField()
    chapter7_death = fields.SmallIntField()
    total_time     = fields.TimeDeltaField()
    total_death    = fields.SmallIntField()

    @classmethod
    async def get_existing(cls, run_id):
        runs = await cls.filter(id = run_id)
        if len(runs) == 0:
            return None
        else:
            return runs[0]

    @staticmethod
    def parse_chapter_line(line, bside=False):
        line = line.split()
        if len(line) == 0:
            return None, None

        regex = '(\d+:)?(\d+)(:|\.)?(\d\d)\.?(\d\d\d)'
        while re.match(regex, line[-1]) is None:
            line.pop()
            if len(line) == 0:
                return None, None

        match = re.match(regex, line[-1])
        hours, minutes, seconds, milliseconds = match.group(1, 2, 4, 5)
        if hours is None:
            hours = 0
        else:
            hours = hours[:-1]

        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
        milliseconds = int(milliseconds)

        time = timedelta(
            hours = hours,
            minutes = minutes,
            seconds = seconds,
            milliseconds = milliseconds
        )
        try:
            death = int(line[-2])
            if bside:
                death += int(line[-3])
        except Exception:
            return None, None

        return time, death

    @staticmethod
    def horizontal_lines(img):
        img = imutils.rotate(img, -1.5)
        height, width, _ = img.shape
        debug = img.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 50)
        cv2.imwrite('data/tmp/edges.png', edges)

        ys = []
        lines = cv2.HoughLines(edges, 1, pi/180, 500)
        for line in lines:
            rho, theta = line[0]
            if abs(theta - pi / 2) > 0.1:
                continue
            b = sin(theta)
            y = int(b * rho)
            ys.append(y)
            cv2.line(debug, (0, y), (width, y), (0, 0, 255), 3)
            cv2.imwrite('data/tmp/debug.png', debug)

        ys.sort()
        return ys

    @staticmethod
    def read_image(path):
        img = cv2.imread(path)
        lines = CelesteRun.horizontal_lines(img)
        data = []
        bside = False
        for i in range(len(lines)-1):
            y0 = lines[i]
            y1 = lines[i+1]
            cropped = img[y0:y1,:]
            text = pytesseract.image_to_string(cropped, config=config)
            if len(data) == 0:
                regex = '\d\d?/20 \d+ \d+ (\d+:)?(\d+)(:|\.)?(\d\d)\.?(\d\d\d)'
                if re.search(regex, text) is not None:
                    bside = True
                    log.debug("B-SIDE ON")
            log.debug(text)
            time, death = CelesteRun.parse_chapter_line(text, bside)
            if time is not None:
                data.append((time, death))
        if len(data) == 8:
            return data
        return None

    @classmethod
    async def from_image(cls, path, date = None):
        json = {'date': date}
        data = CelesteRun.read_image(path)
        if data is None:
            return None

        for i, (time, death) in enumerate(data):
            prefix = 'total' if i == 7 else f'chapter{i+1}'
            json[f'{prefix}_time'] = time
            json[f'{prefix}_death'] = death

        celeste_run = await cls.create(**json)
        log.debug(str(celeste_run))
        return celeste_run

    def __str__(self):
        return f"""
            ID: {self.id}
            Date: {self.date}
            Forsaken City: {self.chapter1_death} | {self.chapter1_time}
            Old Site: {self.chapter2_death} | {self.chapter2_time}
            Celestial Resort: {self.chapter3_death} | {self.chapter3_time}
            Golden Ridge: {self.chapter4_death} | {self.chapter4_time}
            Mirror Temple: {self.chapter5_death} | {self.chapter5_time}
            Reflection: {self.chapter6_death} | {self.chapter6_time}
            The Summit: {self.chapter7_death} | {self.chapter7_time}
            TOTALS: {self.total_death} | {self.total_time}
        """

    def description(self, compare=None):
        fd = lambda d: str(d).rjust(3)
        ft = lambda t: str(t)[:-3] if t.microseconds != 0 else f'{t}.000'
        names = [
            'Forsaken City   ',
            'Old Site        ',
            'Celestial Resort',
            'Golden Ridge    ',
            'Mirror Temple   ',
            'Reflection      ',
            'The summit      ',
            'TOTALS          ',
        ]
        description = ''
        for i in range(8):
            name = names[i]
            pref = 'total' if i == 7 else f'chapter{i+1}'
            death = getattr(self, pref + '_death')
            time = getattr(self, pref + '_time')
            if compare is not None:
                pb = getattr(compare, pref + '_time') >= time
            else:
                pb = False
            emoji = ':star:' if pb else ''
            description += f"`{name}`:skull:`{fd(death)}` | :clock1: `{ft(time)}`{emoji}\n"
        return description


class Runner(Model):
    user_id     = fields.BigIntField(pk = True)
    runs        = fields.ManyToManyField('models.CelesteRun')
    server_rank = fields.IntField(default = 2147483647)

    @classmethod
    async def get_existing(cls, user_id):
        users = await cls.filter(user_id = user_id)
        if len(users) == 0:
            return None
        else:
            return users[0]

    @classmethod
    async def get_existing_or_create(cls, user_id):
        existing_user = await cls.get_existing(user_id)
        if existing_user is None:
            user = await cls.create(user_id = user_id)
            return user
        else:
            return existing_user

    async def add_run(self, run: CelesteRun):
        await self.runs.add(run)

    async def best_times(self):
        json = {
            'date': None,
        }
        async for run in self.runs.all():
            for argname in [f'chapter{x}' for x in range(1, 8)] + ['total']:
                if argname + '_time' not in json:
                    json[argname + '_time'] = getattr(run, argname + '_time')
                    json[argname + '_death'] = getattr(run, argname + '_death')
                else:
                    json[argname + '_time'] = min(
                            json[argname + '_time'],
                            getattr(run, argname + '_time')
                    )
                    json[argname + '_death'] = min(
                            json[argname + '_death'],
                            getattr(run, argname + '_death')
                    )
        best_run = CelesteRun(**json)
        return best_run


class Scoreboard(Model):
    id    = fields.UUIDField(pk = True)
    users = fields.ManyToManyField('models.Runner')

    async def add_user(self, user: Runner):
        await self.users.add(user)

    async def add_user_if_not_present(self, user: Runner):
        users = await self.users.filter(user_id = user.user_id)
        if len(users) == 0:
            await self.add_user(user)
            return True
        return False

    async def remove_user_if_present(self, user: Runner):
        users = await self.users.filter(user_id = user.user_id)
        if len(users) == 0:
            return False
        await self.users.remove(*users)
        return True
