# PGSQLStatsd Stats Gathering

This is a simple docker image to perform stats-gathering queries from PostgreSQL and ship to a statsd.  This is generally engineered with Datadog in mind, but is not limited to usage with datadog.

## Quick Start

Simple to use...

```
docker run -d --name pgsql-datadog-statsd \
  -v /queries.yaml.sample:/app/queries.yaml:ro \
  -e DATABASE_URI="postgres://test:test@localhost/test" \
  PUT_DOCKER_URL_HERE
```

## Configuration

TODO

### Environment variables

Some configuration parameters can be changed with environment variables:

* `STATSD_HOST` is the hostname we want to push stats to, defaults to `localhost`
* `STATSD_PORT` is the port of the STATSD_HOST we want to push stats to, defaults to `8125`
* `TIME_BETWEEN_REQUESTS` is the amount of time in seconds we want in-between stats requests, default `60`
* `DATABASE_URI` is the database uri we want to connect to.  Default: `postgres://test:test@localhost/test`

#### Configuration file

You can also mount YAML configuration files in the `/app/` folder to any sub-path.  The files MUST end in .yaml, any and all files found recursively underneath /app with .yaml will be auto-included.  Do NOT mount to /app alone.

Use the example queries.yaml.sample as a starting point.  Once you're happy with it... mount it to your instance on runtime.  You can mount a file, or a folder full of files.

```
docker run -d --name pgsql-datadog-statsd \
  -v ./queries.yaml.sample:/app/queries.yaml:ro \
  -e DATABASE_URI="postgres://test:test@localhost/test" \
  PUT_DOCKER_URL_HERE
```
or
```
docker run -d --name pgsql-datadog-statsd \
  -v /path/to/configs:/app/my_configs:ro \
  -e DATABASE_URI="postgres://test:test@localhost/test" \
  PUT_DOCKER_URL_HERE
```

## Contribute

If you notice a limitation or a bug with this container, feel free to open a [Github issue](https://github.com/TODO/issues).