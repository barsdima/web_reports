startDev () {
    echo "Starting development server..."

    # Start db server
    docker-compose up -d db

    # check if env/ exists else start new virtual env
    [[ ! -d ./env ]] && echo "Starting new virtual environment..." && python -m venv env

    # Windows 
    [[ -f ./env/Scripts/activate ]] && echo "Activating virtual environment..." && source env/Scripts/activate
    # Linux
    [[ -f ./env/bin/activate ]] && echo "Activating virtual environment..." && source env/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Migrate
    python Reporting/manage.py migrate

    # Start server
    python Reporting/manage.py runserver
}
          

startProd () {
    echo "Starting production server..."

    # Start Docker container
    echo "Starting container..." && docker-compose up -d
}

if [[ "$1" == "backup" ]];
then
    echo "Backing up sql file..." && docker exec qa-web-framework_db_1 mysqldump -uroot -proot reporting > ~/qa-web-framework/mysql_backup/backup_db.sql
fi


if [[ "$1" == "dev" ]]; then
    startDev
else
    startProd
fi

