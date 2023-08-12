from typing import Optional

import cv2, imutils
import pytesseract
custom_config = r'--oem 3 --psm 6'
import re

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
    def parse_chapter_line(line):
        line = line.split()

        regex = '(\d+:)?(\d+):?(\d\d)\.?(\d\d\d)'
        while re.match(regex, line[-1]) is None:
            line.pop()
            if len(line) == 0:
                return None, None

        match = re.match(regex, line[-1])
        hours, minutes, seconds, milliseconds = match.group(1, 2, 3, 4)
        print(hours, minutes, seconds, milliseconds)
        if hours is None:
            hours = 0
        else:
            hours = hours[:-1]

        try:
            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds)
            milliseconds = int(milliseconds)
        except ValueError:
            return None, None

        time = timedelta(
            hours = hours,
            minutes = minutes,
            seconds = seconds,
            milliseconds = milliseconds
        )
        death = line[-2]
        death = death.replace('"', '1')
        if death in 'oO°':
            death = 0
        else:
            death = int(death)

        return time, death

    @classmethod
    async def from_image(cls, path, date = None):
        img = cv2.imread(path)
        img = imutils.rotate(img, -2)

        text = pytesseract.image_to_string(img, config=custom_config)
        print(text)
        lines = text.split('\n')
        start = 0
        starters = ['Fo', 'La']
        while start < len(lines) and lines[start][:2] not in starters:
            start += 1

        if start + 7 >= len(lines):
            log.exception("Tesseract exception.")
            log.exception(text)
            return None

        json = {'date': date}
        chapter_times = []
        chapter_death = []
        for chapter in range(7):
            line = lines[start]
            while line == '':
                start += 1
                if start >= len(lines):
                    log.exception("Not enough chapters.")
                    log.exception(text)
                    return None
                line = lines[start]
            time, death = cls.parse_chapter_line(line)
            if time is None:
                return None
            json[f"chapter{chapter+1}_time"] = time
            json[f"chapter{chapter+1}_death"] = death
            start += 1

        while start < len(lines) and lines[start][:2] != 'TO':
            start += 1

        if start >= len(lines):
            log.exception("Totals not detected.")
            log.exception(text)
            return None

        line = lines[start]
        time, death = cls.parse_chapter_line(line)
        if time is None:
            return None
        json["total_time"] = time
        json["total_death"] = death

        celeste_run = await cls.create(**json)
        print(celeste_run)
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

    def description(self):
        fd = lambda d: str(d).rjust(3)
        ft = lambda t: str(t)[:-3]

        return (
            f"`Forsaken City   `:skull:`{fd(self.chapter1_death)}` | :clock1: `{ft(self.chapter1_time)}`\n"
            f"`Old Site        `:skull:`{fd(self.chapter2_death)}` | :clock1: `{ft(self.chapter2_time)}`\n"
            f"`Celestial Resort`:skull:`{fd(self.chapter3_death)}` | :clock1: `{ft(self.chapter3_time)}`\n"
            f"`Golden Ridge    `:skull:`{fd(self.chapter4_death)}` | :clock1: `{ft(self.chapter4_time)}`\n"
            f"`Mirror Temple   `:skull:`{fd(self.chapter5_death)}` | :clock1: `{ft(self.chapter5_time)}`\n"
            f"`Reflection      `:skull:`{fd(self.chapter6_death)}` | :clock1: `{ft(self.chapter6_time)}`\n"
            f"`The Summit      `:skull:`{fd(self.chapter7_death)}` | :clock1: `{ft(self.chapter7_time)}`\n"
            f"`TOTALS          `:skull:`{fd(self.total_death)   }` | :clock1: `{ft(self.total_time)   }`\n"
        )


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
