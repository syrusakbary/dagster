#!/usr/bin/env bash

set -eux

# See: https://stackoverflow.com/a/56400126/11295366

# Usage of this script: scripts/setup_dev_env.sh /path/to/your/keyfile
if [[ "$#" -ne 1 ]]; then
    echo "Illegal number of parameters"
    exit 1
fi

SPARK_VERSION="2.4.3"
GCS_CONNECTOR_VERSION="hadoop2-1.9.17"


# assumes we're stashing Spark under ~/src_ext
BASE_PATH="${HOME}/src_ext"
SPARK_HOME="${BASE_PATH}/spark"


wget "http://ftp.wayne.edu/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop2.7.tgz" -O "${BASE_PATH}/spark-${SPARK_VERSION}.tgz"

tar xzf "${BASE_PATH}/spark-${SPARK_VERSION}.tgz" -C $BASE_PATH

# symlink to latest versions
ln -s "${BASE_PATH}/spark-${SPARK_VERSION}-bin-hadoop2.7" "${SPARK_HOME}"

cat >> "${SPARK_HOME}/conf/spark-defaults.conf" <<EOL
spark.hadoop.google.cloud.auth.service.account.enable       true
spark.hadoop.google.cloud.auth.service.account.json.keyfile $1
EOL

wget "http://repo2.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/${GCS_CONNECTOR_VERSION}/gcs-connector-${GCS_CONNECTOR_VERSION}-shaded.jar" -O "${SPARK_HOME}/jars/gcs-connector-${GCS_CONNECTOR_VERSION}-shaded.jar"
