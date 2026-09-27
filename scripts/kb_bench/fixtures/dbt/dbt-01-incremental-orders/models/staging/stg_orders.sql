select
    cast(order_id as integer)        as order_id,
    cast(customer_id as integer)     as customer_id,
    lower(status)                    as status,
    cast(amount as decimal(12, 2))   as amount,
    cast(updated_at as timestamp)    as updated_at
from {{ ref('raw_orders') }}
