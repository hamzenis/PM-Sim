# Grant permission to create databases

In order to execute tests, the demo user needs permission to create the database. If the permission is missing, run following command to access the mariadb:

```bash
docker exec -it softdsim-maria_application_db-1 mariadb -u root -p
```

Copy and paste the following Query to grant the demo user all necessary permissions:

```
GRANT ALL PRIVILEGES ON *.* TO 'demo'@'%' IDENTIFIED BY 'demo' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

# Structure of test cases

Each test case is in its respective TestView class. For each endpoint a class exists, using the same name with the suffix "Test". The folder structure in folder test_api remains the same as in src/api/. Each class needs a setUp, which provides the necessary components to run its tests. Some functionalities are sourced out in their own methods to understand their task better. Keep in mind that any changes in the code base may affect the tests directly or indirectly. 

# Run Test

You can run tests by using the Django built-in command:

```bash
python manage.py test
```

If you want to run a specific folder or file, you can specify it by connecting file paths with dots. In this example we want to navigate inside  the path /tests/test_api/views  and run any found test case within the views folder:

```bash
python manage.py test tests.test_api.views
```

This also works for classes and test methods by choosing the respective file. In this example we want to call the test_create_course method within the CourseViewTest class which is located in the test_course file:
````bash
python manage.py test tests.test_api.views.test_course.CourseViewTest.test_create_course