FROM docker.artifactory.gcp.mercadona.com/custom/python3:3.12-v1

ENV APP_MODULE alert_monitoring.api.boot
ENV APP_FILE main
ENV FWK_PATH ${APP_DIR}/alert_monitoring/api

COPY --chown=${USER_NAME}:${USER_NAME} alert_monitoring ./alert_monitoring
COPY --chown=${USER_NAME}:${USER_NAME} pyproject.toml ./
COPY --chown=${USER_NAME}:${USER_NAME} dependencies.tgz ./

RUN tar -xf dependencies.tgz -C /home/${USER_NAME}/.local/ && \
    rm dependencies.tgz && \
    ln -sf /usr/local/bin/python /home/${USER_NAME}/.local/bin && \
    find /home/${USER_NAME}/.local/bin -type f -exec sed -i -e 's%^#!.*python$%#!/home/mdona/.local/bin/python%' {} +