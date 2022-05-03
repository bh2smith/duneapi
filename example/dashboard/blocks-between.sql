select 
    time, 
    hash 
from ethereum."blocks"
-- Begin <= time < End
where time between '{{Begin}}' and '{{End}}'
order by time
