import logging
import asyncio
import os
import google.generativeai as genai
from backend.mqtt_client import mqtt_service

logger = logging.getLogger("governor")

class AutonomousGovernor:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.llm = genai.GenerativeModel('gemini-pro')
            logger.info("Governor: Active (Gemini Connected)")
        else:
            self.llm = None
            logger.warning("Governor: Passive (No API Key)")

        # State tracking to prevent oscillating commands
        self.machine_health_state = {} # {machine_id: "status"}
        self.last_action_time = {}

    async def evaluate_and_act(self, machine_id, telemetry_batch, oee_score):
        """
        Analyzes a 30-second binary snapshot and involuntarily triggers control actions.
        """
        if not self.llm:
            return

        # 1. Summarize the Batch
        # Calculate mean RMS and Vibration Peaks
        current_peaks = [max([r.get(f"current_p{i+1}", 0) for r in telemetry_batch]) for i in range(3)]
        temp_avg = sum([r.get("temperature", 0) for r in telemetry_batch]) / len(telemetry_batch)

        summary = f"""
        Machine: {machine_id}
        OEE: {oee_score}%
        Avg Temp: {temp_avg:.1f}C
        Peak Currents: {current_peaks}
        State: {telemetry_batch[-1].get('state_code')}
        """

        prompt = f"""
        You are an Autonomous Industrial Governor.
        Your job is to protect the machine and optimize value autonomously.

         telemetry snapshot:
        {summary}

        Rules:
        1. If Temp > 80C or Current > 100A, result must be "STOP".
        2. If OEE < 50% and State is Running, result must be "OPTIMIZE".
        3. If normal, result is "MAINTAIN".

        Output ONLY one word: STOP, OPTIMIZE, or MAINTAIN.
        """

        try:
            # Generate Decision
            # In production, we might batch this or run less frequently to save quota
            response = self.llm.generate_content(prompt)
            decision = response.text.strip().upper()

            logger.info(f"Governor Analysis for {machine_id}: {decision}")

            # Execute Action (Involuntary)
            if decision in ["STOP", "OPTIMIZE"]:
                await self.execute_command(machine_id, decision)

        except Exception as e:
            logger.error(f"Governor Logic Failed: {e}")

    async def execute_command(self, machine_id, command):
        target = f"factory/line1/{machine_id}/command"
        payload = {"command": command, "source": "GOVERNOR_AI"}

        # Publish directly via MQTT
        mqtt_service.publish(target, payload)

        # Log to Audit (We need to import db_manager carefully to avoid circular imports, or pass it in)
        from backend.database import db_manager
        await db_manager.log_audit("AUTONOMOUS_ACTION", "GOVERNOR", f"Involuntary Action: {command}", signature="AI_SIGNED")
        logger.warning(f"INVOLUNTARY ACTION TAKEN: {command} on {machine_id}")

governor = AutonomousGovernor()
