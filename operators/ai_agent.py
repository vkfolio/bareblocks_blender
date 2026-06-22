# BareBlocks - the AI agent. Two phases with a human-in-the-loop:
#   1. PLAN  - the model returns a structured checklist (via a forced submit_plan tool). You
#              review / edit / uncheck steps in the panel.
#   2. BUILD - after you Approve, a ReAct loop executes the enabled steps via the tools,
#              streaming a live log; the whole build is one undo step.
#
# The HTTPS call runs on a background thread (Blender never freezes); a modal timer polls and
# executes tool calls on the main thread. urllib only - nothing to install.

import json
import threading
import urllib.request
import urllib.error

import bpy

from ..core.props import get_prefs
from . import ai_tools

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

PLAN_SYSTEM = (
    "You are BareBlocks Architect's planner. Given the user's request, call submit_plan with a "
    "SHORT ordered checklist of how you'll build it from the available greybox block types - "
    "each step naming the block type(s), rough count and placement/size. 4-10 concise steps. "
    "Use a believable human scale, keep pieces on the ground (z=0 plane) and avoid overlaps, "
    "and space repeats evenly. Plan only; the build happens later.\n\n"
    "Available block types (KEY (Label, kind, anchor): parameters):\n{catalog}"
)

SUBMIT_PLAN_TOOL = {"type": "function", "function": {
    "name": "submit_plan", "description": "Return the build plan as an ordered checklist.",
    "parameters": {"type": "object", "properties": {
        "steps": {"type": "array", "items": {"type": "string"},
                  "description": "ordered, short build steps"}}, "required": ["steps"]}}}


class _Holder:
    __slots__ = ("result", "error", "done")

    def __init__(self):
        self.result = None
        self.error = None
        self.done = False


def _request(api_key, model, messages, tools, holder, tool_choice="auto"):
    try:
        payload = {"model": model, "messages": messages}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OPENAI_URL, data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            holder.result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            detail = ""
        holder.error = f"HTTP {exc.code} {detail}"
    except Exception as exc:  # noqa: BLE001
        holder.error = str(exc)
    finally:
        holder.done = True


def _redraw(context):
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


def _status(context, text):
    try:
        context.scene.bareblocks.ai_status = text[:400]
    except Exception:
        pass
    _redraw(context)


def _log(context, line):
    sb = context.scene.bareblocks
    lines = (sb.ai_log + "\n" + line).strip().splitlines()
    sb.ai_log = "\n".join(lines[-12:])
    _redraw(context)


