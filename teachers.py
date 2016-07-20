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

    def criterion_score(self, i):
        if self.count < self.MIN_COUNT:
            return None
        if self.params[i][2] / self.count > 0.5 + self.EPS:
            return 2
        elif (self.params[i][1] + self.params[i][2]) / self.count > 0.5 + self.EPS:
            return 3
        elif self.params[i][0] / self.count >= 1.0 - self.EPS:
            return 5
        elif self.params[i][0] / self.count > 0.5 + self.EPS:
            return 4
        else:
            return None

    def score(self):
        if self.count < self.MIN_COUNT:
            return None
        else:
            sum = 0
            count = 0

            for i in range(self.PARAMS):
                score = self.criterion_score(i)

                if score is not None:
                    sum += score
                    count += 1

            return sum / count

    def criterion_description(self, i):
        description = self.DESCRIPTION[self.ROLE][i]
        question = '- Вопрос: {q}\n'.format(q=description['question'])
        if self.count < self.MIN_COUNT:
            return '{q}- Ответ: Недостаточно данных.'.format(q=question)
        if self.params[i][2] / self.count > 0.5 + self.EPS:
            return '{q}- Ответ: {a}, **над этим нужно работать**. ({c}/{all} = {p:.0f}%)' \
                .format(q=question, a=description['answers'][2],
                        c=self.params[i][2], all=self.count, p=100 * self.params[i][2] / self.count)
        elif (self.params[i][1] + self.params[i][2]) / self.count > 0.5 + self.EPS:
            return '{q}- Ответ: {a}, *этому стоит уделить внимание*. ({c}/{all} = {p:.0f}%)' \
                .format(q=question, a=description['answers'][3],
                        c=self.params[i][1] + self.params[i][2], all=self.count,
                        p=100 * (self.params[i][1] + self.params[i][2]) / self.count)
        elif self.params[i][0] / self.count >= 1.0 - self.EPS:
            return '{q}- Ответ: {a}, единогласно, **отличный результат**!'.format(q=question, a=description['answers'][5])
        elif self.params[i][0] / self.count > 0.5 + self.EPS:
            return '{q}- Ответ: {a}. ({c}/{all} = {p:.0f}%)' \
                .format(q=question, a=description['answers'][4],
                        c=self.params[i][0], all=self.count,
                        p=100 * self.params[i][0] / self.count)
        else:
            return '{q}- Ответ: Недостаточно данных.'.format(q=question)

    def description(self):
        role = {'lecture': 'лекций', 'seminar': 'семинаров'}[self.ROLE]

        description = '## {name}\n\nКачество преподавания *{role}* (в скобках указано количество поддерживающих конкретное утверждение опрошенных).\n\nСредняя оценка преподавания по пятибальной шкале: {score}.\n' \
            .format(name=self.name, role=role, score=self.score())

        if self.begin == self.end:
            description += ('Место в общем рейтинге: {begin} из {top_len}.\n\n'
                            .format(begin=self.begin+1, top_len=self.top_len))
        else:
            description += ('Место в общем рейтинге: {begin}-{end} из {top_len}.\n\n'
                            .format(begin=self.begin+1, end=self.end+1, top_len=self.top_len))

        for i in range(self.PARAMS):
            description += self.criterion_description(i) + '\n'

        return description


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

def get_top(teachers):
    top = []

    def get_end(begin):
        for j in range(begin + 1, len(top)):
            if abs(top[j][0] - top[j-1][0]) > Teacher.EPS:
                return j - 1
        return len(top) - 1

    for key in teachers:
        teacher = teachers[key]
        if teacher.score() is not None:
            top.append([teacher.score(), teacher])
    top.sort(key=lambda pair: pair[0], reverse=True)

    begin, end = 0, get_end(0)

    for i in range(len(top)):
        if i > 0 and abs(top[i][0] - top[i-1][0]) > Teacher.EPS:
            begin, end = i, get_end(i)

        teacher = top[i][1]
        teacher.begin, teacher.end, teacher.top_len = begin, end, len(top)

    return top

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

    top = get_top(teachers)

    for score, teacher in top:
        print(teacher.description())

if __name__ == "__main__":
    main()
