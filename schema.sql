DROP TABLE IF EXISTS Generation ;
DROP TABLE IF EXISTS Cost ;
DROP TABLE IF EXISTS Carbon ;
DROP TABLE IF EXISTS Demand ;


CREATE TABLE Demand (
    publish_time TIMESTAMP PRIMARY KEY,
    Demand_amt INT
);
CREATE TABLE Carbon (
    publish_time TIMESTAMP,
    forecast INT,
    carbon_level VARCHAR(255),
    PRIMARY KEY (publish_time)
);
CREATE TABLE Cost (
    publish_date TIMESTAMP,
    settlement_period INT,
    sell_price FLOAT,
    buy_price FLOAT,
    PRIMARY KEY (publish_date, settlement_period)
);
CREATE TABLE Generation (
    publish_time TIMESTAMP,
    publish_date TIMESTAMP,
    fuel_type VARCHAR(255),
    gain_loss VARCHAR(1),
    generated FLOAT,
    settlement_period INT,
    PRIMARY KEY (publish_time, fuel_type),
    FOREIGN KEY (publish_time) REFERENCES Demand(publish_time),
    FOREIGN KEY (publish_date,settlement_period) REFERENCES Cost(publish_date,settlement_period)
);
