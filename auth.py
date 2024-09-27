# read the api_key.txt file
with open('/etc/secrets/api_key.txt', 'r') as file:
    API_KEY = file.read().replace('\n', '').split(",")
    

def authenticate(key):
    if key in API_KEY:
        return True
    else:
        return False


