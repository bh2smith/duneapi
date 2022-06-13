
-- Fetch CSV Data: (python script)
-- TODO: Should parameterize the fetch csv data {{StartTime}}, {{EndTime}}

-- select * from erc20.tokens

-- select * from erc20."ERC20_evt_Transfer"
-- WHERE '\x9008D19f58AAbD9eD0D60971565AA8510560ab41' in ("to", "from")
-- and evt_block_time between '2022-03-01' and '2022-03-11'

-- with
-- token_times as (
--     select 
--         date_trunc('hour', evt_block_time) as hour,
--         date_trunc('minute', evt_block_time) as minute, 
--         contract_address 
--     from erc20."ERC20_evt_Transfer"
--     where '\x9008D19f58AAbD9eD0D60971565AA8510560ab41' in ("to", "from")
--     and evt_block_time between '2022-03-01' and '2022-03-11'
-- )

-- prices.usd
-- select pusd.* from prices.usd pusd
-- inner join token_times tt
-- on pusd.minute = tt.minute
-- and pusd.contract_address = tt.contract_address

-- prices_from_dex_data
-- select p.* from prices.prices_from_dex_data p
-- inner join token_times tt
-- on p.hour = tt.hour
-- and p.contract_address = tt.contract_address

-- select * from prices.layer1_usd_eth
-- where minute between '2022-03-01' and '2022-03-11'

-- select * from gnosis_protocol_v2."trades"
-- where block_time between '2022-03-01' and '2022-03-11'

-- select * from gnosis_protocol_v2."batches"
-- where block_time between '2022-03-01' and '2022-03-11'

-- $ docker cp ./csvs/ postgres_container:/


-- Create Schemas:
CREATE SCHEMA erc20;
CREATE SCHEMA prices;
CREATE SCHEMA gnosis_protocol_v2;

-- Shemas for each table were defined from dune more or less as follows:
-- select 
--     column_name, 
--     data_type,
--     is_nullable
-- from information_schema.columns
-- where table_schema = 'prices'
-- and table_name = 'usd';

-- Create Tables

-- Tokens:
CREATE TABLE erc20.tokens (
   contract_address bytea UNIQUE,
   symbol text,
   decimals integer
);
CREATE INDEX IF NOT EXISTS tokens_contract_address_decimals_idx ON erc20.tokens USING btree (contract_address) INCLUDE (decimals);
CREATE INDEX IF NOT EXISTS tokens_symbol_decimals_idx ON erc20.tokens USING btree (symbol) INCLUDE (decimals);

CREATE TABLE erc20."ERC20_evt_Transfer" (
   "from" bytea,
   "to" bytea,
   value numeric,
   contract_address bytea not NULL,
   evt_tx_hash bytea not NULL,
   evt_index bigint not NULL,
   evt_block_time timestamptz not NULL,
   evt_block_number bigint not NULL
);

-- Prices:
CREATE TABLE prices.usd (
   minute timestamptz not NULL,
   price double precision not NULL,
   decimals smallint not NULL,
   contract_address bytea not NULL,
   symbol text not NULL
);
CREATE TABLE prices.layer1_usd_eth (
   minute timestamptz not NULL,
   price double precision not NULL,
   symbol text not NULL
);
CREATE TABLE prices.prices_from_dex_data (
   contract_address bytea not NULL,
   hour timestamptz not NULL,
   median_price numeric,
   sample_size integer,
   symbol text,
   decimals smallint
);

-- Protocol

-- Batches:
CREATE TABLE gnosis_protocol_v2.batches
(
    block_time      timestamptz NOT NULL,
    num_trades      int8        NOT NULL,
    dex_swaps       int8        NOT NULL,
    batch_value     numeric,
    gas_per_trade   numeric,
    solver_address  bytea       NOT NULL,
    solver_name     text,
    tx_hash         bytea       NOT NULL,
    gas_price_gwei  float8,
    gas_used        numeric,
    tx_cost_usd     numeric,
    fee_value       numeric,
    call_data_size  numeric,
    unwraps         int8,
    token_approvals int8
);

CREATE UNIQUE INDEX IF NOT EXISTS batches_id ON gnosis_protocol_v2.batches (tx_hash);
CREATE INDEX batches_idx_1 ON gnosis_protocol_v2.batches (block_time);
CREATE INDEX batches_idx_2 ON gnosis_protocol_v2.batches (solver_address);
CREATE INDEX batches_idx_3 ON gnosis_protocol_v2.batches (num_trades);


-- Trades
CREATE TABLE gnosis_protocol_v2.trades
(
    app_data           text,
    atoms_bought       numeric     NOT NULL,
    atoms_sold         numeric     NOT NULL,
    block_time         timestamptz NOT NULL,
    buy_price          numeric,
    buy_token_address  bytea       NOT NULL,
    buy_token          text,
    buy_value_usd      numeric,
    fee                numeric,
    fee_atoms          numeric     NOT NULL,
    fee_usd            numeric,
    order_uid          bytea       NOT NULL,
    receiver           bytea,
    sell_price         numeric,
    sell_token_address bytea       NOT NULL,
    sell_token         text,
    sell_value_usd     numeric,
    trader             bytea       NOT NULL,
    trade_value_usd    numeric,
    tx_hash            bytea       NOT NULL,
    units_bought       numeric,
    units_sold         numeric
);

CREATE UNIQUE INDEX IF NOT EXISTS trades_id ON gnosis_protocol_v2.trades (order_uid, tx_hash);
CREATE INDEX trades_idx_1 ON gnosis_protocol_v2.trades (block_time);
CREATE INDEX trades_idx_2 ON gnosis_protocol_v2.trades (sell_token_address);
CREATE INDEX trades_idx_3 ON gnosis_protocol_v2.trades (buy_token_address);
CREATE INDEX trades_idx_4 ON gnosis_protocol_v2.trades (trader);
CREATE INDEX trades_idx_5 ON gnosis_protocol_v2.trades (app_data);
CREATE INDEX trades_idx_6 ON gnosis_protocol_v2.trades (tx_hash);

-- Solvers
CREATE TABLE gnosis_protocol_v2.view_solvers (
   address bytea NOT NULL,
   environment text NOT NULL,
   name text NOT NULL,
   active bool NOT NULL
);


