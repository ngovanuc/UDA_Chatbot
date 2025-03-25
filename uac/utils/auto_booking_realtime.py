import datetime
import re

from uac.utils.constants import BOOKING_TIME


class BookingTimeUpdater:
    """
    A class to handle automatic updating of booking time slots.

    This class manages and updates booking time slots by ensuring dates are always in the future,
    automatically advancing past dates by weekly intervals.

    Args:
        config (Config): Configuration object containing initial booking time settings.

    Attributes:
        booking_time (str): String containing booking time slots information.
    """

    def __init__(self):
        """
        Initialize the BookingTimeUpdater with configuration settings.

        Args:
            config (Config): Configuration object containing booking_time parameter.
        """
        self.booking_time = BOOKING_TIME

    def parse_booking_time(self, schedule_time: str) -> list:
        """
        Parse the booking time string to extract day and date information.

        Uses regex to extract weekday numbers and dates from the booking_time string.

        Returns:
            list: List of tuples containing (weekday_number, date_string) matches.
        """
        pattern = r"Thứ (\d):.*ngày (\d{2}/\d{2}/\d{4})"
        matches = re.findall(pattern, schedule_time)
        return matches

    def update_booking_time(self):
        """
        Update booking time slots to ensure all dates are in the future.

        Automatically advances any past dates by weekly intervals until they are in the future.
        Updates the internal booking_time string with the new dates.
        """
        this_weeks = []
        next_weeks = []

        schedule_date_split = self.booking_time.split("\n")

        today = datetime.date.today()
        week_day_today = today.weekday() + 2

        # updated_booking_time = self.booking_time
        for date_ in schedule_date_split:
            week_day, date_str = self.parse_booking_time(date_)[0]
            booking_date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()

            if int(week_day) < week_day_today:
                if booking_date < today:
                    # Advance the date by one week until it's in the future
                    while booking_date <= today:
                        booking_date = booking_date + datetime.timedelta(days=7)
                    final_data = date_.replace(date_str, booking_date.strftime("%d/%m/%Y"))
                    next_weeks.append(final_data)
            else:
                if booking_date < today:
                    while booking_date < today:
                        booking_date = booking_date + datetime.timedelta(days=7)
                    final_data = date_.replace(date_str, booking_date.strftime("%d/%m/%Y"))
                    this_weeks.append(final_data)

        return this_weeks, next_weeks
