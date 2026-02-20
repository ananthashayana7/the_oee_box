from fpdf import FPDF
import time
from backend.machine_manager import machine_manager
from backend.database import db_manager

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Universal OEE Interface - Plant Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

async def generate_plant_report(filename="report.pdf"):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    # Date
    pdf.cell(0, 10, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.ln(5)

    # Executive Summary
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Executive Summary", 0, 1)
    pdf.set_font('Arial', '', 11)

    machines = machine_manager.get_all_states()
    if not machines:
        pdf.cell(0, 10, "No active machines connected.", 0, 1)
    else:
        pdf.cell(0, 10, f"Total Machines Online: {len(machines)}", 0, 1)

        # Calculate Aggregates
        avg_oee = sum(m["oee"]["oee"] for m in machines.values()) / len(machines)
        avg_trust = sum(m["oee"].get("trust", 1.0) for m in machines.values()) / len(machines)

        pdf.cell(0, 10, f"Plant Average OEE: {avg_oee:.2f}%", 0, 1)
        pdf.cell(0, 10, f"Data Trust Index: {avg_trust*100:.1f}%", 0, 1)
    pdf.ln(10)

    # Machine Details
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Machine Status", 0, 1)
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Machine ID', 1)
    pdf.cell(30, 10, 'Status', 1)
    pdf.cell(30, 10, 'OEE', 1)
    pdf.cell(30, 10, 'Trust', 1)
    pdf.cell(60, 10, 'Virtual Sensors', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 10)
    for mid, state in machines.items():
        data = state["data"]
        oee = state["oee"]

        status_map = {0: "STOPPED", 1: "RUNNING", 2: "FAULT"}
        status_code = data.get("state_code", 0)
        status_text = status_map.get(status_code, "UNKNOWN")

        virtual_count = len(state.get("virtual_keys", []))

        pdf.cell(40, 10, mid.upper(), 1)
        pdf.cell(30, 10, status_text, 1)
        pdf.cell(30, 10, f"{oee['oee']}%", 1)
        pdf.cell(30, 10, f"{oee.get('trust', 1.0)*100:.0f}%", 1)
        pdf.cell(60, 10, f"{virtual_count} Active", 1)
        pdf.ln()

    pdf.ln(10)

    # Recent Alerts
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Recent Alerts", 0, 1)
    pdf.set_font('Arial', '', 10)

    alerts = await db_manager.get_active_alerts()
    if not alerts:
        pdf.cell(0, 10, "No active alerts.", 0, 1)
    else:
        for alert in alerts:
            ts = time.strftime('%H:%M:%S', time.localtime(alert['timestamp']))
            pdf.cell(0, 10, f"[{ts}] {alert['severity'].upper()}: {alert['message']}", 0, 1)

    pdf.output(filename, 'F')
    return filename
