# Velero-Watchdog-Pro

> [!WARNING]  
**Attention Users:** This project is in active development, and certain tools or features might still be under construction. We kindly urge you to exercise caution while utilizing the tools within this environment. While every effort is being made to ensure the stability and reliability of the project, there could be unexpected behaviors or limited functionalities in some areas.
We highly recommend thoroughly testing the project in non-production or sandbox environments before implementing it in critical or production systems. Your feedback is invaluable to us; if you encounter any issues or have suggestions for improvement, please feel free to [report them](https://github.com/seriohub/velero-watchdog-pro/issues). Your input helps us enhance the project's performance and user experience.
Thank you for your understanding and cooperation.

## Description

This Python project is designed to monitor the status of Velero backups in Kubernetes environments and alert when something is not working.
It provides efficient ways to check the backups status.
The user chooses the synchronization cycles and the elements to monitor.

## Features

### 1. Backup Status Monitoring

The project monitors the backup status of Kubernetes clusters.

### 2. Schedule Change Monitoring

Monitor and alert if the schedule changes.

### 3. Channels notifications

Receive the alerts and the solved messages via notifications channels, allowing immediate action.

Available plugin:
- Telegram
- email


## Requirements

- Python 3.x
- kubectl cli (if [Run in kubernetes](#run-in-kubernetes))
- Telegram API credentials (if telegram notification is enabled)
- SMTP and user account (if email notification is enabled)

## Configuration

| FIELD                       | TYPE   | DEFAULT | DESCRIPTION                                                                                                                                              |
|-----------------------------|--------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DEBUG`                     | Bool   | False   | View debugging information.                                                                                                                              |
| `LOG_SAVE`                  | Bool   | False   | Save log to files                                                                                                                                        |
| `PROCESS_LOAD_KUBE_CONFIG`* | Bool   | True    | Set False if it runs on k8s.                                                                                                                             |
| `PROCESS_KUBE_CONFIG`       | String |         | Path to the kube config file. This is mandatory when the script runs outside the Kubernetes cluster, either in a docker container or as a native script. |
| `PROCESS_CLUSTER_NAME` * ** | String |         | Force the cluster name and it appears in the telegram message                                                                                            |
| `PROCESS_CYCLE_SEC`         | Int    | 120     | Cycle time (seconds)                                                                                                                                     |
| `TELEGRAM_ENABLE`    *      | Bool   | True    | Enable telegram notification                                                                                                                             |
| `TELEGRAM_API_TOKEN` *      | String |         | Token for access to Telegram bot via Http API                                                                                                            |
| `TELEGRAM_CHAT_ID`   *      | String |         | Telegram chat id where send the notifications                                                                                                            |
| `EMAIL_ENABLE`       *      | Bool   | False   | Enable email notification                                                                                                                                |
| `EMAIL_SMTP_SERVER`  *      | String |         | SMTP server                                                                                                                                              |
| `EMAIL_SMTP_PORT`    *      | int    | 587     | SMTP port                                                                                                                                                |
| `EMAIL_ACCOUNT`      *      | String |         | user name account                                                                                                                                        |
| `EMAIL_PASSWORD`     *      | String |         | password account                                                                                                                                         |
| `EMAIL_RECIPIENTS`   *      | Bool   |         | Email recipients                                                                                                                                         |
| `BACKUP_ENABLE`             | Bool   | True    | Enable watcher for backups without schedule or last backup for each schedule                                                                             |
| `EXPIRES_DAYS_WARNING`      | int    | 29      | Number of days to backup expiration below which to display a warning about the backup                                                                    |
| `SCHEDULE_ENABLE`           | Bool   | True    | Enable watcher for schedule                                                                                                                              |
| `K8S_INCLUSTER_MODE` **     | Bool   | False   | Enable in cluster mode                                                                                                                                   |
| `IGNORE_NM_1`               | String |         | regex to ignore a namespace or a group of namespaces                                                                                                     |
| `IGNORE_NM_2`               | String |         | regex to ignore a namespace or a group of namespaces                                                                                                     |
| `IGNORE_NM_3`               | String |         | regex to ignore a namespace or a group of namespaces                                                                                                     |

*Mandatory parameters<br>
** Mandatory if it is deployed on cluster

<br>If you set "TELEGRAM_ENABLE"=False, the application prints out the message only on the stdout

## Installation

Clone the repository:

  ``` bash
    git clone https://github.com/seriohub/velero-watchdog-pro.git
    cd velero-watchdog-pro
  ```

### Run native

1. Navigate to the [src](src) folder

2. Dependencies installation:

    ``` bash
    pip install -r requirements.txt
    ```

3. Configuration

    Create and edit .env file under src folder, you can start from [.env.template](src/.env.template) under [src](src) folder
    Setup mandatory parameters in the src/.env file if runs it in the native mode

4. Usage

    Run the main script:

    ``` bash
    python3 main.py
    ```

### Run in Docker

1. Configuration
   1. Navigate to the [docker](docker) folder
   2. Setup mandatory parameters in the docker-compose.yaml file ([docker-compose.yaml](docker/docker-compose.yaml))

      **Note:** Instead of editing the docker-compose.yaml file, you can create and edit .env file (you can start from [.env.template](docker/.env.template)) file under [docker](docker) folder and use the docker-compose.yaml default  values.
2. Docker image :
   ##### Build docker image from scratch
      1. Navigate to the root folder
      2. Build the docker image
      ``` bash
      docker build --target velero-watchdog-pro -t velero-watchdog-pro:0.1.0 -t velero-watchdog-pro:latest -f ./docker/Dockerfile .
      ```
   ##### Use image published on DockerHub
      1. Pull the image 
      ``` bash
      docker pull dserio83/velero-watchdog-pro
      ```
3. Create docker volume:
   1. Create a volume for store logs
      ``` bash
      docker volume create velero_watchdog_vol
      ```

4. Create the stack and run it

    ``` bash
     docker-compose  -f ./docker/docker-compose.yaml -p velero-watchdog-stack  up -d
    ```

### Run in Kubernetes

1. Configuration
   1. Navigate to the [k8s](k8s) folder
   2. Create and edit .env file under k8s folder, you can start from [.env.template](k8s/.env.template)
  
   3. Export .env

      ``` bash
      export $(cat .env | xargs)
      ```

      Checks that the variables have been exported:

      ``` bash
      printenv | grep K8SW_* 
      ```
 
2. Setup docker image:

   1. Navigate to the root folder
   2. Build image

        ``` bash
        docker build --target velero-watchdog-pro -t ${K8SW_DOCKER_REGISTRY}/${K8SW_DOCKER_IMAGE}:0.1.0 -t ${K8SW_DOCKER_REGISTRY}/${K8SW_DOCKER_IMAGE}:latest -f ./docker/Dockerfile .
        ```

   3. Push image

        ``` bash
        docker push ${K8SW_DOCKER_REGISTRY}/${K8SW_DOCKER_IMAGE} --all-tags
        ```

      >[!INFO]  
      Alternative you can use skip the *Build image* and *Push image* steps and use an deployed image published on DockerHub.<br>
      Edit the .env file:
      **K8SW_DOCKER_REGISTRY=dserio83** <br>
      More info: https://hub.docker.com/r/dserio83/velero-watchdog-pro

3. Kubernetes create objects

   1. Navigate to the [k8s](k8s) folder

   2. Create namespace:

        ``` bash
        cat 10_create_ns.yaml | envsubst | kubectl apply -f -
        ```

   3. Create the PVC:

       ``` bash
       cat 20_pvc.yaml | envsubst | kubectl apply -f -
       ```

   4. Create the ConfigMap:

       ``` bash
       cat 30_cm.yaml | envsubst | kubectl apply -f -
       ```
  
   5. Create the RBAC:

       ``` bash
        cat 40_rbac.yaml | envsubst | kubectl apply -f -
       ```
  
   6. Create the Deployment:

       ``` bash
        cat 50_deployment.yaml | envsubst | kubectl apply -f -
       ```

## Test Environment

The project is developed, tested and put into production on several clusters with the following configuration

1. Kubernetes v1.28.2

## How to Contribute

1. Fork the project
2. Create your feature branch

    ``` bash
    git checkout -b feature/new-feature
    ```

3. Commit your changes

    ``` bash
   git commit -m 'Add new feature'
   ```

4. Push to the branch

    ``` bash
   git push origin feature/new-feature
   ```

5. Create a new pull request

## License

This project is licensed under the [MIT License](LICENSE).

---

Feel free to modify this template according to your project's specific requirements.

In case you need more functionality, create a PR. If you find a bug, open a ticket.
