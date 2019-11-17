# betbrightFlask

# init the tables before running service
1. make sure all necessary packages are installed, such as mysql-connector, Flask, etc. 
2. create DB names betbrightflask in mysql database
sql> create database betbrightflask;
sql> grant all privileges on betbrightflask.* to 'teleuser'@'%';
3. cd root folder, open python console:
>>>from app import db
>>>db.create_all()

# add Swagger UI to python Flask
https://medium.com/@sean_bradley/add-swagger-ui-to-your-python-flask-api-683bfbb32b36