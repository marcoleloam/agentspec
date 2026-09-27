select
    cast(customer_id as integer)  as customer_id,
    cast(full_name as varchar)    as full_name,
    cast(signup_date as date)     as signup_date
from {{ ref('raw_customers') }}
