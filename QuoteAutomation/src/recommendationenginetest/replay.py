# 3363888e-7271-410e-90e3-20f9eafcb1ef
from ReceiveEmail import scheduler_crew
def replay():
  """
  Replay the crew execution from a specific task.
  """
  task_id = 'd224295e-4e46-4992-9a53-39c73c18a159'
#   inputs = {"topic": "CrewAI Training"}  # This is optional; you can pass in the inputs you want to replay; otherwise, it uses the previous kickoff's inputs.
  try:
      scheduler_crew.crew().replay(task_id=task_id)

  except Exception as e:
      raise Exception(f"An error occurred while replaying the crew: {e}")
