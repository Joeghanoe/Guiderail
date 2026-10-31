# Wrong identity for the data lake after a settings change

The ingestion app writes to a data lake in another tenant in production, using a federated credential. When
someone removed one of the two cross-tenant settings during a deployment, the app didn't complain at startup.
It just kept running and the writes failed later with an authorization error that took us a day to explain.

Make that kind of misconfiguration show up at startup instead. Development, where neither setting is used,
must keep working as it does today. Also make it visible in the logs which kind of credential the lake client
ended up with, without logging anything sensitive.
