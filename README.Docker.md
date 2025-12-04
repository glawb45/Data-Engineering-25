### Building and running your application

The project ships with a docker-compose stack for Kafka + Postgres + Streamlit.

1) Build and start the stack from the repo root:
`docker compose -f docker/docker-compose.yml up --build`

2) Wait for the Kafka healthcheck/topic setup to complete, then open the dashboard:
`http://localhost:8501`

3) Verify services if needed:
`docker ps`

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)
