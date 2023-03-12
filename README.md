# iris api
Stacc exercise


# Running with Docker
## Setup
##### Clone project
```Shell
git clone https://github.com/martroben/iris_api
```

##### Change to project dir
```Shell
cd iris_api
```

##### Build image
```Shell
sudo docker build -t iris_api --rm -f api.Dockerfile .
```
Useful resources for building images:
- https://testdriven.io/blog/docker-best-practices/
- https://pythonspeed.com/docker/

##### (Optional) remove build stage
```Shell
sudo docker image prune --filter label=stage=iris_api_builder -f
```
Saves disk space, but slows down re-building image


##### Create volume
```Shell
sudo docker volume create --label iris_data
```

## Run
##### Testing from host
Tested on Ubuntu 22.04, bash 5.1.16
```Shell
sudo docker run \
	--rm \
	--name iris_api \
	--mount source=iris_data,target=/iris_data \
	--publish 7000:7000 \
	--env-file .env_showcase \
	iris_api \
	python3 /api/app.py
```
(`--publish` exposes container port on host)

##### Testing from a tester container shell
Create docker network:
```Shell
sudo docker network create \
    --subnet=188.0.0.0/24 \
    iris_network
```
Start the api container:
```Shell
sudo docker run \
	--rm \
	--name iris_api \
	--mount source=iris_data,target=/iris_data \
	--network iris_network \
	--ip 188.0.0.2 \
	--env-file .env_showcase \
	iris_api \
	python3 /api/app.py
```
Run an interactive tester container:
```Shell
sudo docker run \
    --rm \
	--name tester \
	--network iris_network \
	--ip 188.0.0.3 \
	--it \
	alpine
```
Install curl and head in tester container shell:
```Shell
apk add curl coreutils
```


## Showcase
Use `http://127.0.0.1:7000` in place of `http://188.0.0.1:7000` if testing from host
##### 0. Check if service is up
```Shell
curl http://188.0.0.1:7000/
```

##### 1. Check /summary endpoint with no data added (empty table)
```Shell
curl http://188.0.0.1:7000/api/v1/iris/summary
```
Result:
```
{
  "petal_length": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "petal_width": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "sepal_length": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "sepal_width": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "species": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "str"
  }
}
```

##### 2. Use /sync endpoint to pull, de-duplicate and store data
```Shell
curl http://188.0.0.1:7000/api/v1/iris/sync
```
Result:
```
Inserted 147 rows.
```

##### 3. Get summary again to verify that data has been inserted
```Shell
curl http://188.0.0.1:7000/api/v1/iris/summary
```
Result:
```
{
  "petal_length": {
    "maximum": 6.9,
    "median": 4.4,
    "minimum": 1.0,
    "n_total_values": 147,
    "n_unique_values": 43,
    "type": "float"
  },
  "petal_width": {
    "maximum": 2.5,
    "median": 1.3,
    "minimum": 0.1,
    "n_total_values": 147,
    "n_unique_values": 22,
    "type": "float"
  },
  "sepal_length": {
    "maximum": 7.9,
    "median": 5.8,
    "minimum": 4.3,
    "n_total_values": 147,
    "n_unique_values": 35,
    "type": "float"
  },
  "sepal_width": {
    "maximum": 4.4,
    "median": 3.0,
    "minimum": 2.0,
    "n_total_values": 147,
    "n_unique_values": 23,
    "type": "float"
  },
  "species": {
    "n_total_values": 147,
    "n_unique_values": 3,
    "type": "str"
  }
}
```

##### 4. Post new values in json format
```Shell
curl -X POST http://188.0.0.1:7000/api/v1/iris -H "Content-Type: application/json" -d "[{\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}, {\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}]"
```
Result:
```
Inserted 2 rows.
```

##### 5. Post new values in csv format
```Shell
curl -X POST http://188.0.0.1:7000/api/v1/iris -H "Content-Type: text/csv" -d $'sepal_length,sepal_width,petal_length,petal_width,species\n5.1,3.5,1.4,0.2,setosa\n5.2,2.7,3.9,1.4,versicolor\n7.2,3.0,5.8,1.6,virginica'
```
Have to use `$'csv-data-to-insert'` (with single quotes!) format in bash curl for the `\n` characters to be sent as newlines, not literal \n.

