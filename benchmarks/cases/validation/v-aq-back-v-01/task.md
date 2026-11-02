# Add a dataset: advisor recommendations

The ingestion app pulls a set of datasets per subscription from the cloud management API and lands them as JSON in the data lake (resource health, secure scores, maintenance configurations and so on). The platform team wants the advisor recommendations of each subscription landed the same way, so the rule engine can use them later.

Add a dataset "advisor recommendations", per subscription, from the management API's advisor recommendations list. It should behave like the other per-subscription datasets: its own checkpoint per subscription, its own default cadence, the same throttling behaviour, and its rows land under its own dataset name. Keep the first version simple: land the recommendation id, category, impact, the affected resource id and the short description. It does not need the machine-learning flag.
