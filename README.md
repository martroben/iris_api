# Iris api
Stacc exercise


# Description
REST API to demonstrate downloading, storing and mutating the iris dataset.


## Endpoints
root path: `./api/v1`

### GET:
- `/iris` - query stored data. Use "where" parameter for filtering.
- `/iris/all` - get all stored data.
- `/iris/sync`    - insert iris csv from url specified in "url" parameter. Inserts only non-existing rows.
- `/iris/summary` - get per-column summary of stored data.

### POST:
- `/iris` - add data. Use Content-Type "text/csv" for csv, otherwise "application/json".
- `/iris/unique`- add data. Adds only rows that don't already exist in storage.

### DELETE:
- `/iris`   - delete stored data. Use "where" parameter for specifying rows, otherwise no action.
- `/iris/all`- delete all stored data.

### Using the "where" parameter:
- Available operators: `=`, `!=`, `<`, `>`,`IN` (i.e. `%20IN%20`).
- Multiple "where" parameters are always logically joined by AND in database queries.
- Column names can't contain operators (except "in" without surrounding whitespaces).
- Values can't contain commas.

##### Examples:
- `GET` `./api/v1/iris?where=petal_length=5.5`
- `GET` `./api/v1/iris?where=petal_width<1`
- `DELETE` `./api/v1/iris?where=species%20IN%20(virginica,setosa)`
- `GET` `./api/v1/iris?where=sepal_width>3.3&where=species%20IN%20(virginica,setosa)`


## Repo files
- [.env_showcase](.env_showcase) - Sample .env file to be used when running the [showcase](showcase.md) examples on Docker.
- [Dockerfile](Dockerfile) - Dockerfile for building the API image.
- [app.py](app.py) - Flask app and endpoints. Main.
- [conftest.py](conftest.py) - Emtpy file. Necessary for running `pytest`.
- [entrypoint.sh](entrypoint.sh) - Entrypoint for API container.
- [install_packages.sh](install_packages.sh) - Used while building API Docker image. Upgrades container os and installs packages.
- [iris.py](iris.py) - Home of Iris data type class.
- [log.py](log.py) - Logging-related functions and classes.
- [requirements.txt](requirements.txt) - Python packages. Used while building the API Docker image.
- [sql_operations.py](sql_operations.py) - Functions and classes related to SQLite operations.

# Instructions to run on Docker
Default setup:
```
                                iris csv from url                                               
                                        |                                                       
    +-----------------------------------|--------------------------------------------------+    
    |                                   v                                                  |    
    |                           +---------------+             +---------------+            |    
    |                           |     container |             |     container |            |    
    |             curl tests    |---------------|   syslog    |---------------|            |    
    |           +------------>  |iris_api       | ----------> |log_receiver   |            |    
    |           |               |188.0.0.2:7000 |             |188.0.0.4:7001 |            |    
    |           |               +---------------+             +---------------+            |    
    |           |                 |                             |                          |    
    |   +---------------+         |  /iris_data                 |  /log                    |    
    |   |     container |         |                             |                          |    
    |   |---------------|         |       +---------------+     |       +---------------+  |    
    |   |tester         |         +-------|        volume |     +-------|        volume |  |    
    |   |188.0.0.3      |                 |---------------|             |---------------|  |    
    |   +---------------+                 |iris_data      |             |logs           |  |    
    |                                     |(as SQLite)    |             |(as files)     |  |    
    | iris_network                        +---------------+             +---------------+  |    
    | 188.0.0.0/24                                                                         |    
    +--------------------------------------------------------------------------------------+    
```
## Setup
Setup and [showcase](showcase.md) were tested on Ubuntu 22.04 | Docker 20.10.17 | bash 5.1.16
### 1. Clone project
```Shell
git clone https://github.com/martroben/iris_api
```

##### Change to project dir
```Shell
cd iris_api
```

### 2. Build Docker image
```Shell
sudo docker build \
  --rm \
  -t iris_api \
  -f Dockerfile .
```
Useful resources for building images:
- https://testdriven.io/blog/docker-best-practices/
- https://pythonspeed.com/docker/

##### (Optional) remove build stage
```Shell
sudo docker image prune --filter label=stage=iris_api_builder -f
```
Saves disk space, but slows down re-building image


### 3. Create a Docker volume
```Shell
sudo docker volume create --label iris_data
```

## Test/run
You can test the api either by sending curl requests from the host or from another container within the same Docker network.
### Exposing api on the host

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

### Exposing api inside a Docker network (recommended)
1. Create Docker network:
```Shell
sudo docker network create \
  --subnet=188.0.0.0/24 \
  iris_network
```
2. Start the api container:
```Shell
sudo docker run \
  --rm \
  --name iris_api \
  --mount source=iris_data,target=/iris_data \
  --network iris_network \
  --ip 188.0.0.2 \
  --env-file .env_showcase \
  --log-driver syslog \
  --log-opt syslog-address=udp://188.0.0.4:7001 \
  --log-opt syslog-format=rfc3164 \
  iris_api \
  python3 /api/app.py
```
Note that the following flags can be skipped if a separate [log receiver](https://github.com/martroben/log_receiver) container is not used:
```Shell
  --log-driver syslog
  --log-opt syslog-address=udp://188.0.0.4:7001
  --log-opt syslog-format=rfc3164
```

3. Run an interactive tester container to test the api:
```Shell
sudo docker run \
  --rm \
  --name tester \
  --network iris_network \
  --ip 188.0.0.3 \
  -it \
  alpine
```
`curl` and `head` need to be installed, since the alpine image doesn't have them:
```Shell
apk add curl coreutils
```

##### Directing logs to a separate log receiver container (optional)
Deploy [log receiver](https://github.com/martroben/log_receiver) with appropriate Docker network names.

Use matching `LOG_INDICATOR` variable in both iris_api and log_receiver .env files (current defaults already match).


## Showcase
See [showcase](showcase.md) for curl requests that demonstrate the app capabilities.


## Ideas
Check [Issues](https://github.com/martroben/iris_api/issues) for future ideas / current limitations.

## Tests
Currently very basic and partial.
```Shell
pytest ./tests
```