Result:
```
Inserted 3 rows.
```

##### 6. Post duplicates of existing values
```Shell
curl -X POST http://188.0.0.1:7000/api/v1/iris -H "Content-Type: application/json" -d "[{\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}, {\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}]"
```
Result:
```
Inserted 2 rows.
```

##### 7. Post duplicates of existing values by the /unique endpoint
```Shell
curl -X POST http://188.0.0.1:7000/api/v1/iris/unique -H "Content-Type: application/json" -d "[{\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}, {\"petal_length\": 10, \"petal_width\": 20, \"sepal_length\": 30, \"sepal_width\": 40}]"
```
Result:
```
Inserted 0 rows.
```

##### 8. Get all
```Shell
curl -sN http://188.0.0.1:7000/api/v1/iris/all | head --bytes 512
```
Result:
```
[
  {
    "petal_length": 1.7,
    "petal_width": 0.2,
    "sepal_length": 5.4,
    "sepal_width": 3.4,
    "species": "setosa"
  },
  {
    "petal_length": 4.6,
    "petal_width": 1.3,
    "sepal_length": 6.6,
    "sepal_width": 2.9,
    "species": "versicolor"
  },
  {
    "petal_length": 4.6,
    "petal_width": 1.4,
    "sepal_length": 6.1,
    "sepal_width": 3.0,
    "species": "versicolor"
  },
  {
    "petal_length": 1.4,
    "petal_width": 0.2,
    "sepal_length": 5.0,
    "sepal_width": 3.6,
    "sp
```

##### 9. Get with 'where' filter
```Shell
curl "http://188.0.0.1:7000/api/v1/iris?where=sepal_width>3.9&where=species%20IN%20(virginica,setosa)"
```
Result:
```
[
  {
    "petal_length": 1.5,
    "petal_width": 0.1,
    "sepal_length": 5.2,
    "sepal_width": 4.1,
    "species": "setosa"
  },
  {
    "petal_length": 1.5,
    "petal_width": 0.4,
    "sepal_length": 5.7,
    "sepal_width": 4.4,
    "species": "setosa"
  },
  {
    "petal_length": 1.2,
    "petal_width": 0.2,
    "sepal_length": 5.8,
    "sepal_width": 4.0,
    "species": "setosa"
  },
  {
    "petal_length": 1.4,
    "petal_width": 0.2,
    "sepal_length": 5.5,
    "sepal_width": 4.2,
    "species": "setosa"
  }
]
```

##### 10. Delete with the same 'where' filter
```Shell
curl -X DELETE "http://188.0.0.1:7000/api/v1/iris?where=sepal_width>3.9&where=species%20IN%20(virginica,setosa)"
```
Result:
```
Deleted 4 rows
```

##### 11. Summary of current state
```Shell
curl http://188.0.0.1:7000/api/v1/iris/summary
```
Result:
```
{
  "petal_length": {
    "maximum": 10.0,
    "median": 4.45,
    "minimum": 1.0,
    "n_total_values": 150,
    "n_unique_values": 44,
    "type": "float"
  },
  "petal_width": {
    "maximum": 20.0,
    "median": 1.4,
    "minimum": 0.1,
    "n_total_values": 150,
    "n_unique_values": 23,
    "type": "float"
  },
  "sepal_length": {
    "maximum": 30.0,
    "median": 5.85,
    "minimum": 4.3,
    "n_total_values": 150,
    "n_unique_values": 36,
    "type": "float"
  },
  "sepal_width": {
    "maximum": 40.0,
    "median": 3.0,
    "minimum": 2.0,
    "n_total_values": 150,
    "n_unique_values": 20,
    "type": "float"
  },
  "species": {
    "n_total_values": 150,
    "n_unique_values": 4,
    "type": "str"
  }
}
```

##### 12. Delete using the /all endpoint
```Shell
curl -X DELETE http://188.0.0.1:7000/api/v1/iris/all
```
Result:
```
Deleted 150 rows
```

##### 13. Get summary to verify that all data is deleted
```Shell
curl http://188.0.0.1:7000/api/v1/iris/summary
```
Result:
```
{
  "petal_length": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "petal_width": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "sepal_length": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "sepal_width": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "float"
  },
  "species": {
    "n_total_values": 0,
    "n_unique_values": 0,
    "type": "str"
  }
}
```