class BAREBLOCKS_OT_ai_run(bpy.types.Operator):
    bl_idname = "bareblocks.ai_run"
    bl_label = "BareBlocks AI"
    bl_description = "Plan, or build the approved plan, with the AI agent"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        items=[("PLAN", "Plan", "Make a checklist to review"),
               ("BUILD", "Build", "Execute the enabled plan steps with the tools")],
        default="PLAN", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def invoke(self, context, event):
        prefs = get_prefs(context)
        if not prefs or not prefs.openai_api_key.strip():
            self.report({"ERROR"}, "Set your OpenAI API key in BareBlocks add-on Preferences")
            return {"CANCELLED"}
        sb = context.scene.bareblocks
        prompt = sb.ai_prompt.strip()
        if not prompt:
            self.report({"ERROR"}, "Type a prompt first")
            return {"CANCELLED"}

        self._key = prefs.openai_api_key.strip()
        self._model = (prefs.openai_model or "gpt-4o").strip()
        self._max_steps = int(prefs.ai_max_steps)
        self._steps = 0
        self._holder = None
        self._tool_choice = "auto"

        if self.mode == "PLAN":
            self._tools = [SUBMIT_PLAN_TOOL]
            self._tool_choice = {"type": "function", "function": {"name": "submit_plan"}}
            sysmsg = PLAN_SYSTEM.format(catalog=ai_tools.type_catalog())
            self._messages = [{"role": "system", "content": sysmsg},
                              {"role": "user", "content": prompt}]
            _status(context, "Planning...")
        else:  # BUILD
            self._tools = ai_tools.tool_specs()
            plan_lines = [s.text for s in sb.ai_plan_steps if s.enabled and s.text.strip()]
            user = prompt
            if plan_lines:
                user += "\n\nApproved plan to follow:\n" + "\n".join(
                    f"{i + 1}. {t}" for i, t in enumerate(plan_lines))
            user += ("\n\nBuild it now by calling the tools; adjust positions/sizes to avoid "
                     "unwanted overlaps. Give a one-line summary when finished.")
            self._messages = [{"role": "system", "content": ai_tools.system_prompt()},
                              {"role": "user", "content": user}]
            sb.ai_log = ""
            _status(context, "Building...")

        self._start_request()
        self._timer = context.window_manager.event_timer_add(0.25, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def _start_request(self):
        self._holder = _Holder()
        threading.Thread(
            target=_request,
            args=(self._key, self._model, self._messages, self._tools, self._holder,
                  self._tool_choice),
            daemon=True).start()

    def _cleanup(self, context):
        if getattr(self, "_timer", None):
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    def _populate_plan(self, context, steps):
        sb = context.scene.bareblocks
        sb.ai_plan_steps.clear()
        for s in steps:
            item = sb.ai_plan_steps.add()
            item.text = str(s)
            item.enabled = True

    def modal(self, context, event):
        if event.type == "ESC":
            self._cleanup(context)
            _status(context, "Cancelled")
            return {"CANCELLED"}
        if event.type != "TIMER" or self._holder is None or not self._holder.done:
            return {"PASS_THROUGH"}

        if self._holder.error:
            self._cleanup(context)
            _status(context, "Error: " + self._holder.error)
            self.report({"ERROR"}, self._holder.error)
            return {"CANCELLED"}
        try:
            msg = self._holder.result["choices"][0]["message"]
        except Exception:
            self._cleanup(context)
            _status(context, "Error: unexpected API response")
            return {"CANCELLED"}

        # --- planning phase: parse submit_plan into editable steps ---
        if self.mode == "PLAN":
            self._cleanup(context)
            steps = []
            for tc in (msg.get("tool_calls") or []):
                if tc.get("function", {}).get("name") == "submit_plan":
                    try:
                        steps = json.loads(tc["function"]["arguments"]).get("steps", [])
                    except Exception:
                        steps = []
            if not steps and msg.get("content"):
                steps = [ln.lstrip("-*0123456789. ").strip()
                         for ln in msg["content"].splitlines() if ln.strip()]
            self._populate_plan(context, steps)
            _status(context, f"Plan ready ({len(steps)} steps) - review/edit, then Approve & Build.")
            return {"FINISHED"}

        # --- build phase: ReAct loop with live log ---
        tool_calls = msg.get("tool_calls") or []
        self._messages.append({"role": "assistant", "content": msg.get("content"),
                               "tool_calls": tool_calls or None})
        # Stream the model's reasoning/narration as it works.
        if msg.get("content"):
            _log(context, "* " + " ".join(msg["content"].split())[:90])
        if not tool_calls:
            self._cleanup(context)
            _status(context, msg.get("content") or "Done")
            return {"FINISHED"}

        for tc in tool_calls:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                args = {}
            try:
                result = ai_tools.execute_tool(context, fn.get("name", ""), args)
            except Exception as exc:  # noqa: BLE001
                result = "ERROR: " + str(exc)
            self._messages.append({"role": "tool", "tool_call_id": tc.get("id"),
                                   "content": str(result)})
            mark = "x" if str(result).startswith("ERROR") else "v"
            _log(context, f"[{mark}] {str(result)[:60]}")

        self._steps += 1
        if self._steps >= self._max_steps:
            self._cleanup(context)
            _status(context, f"Stopped at step cap ({self._max_steps}). Approve & Build to continue.")
            return {"FINISHED"}
        _status(context, f"Building... (round {self._steps})")
        self._start_request()
        return {"RUNNING_MODAL"}


class BAREBLOCKS_OT_ai_step_add(bpy.types.Operator):
    bl_idname = "bareblocks.ai_step_add"
    bl_label = "Add Step"
    bl_description = "Add a blank plan step"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.scene.bareblocks.ai_plan_steps.add().text = "New step"
        return {"FINISHED"}


class BAREBLOCKS_OT_ai_step_remove(bpy.types.Operator):
    bl_idname = "bareblocks.ai_step_remove"
    bl_label = "Remove Step"
    bl_description = "Remove this plan step"
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty(default=-1, options={"HIDDEN"})

    def execute(self, context):
        steps = context.scene.bareblocks.ai_plan_steps
        if 0 <= self.index < len(steps):
            steps.remove(self.index)
        return {"FINISHED"}


class BAREBLOCKS_OT_ai_clear(bpy.types.Operator):
    bl_idname = "bareblocks.ai_clear"
    bl_label = "Clear Plan"
    bl_description = "Clear the plan, log and status"
    bl_options = {"REGISTER"}

    def execute(self, context):
        sb = context.scene.bareblocks
        sb.ai_plan_steps.clear()
        sb.ai_log = ""
        sb.ai_status = ""
        return {"FINISHED"}


classes = [BAREBLOCKS_OT_ai_run, BAREBLOCKS_OT_ai_step_add,
           BAREBLOCKS_OT_ai_step_remove, BAREBLOCKS_OT_ai_clear]
