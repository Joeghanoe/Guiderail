# Resource health is missing for some subscriptions and nothing was red

Support noticed that resource health rows are missing for a few subscriptions for several days. The ingestion runs all show as succeeded and no alert fired. Our platform contact says the management API had an incident on its resource health endpoint that week and returned server errors.

Find out why the run stayed green and fix it. The ingestion should not report success for data it did not get.
