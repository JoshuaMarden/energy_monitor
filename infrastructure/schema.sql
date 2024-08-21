DROP TABLE IF EXISTS Generation ;
DROP TABLE IF EXISTS Carbon ;
DROP TABLE IF EXISTS Demand ;
DROP TABLE IF EXISTS user_data ;
DROP TABLE IF EXISTS generation_percent ;


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
CREATE TABLE user_data (
    users_name VARCHAR,
    user_email VARCHAR,
    user_postcode VARCHAR,
    hours_to_charge INT,
    user_preference VARCHAR,
    PRIMARY KEY (users_name)
);
CREATE TABLE generation_percent (
    fuel_type INT,
    slice_percentage FLOAT,
    PRIMARY KEY (fuel_type)
);
CREATE TABLE Generation (
    publish_time TIMESTAMP,
    publish_date DATE,
    fuel_type VARCHAR(255),
    gain_loss VARCHAR(1),
    generated FLOAT,
    settlement_period INT,
    PRIMARY KEY (publish_time, fuel_type),
    FOREIGN KEY (publish_time) REFERENCES Demand(publish_time),
);
