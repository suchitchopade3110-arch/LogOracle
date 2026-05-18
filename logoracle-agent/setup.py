from setuptools import setup, find_packages

setup(
    name="logoracle-agent",
    version="0.1.0",
    description="LogOracle local agent — tails logs and streams to LogOracle backend",
    author="LogOracle Team",
    packages=find_packages(include=["logoracle_agent", "logoracle_agent.*", "logoracle_sdk", "logoracle_sdk.*"]),
    install_requires=[
        "httpx>=0.27.0",
        "watchdog>=4.0.0",
        "psutil>=5.9.0",
        "rich>=13.0.0",
        "click>=8.1.0",
        "textual>=0.86.0",
    ],
    entry_points={
        "console_scripts": [
            "logoracle-agent=logoracle_agent.main:cli",
        ]
    },
    python_requires=">=3.10",
)
