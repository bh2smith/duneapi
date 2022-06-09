select "number",
       miner,
       size,
       time,
       CONCAT('0x', ENCODE(hash, 'hex')) as block_hash,
       gas_limit * gas_used / 10 ^ 15    as tx_fees
from ethereum.blocks
where date(time) = date('{{DateParam}}')
  and text(hash) ilike '%{{TextParam}}%'
order by "number" desc
limit '{{IntParam}}'