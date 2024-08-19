"""
Test script for extract_production.py
"""
import datetime
import pandas as pd
from pipeline.transform import Transform

transform = Transform()


class TestTransform:
    def test_generation_transform_general(self, mock_gen_df):
        trans_df = transform.generation_transform(mock_gen_df)
        for row in trans_df:
            assert len(row) == 6
            assert row[1] in row[0]
            assert isinstance(row[2], str) == True
            assert row[3] in ['-', '+']
            assert isinstance(row[4], int) == True

    def test_generation_transform_gain_loss(self, mock_gen_df):
        trans_df = transform.generation_transform(mock_gen_df)
        assert trans_df[0][3] == '+'
        assert trans_df[1][3] == '-'
        assert trans_df[2][3] == '-'

    def test_generation_transform_valid_dates(self, mock_gen_df):
        trans_df = transform.generation_transform(mock_gen_df)
        for row in trans_df:
            time = datetime.datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ")
            assert isinstance(time, datetime.datetime) == True
            date = datetime.datetime.strptime(row[1], "%Y-%m-%d")
            assert isinstance(date, datetime.datetime) == True

    def test_demand_transform_general(self, mock_demand_df):
        trans_df = transform.demand_transform(mock_demand_df)
        for row in trans_df:
            assert len(row) == 2
            time = datetime.datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ")
            assert isinstance(time, datetime.datetime) == True
            assert isinstance(row[1], int) == True

    def test_cost_transform_general(self, mock_cost_df):
        trans_df = transform.cost_transform(mock_cost_df)
        for row in trans_df:
            assert len(row) == 4
            date = datetime.datetime.strptime(row[0], "%Y-%m-%d")
            assert isinstance(date, datetime.datetime) == True
            assert isinstance(row[1], int) == True
            assert isinstance(row[2], int) == True
            assert isinstance(row[3], int) == True

    def test_carbon_transform_general(self, mock_carbon_df):

        trans_df = transform.carbon_transform(mock_carbon_df)
        for row in trans_df:
            assert len(row) == 3
            time = datetime.datetime.strptime(row[0], "%Y-%m-%dT%H:%MZ")
            assert isinstance(time, datetime.datetime) == True
            assert isinstance(row[1], int)
            assert row[2] in ["very low", "low",
                              "moderate", "high", "very high"]

    def test_carbon_transform_general(self, mock_carbon_df):
        assert mock_carbon_df['carbon level'][2] == 'low'
        assert mock_carbon_df['carbon level'][2] == 'low'
        assert mock_carbon_df['carbon level'][2] == 'low'
        trans_df = transform.carbon_transform(mock_carbon_df)

        assert trans_df[0][2] == 'very low'
        assert trans_df[1][2] == 'low'
        assert trans_df[2][2] == 'high'

    def test_get_difference_of_dates(self, mock_demand_df, mock_gen_df):
        demand_tuple = transform.demand_transform(mock_demand_df)

        assert '2024-08-18T23:00:00Z' not in mock_demand_df['startTime']
        assert mock_demand_df['startTime'].size == 3
        gen_tuple = transform.generation_transform(mock_gen_df)
        data = {'generation': gen_tuple, 'demand': demand_tuple}
        data = transform.difference_of_dates(data)
        times = []
        for values in data['demand']:
            times.append(values[0])
        assert '2024-08-18T23:00:00Z' in times
        assert len(times) == 4
