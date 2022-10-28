BINIT Ltd.

This api connects the database and the waste classification system to any forward facing pieces of this project. While it may be functional, it is not intended as a finalized product. There are glaring security vunuabilities and wonky implementations.

As of right now, the ip address of the AWS instance in 3.131.128.222 and the port this runs through is 8000. When the instance is running, typing 'http://13.59.146.184/' into a browser should display 'hello world!'. 

ROUTES

===================================================
'/'
Returns hello world; intended to simply be a test

===================================================
'/upload/<username>'
In a browser, this will display a little interface to upload a picture to the database under the username indicated by <username>. Using a POST method and attaching an image to it will allow you to bypass the interface

It returns a dummy classification as of now, a random selection between 'Trash', 'Recycle', and 'Compost'

===================================================
'<username>/unclassified'
This will return a list of all the files in the database that that user has uploaded, ut that haven't been manually classified. Each location in the list holds both the id of the file, the name, and the classification given by the machine

If there are no files, it will return an empty list

===================================================
'/<username>/weekly_total'
returns the total number of items uploaded in the last seven days

===================================================
'/<username>/monthly_total'
returns the total number of items uploaded in the last thirty days

===================================================
'/<username>/last_month_total'
returns the total number of items uploaded between thirty and sixty days ago

===================================================
'/<username>/waste_log_weekly'
returns a list of machine classifications and times of items uploaded in the last seven days

===================================================
'/download_by_name/<filename>'
This will return a file if there exists a file of that name in the Unclassified folder, or a 404 error if none are found

===================================================
'/download_by_id/<id>'
This will return a file if there exists a file of that id in the Unclassified folder, or a 404 error if none are found

===================================================
'/classify/<id>/<user classification>'
This attempts to reclassify the image of that id to the integer value given by <user classification>:
-1 - deletes the image
0 - Trash
1 - Recycle
2 - Compost.
If a different number is given, it will return -1
Otherwise it will attempt to reclassify the file in the database, and move that file to the appropriate folder. Returning 1 on a success or 0 on a failure

===================================================
'/delete/<id>'
This attempts to delete a file with that id. If the file has already been classified by the user, it will not be deleted
Returns 1 on a success, 0 on a failure

===================================================
'/data/<username>/<machine classification>/<days>'
This returns a list of all  the files that meet the parameters. It was uploaded by <username>, the machine classified it as <machine classification> (The same integers as <user classification> above) and it was within the last <days> days

===================================================
'/register/<username>/<password>/<email>/<household_size>/<location>'
This creates a user in the database with this information. Returns 1 if successful and 0 if either the username or the email are already in use
!!!! DO NOT USE THIS IN A PRODUCTION ENVIRONMENT THIS IS SIMPLY A PROOF OF CONCEPT AND HAS GLARING SECURITY VULNERABILITIES !!!!

===================================================
'/login/<username>/<password>'
This checks if the username and password are valid. Returns 1 if successful and 0 if not
!!!! DO NOT USE THIS IN A PRODUCTION ENVIRONMENT THIS IS SIMPLY A PROOF OF CONCEPT AND HAS GLARING SECURITY VULNERABILITIES !!!!