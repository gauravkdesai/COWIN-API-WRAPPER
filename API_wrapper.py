import urllib.request
import urllib.parse
import logging
from datetime import date
import datetime
import json
import ast
import time
import platform
import os
from urllib.error import HTTPError, URLError
import config


class COWINConnection:
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s')
    logging.root.setLevel(logging.WARNING)

    @staticmethod
    def generate_url(api_name, api_type):
        assert api_type in config.COWIN_API
        api_url = config.COWIN_API[api_type][api_name]
        full_url = config.PROD_SERVER + api_url
        logging.info(f'full_url={full_url}')
        return full_url

    @staticmethod
    def get_data_from_url(api_name, api_type, url_input=None, data_input=None):
        url = COWINConnection.generate_url(api_name, api_type)
        if url_input:
            for k, v in url_input.items():
                url = url.replace(k, str(v))

        headers = {'User-Agent': config.user_agent, }
        try:
            if config.COWIN_API[api_type]['HTTP_METHOD'] == "POST":
                response = COWINConnection.fetch_data_using_POST(data_input, url, headers)
            else:  # GET
                response = COWINConnection.fetch_data_using_GET(data_input, url, headers)

            return_code = response.getcode()
            logging.info(f"Return code = {return_code}")
            if return_code == 200:  # OK
                data = response.read().decode('utf-8')
                data = ast.literal_eval(data)
                logging.info(f"data={(data)}")
                return data
            else:
                logging.warning(f'For url {url}, server returned code {return_code}. No data retrieved.')
        except HTTPError as e:
            logging.warning(f'HTTPError. Error code={e.errno}, Reason:{e.reason}')
        except URLError as e:
            logging.warning(f'URLError:Unable to reach to server. Error code={e.errno}, Reason:{e.reason}')

        return None

    @staticmethod
    def fetch_data_using_GET(data_input, url, headers):
        url = (url + "?" + urllib.parse.urlencode(data_input)) if data_input else url
        logging.info(f'GET request data={url}')
        request = urllib.request.Request(url, data=None, headers=headers)
        response = urllib.request.urlopen(request)
        return response

    @staticmethod
    def fetch_data_using_POST(data_input, url, headers):
        data = json.dumps(data_input)
        data = data.encode('ascii')
        logging.debug(f"After ascii encode data={data}")
        headers['content-type'] = 'application/json'
        request = urllib.request.Request(url, data,
                                         headers=headers)
        response = urllib.request.urlopen(request)
        return response

    @staticmethod
    def _format_date(date_obj):
        return date_obj.strftime("%d-%m-%Y")

    @staticmethod
    def _reverse_format_date(sdate):
        return datetime.datetime.strptime(sdate, '%d-%m-%Y').date()

    @staticmethod
    def get_formatted_date(date_obj):
        logging.debug(f'date_obj datatype={type(date_obj)}')
        if date_obj:
            if type(date_obj) == str:  # already formatted
                return date_obj
            else:
                return COWINConnection._format_date(date_obj)
        else:
            date_obj = date.today()
            return COWINConnection._format_date(date_obj)

    def get_states(self):
        return self.get_data_from_url('GET_STATES', 'METADATA_API')

    def get_districts(self, state_id):
        return self.get_data_from_url('GET_DISTRICT', 'METADATA_API', url_input={'{state_id}': state_id})

    def find_appointment_by_pin(self, pincode, for_date=None):
        for_date = COWINConnection.get_formatted_date(for_date)
        return self.get_data_from_url('GET_SESSIONS_BY_PIN', 'APPOINTMENT_AVAILABILITY_API',
                                      data_input={'pincode': str(pincode), 'date': for_date})

    def find_appointment_by_district(self, district_id, for_date=None):
        for_date = COWINConnection.get_formatted_date(for_date)
        return self.get_data_from_url('GET_SESSIONS_BY_DISTRICT', 'APPOINTMENT_AVAILABILITY_API',
                                      data_input={'district_id': str(district_id), 'date': for_date})

    def find_appointment_by_calendar_pin(self, pincode, for_date=None):
        for_date = COWINConnection.get_formatted_date(for_date)
        return self.get_data_from_url('GET_SESSIONS_BY_PIN_7_DAYS', 'APPOINTMENT_AVAILABILITY_API',
                                      data_input={'pincode': str(pincode), 'date': for_date})

    def find_appointment_by_calendar_district(self, district_id, for_date=None):
        for_date = COWINConnection.get_formatted_date(for_date)
        return self.get_data_from_url('GET_SESSIONS_BY_DISTRICT_7_DAYS', 'APPOINTMENT_AVAILABILITY_API',
                                      data_input={'district_id': str(district_id), 'date': for_date})

    def generate_otp(self, mobile):
        return self.get_data_from_url('GENERATE_OTP', 'USER_AUTHENTICATION_API', data_input={'mobile': mobile})

    def find_appointment_for_age_by_district(self, district_id=None, min_age_limit=None, from_date=None):
        from_date = COWINConnection.get_formatted_date(from_date)
        returned_data = self.find_appointment_by_calendar_district(district_id, from_date)

        if not returned_data or "centers" not in returned_data.keys():
            logging.warning("API did not return any data. continuing to check")
            return 0

        centers = returned_data["centers"]
        logging.info(f"Received {len(centers)} centers before filter")

        eligible_centers = []
        for center in centers:
            cur_sessions = center['sessions']
            eligible_sessions = []
            for cur_ses in cur_sessions:
                if cur_ses['min_age_limit'] <= min_age_limit and cur_ses['available_capacity'] > 0:
                    logging.info(f"Eligible session {cur_ses} at center {center}")
                    eligible_sessions.append(cur_ses)

            if len(eligible_sessions) > 0:
                temp_center = center.copy()
                temp_center['sessions'] = eligible_sessions
                eligible_centers.append(temp_center)

        logging.info(f'After filtering found {len(eligible_centers)} eligible and available centers')
        return eligible_centers

    @staticmethod
    def print_centers(centers):
        print("*" * 50)
        localtime = time.localtime()
        print(f"{len(centers)} Centers found at {time.strftime('%d-%m-%Y %I:%M:%S %p', localtime)}")
        if len(centers) > 0:
            for i, cen in enumerate(centers):
                print(f"{i + 1}.")
                print(
                    f"Name:{cen['name']}\nAddress:{cen['address']}\nblock_name:{cen['block_name']}\npincode:{cen['pincode']}\nCenter timing:{cen['from']} to {cen['to']}\nFee:{cen['fee_type']}")
                print(f"\tSessions:")
                for j, session in enumerate(cen['sessions']):
                    print(
                        f"\t{j + 1}.\tDate:{session['date']}\tAvailability:{session['available_capacity']}\tAge Limit:{session['min_age_limit']}\tVaccine:{session['vaccine']}")
                print("\n")

        print("*" * 50)

    def continuous_run(self, func, mobile=None, sleep_minutes=1, stop_if_found=False, push_notification_required=True,
                       otp_required=False, **kwargs):
        SLEEP_SECONDS = 60 * sleep_minutes  # 1 minutes
        while True:
            try:
                available_centers = func(self, **kwargs)
                if len(available_centers) > 0:
                    # success
                    if push_notification_required:
                        self.push_notification()
                    if otp_required:
                        otp = self.generate_otp(mobile=mobile)
                    if stop_if_found:
                        logging.warning(f'stop_if_found is set to {stop_if_found}, hence stopping the program')
                        break
                logging.info(f'Sleeping for {SLEEP_SECONDS} seconds')
                time.sleep(SLEEP_SECONDS)
            except Exception as e:
                logging.error(f'Exception while executing {str(func)}.\n{e}')

    @staticmethod
    def push_notification():
        title = config.push_notification_title
        message = config.push_notification_message

        if platform.system() == 'Darwin':
            command = f'''
            osascript -e 'display notification "{message}" with title "{title}"'
            '''
        else:
            logging.warning(f'Push notifications not supported for this system ({platform.system()})')
            return

        os.system(command)
