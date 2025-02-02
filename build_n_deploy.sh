#!/bin/bash
# ©2025, Ovais Quraishi
# NOTE: assumes that config_vals.txt, with all settings assigned
#		exists

# Define a function for each operation
build_docker() {
  cp setup.config.template setup.config
  sed -i "s|=PSQLHOST|=$PSQLHOST|" setup.config
  sed -i "s|=PSQLDB|=$PSQLDB|" setup.config
  sed -i "s|=PSQLUSER|=$PSQLUSER|" setup.config
  sed -i "s|=PSQLPASS|=$PSQLPASS|" setup.config
  sed -i "s|=OLLAMA_API_URL|=$OLLAMA_API_URL|" setup.config
  sed -i "s|=LLMS|=$LLMS|" setup.config
  sed -i "s|=MEDLLMS|=$MEDLLMS|" setup.config
  sed -i "s|=SEMVER|=$SEMVER|" setup.config
  sed -i "s|=SERVICE_NAME|=$SERVICE_NAME|" setup.config
  sed -i "s|=JWT_SECRET_KEY|=$JWT_SECRET_KEY|" setup.config
  sed -i "s|=SRVC_SHARED_SECRET|=$SRVC_SHARED_SECRET|" setup.config
  sed -i "s|=APP_SECRET_KEY|=$APP_SECRET_KEY|" setup.config
  sed -i "s|=IDENTITY|=$IDENTITY|" setup.config
  sed -i "s|=CSRF_PROTECTION_KEY|=$CSRF_PROTECTION_KEY|" setup.config
  sed -i "s|=DOCKER_HOST_URI|=$DOCKER_HOST_URI|" setup.config
  ./build_docker.py
}

push_image() {

  echo "docker tag ${SERVICE_NAME}:${SEMVER} ${DOCKER_HOST_URI}/${SERVICE_NAME}:${SEMVER}"
  docker tag "${SERVICE_NAME}:${SEMVER}" "${DOCKER_HOST_URI}/${SERVICE_NAME}:${SEMVER}"
  echo "docker push ${DOCKER_HOST_URI}/${SERVICE_NAME}:${SEMVER}"
  docker push "${DOCKER_HOST_URI}/${SERVICE_NAME}:${SEMVER}"
}

apply_kubernetes() {

  #cp deployment.yaml.orig deployment.yaml
  sed -i "s|SEMVER|$SEMVER|" deployment.yaml
  sed -i "s|DOCKER_HOST_URI|$DOCKER_HOST_URI|" deployment.yaml
  kubectl -n ollamagpt apply -f deployment.yaml
  kubectl -n ollamagpt apply -f service.yaml
}

# Read config
source config_vals.txt

# Call the functions with the version as an argument
build_docker $SEMVER
push_image $SEMVER $SERVICE_NAME $DOCKER_HOST_URI
apply_kubernetes $SEMVER

# Clean up
rm -f setup.config
rm -f config_vals.txt
rm -f deployment.yaml
rm -f service.yaml
