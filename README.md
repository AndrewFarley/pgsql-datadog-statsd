# PGSQL Statsd Stats via Docker/K8s

This is a simple docker image to perform stats-gathering queries from PostgreSQL and ship to a statsd.  This is generally engineered with Datadog in mind, but is not limited to usage with datadog.  This is engineered with leveraging Kubernetes in mind, this can be deployed as a sidecar, or as its own single-pod deployment.

## Quick Start

Simple to use...
 * First make a configuration file (see: [queries.yaml.sample](./queries.yaml.sample))
 * Mount that configuration file into the app folder and run via Docker
 * Make sure to set your `STATSD_HOST` and `DATABASE_URI`
 * Optionally set the `TIME_BETWEEN_REQUESTS` if you don't want it to run once a minute (eg: 5 seconds instead)

```
# Just for a PoC, when you deploy it you'll probably just run the last command
docker network create my-network
docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -d -P --net=my-network postgres
mkdir sample-pgsql-datadog-statsd
echo 'servicename.test.set: "select 5"' > sample-pgsql-datadog-statsd/sample.yaml
# NOTE: You may omit the --net when you deploy this on your environment
# especially with kubernetes, it's just for a working PoC here
docker run --name pgsql-datadog-statsd \
  --net my-network \
  -v `pwd`/sample-pgsql-datadog-statsd:/app/test:ro \
  -e STATSD_HOST=host.name.or.ip.should.go.here \
  -e STATSD_PORT=8125 \
  -e TIME_BETWEEN_REQUESTS=60 \
  -e DATABASE_URI="postgresql://postgres:mysecretpassword@some-postgres/template1" \
  andrewfarley/pgsql-datadog-statsd
```

### Environment variables

Some configuration parameters can be changed with environment variables:

* `DATABASE_URI` is the database uri we want to connect to.
  * This one is REQUIRED to set
* `STATSD_HOST` is the hostname we want to push stats to.
  * This one is REQUIRED to set
* `STATSD_PORT` is the port of the STATSD_HOST we want to push stats to, defaults to `8125`
* `TIME_BETWEEN_REQUESTS` is the amount of time in seconds we want in-between stats requests, default `60`

#### Configuration file

You will also need to mount YAML configuration files in the `/app/` folder to any sub-path.  The files MUST end in .yaml, any and all files found recursively underneath `/app` with .yaml will be auto-included.  WARNING: Do NOT mount to `/app` directly, use a subpath, eg: `/app/configs`.

Use the example [queries.yaml.sample](./queries.yaml.sample) as a starting point.  Once you're happy with it... mount it to your instance on runtime.  You can mount it to a file or a folder full of files, up to you.

## Contribute

If you notice a limitation or a bug with this container, feel free to open a [Github issue](https://github.com/TODO/issues).