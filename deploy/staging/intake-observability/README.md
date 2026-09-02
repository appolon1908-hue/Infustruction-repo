# Staging intake observability deployment

Execute runtime actions only from a standalone, root-owned protected checkout.
Do not invoke repository scripts as root from a checkout writable by a deployment
or login account. Prepare the accepted exact main revision without executing any
repository code:

~~~bash
install -d -o root -g root -m 0755 /opt/codestra-observability
install -d -o root -g root -m 0700 /opt/codestra-observability/infrastructure-authority
git -C /opt/codestra-observability/infrastructure-authority init
git -C /opt/codestra-observability/infrastructure-authority remote add origin https://github.com/appolon1908-hue/Infustruction-repo.git
git -C /opt/codestra-observability/infrastructure-authority fetch --no-tags origin refs/heads/main
git -C /opt/codestra-observability/infrastructure-authority checkout --detach <accepted-main-sha>
chown -R root:root /opt/codestra-observability/infrastructure-authority
chmod -R go-w /opt/codestra-observability/infrastructure-authority
~~~

Use an explicit state path rather than an implicit home-directory default. The
deployment entrypoint verifies the exact merged Infrastructure SHA and the
protected source closure before it pulls or starts a container:

~~~bash
INFRASTRUCTURE_SOURCE_SHA=<accepted-main-sha> \
CODESTRA_STAGING_ROOT=/var/lib/codestra/staging/intake-observability \
KEYCLOAK_PUBLIC_URL=https://auth-staging.codestra.co \
KEYCLOAK_REALM=codestra \
/opt/codestra-observability/infrastructure-authority/scripts/deploy_intake_observability_staging.sh deploy
~~~

This authority deploys only the isolated staging Middleware, PostgreSQL, and
Redis project. It publishes no host port and shares no network or volume with
Klyrow or Postal. Prometheus and Grafana remain separately owned and deployed.
