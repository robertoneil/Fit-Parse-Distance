# Fit-Parse-Distance
Parse a .fit file, determine the distance the rider would have gone on a flat course with no head wind.

This is a basic lambda function for AWS.  It can be triggered by uploading a .fit file to an S3 bucket, which will call this lambda function.
The function will place the result in an output S3 bucket with the same file name, but a .txt extentsion that can be downloaded.  This
action can be modified so the results could be sent via another mechanism.

To provide the script with personalized user data (weight and CdA) you can add an option to look for a .txt parameter file based on the TR username which
can be parsed from the name of the fit file (the TR fit file naming convention starts with the username followed by the date and ride name).
