
MESSAGE_TABLE = {
    400: 'Bad Request',
    404: 'Not Found',
    500: 'Internal Server Error',
}

def formatter(status_code, 
                    error_message, 
                    cause_message = 'Not provided',
                    solve_message = 'Contact admin'):
    data = {
        'code': status_code,
        'message': MESSAGE_TABLE[status_code],
        'data': {
            'error': error_message,
            'cause': cause_message,
            'solve': solve_message
        }
    }

    return data