# POC_oss

POC utilizing open-source systems.

Applications:
Amundsen.io + Apache Atlas

The setup of this poc is borrowed from https://github.com/amundsen-io/amundsen


The POC consists of 5 services:
- Amundsen frontend
- Amundsen metadata
- Amundsen search
- Apache Atlas
- Elasticsearch

Network:
- Ingress for atlas
- Ingress for amundsen

(The multiple Ingress setup is only needed since the GCP project used for this POC doesn't have any certificates/dns.)

Images are fetched from dockerhub.

The helm spec has been based on amundsens "docker-amundsen-atlas" docker-compose file:
https://github.com/amundsen-io/amundsen/blob/main/docker-amundsen-atlas.yml

Values used for deploy/environment values are defined either in the staging.yaml file, or as a secret in Google Cloud.

Issues:

- Atlas has a slow startup, approx. 10-15 mins.
- The indices in elasticsearch doesn't seem to be created by this setup. Amundsen Search expects them to exist. The atlas image seems to use a deprecated version of databuilder.