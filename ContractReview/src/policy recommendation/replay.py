import os
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
# 3363888e-7271-410e-90e3-20f9eafcb1ef
from QuoteManagement import quote_management_crew

def replay():
  """
  Replay the crew execution from a specific task.
  """
  task_id = 'a3cb08ec-85ba-4a8c-b5aa-f11985494077'
  try:
      quote_management_crew.crew().replay(task_id=task_id)

  except Exception as e:
      raise Exception(f"An error occurred while replaying the crew: {e}")
