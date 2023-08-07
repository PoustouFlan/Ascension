from typing import Optional

import cv2
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
    date           = fields.DateField(null = True)
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

    @staticmethod
    def parse_chapter_line(line):
        line = line.split()

        regex = '(\d*:)?(\d*):(\d\d)\.(\d\d\d)'
        while re.match(regex, line[-1]) is None:
            line.pop()
            if len(line) == 0:
                return None, None

        match = re.match(regex, line[-1])
        hours, minutes, seconds, milliseconds = match.group(1, 2, 3, 4)
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
        death = int(line[-2])

        return time, death

    @classmethod
    async def from_image(cls, path):
        img = cv2.imread(path)
        text = pytesseract.image_to_string(img, config=custom_config)
        lines = text.split('\n')
        start = 0
        starters = ['Fo', 'La']
        while start < len(lines) and lines[start][:2] not in starters:
            start += 1

        if start + 7 >= len(lines):
            log.exception("Tesseract exception.")
            log.exception(text)
            return None

        json = {}
        chapter_times = []
        chapter_death = []
        for chapter in range(7):
            line = lines[start + chapter]
            time, death = cls.parse_chapter_line(line)
            json[f"chapter{chapter+1}_time"] = time
            json[f"chapter{chapter+1}_death"] = death

        start += 7
        while start < len(lines) and lines[start][:2] != 'TO':
            start += 1

        if start >= len(lines):
            log.exception("Totals not detected.")
            log.exception(text)
            return None

        line = lines[start]
        time, death = cls.parse_chapter_line(line)
        json["total_time"] = time
        json["total_death"] = death

        print(json)
        celeste_run = await cls.create(**json)
        return celeste_run

    def __str__(self):
        return f"""
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


class Runner(Model):
    user_id   = fields.BigIntField(pk = True)
    runs      = fields.ManyToManyField('models.CelesteRun')

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


class Scoreboard(Model):
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
