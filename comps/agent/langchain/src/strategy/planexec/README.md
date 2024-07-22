# Plan Execute

This strategy is a practise provided with [LangGraph](https://github.com/langchain-ai/langgraph/blob/main/examples/plan-and-execute/plan-and-execute.ipynb?ref=blog.langchain.dev)

1. Planner

   Plan steps to achieve final Goal => Goto "Executor"

2. Executor:

   Leverage React Agent Executor to complete steps one by one => Goto "Planner"

3. Replanner:

   Judge on executor result and provide response => Goto "CompletionChecker"

4. CompletionChecker:

   Judge on Replanner output

   - option plan_executor: Goto "Executor"
   - option END: Complete the query with Final answer.

![PlanExecute](https://raw.githubusercontent.com/langchain-ai/langgraph/3a53843185d64a2759fb422c74e967d462315246/examples/plan-and-execute/img/plan-and-execute.png)
