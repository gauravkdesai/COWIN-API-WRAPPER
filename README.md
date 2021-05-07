# COWIN API Wrapper

[COWIN](https://www.cowin.gov.in) is an app created by Government of India(GOI) to track COVID vaccination program. This application allows citizens of India to schedule appointments for their vaccine doses.

Recently GOI released public API to this COWIN app on [API Setu](https://apisetu.gov.in/public/api/cowin#/Appointment%20Availability%20APIs/calendarByDistrict). This API makes it easier to find an appointment slot programmatically.

To make a developer's life easy, here I am releasing a python wrapper code that makes is easy for anyone to access COWIN public API programmatically. You can use this wrapper to check vaccination availability in your area. You can even generate an OTP using this wrapper. Using this wrapper you can write a code that filters available appointments to your location (using latitude and longitude), for your age group and send you an alert. 

I have written a quick program `ppointment_monitor.py` that uses wrapper `API_wrapper.py` in order continuously monitor COWIN app for available slots in a particular district for an age group and then generate MACOS alert and also generate an otp so that the person would get notified on mobile.

The usage is as follows
```
python /Users/gauravdesai/Documents/GitHub.nosync/Smart_COWIN/appointment_monitor.py <district_id> <min_age_limit> <mobile_number>
```

If you are wondering what is your district id then I have written two wrapper functions `get_states` and `get_districts` to get your state_id and then district_id.

Finally, 
I have written this wrapper primarily for myself to find an appointment slot but I will be very happy if this is useful to anyone else.
If you need any particular feature or you have written a piece of code generic enough to be included in this project, feel free to reach out to me.
