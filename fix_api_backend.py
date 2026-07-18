with open('backend/services/railways_api.py', 'r') as f:
    content = f.read()

# restore original logic to output 'high' for 30 minutes
content = content.replace('''    elif delay_minutes <= 15:
        passenger_load = "medium"
    elif delay_minutes <= 30:
        passenger_load = "medium"''', '''    elif delay_minutes <= 15:
        passenger_load = "medium"
    elif delay_minutes <= 30:
        passenger_load = "high"''')

content = content.replace('''    elif delay_minutes <= 15: passenger_load = "medium"
    elif delay_minutes <= 30: passenger_load = "medium"''', '''    elif delay_minutes <= 15: passenger_load = "medium"
    elif delay_minutes <= 30: passenger_load = "high"''')

with open('backend/services/railways_api.py', 'w') as f:
    f.write(content)
