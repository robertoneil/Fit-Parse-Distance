import boto3
import uuid
from urllib.parse import unquote_plus
#fitdecode from https://pypi.org/project/fitdecode/
import fitdecode

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        tmpkey = key.replace('/', '')
        fit_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
        s3_client.download_file(bucket, key, fit_path)
        get_distance(fit_path,key)
        
def get_distance(fit_path,key):
    g = 9.81           #gravity in m/s^2
    m = 79.4 + 1       #rider + bike mass in kg with 1kg more simulating the wheel's rotational intertia
    Crr = 0.005        #approximate rolling resistance
    CdA = 0.324        #approximate CdA in m^2 - hands on hoods elbows bent - can be varied
    Rho = 1.225        #air density sea level STP
    dt = 1             #time step from the fit file; will be updated below
    speed_total = 0    #add up all the speeds, later divide by total steps to get average
    Vi = 0             #initialize the starting speed at 0  
    count = 0          #used to average the speed
    
    time_prev = None   #last fit message time, for edge cases when not just 1 second intervals
    total_time = 0     #length of the ride in seconds

    with fitdecode.FitReader(fit_path) as fit:
        for frame in fit:
            if isinstance(frame, fitdecode.FitDataMessage) and frame.has_field('power'):
                time_current = frame.get_field('timestamp').value
                if time_prev:
                    dt = (time_current-time_prev).seconds
                    total_time += dt
                
                p=(frame.get_field('power').value)
                Vf = ((-dt*(CdA*Rho*Vi**3-2*p+2*Crr*Vi*g*m)+Vi**2*m)/m)**.5
                speed_total += Vf
                count += 1
                Vi = Vf
                time_prev = time_current

    v = speed_total* 2.23694/count #convert from m/s to mph and average        
    t = total_time/3600

    #create a string with the results
    string = 'Average Speed: {:.2f} mph - Time: {:.2f} hours - Distance: {:.2f} miles'.format(v,t,(v*t))

    #write the data to a file
    file_name = '{}.txt'.format(key)
    lambda_path = '/tmp/{}'.format(file_name)
    s3_path = file_name
    
    with open(lambda_path, 'w+') as file:
        file.write(string)
        file.close()
    
    #move the file to the tr-fit-results bucket
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(lambda_path, 'tr-fit-results', s3_path, ExtraArgs={'ACL': 'public-read'})

    #print ('done -> {}'.format(string))  #for logging results