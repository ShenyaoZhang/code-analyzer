import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def sample_python_code():
    """Fixture providing sample Python code for testing"""
    return """
def calculate_sum(a, b):
    '''Calculate sum of two numbers'''
    return a + b

def main():
    result = calculate_sum(5, 3)
    print(f"Result: {result}")
"""


@pytest.fixture
def sample_complex_code():
    """Fixture providing complex Python code for testing"""
    return """
def complex_function(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
            else:
                continue
        while x > 0:
            x -= 1
            try:
                result = 10 / x
            except ZeroDivisionError:
                break
    return x
"""


@pytest.fixture
def sample_insecure_code():
    """Fixture providing insecure Python code for testing"""
    return """
import os

password = "hardcoded-password"

def dangerous():
    user_input = input("Enter command: ")
    eval(user_input)
    os.system("rm -rf /tmp")
"""

