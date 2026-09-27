-- Loyalty tier rules (agreed with the CRM team):
--   returned orders do not count towards lifetime value
--   lifetime_value >= 1000 -> gold, >= 250 -> silver, otherwise bronze
with order_totals as (

    select
        customer_id,
        count(*)    as order_count,
        sum(amount) as lifetime_value
    from {{ ref('stg_orders') }}
    where status <> 'returned'
    group by customer_id

)

select
    cast(c.customer_id as integer)                        as customer_id,
    cast(c.full_name as varchar)                          as full_name,
    cast(coalesce(o.order_count, 0) as integer)           as order_count,
    cast(coalesce(o.lifetime_value, 0) as decimal(12, 2)) as lifetime_value,
    cast(
        case
            when coalesce(o.lifetime_value, 0) >= 1000 then 'gold'
            when coalesce(o.lifetime_value, 0) >= 250 then 'silver'
            else 'bronze'
        end as varchar
    )                                                     as tier
from {{ ref('stg_customers') }} as c
left join order_totals as o
    on c.customer_id = o.customer_id
