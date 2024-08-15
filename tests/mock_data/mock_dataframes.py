import pandas as pd

def get_simple_mock_dataframe() -> pd.DataFrame:
    data = {
        'column1': [1, 2, 3],
        'column2': ['sherbet', 'liquorice', 'bon-bon']
    }
    return pd.DataFrame(data)