import pandas as pd
import os
import streamlit as st
import psycopg2
import altair as alt
from dotenv import load_dotenv

load_dotenv('.env')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')


class DataLoader:
    @staticmethod
    def connect_to_db(db_host: str = DB_HOST, db_port: str = DB_PORT,
                      db_user: str = DB_USER, db_password: str = DB_PASSWORD,
                      db_name: str = DB_NAME):
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        return conn

    @staticmethod
    def fetch_data_from_tables(conn):

        demand_query = "SELECT * FROM Demand"
        gen_query = "SELECT * FROM Generation"
        cost_query = "SELECT * FROM Cost"
        carbon_query = "SELECT * FROM Carbon"
        demand_df = pd.read_sql_query(demand_query, conn)
        cost_df = pd.read_sql_query(cost_query, conn)
        gen_df = pd.read_sql_query(gen_query, conn)
        carbon_df = pd.read_sql_query(carbon_query, conn)

        if conn:
            conn.close()
            return gen_df, demand_df, cost_df, carbon_df
        print("Error")


class dashboard:
    def __init__(self) -> None:
        pass

    def carbon_plots(self, carbon_df: pd.DataFrame):
        carbon_bar_chart = alt.Chart(carbon_df).mark_bar().encode(alt.X('publish_time:T', title='Time'),
                                                                  y=alt.Y('forecast:Q', title='Carbon Intensity'), color='carbon_level').properties(width=650, height=400)
        return carbon_bar_chart

    def generation_fuel_type(self, gen_df):
        fuel_types = ["BIOMASS", "CCGT", "COAL", "NPSHYD",
                      "NUCLEAR", "OCGT", "OIL", "OTHER", "PS", "WIND"]
        df_fuel_types = gen_df[gen_df['fuel_type'].isin(
            fuel_types)]

        return alt.Chart(df_fuel_types[["publish_time", "generated", "fuel_type"]]).mark_line().encode(
            x="publish_time", y="generated", color="fuel_type").properties(width=1000, height=1000)

    # def generation_interconnection(self, gen_df):

    def generate_dashboard(self, gen_df, demand_df, cost_df, carbon_df):
        st.set_page_config(layout="wide")
        st.title("Energy Monitor")
        with st.container():
            st.header("Carbon Intensity Forecast")
            col1, col2 = st.columns(2)
            with col1:
                st.altair_chart(self.carbon_plots(carbon_df))
            with col2:
                st.header("What is Carbon Intensity?")
                st.write("The carbon intensity of electricity is a measure of how much CO2 emissions are produced per kilowatt hour of electricity consumed.The carbon intensity of electricity is sensitive to small changes in carbon-intensive generation. Carbon intensity varies due to changes in electricity demand, low carbon generation (wind, solar, hydro, nuclear, biomass) and conventional generation.")
                with st.expander("Find out more"):
                    st.write("TBC info")

        with st.container():
            st.header("Energy Generation by Fuel Type")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.altair_chart(self.generation_fuel_type(gen_df))
            with col2:
                with st.expander("Fuel Type Information"):
                    st.write("""
- **BIOMASS**: Organic materials used as a renewable energy source. It includes plant materials and animal waste that can be burned or converted to biofuels.
- **CCGT (Combined Cycle Gas Turbine)**: A form of highly efficient energy generation that combines a gas-fired turbine with a steam turbine. 
- **COAL**: Traditional fossil fuel used for generating electricity through combustion.
- **NPSHYD (Non-Pumped Storage Hydro)**: Refers to the conventional hydroelectric generation where water flows through turbines to generate power, with no pumped storage components.
- **NUCLEAR**: Power generated using nuclear reactions.Provides a stable base-load energy supply.
- **OCGT (Open Cycle Gas Turbine)**: A type of gas power plant where air is compressed, mixed with fuel, and burned in a simple cycle. It's less efficient than CCGT but is often quicker to start and stop.
- **OIL**: Oil-fired power plants burn petroleum or its derivatives to generate electricity. Similar to coal, it has large environmental impacts. 
- **OTHER**: This category usually encompasses any generation sources not specifically listed, which could include experimental or less common technologies like tidal or certain types of bio-gas plants.
- **PS (Pumped Storage)**: A type of hydropower generation where water is pumped to a higher elevation during low demand periods and released through turbines for electricity during high demand.
- **WIND**: The use of wind turbines to convert wind energy into electricity. It's a clean, renewable source increasingly used worldwide, particularly in areas with strong, consistent winds.
""")
        '''            
        with st.container():
            st.header("Energy Generation by Fuel Type")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.altair_chart(self.generation_fuel_type(gen_df))
            with col2:
                with st.expander("Fuel Type Information"):
                    st.write("")
        '''


if __name__ == "__main__":
    connection = DataLoader.connect_to_db()
    gen_df, demand_df, cost_df, carbon_df = DataLoader.fetch_data_from_tables(
        connection)
    energy_dashboard = dashboard()
    energy_dashboard.generate_dashboard(gen_df, demand_df, cost_df, carbon_df)
