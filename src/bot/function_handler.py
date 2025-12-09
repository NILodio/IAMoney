import datetime
import logging

class FunctionHandler:
    def __init__(self):
        self.functions = self.initialize_functions()

    def get_functions_for_openai(self):
        tools = []
        for func in self.functions.values():
            tools.append({
                'type': 'function',
                'function': {
                    'name': func['name'],
                    'description': func['description'],
                    'parameters': func.get('parameters', {'type': 'object', 'properties': {}}),
                    'strict': func.get('strict', False),
                },
            })
        return tools

    def execute_function(self, function_name, parameters, context=None):
        if function_name not in self.functions:
            logging.error(f"Function not found: {function_name}")
            return f"Function '{function_name}' not found."
        func = self.functions[function_name]
        try:
            logging.debug(f"Executing function: {function_name}, parameters={parameters}")
            result = func['run'](parameters, context or {})
            logging.debug(f"Function executed successfully: {function_name}, result_length={len(str(result))}")
            return result
        except Exception as e:
            logging.error(f"Function execution failed: {function_name}, error={e}, parameters={parameters}")
            return f"Error executing function '{function_name}': {e}"

    def initialize_functions(self):
        return {
            'getPlanPrices': {
                'name': 'getPlanPrices',
                'description': 'Get available plans and prices information',
                'parameters': {'type': 'object', 'properties': {}},
                'run': self.get_plan_prices,
            },
            'loadUserInformation': {
                'name': 'loadUserInformation',
                'description': 'Find user name and email from the CRM',
                'parameters': {'type': 'object', 'properties': {}},
                'run': self.load_user_information,
            },
            'verifyMeetingAvailability': {
                'name': 'verifyMeetingAvailability',
                'description': 'Verify if a given date and time is available for a meeting before booking it',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'date': {
                            'type': 'string',
                            'format': 'date-time',
                            'description': 'Date of the meeting',
                        },
                    },
                    'required': ['date'],
                },
                'run': self.verify_meeting_availability,
            },
            'bookSalesMeeting': {
                'name': 'bookSalesMeeting',
                'description': 'Book a sales or demo meeting with the customer on a specific date and time',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'date': {
                            'type': 'string',
                            'format': 'date-time',
                            'description': 'Date of the meeting',
                        },
                    },
                    'required': ['date'],
                },
                'run': self.book_sales_meeting,
            },
            'currentDateAndTime': {
                'name': 'currentDateAndTime',
                'description': 'What is the current date and time',
                'parameters': {'type': 'object', 'properties': {}},
                'run': self.current_date_and_time,
            },
        }

    def get_plan_prices(self, parameters, context):
        return """*Service Plans and Pricing*

- Basic Plan: Includes core messaging features
- Professional Plan: Advanced features and higher limits
- Enterprise Plan: Unlimited features and priority support

Please contact us for detailed pricing information."""

    def load_user_information(self, parameters, context):
        return 'I am sorry, I am not able to access the CRM at the moment. Please try again later.'

    def verify_meeting_availability(self, parameters, context):
        try:
            date = datetime.datetime.fromisoformat(parameters['date'])
            if date.weekday() > 4:
                return 'Not available on weekends'
            hour = date.hour
            if hour < 9 or hour > 17:
                return 'Not available outside business hours: 9 am to 5 pm'
            return 'Available'
        except Exception:
            return 'Invalid date format provided'

    def book_sales_meeting(self, parameters, context):
        return 'Meeting booked successfully. You will receive a confirmation email shortly.'

    def current_date_and_time(self, parameters, context):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')

    def get_business_hours(self):
        return {
            'monday': '9:00 AM - 6:00 PM',
            'tuesday': '9:00 AM - 6:00 PM',
            'wednesday': '9:00 AM - 6:00 PM',
            'thursday': '9:00 AM - 6:00 PM',
            'friday': '9:00 AM - 6:00 PM',
            'saturday': 'Closed',
            'sunday': 'Closed',
        }

    def get_functions(self):
        return {
            'get_business_hours': self.get_business_hours,
            # Add more functions as needed
        } 