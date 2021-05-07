PROD_SERVER = '''https://cdn-api.co-vin.in/api'''

COWIN_API = {'METADATA_API': {
    'GET_STATES': """/v2/admin/location/states""",
    'GET_DISTRICT': """/v2/admin/location/districts/{state_id}""",
    'HTTP_METHOD': 'GET'
}, 'APPOINTMENT_AVAILABILITY_API': {
    'GET_SESSIONS_BY_PIN': """/v2/appointment/sessions/public/findByPin""",
    'GET_SESSIONS_BY_DISTRICT': """/v2/appointment/sessions/public/findByDistrict""",
    'GET_SESSIONS_BY_PIN_7_DAYS': """/v2/appointment/sessions/public/calendarByPin""",
    'GET_SESSIONS_BY_DISTRICT_7_DAYS': """/v2/appointment/sessions/public/calendarByDistrict""",
    'HTTP_METHOD': 'GET'
}, 'USER_AUTHENTICATION_API': {
    'GENERATE_OTP': """/v2/auth/public/generateOTP""",
    'CONFIRM_OTP': """/v2/auth/public/confirmOTP""",
    'HTTP_METHOD': 'POST'
}}

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

push_notification_title: str = "COWIN Alert"
push_notification_message: str = 'COWIN appoints available'
