# Jupyter minimal notebook image as base image
FROM jupyter/minimal-notebook

USER root

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends ffmpeg dvipng cm-super && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Create the Python enviroment
RUN mamba install --yes \
    'python=3.9' \
    'notebook' \
    'pandas' \
    'scikit-learn' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}" && \
    rmdir work

USER ${NB_UID}

WORKDIR "${HOME}"