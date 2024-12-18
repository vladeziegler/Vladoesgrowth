from crew_youtube_simple import YoutubeCrew

def replay():
    task_id = "your_task_id"
    try:
        YoutubeCrew().crew().replay(task_id=task_id)
    except Exception as e:
        print(f"An error occurred while replaying the crew: {e}")

if __name__ == "__main__":
    replay()