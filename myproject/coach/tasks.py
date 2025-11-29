# # coach/tasks.py
# from celery import shared_task
# from django.core.management import call_command
# import logging

# logger = logging.getLogger(__name__)

# @shared_task
# def run_coach_agent_task():
#     try:
#         logger.info("Starting run_coach_agent")
#         call_command('run_coach_agent')
#         logger.info("run_coach_agent finished")
#     except Exception:
#         logger.exception("run_coach_agent failed")
#         raise

