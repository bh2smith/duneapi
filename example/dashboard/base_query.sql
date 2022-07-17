with sub_query (name, value) as (
    select *
    from (
             values ('Alice', 1), ('Bob', 2)
         ) as _
)
