import yaml
import time
import aiohttp
import asyncio
import datetime
from collections import defaultdict

# Function to load configuration from the YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def get_method(endpoint):
    valFromFile = endpoint.get('method')
    # if no value in the file, we can assume that the correct method is GET
    return valFromFile if valFromFile != None else 'GET'

# Function to perform health checks
async def check_health_async(endpoint, session):
    try:
        url = endpoint['url']
        method = get_method(endpoint)
        headers = endpoint.get('headers')
        body = endpoint.get('body')
        # getting the current time to track request lifetime
        startTime = datetime.datetime.now()
        async with session.request(method, url, headers=headers, json=body, timeout=1) as response:
            elapsed = datetime.datetime.now() - startTime
            # UP requires a status code of 200-299 and a response time of less than 500ms
            if 200 <= response.status < 300 and elapsed.microseconds <= 500000:
                return "UP"
            else:
                return "DOWN"
    except TimeoutError: # we can assume with a timeout value that the endpoint is down per 500ms required response time
        return "DOWN"

# function for checking and tracking the result of an endpoint call
async def endpoint_check_async(endpoint, session, dict):
    domain = endpoint["url"].split("//")[-1].split("/")[0].split(":")[0]
    result = await check_health_async(endpoint, session)

    dict[domain]["total"] += 1
    if result == "UP":
        dict[domain]["up"] += 1

# async loop method for dispatching individual batches of monitored endpoints
async def monitor_loop_async(yamlConfig):
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})
    # using a single ClientSession per batch of endpoints (maybe this should be changed to be more performant?)
    # disabling ssl validation on the checks as the provided endpoints don't have valid certs, so any call would throw an except
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        await asyncio.gather(*(endpoint_check_async(endpoint, session, domain_stats) for endpoint in yamlConfig))

        # Log cumulative availability percentages
        for domain, stats in domain_stats.items():
            availability = round(100 * stats["up"] / stats["total"])
            print(f"{domain} has {availability}% availability percentage")

        print("---")

# Main function to monitor endpoints
def monitor_endpoints(file_path):
    # loading config once before executing - in the case that config is changed mid-run we'd have to introduce some way to reload
    config = load_config(file_path)

    while True:
        asyncio.run(monitor_loop_async(config))
        time.sleep(15)

# Entry point of the program
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")