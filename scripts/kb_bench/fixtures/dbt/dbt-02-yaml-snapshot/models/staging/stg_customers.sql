select
    cast(customer_id as integer)  as customer_id,
    lower(email)                  as email,
    tier,
    cast(updated_at as timestamp) as updated_at
from {{ source('crm', 'customers') }}
