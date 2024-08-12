#!/bin/bash

MOUNT_POINT=/shared-drive/entrd_qa
SHARED_DRIVE_MYSQL_BACKUP_DIR=/shared-drive/entrd_qa/LanguageQA/qa-web-framework-db_and_reports-backups/MySQL-db-backup
SHARED_DRIVE_REPORTS_BACKUP_DIR=/shared-drive/entrd_qa/LanguageQA/qa-web-framework-db_and_reports-backups/uploaded-reports-backup

if mountpoint -q $MOUNT_POINT; then
        echo "$MOUNT_POINT is a mountpoint"
else
        echo "$MOUNT_POINT is not a mountpoint"
        exit 1
fi

if [[ -d "$SHARED_DRIVE_MYSQL_BACKUP_DIR" ]];
then
        echo "mt-afs01:/entrd_qa is properly mounted at /shared-drive/entrd_qa and there exists a MySQL backup directory"
else
        echo "Either mt-afs01:/entrd_qa was not properly mounted at /shared-drive/entrd_qa or a MySQL backup directory does not exist in the shared drive"
        exit 1
fi

if [[ -d "$SHARED_DRIVE_REPORTS_BACKUP_DIR" ]];
then
        echo "mt-afs01:/entrd_qa is properly mounted at /shared-drive/entrd_qa and there exists a reports backup directory"
else
        echo "Either mt-afs01:/entrd_qa was not properly mounted at /shared-drive/entrd_qa or a reports backup directory does not exist in the shared
drive"
        exit 1
fi

cd ~/qa-web-framework
docker compose up
