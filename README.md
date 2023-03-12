# iris api
Stacc exercise


## Running with Docker
Tested on Ubuntu 22.04
### Setup
##### Clone project
```Shell
git clone 
```

##### Build image and create volume
```Shell
sudo docker build -t iris_api --rm -f Dockerfile_api .
sudo docker volume create --label iris_data
```

##### (Optional) remove build stage
```Shell
sudo docker image prune --filter label=stage=iris_api_builder -f
```

##### Run for local testing (-p exposes container port on host)
```Shell
sudo docker run \
	--rm \
	--name iris_api \
	--mount source=iris_data,target=/iris_data \
	-p 7000:7000 \
	--env-file .env_showcase \
	iris_api \
	python3 /api/app.py
```


### Showcase
##### 1. Check summary on an empty table - returns only column names and types
```Shell
curl http://127.0.0.1:7000/api/v1/iris/summary

> {"petal_length":{"type":"float"},"petal_width":{"type":"float"},"sepal_length":{"type":"float"},"sepal_width":{"type":"float"},"species":{"type":"str"}}
```

##### 2. Sync to download, de-duplicate and store data
```Shell
curl http://127.0.0.1:7000/api/v1/iris/sync

> Inserted 147 rows.
```

##### 3. Get summary again to see that data has been inserted
```Shell
curl http://127.0.0.1:7000/api/v1/iris/summary

> {"petal_length":{"maximum":6.9,"median":4.4,"minimum":1.0,"n_total_values":147,"n_unique_values":43,"type":"float"},"petal_width":{"maximum":2.5,"median":1.3,"minimum":0.1,"n_total_values":147,"n_unique_values":22,"type":"float"},"sepal_length":{"maximum":7.9,"median":5.8,"minimum":4.3,"n_total_values":147,"n_unique_values":35,"type":"float"},"sepal_width":{"maximum":4.4,"median":3.0,"minimum":2.0,"n_total_values":147,"n_unique_values":23,"type":"float"},"species":{"n_total_values":147,"n_unique_values":3,"type":"str"}}
```

##### 4. Post new values in json
```Shell
curl -X POST http://127.0.0.1:7000/api/v1/iris -H "Content-Type: application/json" -d "[{\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}, {\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}]"

> Inserted 2 rows.
```

##### 5. Insert csv
working on it

##### 6. Insert same values again
```Shell
curl -X POST http://127.0.0.1:7000/api/v1/iris -H "Content-Type: application/json" -d "[{\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}, {\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}]"

> Inserted 2 rows.
```

##### 7. Insert same values with /unique endpoint
```Shell
curl -X POST http://127.0.0.1:7000/api/v1/iris/unique -H "Content-Type: application/json" -d "[{\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}, {\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}]"

> Inserted 0 rows.
```

##### 8. Get all
```Shell
curl -sN http://127.0.0.1:7000/api/v1/iris/all | head --bytes 512

> [{"petal_length":1.4,"petal_width":0.2,"sepal_length":4.9,"sepal_width":3.0,"species":"setosa"},{"petal_length":5.6,"petal_width":2.1,"sepal_length":6.4,"sepal_width":2.8,"species":"virginica"},{"petal_length":1.9,"petal_width":0.4,"sepal_length":5.1,"sepal_width":3.8,"species":"setosa"},{"petal_length":4.0,"petal_width":1.3,"sepal_length":6.1,"sepal_width":2.8,"species":"versicolor"},{"petal_length":3.9,"petal_width":1.2,"sepal_length":5.8,"sepal_width":2.7,"species":"versicolor"},{"petal_length":1.4,"peta
```

##### 9. Get with 'where' filter
```Shell
curl "http://127.0.0.1:7000/api/v1/iris?where=sepal_width>3.9&where=species%20IN%20(virginica,setosa)"

> [{"petal_length":1.5,"petal_width":0.4,"sepal_length":5.7,"sepal_width":4.4,"species":"setosa"},{"petal_length":1.2,"petal_width":0.2,"sepal_length":5.8,"sepal_width":4.0,"species":"setosa"},{"petal_length":1.5,"petal_width":0.1,"sepal_length":5.2,"sepal_width":4.1,"species":"setosa"},{"petal_length":1.4,"petal_width":0.2,"sepal_length":5.5,"sepal_width":4.2,"species":"setosa"}]
```

##### 10. Delete with 'where' filter
```Shell
curl -X DELETE "http://127.0.0.1:7000/api/v1/iris?where=sepal_width>3.9&where=species%20IN%20(virginica,setosa)"

> Deleted 4 rows
```

##### 11. Summary to get current state
```Shell
curl http://127.0.0.1:7000/api/v1/iris/summary

> {"petal_length":{"maximum":10.0,"median":4.5,"minimum":1.0,"n_total_values":147,"n_unique_values":44,"type":"float"},"petal_width":{"maximum":20.0,"median":1.4,"minimum":0.1,"n_total_values":147,"n_unique_values":23,"type":"float"},"sepal_length":{"maximum":30.0,"median":5.9,"minimum":4.3,"n_total_values":147,"n_unique_values":36,"type":"float"},"sepal_width":{"maximum":40.0,"median":3.0,"minimum":2.0,"n_total_values":147,"n_unique_values":20,"type":"float"},"species":{"n_total_values":147,"n_unique_values":4,"type":"str"}}
```

##### 12. Delete using the /all endpoint
```Shell
curl -X DELETE http://127.0.0.1:7000/api/v1/iris/all

> Deleted 147 rows
```

##### 13. Get summary to see that data is deleted
```Shell
curl http://127.0.0.1:7000/api/v1/iris/summary/v1/iris/summary

> {"petal_length":{"type":"float"},"petal_width":{"type":"float"},"sepal_length":{"type":"float"},"sepal_width":{"type":"float"},"species":{"type":"str"}}
```

