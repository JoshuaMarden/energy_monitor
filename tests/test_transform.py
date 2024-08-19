"""
Test script for extract_production.py
"""
import pandas as pd
import pytest
from pipeline.transform import Transform

transform = Transform()


class TestTransform:
    def test_generation_transform(self):
        transform.generation_transform
