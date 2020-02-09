from datetime import datetime, timedelta
from enum import Enum


class EntryType(Enum):
    # the default type
    ENTRY_TYPE_UNSPECIFIED = 0

    # Indicate the entry is the end of a night shift
    NIGHT_SHIFT = 1


class Entry:
    def __init__(self, entry_type, entry_time):
        # the type of entry
        self.entry_type = entry_type

        # the timestamp of entry
        self.entry_time = entry_time


class ReportData:
    def __init__(self, data):
        # a dictionary, key is date, value is a list of entries
        self.data = data


class Calculator:

    def __init__(self, start_date):
        # only time entries within [start, end] are considerd. Both sides are inclusive.
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=13)

    def is_date_valid(self, cur_date):
        if self.start_date <= cur_date <= self.end_date:
            return True
        return False

    def calc(self, content):
        # a dictionary, key is employee alia, value is ReportData
        result = {}

        rows = content.split('\n')
        for row in rows:
            if row.strip().endswith('DateTime'):
                continue
            cells = row.split('\t')
            if len(cells) < 7:
                continue

            alias = cells[3].strip()
            date_time = cells[6].strip()
            date_time_elem = date_time.split(' ')
            date_elem = datetime.strptime(date_time_elem[0], '%Y/%m/%d')
            time_elem = date_time_elem[-1]

            if not self.is_date_valid(date_elem):
                continue

            if alias not in result:
                result[alias] = []
                # two weeks:
                for _ in range(14):
                    # four entries each day
                    result[alias].append([])
            report_data = result[alias]

            index = (date_elem - self.start_date).days

            # if previous day doesn't have end entry, make a night shift entry
            if index > 0:
                if len(report_data[index - 1]) % 2 != 0:
                    report_data[index - 1].append(time_elem)
                    continue

            if len(report_data[index]) < 4:
                report_data[index].append(time_elem)
        return result
