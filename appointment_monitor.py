import logging
import sys
from datetime import date
from logging.handlers import TimedRotatingFileHandler

from API_wrapper import COWINConnection


class AppointmentMonitor:
    log_file_name = "APPOINTMENT_MONITOR.log"
    log_format = '%(asctime)s %(levelname)s:%(message)s'
    log_handler = TimedRotatingFileHandler(log_file_name, when="midnight", interval=1)
    
    formatter = logging.Formatter(log_format)
    log_handler.setFormatter(formatter)

    log_handler.suffix = "%Y%m%d"
    logger = logging.getLogger("AppointmentMonitor")
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    @staticmethod
    def find_appointment_for_age_by_district(wrapper_conn, district_id=None, min_age_limit=None, from_date=None):
        returned_data = wrapper_conn.find_appointment_by_calendar_district(district_id, from_date)

        if not returned_data or "centers" not in returned_data.keys():
            AppointmentMonitor.logger.warning("API did not return any data. continuing to check")
            return 0

        centers = returned_data["centers"]
        AppointmentMonitor.logger.info(f"Received {len(centers)} centers before filter")

        eligible_centers = []
        for center in centers:
            cur_sessions = center['sessions']
            eligible_sessions = []
            for cur_ses in cur_sessions:
                if cur_ses['min_age_limit'] <= int(min_age_limit) and cur_ses['available_capacity'] > 0:
                    AppointmentMonitor.logger.info(f"Eligible session {cur_ses} at center {center}")
                    eligible_sessions.append(cur_ses)

            if len(eligible_sessions) > 0:
                temp_center = center.copy()
                temp_center['sessions'] = eligible_sessions
                eligible_centers.append(temp_center)

        AppointmentMonitor.logger.info(f'After filtering found {len(eligible_centers)} eligible and available centers')
        wrapper_conn.print_centers(eligible_centers)
        return eligible_centers


def main():
    district_id = sys.argv[1] if len(sys.argv) > 1 else None
    min_age_limit = sys.argv[2] if len(sys.argv) > 2 else None
    mobile = sys.argv[3] if len(sys.argv) > 3 else None

    conn = COWINConnection()
    monitor = AppointmentMonitor()
    kargs = {'district_id': district_id, 'min_age_limit': min_age_limit, 'from_date': date.today()}
    conn.continuous_run(monitor.find_appointment_for_age_by_district, mobile=mobile,
                        **kargs)


if __name__ == '__main__':
    main()
