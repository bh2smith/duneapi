-- Copy CSV data into tables
COPY erc20.tokens(contract_address, symbol, decimals)
FROM '/csv/erc20.tokens.csv'
DELIMITER ','
CSV HEADER;

COPY erc20."ERC20_evt_Transfer"
FROM '/csv/erc20.ERC20_evt_Transfer.csv'
DELIMITER ','
CSV HEADER;

COPY prices.usd
FROM '/csv/prices.usd.csv'
DELIMITER ','
CSV HEADER;

COPY prices.prices_from_dex_data
FROM '/csv/prices.prices_from_dex_data.csv'
DELIMITER ','
CSV HEADER;

COPY prices.layer1_usd_eth
FROM '/csv/prices.layer1_usd_eth.csv'
DELIMITER ','
CSV HEADER;


COPY gnosis_protocol_v2.trades
FROM '/csv/gnosis_protocol_v2.trades.csv'
DELIMITER ','
CSV HEADER;

COPY gnosis_protocol_v2.batches
FROM '/csv/gnosis_protocol_v2.batches.csv'
DELIMITER ','
CSV HEADER;

COPY gnosis_protocol_v2.view_solvers
FROM '/csv/gnosis_protocol_v2.view_solvers.csv'
DELIMITER ','
CSV HEADER;