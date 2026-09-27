{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='delete+insert'
    )
}}

with changes as (

    select *
    from {{ ref('stg_orders') }}

    {% if is_incremental() %}
    where updated_at > (select coalesce(max(updated_at), timestamp '1900-01-01') from {{ this }})
    {% endif %}

),

latest as (

    select
        *,
        row_number() over (partition by order_id order by updated_at desc) as rn
    from changes

)

select
    order_id,
    customer_id,
    status,
    amount,
    updated_at
from latest
where rn = 1
