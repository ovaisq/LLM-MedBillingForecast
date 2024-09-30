#!/usr/bin/env python3
"""Seed Medicare locality data
    ©2024, Ovais Quraishi
"""

import csv
import json
from utils import ts_int_to_dt_obj
from utils import serialize_datetime
from database import insert_data_into_table

class TabDelimitedDictReader(csv.DictReader):
    def __init__(self, f, fieldnames=None, restkey=None, restval=None, dialect="excel", *args, **kwds):
        if fieldnames is not None:
            fieldnames = [fieldname.strip() for fieldname in fieldnames]
        super().__init__(f, fieldnames, restkey, restval, dialect, *args, **kwds)

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            self._fieldnames = next(self.reader)
            self._fieldnames = [fieldname.strip() for fieldname in self._fieldnames]
        return self._fieldnames

foo = []
with open('medicare_locality_configuration.txt', 'r', newline='') as csvfile:
    reader = TabDelimitedDictReader(csvfile, delimiter='\t')
    for row in reader:
        medicare_data = {
                         'mac': row['Medicare Adminstrative Contractor'],
                         'lnum': row['Locality Number'],
                         'state': row['State'],
                         'fsa': row['Fee Schedule Area'],
                         'counties': row['Counties']
                        }
        insert_data_into_table('medicare_data', medicare_data)
