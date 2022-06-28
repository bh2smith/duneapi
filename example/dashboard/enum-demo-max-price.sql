select 
    contract_address as token, 
    symbol, 
    max(price) as max_price
from prices.usd 
where symbol = '{{EnumParam}}'
and minute > now() - interval '1 year'
group by token, symbol
