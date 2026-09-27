# Sales bronze ingestion — environment ids

| Item | Value |
|------|-------|
| Workspace id | `8d2f5c1e-3b7a-4c9e-9f10-2a6b7c8d9e01` |
| Lakehouse `lh_bronze` artifact id | `5a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d` |
| Azure SQL Database connection id | `c0ffee00-1234-4abc-9def-001122334455` |
| Azure SQL database name | `salesdb` |
| Notebook `nb_build_silver` artifact id | `7e6d5c4b-3a29-4180-9f7e-6d5c4b3a2918` |

Source tables live in schema `dbo` of `salesdb`. The pipeline is stored in Git
using the Fabric Git-integration folder layout (one folder per item).
