import requests

def main():
    response = requests.get("http://localhost:8000/flight_plan/1ddfb7e7-34ab-4158-9454-ee21bb8d93b5/scheduled_passes").json()
    print("Scheduled Passes: " + str(response))


if __name__ == "__main__":
    main()