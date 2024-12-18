from crew_youtube_simple import YoutubeCrew

def replay():
    task_id = "c0d373ad-e088-41c5-9356-bd37902ca6b1"
    # inputs = {"instagram_username": "clubvipfinance"}  # Add any inputs if needed
    try:
        YoutubeCrew().crew().replay(task_id=task_id)
    except Exception as e:
        print(f"An error occurred while replaying the crew: {e}")

if __name__ == "__main__":
    replay()