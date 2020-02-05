from datetime import datetime, timedelta
from enum import Enum


class EntryType(Enum):
    # the default type
    ENTRY_TYPE_UNSPECIFIED = 1

    # Indicate the entry is the end of a night shift
    NIGHT_SHIFT = 2


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

    def calc(self, content, start_date):
        # a dictionary, key is employee alia, value is ReportData
        result = {}

        rows = content.split('\n')
        for row in rows:
            if row.strip().endswith('DateTime'):
                continue
            cells = row.split('\t')
            if len(cells) < 7:
                continue

            alias = cells[3]
            date_time = cells[6].strip()
            date_time_elem = date_time.split(' ')
            date_elem = datetime.strptime(date_time_elem[0], '%Y/%m/%d')
            time_elem = datetime.strptime(date_time_elem[-1], '%H:%M:%S')

            if not self.is_date_valid(date_elem):
                continue

            if alias not in result:
                result[alias] = ReportData({})
            report_data = result[alias].data

            # if previous day doesn't have end entry, make a night shift entry
            previous_day = date_elem - timedelta(1)
            if previous_day in report_data and len(report_data[previous_day]) % 2 != 0:
                report_data[previous_day].append(
                    Entry(EntryType.NIGHT_SHIFT, time_elem))
                continue

            if date_elem not in report_data:
                report_data[date_elem] = []
            report_data[date_elem].append(
                Entry(EntryType.ENTRY_TYPE_UNSPECIFIED, time_elem))

        return result
