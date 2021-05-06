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
import sys
from urllib.error import HTTPError


class COWIN_Connection:
    
    # logger = logging.Logger('COWIN_Connection')
    # logger.setLevel(logging.DEBUG)
    logging.basicConfig()
    logging.root.setLevel(logging.WARNING)
    
    prod_server = """https://cdn-api.co-vin.in/api"""
    
    APIs = {
        'METADATA_API' :{
            'GET_STATES': """/v2/admin/location/states""",
            'GET_DISTRICT': """/v2/admin/location/districts/{state_id}"""
        },
        
        'APPOINTMENT_AVAILABILITY_API' :{
            'GET_SESSIONS_BY_PIN': """/v2/appointment/sessions/public/findByPin""",
            'GET_SESSIONS_BY_DISTRICT': """/v2/appointment/sessions/public/findByDistrict""",
            'GET_SESSIONS_BY_PIN_7_DAYS': """/v2/appointment/sessions/public/calendarByPin""",
            'GET_SESSIONS_BY_DISTRICT_7_DAYS': """/v2/appointment/sessions/public/calendarByDistrict"""
        },
        
        'USER_AUTHENTICATION_API' :{
            'GENERATE_OTP': """/v2/auth/public/generateOTP""",
            'CONFIRM_OTP': """/v2/auth/public/confirmOTP"""
        }
    }
    
    @staticmethod
    def generate_url(api, type):
        assert(type in COWIN_Connection.APIs.keys())
        api_url = COWIN_Connection.APIs[type][api]
        full_url = COWIN_Connection.prod_server + api_url
        logging.info(f'full_url={full_url}')
        return full_url
            
    def get_data_from_url(self, api, type, url_input=None, data_input=None):
    
        url = COWIN_Connection.generate_url(api, type)
        if url_input:
            for k,v in url_input.items():
                url = url.replace(k, str(v))

        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'


        if type == "USER_AUTHENTICATION_API": #POST
            data = json.dumps(data_input)
            # data = urllib.parse.urlencode(data)
            logging.debug(f"After urlencode data={data}")
            data = data.encode('ascii')
            logging.debug(f"After ascii encode data={data}")
            request = urllib.request.Request(url, data, headers={'User-Agent':user_agent, 'content-type': 'application/json'})
            response = urllib.request.urlopen(request)
        else:
            url = (url+"?"+urllib.parse.urlencode(data_input)) if data_input else url
            logging.info(f'GET request data={url}')
            request = urllib.request.Request(url, data=None, headers={'User-Agent':user_agent,} )
            response = urllib.request.urlopen(request)
    
   
        return_code = response.getcode()
        logging.info(f"Return code = {return_code}")
        if return_code == 200: #OK
            data = response.read().decode('utf-8')
            data = ast.literal_eval(data)
            logging.info(f"data={(data)}")
            return data
                
        return None
    
    @staticmethod
    def _format_date(date_obj):
        return date_obj.strftime("%d-%m-%Y")
    
    @staticmethod
    def _reverse_format_date(sdate):
        return datetime.datetime.strptime(sdate, '%d-%m-%Y').date()
    
    @staticmethod
    def get_date(date_obj):
        logging.debug(f'date_obj datatype={type(date_obj)}')
        if date_obj:
            if type(date_obj) == str:
                return date_obj
            else:
                return COWIN_Connection._format_date(date_obj)
        else:
            date_obj = date.today()
            return COWIN_Connection._format_date(date_obj)
        
    def get_states(self):
        return self.get_data_from_url('GET_STATES', 'METADATA_API')
    
    def get_districts(self, state_id):
        return self.get_data_from_url('GET_DISTRICT', 'METADATA_API', url_input={'{state_id}':state_id})
    
    def find_appointment_by_pin(self, pincode, date=None):
        date = COWIN_Connection.get_date(date)
        return self.get_data_from_url('GET_SESSIONS_BY_PIN', 'APPOINTMENT_AVAILABILITY_API', data_input={'pincode':str(pincode), 'date': date})
    
    def find_appointment_by_district(self, district_id, date=None):
        date = COWIN_Connection.get_date(date)
        return self.get_data_from_url('GET_SESSIONS_BY_DISTRICT', 'APPOINTMENT_AVAILABILITY_API', data_input={'district_id':str(district_id), 'date': date})
    
    def find_appointment_by_calendar_pin(self, pincode, date=None):
        date = COWIN_Connection.get_date(date)
        return self.get_data_from_url('GET_SESSIONS_BY_PIN_7_DAYS', 'APPOINTMENT_AVAILABILITY_API', data_input={'pincode':str(pincode), 'date':date})
    
    def find_appointment_by_calendar_district(self, district_id, date=None):
        date = COWIN_Connection.get_date(date)
        return self.get_data_from_url('GET_SESSIONS_BY_DISTRICT_7_DAYS', 'APPOINTMENT_AVAILABILITY_API', data_input={'district_id':str(district_id), 'date':date})
    
    def generate_otp(self, mobile):
        return self.get_data_from_url('GENERATE_OTP', 'USER_AUTHENTICATION_API', data_input={'mobile': mobile})

    def find_appointment_for_age_by_district(self, district_id=None, min_age_limit=None, from_date=None):
        from_date = COWIN_Connection.get_date(from_date)
        returned_data = self.find_appointment_by_calendar_district(district_id, from_date)
        
        if"centers" not in returned_data.keys():
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
                    
            if len(eligible_sessions)>0 :
                temp_center = center.copy()
                temp_center['sessions'] = eligible_sessions
                eligible_centers.append(temp_center)
                
        logging.info(f'After filtering found {len(eligible_centers)} eligible and available centers')
        self.print_centers(eligible_centers)
        return len(eligible_centers)

    @staticmethod
    def print_centers(centers):
        print("*"*50)
        localtime = time.localtime()
        print(f"{len(centers)} Centers found at {time.strftime('%d-%m-%Y %I:%M:%S %p', localtime)}")
        if len(centers) > 0: 
            for i, cen in enumerate(centers):
                print(f"{i+1}.")
                print(f"Name:{cen['name']}\nAddress:{cen['address']}\nblock_name:{cen['block_name']}\npincode:{cen['pincode']}\nCenter timing:{cen['from']} to {cen['to']}\nFee:{cen['fee_type']}")
                print(f"\tSessions:")
                for j, session in enumerate(cen['sessions']):
                    print(f"\t{j+1}.\tDate:{session['date']}\tAvailability:{session['available_capacity']}\tAge Limit:{session['min_age_limit']}\tVaccine:{session['vaccine']}")
                print("\n")
            
        
        print("*" * 50)
        
    def run_till_found(self, func, mobile=None, **kwargs):
        SLEEP_SECONDS = 60 * 10 #10 minutes
        while func(**kwargs) == 0:
            logging.info(f'Sleeping for {SLEEP_SECONDS} seconds')
            time.sleep(SLEEP_SECONDS)
        
        ### success
        self.push_notification(mobile=mobile)

    def push_notification(self, mobile=None):
        title = "Urgent"
        message = 'Book COWIN appointment urgently'
        
        if platform.system() == 'Darwin':
            command = f'''
            osascript -e 'display notification "{message}" with title "{title}"'
            '''
        else:
            logging.warning(f'Push notifications not supported for this system ({platform.system()})')
            return

        os.system(command)
        
        if mobile:
            logging.info(f'OTP generation request sent to {mobile}')
            try:
                otp = self.generate_otp(mobile=mobile)
            except HTTPError as e:
                logging.error(f'HTTPError {e.name} while generating otp to {mobile}.\n{e.getcode()}')

if __name__ == '__main__':
    mobile = sys.argv[1] if len(sys.argv) > 1 else None
    conn = COWIN_Connection()
    # conn.get_states()
    # conn.get_districts(21)
    # conn.find_appointment_by_pin(pincode=400067)
    # conn.find_appointment_by_district(district_id=395, date='04-05-2021')
    # conn.find_appointment_by_calendar_pin(pincode=400067)
    # conn.find_appointment_by_calendar_district(district_id=395) # Mumbai
    # conn.find_appointment_for_age_by_district(district_id = 395, min_age_limit = 18, from_date = date.today())
    kargs = {'district_id': 395, 'min_age_limit': 18, 'from_date': date.today()}
    conn.run_till_found(conn.find_appointment_for_age_by_district, mobile=mobile, **kargs) # add filters for type of vaccins, time slots
    # print(conn.generate_otp(mobile=mobile))
