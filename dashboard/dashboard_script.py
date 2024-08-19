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
        raise ConnectionError("Failed to connect to Database")


class dashboard:
    def __init__(self) -> None:
        pass

    def carbon_plots(self, carbon_df: pd.DataFrame) -> alt.Chart:
        return alt.Chart(carbon_df).mark_bar().encode(alt.X('publish_time:T', title='Time'),
                                                      y=alt.Y('forecast:Q', title='Carbon Intensity'), color='carbon_level').properties(width=650, height=400)

    def time_of_lowest_carbon(self, carbon_df: pd.DataFrame):
        return carbon_df.loc[carbon_df["forecast"] == min(
            carbon_df["forecast"].values), "publish_time"].dt.time.iloc[0]

    def time_of_highest_carbon(self, carbon_df: pd.DataFrame):
        return carbon_df.loc[carbon_df["forecast"] == max(
            carbon_df["forecast"].values), "publish_time"].dt.time.iloc[0]

    def generation_fuel_type(self, gen_df: pd.DataFrame) -> alt.Chart:
        fuel_types = ["BIOMASS", "CCGT", "COAL", "NPSHYD",
                      "NUCLEAR", "OCGT", "OIL", "OTHER", "PS", "WIND"]
        df_fuel_types = gen_df[gen_df['fuel_type'].isin(
            fuel_types)]

        return alt.Chart(df_fuel_types[["publish_time", "generated", "fuel_type"]]).mark_line().encode(
            x=alt.X('publish_time:T', title='Time'), y=alt.Y('generated:Q', title='Energy Generated MW'),
            color="fuel_type").properties(width=1000, height=1000)

    def intensity_factors_df(self) -> alt.Chart:
        intensity_factors = {'Energy Source': ['Biomass', 'Coal', 'Dutch Imports', 'French Imports', 'Gas (Combined Cycle)', 'Gas (Open Cycle)',
                                               'Hydro', 'Irish Imports', 'Nuclear', 'Oil', 'Other', 'Pumped Storage', 'Solar', 'Wind'],
                             'Intensity (gCO₂/kWh)': [120, 937, 474, 53, 394, 651, 0, 458, 0, 935, 300, 0, 0, 0],
                             'Explanation': [
            'Uses organic materials which result in moderate emissions.',
            'High carbon emissions due to combustion of fossil fuels.',
            'Mixed source imports with moderate carbon impact.',
            'Imported nuclear and renewable energy with low emissions.',
            'More efficient gas-burning technology, lower emissions.',
            'Less efficient gas technology, higher emissions.',
            'Zero emissions as it relies on water flow.',
            'Mixed source imports with moderate carbon impact.',
            'Zero emissions from nuclear reactions.',
            'High emissions from oil combustion.',
            'Varied sources with different emissions levels.',
            'Storage method that does not emit carbon.',
            'Zero emissions harnessing solar power.',
            'Zero emissions capturing wind energy.']}

        return pd.DataFrame(intensity_factors)

    def generation_interconnection(self, gen_df: pd.DataFrame) -> alt.Chart:
        interconnector_mapping = {
            "INTELEC": "England(INTELEC)",
            "INTEW": "Wales(INTEW)",
            "INTFR": "France(INTFR)",
            "INTGRNL": "Greenland(INTGRNL)",
            "INTIFA2": "Ireland-Scotland(INTIFA2)",
            "INTIRL": "Ireland(INTIRL)",
            "INTNED": "Netherlands(INTNED)",
            "INTNEM": "Belgium(INTNEM)",
            "INTNSL": "Norway(INTNSL)",
            "INTVKL": "Denmark(INTVKL)"
        }

        df_interconnectors = gen_df[gen_df['fuel_type'].isin(
            interconnector_mapping)].copy()

        df_interconnectors['fuel_type'] = df_interconnectors['fuel_type'].map(
            interconnector_mapping)
        df_interconnectors.rename(
            columns={'fuel_type': 'country'}, inplace=True)

        return alt.Chart(df_interconnectors[["publish_time", "generated", "country"]]).mark_line().encode(x=alt.X('publish_time:T', title='Time'), y=alt.Y('generated:Q', title='Energy Generated MW'), color="country").properties(width=1400, height=1000)

    def generate_dashboard(self, gen_df: pd.DataFrame, demand_df: pd.DataFrame, cost_df: pd.DataFrame, carbon_df: pd.DataFrame):
        st.set_page_config(layout="wide")
        st.title("Energy Monitor")
        with st.container():
            st.header("Carbon Intensity Forecast")
            col1, col2 = st.columns(2)
            with col1:
                st.altair_chart(self.carbon_plots(carbon_df))
                carbon_container = st.container(border=True)
                with carbon_container:
                    low_col, high_col = carbon_container.columns(2)
                    with low_col:
                        st.metric(label="Lowest Carbon Footprint at:", value=f"{self.time_of_lowest_carbon(
                            carbon_df)}", delta=f"{min(carbon_df["forecast"].values)}")
                    with high_col:
                        st.metric(label="Highest Carbon Footprint at:", value=f"{
                            self.time_of_highest_carbon(carbon_df)}", delta=f"{max(carbon_df["forecast"].values)}", delta_color="inverse")
            with col2:
                st.header("What is Carbon Intensity?")
                st.write("The carbon intensity of electricity is a measure of how much CO2 emissions are produced per kilowatt hour of electricity consumed.The carbon intensity of electricity is sensitive to small changes in carbon-intensive generation. Carbon intensity varies due to changes in electricity demand, low carbon generation (wind, solar, hydro, nuclear, biomass) and conventional generation.")
                with st.expander("Find out more"):
                    Method_tab, Factors_tab = st.tabs(
                        ["Methodology", "Intensity Factors"])
                    with Method_tab:
                        st.write("The demand and generation by fuel type (gas, coal, wind, nuclear, solar etc.) for each region is forecast several days ahead at 30-min temporal resolution using an ensemble of state-of-the-art supervised Machine Learning (ML) regression models. An advanced model ensembling technique is used to blend the ML models to generate a new optimised meta-model. The forecasts are updated every 30 mins using a nowcasting technique to adjust the forecasts a short period ahead. The carbon intensity factors are applied to each technology type for each import generation mix to calculate the forecast")
                    with Factors_tab:
                        st.table(self.intensity_factors_df())

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

        with st.container():
            st.header("Where is your energy coming from ? ")
            st.write("Interconnectors are high-voltage links allowing electricity to flow between regions or countries, providing crucial flexibility and reliability to power supplies. They help balance energy demand and supply, integrate renewable energy sources, and enhance grid resilience and sustainability. This leads to more stable electricity prices and a more reliable power supply for everyone.")
            st.altair_chart(self.generation_interconnection(gen_df))


if __name__ == "__main__":
    connection = DataLoader.connect_to_db()
    gen_df, demand_df, cost_df, carbon_df = DataLoader.fetch_data_from_tables(
        connection)
    energy_dashboard = dashboard()
    energy_dashboard.generate_dashboard(gen_df, demand_df, cost_df, carbon_df)
