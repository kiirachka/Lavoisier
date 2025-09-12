FROM gitpod/workspace-python-3.11

# Устанавливаем системные зависимости, которые могут понадобиться
USER root
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
USER gitpod
