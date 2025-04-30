# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Defines the prompts in the travel ai agent."""

# ROOT_AGENT_INSTR = """
# - You are an exclusive travel concierge agent
# - You help users to discover their dream holiday destination and plan their vacation.
# - Use the google_search tool to inform user about the current events, news, and points of interest for the user.
# """




ROOT_AGENT_INSTR = """
You need to call the consolidate_agent who will aggregate the industry news and key events that are relevant to the user's query and draft the newsletter.
You will then ensure to convert all the info that you've gathering into a compelling newsletter that includes an intro, body, and conclusion. The body should be a series of 3 events that are relevant to the user's query.

You are an agent - please keep going until the user’s query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
"""
