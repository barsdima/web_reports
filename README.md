QA test result management tool for Language team
Please find the documentation for this version of the tool here
https://confluence.labs.nuance.com/display/CTP/Language+QA+Test+Report+Tracking+Application

### How to use the application

#### View Reports

- http://mtl-coretech-qa03:8000/reports/
- Display reports that were submitted
- Can filter reports to be displayed
- Allows comparison of one or more reports
  - Uses the file that was uploaded during submission
- When logged in, you can edit or delete a report
- The table is sortable by column
  - Click on the header of the column you would like to sort the table by
  - Can be sorted in ascending/descending order
  - Currently, it's not very obvious that the table is sortable => an area for improvement

#### Submitting a Report

- http://mtl-coretech-qa03:8000/reports/submit_report/
- User must be logged in
- Datapack:
  - Please ensure the datapack's name is of the following format:
    - language-country-topic-version
    - e.g. fra-FRA-GEN-4.3.3
    - RegEx: ^[a-z]{3}-[A-Z]{3}-[A-Z]{3,}(\d\.\d+)?-(\d\.\d+)?\.\d+$
    - Code can be found in models.py  (`DataPack` model's `is_valid_name` method)
  - The application will make sure that the topic of the datapack is currently supported
    - If not, an error message of the following format will be shown:
      - {topic_name} is currently not supported. Please create a {topic_name} topic.
      - If this occurs, please inquire to a user who has administrative access to the Django application, to add a new topic.
- Testing type and Environment:
  - The lists of possible testing types and environments to choose from are provided as drop-downs
  - If your desired testing type and/or environment is not available, please inquire to a user who has administrative access to the Django application, to add a new testing type or environment.

This application has a feature that allows users to compare uploaded test result files.
The functionality of this feature is entirely dependent on the content of the uploaded file.
For each testing type, a specific file is expected to function correctly.
To ensure that this comparison feature works properly, please upload the correct test result file for each testing type.

- For the accuracy tests, please upload `result.txt`
- For the travel corpus tests, please upload `console_output_Obfuscated.txt`
- For the NTE5 tests, please upload the test-report csv
- For the load tests, please upload the krgloadSummary.xlsx

#### Datapack Tracking

- http://mtl-coretech-qa03:8000/reports/dptracking/
- Displays all the Datapacks that were reported about, and the reports belonging to them
- Can filter datapacks to be displayed
- When logged in, you can edit a Datapack
- The table is sortable by column
  - Click on the header of the column you would like to sort the table by
  - Can be sorted in ascending/descending order
  - Currently, it's not very obvious that the table is sortable => an area for improvement

#### Report Detail Page

- http://mtl-coretech-qa03:8000/reports/report/{report-id}/
- Display details about a report

#### Edit Report

- http://mtl-coretech-qa03:8000/reports/update_report/{report-id}/
- Allows user to edit a report
- User must be logged in
- The following fields are editable:
  - Status
  - Notes
  - JIRA

#### Delete Report

- http://mtl-coretech-qa03:8000/reports/delete_report/{report-id}/
- Allows user to delete a report
- User must be logged in

#### Edit Datapack
- http://mtl-coretech-qa03:8000/reports/update_datapack/{datapack-id}/
- Allows user to update a datapack's status
- User must be logged in

#### Creating a user

Currently, this application does not allow users to sign up for an account themselves.
Instead, they have to be created by an admin user (superuser) in the Django admin interface.

#### View a report file
- http://mtl-coretech-qa03:8000/reports/view_file/{report-id}
- Allows user to view a report file within the browser
- This only applied to browser viewable files under 1 MB

#### Donwload a report file
- http://mtl-coretech-qa03:8000/reports/download_file/{report-id}
- Allows user to download a report file from the browser

#### View the history of a Datapack
- http://mtl-coretech-qa03:8000/reports/datapack_history/{datapack-id}
- Allows user to view the history of all datapacks with this specific datapack-id
- This can be accessed by clicking on a datapack from the reports page

### Deployment on VM
1. Download docker engine (make sure `docker compose` is available)
2. `git clone` this project, and switch to this ("language") branch
3. Mount `mt-afs01:/entrd_qa` to `/shared-drive/entrd_qa` using NFSv4
   1. We will be backing up the uploaded reports and MySQL DB to the following locations in the file share:
      1. MySQL DB will be backed up to `\\mt-afs01\entrd_qa\LanguageQA\qa-web-framework-db_and_reports-backups\MySQL-db-backup`
      2. Uploaded reports will be backed up to `\\mt-afs01\entrd_qa\LanguageQA\qa-web-framework-db_and_reports-backups\uploaded-reports-backup`
      3. The DB can be backed up manually be running `./qa-web-framework-backup-db-and-reports.sh` in the root directory of the mtl-coretech-qa03 VM
    - Recovery of the db can be achieved using the following command: 
        - `cat /shared-drive/entrd_qa/LanguageQA/qa-web-framework-db_and_reports-backups/MySQL-db-backup/backup_db_<YYYY-MM-DD>.sql | docker exec -i $(docker container ps | grep qa-web-framework-db-1| cut -f1 -d" ") /usr/bin/mysql -u root -p reporting --password=root`
4. run `docker compose down`
5. To spin up the project, run `docker compose up`. If there are backend changes, run `docker compose up --build`. To view css changes, you may need to clear your browser cache.
    - At this stage, if the database was disconnected during deployment, you may ssh into root@mtl-coretech-qa03 and cd into `/root/qa-web-framework-db-backup` and run the folowing
    - command: `cat backup_db_<YYYY-MM-DD>.sql| docker exec -i $(docker container ps | grep qa-web-framework-db-1| cut -f1 -d" ") /usr/bin/mysql -u root -p reporting --password=root`, where `<YYYY-MM-DD>` is the date from which you wish to recover the database from
6. We would like to pre-populate the database with environments, testing types, and topics using fixtures:
   1. `docker exec -it qa-web-framework-web-1 bash` ("Enter" the Django container)
   2. `cd Reporting` (Where `manage.py` is located)
   3. `BUILD_TYPE=PROD python manage.py loaddata environments.json`
   4. `BUILD_TYPE=PROD python manage.py loaddata testing_types.json`
   5. `BUILD_TYPE=PROD python manage.py loaddata topics.json`
7. If there are migrations to apply, you may enter the Django Docker container in a new terminal, run `cd Reporting` and `python manage.py makemigrations`
8. To create a superuser (admin user), run the following commands:
   1. If not already "inside" the Django container: `docker exec -it qa-web-framework-web-1 bash` ("Enter" the Django container)
   2. `cd Reporting` (Where `manage.py` is located)
   3. `BUILD_TYPE=PROD python manage.py createsuperuser` (`BUILD_TYPE=PROD` is provided to `settings.py`)
   4. Follow the instructing prompts of the previous command