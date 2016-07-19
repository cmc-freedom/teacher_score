#!/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import csv
import sys
import os
import yaml

USAGE = "usage: {prog} input.csv"

class Teacher(object):

    PARAM_DICT = {'а': 0, 'б': 1, 'в': 2}
    EPS = 0.00001
    MIN_COUNT = 5
    DESCRIPTION = ''

    def __init__(self, name, subject):
        self.name = name
        self.subject = subject
        self.count = 0
        self.params = [[0, 0, 0] for i in range(self.PARAMS)]

    def vote(self, data):

        self.count += 1

        for i in range(self.PARAMS):
            j = self.PARAM_DICT.get(data[i], -1)

            if j != -1:

                self.params[i][j] += 1

    def score(self, i):
        if self.count < self.MIN_COUNT:
            return 'н/д'
        if self.params[i][2] / self.count > 0.5 + self.EPS:
            return 2
        elif (self.params[i][1] + self.params[i][2]) / self.count > 0.5 + self.EPS:
            return 3
        elif self.params[i][0] / self.count >= 1.0 - self.EPS:
            return 5
        elif self.params[i][0] / self.count > 0.5 + self.EPS:
            return 4
        else:
            return 'н/д'

    def criterion_description(self, i):
        description = self.DESCRIPTION[self.ROLE][i]
        if self.count < self.MIN_COUNT:
            return '## {q}\nНедостаточно данных'.format(q=description['question'])
        if self.params[i][2] / self.count > 0.5 + self.EPS:
            return '## {q}\n{a} ({c}/{all} = {p:.0f}%)' \
                .format(q=description['question'], a=description['answers'][2],
                        c=self.params[i][2], all=self.count, p=100 * self.params[i][2] / self.count)
        elif (self.params[i][1] + self.params[i][2]) / self.count > 0.5 + self.EPS:
            return '## {q}\n{a} ({c}/{all} = {p:.0f}%)' \
                .format(q=description['question'], a=description['answers'][3],
                        c=self.params[i][1] + self.params[i][2], all=self.count,
                        p=100 * (self.params[i][1] + self.params[i][2]) / self.count)
        elif self.params[i][0] / self.count >= 1.0 - self.EPS:
            return '## {q}\n{a}'.format(q=description['question'], a=description['answers'][5])
        elif self.params[i][0] / self.count > 0.5 + self.EPS:
            return '## {q}\n{a} ({c}/{all} = {p:.0f}%)' \
                .format(q=description['question'], a=description['answers'][4],
                        c=self.params[i][0], all=self.count,
                        p=100 * self.params[i][0] / self.count)
        else:
            return '## {q}\nНедостаточно данных'.format(q=description['question'])

    def description(self):
        result = '# {name}\n\nПерсональная статистика (в скобках указано количество проголосовавших)\n\n' \
            .format(name=self.name)

        for i in range(self.PARAMS):
            result += self.criterion_description(i) + '\n'

        return result


def mutate(c, mutate_dict):
    return mutate_dict.get(c, c)

class Lecturer(Teacher):

    PARAMS = 5
    ROLE = 'lecture'

    def vote(self, data):
        data[0] = mutate(data[0], {'б': 'в', 'в': '-'})
        data[1] = mutate(data[1], {'б': 'в', 'в': '-'})
        data[4] = mutate(data[4], {'а': 'в', 'б': 'а', 'в': '-'})

        super().vote(data)

class Seminarist(Teacher):

    PARAMS = 8
    ROLE = 'seminar'

    def vote(self, data):
        data[4] = mutate(data[4], {'а': 'в', 'б': 'а', 'в': '-'})

        super().vote(data)

def main():
    dirname = os.path.abspath(os.path.dirname(__file__))
    teacher_description = os.path.join(dirname, 'teacher_description.yaml')
    with open(teacher_description) as teacher_description:
        Teacher.DESCRIPTION = yaml.load(teacher_description)

    if len(sys.argv) != 2:
        print(USAGE.format(prog=sys.argv[0]), file=sys.stderr)
        exit(1)

    teachers = {}

    with open(sys.argv[1], 'r') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)

        for i, row in enumerate(reader):
            if i > 0:
                name, subject, data = row[0], row[2], row[4:]

                t = teachers.get(name, None)

                if t is None:
                    t = teachers[name] = Lecturer(name, subject)

                t.vote(data)

    result = []
    for key in sorted(teachers.keys()):
        t = teachers[key]
        result.append([t.subject, t.name, t.description()])
    result.sort()

    for subject, name, description in result:
        print(description)

if __name__ == "__main__":
    main()
