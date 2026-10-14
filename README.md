# Isolated merge queue experiment

Disposable synthetic application and migrations for testing GitHub merge queue behavior on one dedicated DigitalOcean runner.

No Dopamina application source, credentials, deployments, or production runner labels are included. This demonstrates queue mechanics, not production CI equivalence or cost savings.

Expected experiments: compatible candidates merge without updating their feature branches; incompatible migration heads fail integration; independent candidates proceed; changed queued candidates require fresh results.
