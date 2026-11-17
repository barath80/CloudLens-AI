# Data Requirements (what ML needs from the backend)

Phase 1 uses simulated data only. These are the real inputs needed before any claim about real-world performance.

| Need | Detail | Why |
|---|---|---|
| EC2 `CPUUtilization` | Datapoint per 5 min (or 1 min with detailed monitoring), per instance, with instance id and region | Underutilization and utilization forecasts |
| Retention beyond CloudWatch | CloudWatch keeps 5-min data for about 63 days and 1-hour data for about 15 months. Archive to S3/Parquet | Weekly and longer seasonality needs 8+ weeks at fine grain |
| Memory metrics | Requires the CloudWatch Agent (per the decision record) | CPU alone must never justify rightsizing; memory is not evaluated today and results say so |
| EBS / network | Volume ops and throughput, network in/out | Same reason; later phases |
| Daily cost per resource | CUR 2.0 line items with resource id; state which cost measure (unblended, amortized, net) | Cost anomaly and spend forecasting. Needs 8+ weeks; 12+ months to see yearly seasonality |
| Lifecycle events | Start/stop, resize, instance-type, AMI and autoscaling changes with timestamps | Series must not span two different machines |
| Resource attributes | Instance type, family, region, tags, workload class | Peer grouping and clustering later |
| Quality flags | Missing, late, corrected and estimated datapoints marked as such | Missing must never be conflated with zero |
| Outcome labels | Recommendation accepted or rejected, post-change verification result | Only trustworthy supervised label; needed to calibrate `confidence` |

Format: UTC timestamps aligned to the sampling step, one row per resource, metric and timestamp; the backend supplies stable record ids for `evidence_ids`.

Minimum viable real dataset to start Phase 2: 8 weeks of 5-min CPU for 50+ instances across several workload types, with lifecycle events, from one consenting account.
