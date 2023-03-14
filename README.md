# iris api
Stacc exercise


# Running on Docker
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
    |           v                 |                             |                          |    
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
You can test the api either by sending curl requests from the host or from another container.
### Exposing api on localhost
[Showcase](showcase.md) was tested on Ubuntu 22.04, bash 5.1.16
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

### Directing logs to a separate log receiver container (optional)
Deploy [log receiver](https://github.com/martroben/log_receiver) with appropriate network/container names.

Use matching `LOG_INDICATOR` variable in both iris_api and log_receiver .env files (current defaults already match).


## Showcase
See [showcase](showcase.md) for curl requests that demonstrate the capabilities.

